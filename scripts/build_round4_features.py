"""Build Round-4 label-free candidate features H15-H18 (preregistered).

Register: docs/hypotheses-round4.md (written BEFORE this file).
Uses only supplied bands from data/training_features.tif. No labels, no fold
assignments, no external data, no model output, no coordinates.

Channels in data/round4_features.npy (float32, (H, W, 4)):
  0 H15 coincident multi-physics boundary alignment (B15/B13/B17/B2)
  1 H16 strain-gradient block-boundary ridges (B8/B7)
  2 H17 gravity VG zero-contour x |HG| ridge coincidence (B11/B18)
  3 H18 tc total-curvature lineament topology (B6)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, maximum_filter, minimum_filter, uniform_filter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
FEATURES = ROOT / "data/training_features.tif"
OUT = ROOT / "data/round4_features.npy"
SIDECAR = ROOT / "evidence/round4-feature-build.json"

# 0-based positions in the official 19-band supplied raster.
RTP, TC, SHEAR, DILATE = 1, 5, 6, 7
VG, ISOGRAV = 10, 12
DTB, COND, HG = 14, 16, 17


def robust_unit(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    q50, q95 = np.percentile(a[valid], [50, 95])
    return np.clip((a - q50) / (q95 - q50 + 1e-12), 0.0, 1.0)


def zplus(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    med = float(np.median(a[valid]))
    iqr = float(np.subtract(*np.percentile(a[valid], [75, 25])))
    return np.clip((a - med) / (iqr + 1e-9), 0, None)


def line_kernels() -> list[np.ndarray]:
    h = np.zeros((9, 9), dtype="float64")
    h[4, :] = 1 / 9
    v = h.T.copy()
    d1 = np.eye(9, dtype="float64") / 9
    d2 = np.fliplr(d1)
    return [h, v, d1, d2]


def line_max(a: np.ndarray) -> np.ndarray:
    return np.maximum.reduce([convolve(a, k, mode="nearest") for k in line_kernels()])


def unit_gradients(f: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy, gx = np.gradient(f.astype("float64"))
    m = np.sqrt(gx * gx + gy * gy)
    s = np.maximum(m, 1e-12)
    return gy / s, gx / s, m


def build_h15(dtb: np.ndarray, isograv: np.ndarray, cond: np.ndarray,
              rtp: np.ndarray, valid: np.ndarray) -> np.ndarray:
    fields = [unit_gradients(f) for f in (dtb, isograv, cond, rtp)]
    uy = [u for u, _, _ in fields]
    ux = [u for _, u, _ in fields]
    mags = [zplus(m, valid) for _, _, m in fields]
    agree = np.zeros(dtb.shape, dtype="float64")
    n = 0
    for i in range(4):
        for j in range(i + 1, 4):
            agree += np.abs(uy[i] * uy[j] + ux[i] * ux[j])
            n += 1
    agree /= n
    joint = np.minimum.reduce(mags)
    out = robust_unit(line_max(agree * np.clip(joint, 0, 1)), valid)
    return out.astype("float32")


def build_h16(dilate: np.ndarray, shear: np.ndarray, valid: np.ndarray) -> np.ndarray:
    _, _, md = unit_gradients(dilate)
    _, _, ms = unit_gradients(shear)
    out = robust_unit(line_max(zplus(md, valid) + zplus(ms, valid)), valid)
    return out.astype("float32")


def build_h17(vg: np.ndarray, hg: np.ndarray, valid: np.ndarray) -> np.ndarray:
    zero = (maximum_filter(vg, size=3, mode="nearest") > 0) & (
        minimum_filter(vg, size=3, mode="nearest") < 0)
    if not bool(zero[valid].any()):
        raise ValueError("H17 guard: no VG sign change in footprint; refusing "
                         "a degenerate all-zero feature")
    strength = np.clip(zplus(np.abs(hg), valid), 0, 1)
    density = uniform_filter((zero & valid).astype("float32") * strength, 5)
    out = robust_unit(density, valid)
    return out.astype("float32")


def build_h18(tc: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = robust_unit(line_max(zplus(tc, valid)), valid)
    return out.astype("float32")


def main() -> None:
    with rasterio.open(TEMPLATE) as ds:
        valid = ds.read_masks(1) > 0
        template_sha = sha(TEMPLATE)
    with rasterio.open(FEATURES) as ds:
        feats_sha = sha(FEATURES)
        bands = {i: ds.read(i + 1, masked=True).filled(np.nan).astype("float64")
                 for i in (RTP, TC, SHEAR, DILATE, VG, ISOGRAV, DTB, COND, HG)}
    medians = {}
    for i, a in bands.items():
        m = float(np.nanmedian(a[valid]))
        medians[i] = m
        a[~np.isfinite(a)] = m

    h15 = build_h15(bands[DTB], bands[ISOGRAV], bands[COND], bands[RTP], valid)
    h16 = build_h16(bands[DILATE], bands[SHEAR], valid)
    h17 = build_h17(bands[VG], bands[HG], valid)
    h18 = build_h18(bands[TC], valid)
    stack = np.stack([h15, h16, h17, h18], axis=-1).astype("float32")
    stack[:, :4, :] = stack[:, -4:, :] = 0.0
    stack[:4, :, :] = stack[-4:, :, :] = 0.0
    stack[~valid] = 0.0
    if not np.isfinite(stack[valid]).all():
        raise ValueError("non-finite Round-4 values inside footprint")
    np.save(OUT, stack, allow_pickle=False)

    evidence = {
        "built_by": "scripts/build_round4_features.py",
        "preregistered_register": "docs/hypotheses-round4.md",
        "code_sha256": sha(Path(__file__)),
        "output": {"file": "data/round4_features.npy", "sha256": sha(OUT),
                   "shape": list(stack.shape), "dtype": "float32",
                   "channels": {0: "H15 coincident multi-physics boundary alignment",
                                1: "H16 strain-gradient block-boundary ridges",
                                2: "H17 gravity VG zero-contour x |HG| coincidence",
                                3: "H18 tc lineament topology"}},
        "inputs": {"training_features.tif": feats_sha,
                   "sample_submission.tif": template_sha},
        "official_band_indices_1_based": {"rtp": RTP + 1, "tc": TC + 1,
                                          "geod_shearrate": SHEAR + 1,
                                          "geod_dilaterate": DILATE + 1,
                                          "iso_grav_anom_vg": VG + 1,
                                          "iso_grav_anom": ISOGRAV + 1,
                                          "depth_to_base_surf": DTB + 1,
                                          "cond_surf": COND + 1,
                                          "iso_grav_anom_hg": HG + 1},
        "parameters": {"line_aggregation_pixels": 9, "orientations": 4,
                       "h17_zero_window_pixels": 3, "h17_density_window_pixels": 5,
                       "boundary_zero_pixels": 4,
                       "normalization": "robust [p50,p95]->[0,1] on valid footprint"},
        "within_footprint_median_imputation": {str(k): v for k, v in medians.items()},
        "labels_used": False,
    }
    SIDECAR.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({k: evidence[k] for k in ("output", "labels_used")}, indent=2))


if __name__ == "__main__":
    main()
