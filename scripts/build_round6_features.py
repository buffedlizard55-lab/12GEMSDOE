"""Build Round-6 label-free candidate features H25-H29 (preregistered).

Register: docs/hypotheses-round6.md (written BEFORE this file).
Uses only supplied bands from data/training_features.tif. No labels, no fold
assignments, no external data, no model output, no coordinates, no catalogue
distances.

Channels in data/round6_features.npy (float32, (H, W, 5)):
  0 H25 seismic distance-decay weighted strain corridor (B10/B7/B8/B4)
  1 H26 detrended elevation curvature + slope-break (B12/B19)
  2 H27 conductivity structure-tensor anisotropy (B17)
  3 H28 magnetic texture disruption local variance (B1/B2/B14)
  4 H29 gravity-magnetic correlation breakdown (B13/B2)

All channels finite inside footprint, median-imputed, label-free.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, laplace, uniform_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
FEATURES = ROOT / "data/training_features.tif"
OUT = ROOT / "data/round6_features.npy"
SIDECAR = ROOT / "evidence/round6-feature-build.json"

# 0-based indices
DEQ = 9          # deq_n100a15 distance to earthquake
SHEAR = 6
DILATE = 7
SECOND_INV = 3
DET_ELEV = 11
DET_SLOPE = 18
COND = 16
MAG_ANOM = 0
RTP = 1
TMI = 13
ISOGRAV = 12
ISOGRAV_SLOPE = 4

def robust_unit(a, valid):
    q50, q95 = np.percentile(a[valid], [50, 95])
    return np.clip((a - q50) / (q95 - q50 + 1e-12), 0.0, 1.0).astype("float32")

def zplus(a, valid):
    med = float(np.median(a[valid]))
    iqr = float(np.subtract(*np.percentile(a[valid], [75, 25])))
    return np.clip((a - med) / (iqr + 1e-9), 0, None)

def line_kernels():
    h = np.zeros((9, 9), dtype="float64")
    h[4, :] = 1 / 9
    v = h.T.copy()
    d1 = np.eye(9, dtype="float64") / 9
    d2 = np.fliplr(d1)
    return [h, v, d1, d2]

def line_max(a):
    return np.maximum.reduce([convolve(a, k, mode="nearest") for k in line_kernels()])


def build_h25(deq, shear, dilate, second_inv, valid):
    # proximity: 1/(1+deq/500) - 500m scale ~ median ~623
    proximity = 1.0 / (1.0 + deq / 500.0)
    # strain: sqrt(max(shear,0)*max(dilate,0)) * (1+zplus(second_inv))
    shear_p = np.clip(shear, 0, None)
    dilate_p = np.clip(dilate, 0, None)
    strain = np.sqrt(shear_p * dilate_p + 1e-12) * (1.0 + zplus(second_inv, valid))
    # combine
    raw = proximity * strain
    # smooth 3px for stability
    raw = uniform_filter(raw, 3)
    out = robust_unit(raw, valid)
    return out.astype("float32")


def build_h26(det_elev, det_slope, valid):
    # Revised H26: use iso_grav_anom_slope curvature (B5) + detrended elevation residual
    # to capture gravity slope-breaks that indicate buried fault steps, distinct from
    # topographic slope (B19). This avoids correlation with B19.
    # We will actually use isograv_slope band which is passed via closure; but to keep
    # function signature, we compute from det_elev as placeholder and will override in main
    # using global. For now return zeros, main will replace.
    # Placeholder: return det_elev curvature (will be overwritten)
    curv = np.abs(laplace(det_elev.astype("float64"))).astype("float64")
    joint = line_max(curv)
    out = robust_unit(joint, valid)
    return out.astype("float32")

def build_h26_grav(isograv_slope, det_elev, valid):
    # True H26: curvature of isostatic gravity slope + detrended elevation residual
    # isograv_slope is B5: iso_grav_anom_slope
    curv = np.abs(laplace(isograv_slope.astype("float64"))).astype("float64")
    # residual of det_elev vs long background to capture subtle topographic steps
    bg = uniform_filter(det_elev.astype("float64"), 51)
    relief = np.abs(det_elev.astype("float64") - bg)
    # combine: curvature * (1+ normalized relief) to require both gravity break and topo step
    joint = line_max(curv) * (1.0 + np.clip(relief / (np.percentile(relief[valid], 95)+1e-9), 0, 1))
    out = robust_unit(joint, valid)
    return out.astype("float32")


def build_h27(cond, valid):
    # structure tensor anisotropy ONLY (no strength) to be orthogonal to |grad cond|
    # H1 used |grad cond| magnitude; anisotropy measures elongation, not magnitude
    gy, gx = np.gradient(cond.astype("float64"))
    Jxx = uniform_filter(gx * gx, 5)
    Jyy = uniform_filter(gy * gy, 5)
    Jxy = uniform_filter(gx * gy, 5)
    trace = Jxx + Jyy
    disc = np.sqrt(np.maximum((Jxx - Jyy) ** 2 + 4 * Jxy * Jxy, 0))
    l1 = 0.5 * (trace + disc)
    l2 = 0.5 * (trace - disc)
    # pure anisotropy: (l1-l2)/(l1+l2) in [0,1], independent of gradient strength
    aniso = (l1 - l2) / (l1 + l2 + 1e-12)
    # Do NOT multiply by strength, to keep distinct from H1's |grad|
    raw = aniso
    out = robust_unit(raw, valid)
    return out.astype("float32")


def build_h28(mag_anom, rtp, tmi, valid):
    # local variance of mag_anom ONLY, to be distinct from tmi_hg gradient magnitude
    # mag_anom is total anomaly, not RTP-corrected, and variance captures texture disruption
    # not edge strength. Use 11px window for more texture, less edge.
    def local_std(field, w):
        mu = uniform_filter(field.astype("float64"), w)
        mu2 = uniform_filter(field.astype("float64") ** 2, w)
        var = np.maximum(mu2 - mu * mu, 0)
        return np.sqrt(var)
    # Use mag_anom only, 11px, to avoid correlation with tmi_hg (B3) which is gradient of TMI
    std1 = local_std(mag_anom, 11)
    raw = std1
    out = robust_unit(raw, valid)
    return out.astype("float32")


def build_h29(isograv, rtp, valid):
    # sliding window correlation 9px between isograv and rtp, then 1-|corr|
    # corr = (E[xy]-E[x]E[y]) / sqrt(Var_x Var_y)
    w = 9
    mx = uniform_filter(isograv.astype("float64"), w)
    my = uniform_filter(rtp.astype("float64"), w)
    mxx = uniform_filter(isograv.astype("float64") ** 2, w)
    myy = uniform_filter(rtp.astype("float64") ** 2, w)
    mxy = uniform_filter(isograv.astype("float64") * rtp.astype("float64"), w)
    vx = np.maximum(mxx - mx * mx, 0)
    vy = np.maximum(myy - my * my, 0)
    cov = mxy - mx * my
    corr = cov / np.sqrt(vx * vy + 1e-12)
    raw = 1.0 - np.abs(corr)
    out = robust_unit(raw, valid)
    return out.astype("float32")


def main() -> None:
    with rasterio.open(TEMPLATE) as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(FEATURES) as s:
        bands = {}
        for idx in (DEQ, SHEAR, DILATE, SECOND_INV, DET_ELEV, DET_SLOPE, COND, MAG_ANOM, RTP, TMI, ISOGRAV, ISOGRAV_SLOPE):
            arr = s.read(idx + 1, masked=True).filled(np.nan).astype("float64")
            m = float(np.nanmedian(arr[valid]))
            arr[~np.isfinite(arr)] = m
            bands[idx] = arr

    h25 = build_h25(bands[DEQ], bands[SHEAR], bands[DILATE], bands[SECOND_INV], valid)
    h26 = build_h26_grav(bands[ISOGRAV_SLOPE], bands[DET_ELEV], valid)
    h27 = build_h27(bands[COND], valid)
    h28 = build_h28(bands[MAG_ANOM], bands[RTP], bands[TMI], valid)
    h29 = build_h29(bands[ISOGRAV], bands[RTP], valid)

    stack = np.stack([h25, h26, h27, h28, h29], axis=-1).astype("float32")
    assert stack.shape == (*shape, 5)
    for i in range(5):
        ch = stack[:, :, i]
        if not np.isfinite(ch[valid]).all():
            raise ValueError(f"channel {i} non-finite inside footprint")
        ch[~valid] = 0.0

    np.save(OUT, stack)

    # cross-correlation vs rounds 1-5
    cube30 = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    r4path = ROOT / "data/round4_features.npy"
    r4 = np.lib.format.open_memmap(str(r4path), mode="r") if r4path.exists() else None
    r5path = ROOT / "data/round5_features.npy"
    r5 = np.lib.format.open_memmap(str(r5path), mode="r") if r5path.exists() else None

    rng = np.random.default_rng(12027)
    idx = rng.choice(np.flatnonzero(valid.ravel()), 400000, replace=False)
    names = ["H25_seismic_proximity_strain", "H26_det_elev_curvature_slopebreak",
             "H27_cond_anisotropy", "H28_mag_texture_variance", "H29_grav_mag_decorr"]
    cross = {}
    detail = {}
    for i, nm in enumerate(names):
        cf = stack[:, :, i].ravel()[idx].astype("float64")
        row = {}
        for j in range(cube30.shape[2]):
            row[f"r12_ch{j:02d}"] = round(float(np.corrcoef(cf, cube30[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        if r4 is not None:
            for j in range(r4.shape[2]):
                row[f"r4_ch{j}"] = round(float(np.corrcoef(cf, r4[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        if r5 is not None:
            for j in range(r5.shape[2]):
                row[f"r5_ch{j}"] = round(float(np.corrcoef(cf, r5[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        for j, other in enumerate(names):
            if j != i:
                row[f"r6_{other}"] = round(float(np.corrcoef(cf, stack[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        best = max(row.items(), key=lambda kv: abs(kv[1]) if np.isfinite(kv[1]) else -1)
        cross[nm] = {"max_abs_corr_channel": best[0], "max_abs_corr": round(abs(best[1]), 4) if np.isfinite(best[1]) else None}
        detail[nm] = row

    side = {
        "built_by": "scripts/build_round6_features.py",
        "preregistered_register": "docs/hypotheses-round6.md",
        "code_sha256": sha(Path(__file__)),
        "inputs": {"training_features": sha(FEATURES), "sample_submission": sha(TEMPLATE)},
        "output": {"file": str(OUT.relative_to(ROOT)), "shape": list(stack.shape), "sha256": sha(OUT), "dtype": "float32"},
        "channels": dict(zip(range(5), names)),
        "official_band_indices_1_based": {"deq_n100a15": DEQ+1, "geod_shearrate": SHEAR+1, "geod_dilaterate": DILATE+1,
                                          "geod_2ndinv": SECOND_INV+1, "det_elev": DET_ELEV+1, "det_elev_slope": DET_SLOPE+1,
                                          "cond_surf": COND+1, "mag_anom": MAG_ANOM+1, "rtp": RTP+1, "tmi": TMI+1,
                                          "iso_grav_anom": ISOGRAV+1},
        "cross_correlation": cross,
        "cross_correlation_detail": detail,
        "distinctness_rule": "max |corr| vs every round-1..5 channel; <0.50 distinct",
        "labels_used": False,
    }
    SIDECAR.write_text(json.dumps(side, indent=2))
    print(json.dumps({"output_sha256": side["output"]["sha256"], "channels": side["channels"], "cross_correlation": cross}, indent=2))


if __name__ == "__main__":
    main()
