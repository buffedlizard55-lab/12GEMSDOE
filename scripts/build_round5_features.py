"""Build Round-5 label-free candidate features H20-H23 (preregistered).

Register: docs/hypotheses-round5.md (written BEFORE this file).
Uses only supplied bands from data/training_features.tif. No labels, no fold
assignments, no external data, no model output, no coordinates, no catalogue
distances.

Channels in data/round5_features.npy (float32, (H, W, 4)):
  0 H20 magnetic-basement relief step      ||grad(smooth5(tc))||
  1 H21 two-depth-surface step coincidence axial(tc,dtb) * min(edge_tc, edge_dtb)
  2 H22 local singularity exponent of tc   |alpha - 2| over dyadic windows
  3 H23 asymmetric-step (monocline) dtb    |f-b| / (|f-c| + |b-c|), max over 4 axes

Note on `tc` (B5): identity check C3 (evidence/round5-identity-checks.json)
shows tc is strictly positive, median 18.48, max 88.57, correlation -0.0012 with
|tilt angle|. That is inconsistent with the raster band description ("Tilt angle
or total curvature") and consistent with the official problem-description layer
"top-of-crustal magnetic source depth estimate". H20/H21/H22 treat it as a
depth surface, which is the reading the data supports.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import shift as ndshift, uniform_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
FEATURES = ROOT / "data/training_features.tif"
OUT = ROOT / "data/round5_features.npy"
SIDECAR = ROOT / "evidence/round5-feature-build.json"

TC, DTB = 5, 14          # 0-based positions in the official 19-band raster
SMOOTH = 5
DYO = (1, 2, 4, 8, 16)   # dyadic windows for the singularity exponent
AXES = ((1, 0), (0, 1), (1, 1), (1, -1))
LAGS = (2, 4)


def robust_unit(a, valid):
    q50, q95 = np.percentile(a[valid], [50, 95])
    return np.clip((a - q50) / (q95 - q50 + 1e-12), 0.0, 1.0).astype("float32")


def main() -> None:
    with rasterio.open(TEMPLATE) as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(FEATURES) as s:
        tc = s.read(TC + 1, masked=True).filled(np.nan).astype("float64")
        dtb = s.read(DTB + 1, masked=True).filled(np.nan).astype("float64")
    stats = {}
    for name, arr in (("tc", tc), ("depth_to_base_surf", dtb)):
        m = float(np.nanmedian(arr[valid]))
        arr[~np.isfinite(arr)] = m
        stats[name] = {"median_imputation": m,
                       "nan_inside_footprint_filled": int((~np.isfinite(arr)).sum())}

    tc_s = uniform_filter(tc, SMOOTH)
    dtb_s = uniform_filter(dtb, SMOOTH)

    # ---- H20 magnetic-basement relief step ---------------------------------
    gy, gx = np.gradient(tc_s)
    g_tc = np.sqrt(gx * gx + gy * gy)
    h20 = g_tc.astype("float32")

    # ---- H21 two-depth-surface step coincidence -----------------------------
    dy2, dx2 = np.gradient(dtb_s)
    g_dtb = np.sqrt(dx2 * dx2 + dy2 * dy2)
    axial = np.abs((gx * dx2 + gy * dy2) / (g_tc * g_dtb + 1e-12))
    h21 = (axial * np.minimum(robust_unit(g_tc.astype("float32"), valid),
                              robust_unit(g_dtb.astype("float32"), valid))).astype("float32")

    # ---- H22 local singularity exponent of tc -------------------------------
    a = np.abs(tc_s)
    Y = np.stack([np.log(np.maximum(uniform_filter(a, w) if w > 1 else a, 1e-12))
                  for w in DYO])
    X = np.log(np.array(DYO, dtype="float64"))
    Xc = X - X.mean()
    alpha = (Xc[:, None, None] * Y).sum(0) / (Xc ** 2).sum()
    h22 = np.abs(alpha - 2.0).astype("float32")
    del Y, alpha, a

    # ---- H23 asymmetric-step (monocline) detector on dtb ---------------------
    # scipy.ndimage.shift takes SCALAR per-axis shifts, so the four principal
    # axes are handled explicitly (the first implementation attempt passed
    # array-valued shifts, which is unsupported and silently produced a
    # constant field; see docs/hypotheses-round5.md section 6).
    h23 = np.zeros(shape, dtype="float64")
    for sy, sx in AXES:
        n = float(np.hypot(sy, sx))
        for lag in LAGS:
            f = ndshift(dtb_s, (-sy * lag / n, -sx * lag / n), order=1, mode="nearest")
            b = ndshift(dtb_s, (sy * lag / n, sx * lag / n), order=1, mode="nearest")
            asym = np.abs(f - b) / (np.abs(f - dtb_s) + np.abs(b - dtb_s) + 1e-6)
            h23 = np.maximum(h23, asym)
            del f, b, asym
    h23 = h23.astype("float32")

    out = np.stack([h20, h21, h22, h23], axis=-1).astype("float32")
    assert out.shape == (*shape, 4), out.shape
    for i in range(4):
        ch = out[:, :, i]
        if not np.isfinite(ch[valid]).all():
            raise ValueError(f"channel {i} has non-finite values inside the footprint")
        ch[~valid] = 0.0
    np.save(OUT, out)

    # cross-correlation certification against rounds 1-4
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    r4path = ROOT / "data/round4_features.npy"
    r4 = np.lib.format.open_memmap(str(r4path), mode="r") if r4path.exists() else None
    rng = np.random.default_rng(12027)
    idx = rng.choice(np.flatnonzero(valid.ravel()), 400000, replace=False)
    names = ["H20_magnetic_basement_step", "H21_two_depth_step_coincidence",
             "H22_singularity_tc", "H23_step_asymmetry_dtb"]
    cross, detail = {}, {}
    for i, nm in enumerate(names):
        cf = out[:, :, i].ravel()[idx].astype("float64")
        row = {}
        for j in range(cube.shape[2]):
            row[f"r12_ch{j:02d}"] = round(float(np.corrcoef(
                cf, cube[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        if r4 is not None:
            for j in range(r4.shape[2]):
                row[f"r4_ch{j}"] = round(float(np.corrcoef(
                    cf, r4[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        for j, other in enumerate(names):
            if j != i:
                row[f"r5_{other}"] = round(float(np.corrcoef(
                    cf, out[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        best = max(row.items(), key=lambda kv: abs(kv[1]))
        cross[nm] = {"max_abs_corr_channel": best[0], "max_abs_corr": round(abs(best[1]), 4)}
        detail[nm] = row

    side = {
        "built_by": "scripts/build_round5_features.py",
        "code_sha256": sha(Path(__file__)),
        "inputs": {"training_features": sha(FEATURES), "sample_submission": sha(TEMPLATE)},
        "output": {"file": str(OUT.relative_to(ROOT)), "shape": list(out.shape),
                   "sha256": sha(OUT), "dtype": "float32"},
        "band_identity_note": (
            "tc (B5) is treated as the official 'top-of-crustal magnetic source "
            "depth estimate', not the raster description's 'tilt angle or total "
            "curvature'; see evidence/round5-identity-checks.json C3."),
        "channels": dict(zip(range(4), names)),
        "input_stats": stats,
        "cross_correlation": cross,
        "cross_correlation_detail": detail,
        "distinctness_rule": "max |corr| vs every round-1..4 channel; <0.50 distinct",
        "labels_used": False,
    }
    SIDECAR.write_text(json.dumps(side, indent=2))
    print(json.dumps({"output_sha256": side["output"]["sha256"],
                      "channels": side["channels"],
                      "cross_correlation": cross}, indent=2))


if __name__ == "__main__":
    main()
