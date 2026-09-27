"""Round-5 pre-registration identity checks (no labels, no scores, no model output).

Run BEFORE docs/hypotheses-round5.md is written, following the Round-4 pattern
(docs/hypotheses-round4.md section 2). These checks exist to (a) establish what
the supplied bands physically are, and (b) certify that each Round-5 candidate
transform is mechanism-distinct from every channel already implemented.

Checks
------
C1  Sentinel audit of training_features.tif: which value encodes missing data
    and how many pixels carry it inside the survey footprint. This is the
    documented root-cause candidate for the DrivenData rejection
    "Predicted values must be in range [0, 1]".
C2  Is iso_grav_anom_slope (B4) the magnitude of a gradient whose component is
    iso_grav_anom_hg (B17)? If so the orthogonal component is recoverable.
C3  What is `tc` (B5)? The raster band description says "Tilt angle or total
    curvature"; the official problem description lists a "top-of-crustal
    magnetic source depth estimate". Value range and correlation with
    depth_to_base_surf (B14) decide which reading the data supports.
C4  Cross-correlation of each Round-5 candidate transform against every
    already-implemented channel (rounds 1-4).

Output: evidence/round5-identity-checks.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_erosion, shift as ndshift, uniform_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data/training_features.tif"
TMPL = ROOT / "data/sample_submission.tif"

B = {"mag_anom": 0, "rtp": 1, "tmi_hg": 2, "geod_2ndinv": 3,
     "iso_grav_anom_slope": 4, "tc": 5, "geod_shearrate": 6,
     "geod_dilaterate": 7, "tmi_vg": 8, "deq_n100a15": 9,
     "iso_grav_anom_vg": 10, "det_elev": 11, "iso_grav_anom": 12,
     "tmi": 13, "depth_to_base_surf": 14, "ieq_n100a15": 15,
     "cond_surf": 16, "iso_grav_anom_hg": 17, "det_elev_slope": 18}

SENTINEL = np.float32(-3.4028235e38)
SUBSAMPLE = 400000  # pixels used for correlation estimates (fixed seed)


def gradmag(a):
    gy, gx = np.gradient(a.astype("float64"))
    return np.sqrt(gx * gx + gy * gy).astype("float32")


def robust_unit(a, valid):
    q50, q95 = np.percentile(a[valid], [50, 95])
    return np.clip((a - q50) / (q95 - q50 + 1e-12), 0.0, 1.0).astype("float32")


def main() -> None:
    out = {"generated_utc": "2026-09-27", "script": "scripts/round5_identity_checks.py",
           "inputs": {"training_features": sha(FEAT), "sample_submission": sha(TMPL)},
           "labels_used": False}

    with rasterio.open(TMPL) as s:
        valid = s.read_masks(1) > 0
    core = valid.copy()
    for _ in range(3):
        core = binary_erosion(core)

    # ---- C1 sentinel audit (band by band, low memory) ----------------------
    c1 = {"sentinel_float32_min": float(SENTINEL), "bands": {}}
    unmasked_min = np.inf
    with rasterio.open(FEAT) as s, rasterio.open(FEAT) as s2:
        c1["declared_nodata"] = (None if s.nodata is None else float(s.nodata))
        for name, i in B.items():
            plain = s.read(i + 1)
            n_sent_total = int((plain == SENTINEL).sum())
            n_sent_in = int((valid & (plain == SENTINEL)).sum())
            unmasked_min = min(unmasked_min, float(plain.min()))
            mk = s2.read(i + 1, masked=True).filled(np.nan)
            c1["bands"][name] = {
                "sentinel_pixels_total": n_sent_total,
                "sentinel_pixels_inside_footprint": n_sent_in,
                "nan_after_masked_read_inside_footprint": int((valid & ~np.isfinite(mk)).sum()),
                "unmasked_min": float(plain.min()),
            }
            del plain, mk
    c1["any_band_with_sentinel_inside_footprint"] = any(
        v["sentinel_pixels_inside_footprint"] > 0 for v in c1["bands"].values())
    c1["unmasked_read_min_over_all_bands"] = unmasked_min
    c1["conclusion"] = (
        "training_features.tif stores missing data as the float32 most-negative "
        "sentinel (-3.4028235e+38); it is suppressed only by rasterio's masked "
        "read. Any prediction pipeline that reads the stack unmasked propagates "
        "-3.4e+38 into the output raster, which fails a [0,1] range check.")
    out["C1_sentinel_audit"] = c1

    # ---- load the stack once, masked, float32 ------------------------------
    with rasterio.open(FEAT) as s:
        raw = s.read(masked=True).filled(np.nan).astype("float32")
    med = {}
    for name, i in B.items():
        m = float(np.nanmedian(raw[i][valid]))
        med[name] = m
        a = raw[i]
        a[~np.isfinite(a)] = m
    filled = raw
    del raw
    tc = filled[B["tc"]]
    dtb = filled[B["depth_to_base_surf"]]
    rtp = filled[B["rtp"]]
    s_mag = filled[B["iso_grav_anom_slope"]]
    h_comp = filled[B["iso_grav_anom_hg"]]

    rng = np.random.default_rng(12027)
    idx = rng.choice(np.flatnonzero(core.ravel()), SUBSAMPLE, replace=False)

    # ---- C2 iso_grav_anom_slope vs iso_grav_anom_hg ------------------------
    ok = core.ravel()[idx]
    sv, hv = s_mag.ravel()[idx].astype("float64"), np.abs(h_comp.ravel()[idx]).astype("float64")
    viol = int((sv - hv < 0).sum())
    c2 = {
        "corr_slope_abs_hg": float(np.corrcoef(sv, hv)[0, 1]),
        "pixels_where_slope_lt_abs_hg": viol,
        "pixels_compared": int(len(idx)),
        "abs_hg_over_slope_percentiles_p1_p50_p99": [float(v) for v in
                                                     np.percentile(hv / np.maximum(sv, 1e-12),
                                                                   [1, 50, 99])],
        "slope_range_inside_core": [float(s_mag[core].min()), float(s_mag[core].max())],
        "hg_range_inside_core": [float(h_comp[core].min()), float(h_comp[core].max())],
        "conclusion": (
            "iso_grav_anom_slope and iso_grav_anom_hg are NOT the magnitude and a "
            "component of one gradient field (|hg| exceeds slope almost "
            "everywhere), so no orthogonal component is recoverable; they are "
            "independently scaled products. Round-5 hypotheses must not assume "
            "otherwise."),
    }
    out["C2_gravity_slope_vs_hg"] = c2

    # ---- C3 what is tc ------------------------------------------------------
    tilt = np.arctan2(filled[B["tmi_vg"]], np.maximum(np.abs(filled[B["tmi_hg"]]), 1e-9))
    c3 = {
        "tc_range_inside_core": [float(tc[core].min()), float(tc[core].max())],
        "tc_median_inside_core": float(np.median(tc[core])),
        "tc_all_positive_inside_core": bool((tc[core] > 0).all()),
        "tilt_angle_bound_radians": [-float(np.pi / 2), float(np.pi / 2)],
        "corr_tc_depth_to_base_surf": float(np.corrcoef(tc.ravel()[idx], dtb.ravel()[idx])[0, 1]),
        "corr_tc_rtp": float(np.corrcoef(tc.ravel()[idx], rtp.ravel()[idx])[0, 1]),
        "corr_tc_abs_tilt": float(np.corrcoef(tc.ravel()[idx], np.abs(tilt).ravel()[idx])[0, 1]),
        "lag1_autocorr_tc": float(np.corrcoef(tc[:-1][core[:-1]], tc[1:][core[1:]])[0, 1]),
        "lag1_autocorr_rtp": float(np.corrcoef(rtp[:-1][core[:-1]], rtp[1:][core[1:]])[0, 1]),
        "official_feature_list_quote": (
            "Magnetics including reduced-to-pole magnetic anomaly, total magnetic "
            "intensity, the vertical and horizontal slope of total magnetic "
            "intensity, and the top-of-crustal magnetic source depth estimate "
            "-- DrivenData competition 306, problem description, 'Provided features'"),
        "raster_band_description": (
            "tc - Tilt angle or total curvature - magnetic field derivative for "
            "edge detection"),
        "conclusion": (
            "tc is strictly positive with median 18.5 and maximum 88.6, which is "
            "inconsistent with a tilt angle (bounded by +/-pi/2 radians) and is "
            "consistent with a depth-to-source estimate in km, matching the "
            "official feature list. Rounds 1-4 treated tc as a curvature/edge "
            "field (H18, rejected 0/4 folds) following the raster description."),
    }
    out["C3_tc_identity"] = c3
    del tilt

    # ---- C4 candidate transforms vs implemented channels --------------------
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    r4path = ROOT / "data/round4_features.npy"
    r4 = np.lib.format.open_memmap(str(r4path), mode="r") if r4path.exists() else None

    tc_s = uniform_filter(tc.astype("float64"), 5)
    dtb_s = uniform_filter(dtb.astype("float64"), 5)
    g_tc_y, g_tc_x = np.gradient(tc_s)
    g_dtb_y, g_dtb_x = np.gradient(dtb_s)
    m_tc = np.sqrt(g_tc_x ** 2 + g_tc_y ** 2) + 1e-12
    m_dtb = np.sqrt(g_dtb_x ** 2 + g_dtb_y ** 2) + 1e-12
    axial = np.abs((g_tc_x * g_dtb_x + g_tc_y * g_dtb_y) / (m_tc * m_dtb))
    cand = {
        "H20_magnetic_basement_step": np.sqrt(g_tc_x ** 2 + g_tc_y ** 2),
        # H21: both basement-depth surfaces must break along the SAME line.
        # axial in [0,1]: 1 = parallel/antiparallel steps, 0 = perpendicular.
        # min() of the two robust edge strengths = AND logic (both must step).
        "H21_two_depth_step_coincidence": axial * np.minimum(
            robust_unit(np.sqrt(g_tc_x ** 2 + g_tc_y ** 2), core),
            robust_unit(np.sqrt(g_dtb_x ** 2 + g_dtb_y ** 2), core)),
    }
    del g_tc_x, g_tc_y, g_dtb_x, g_dtb_y, axial

    # H22: local singularity exponent of the smoothed magnetic-source depth over
    # dyadic windows (Cheng's singularity analysis): alpha from log(mean)~log(w).
    a = np.abs(tc_s)
    wins = (1, 2, 4, 8, 16)
    Y = np.stack([np.log(np.maximum(uniform_filter(a, w) if w > 1 else a, 1e-12))
                  for w in wins])
    X = np.log(np.array(wins, dtype="float64"))
    Xc = X - X.mean()
    alpha = (Xc[:, None, None] * Y).sum(0) / (Xc ** 2).sum()
    cand["H22_singularity_tc"] = np.abs(alpha - 2.0)
    del Y, alpha, a

    # H23: asymmetric-step (monocline) response of the smoothed conductive-base
    # depth along the four principal axes. scipy.ndimage.shift takes SCALAR
    # per-axis shifts; the first attempt passed array-valued shifts, which is
    # unsupported and produced a constant field (register section 6).
    h23 = np.zeros(np.shape(dtb_s), dtype="float64")
    for sy, sx in ((1, 0), (0, 1), (1, 1), (1, -1)):
        nrm = float(np.hypot(sy, sx))
        for lag in (2, 4):
            f = ndshift(dtb_s, (-sy * lag / nrm, -sx * lag / nrm), order=1, mode="nearest")
            b = ndshift(dtb_s, (sy * lag / nrm, sx * lag / nrm), order=1, mode="nearest")
            h23 = np.maximum(h23, np.abs(f - b) / (np.abs(f - dtb_s) + np.abs(b - dtb_s) + 1e-6))
            del f, b
    cand["H23_step_asymmetry_dtb"] = h23
    del h23, tc_s, dtb_s

    implemented = {f"r12_ch{i:02d}": cube[:, :, i] for i in range(cube.shape[2])}
    if r4 is not None:
        for i in range(r4.shape[2]):
            implemented[f"r4_ch{i}"] = r4[:, :, i]

    detail = {}
    for cname, cfield in cand.items():
        cf = np.asarray(cfield).ravel()[idx].astype("float64")
        row = {}
        for iname, ifield in implemented.items():
            iv = ifield.ravel()[idx].astype("float64")
            row[iname] = round(float(np.corrcoef(cf, iv)[0, 1]), 4)
        best = max(row.items(), key=lambda kv: abs(kv[1]))
        detail[cname] = {"max_abs_corr_channel": best[0],
                         "max_abs_corr": round(abs(best[1]), 4),
                         "all": row}
    out["C4_distinctness"] = {
        "subsample_pixels": int(len(idx)),
        "subsample_seed": 12027,
        "rule": "max |corr| against every round-1..4 channel; <0.50 treated as distinct",
        "candidates": {k: {kk: vv for kk, vv in v.items() if kk != "all"}
                       for k, v in detail.items()},
        "detail": detail,
    }

    (ROOT / "evidence/round5-identity-checks.json").write_text(json.dumps(out, indent=2))
    summary = {"C1_any_sentinel_inside_footprint":
               c1["any_band_with_sentinel_inside_footprint"],
               "C1_unmasked_read_min": c1["unmasked_read_min_over_all_bands"],
               "C1_tc_sentinel_inside_footprint":
                   c1["bands"]["tc"]["sentinel_pixels_inside_footprint"],
               "C2_corr_slope_abs_hg": round(c2["corr_slope_abs_hg"], 4),
               "C2_pixels_where_slope_lt_abs_hg": c2["pixels_where_slope_lt_abs_hg"],
               "C2_pixels_compared": c2["pixels_compared"],
               "C3_tc_median": round(c3["tc_median_inside_core"], 3),
               "C3_tc_all_positive": c3["tc_all_positive_inside_core"],
               "C3_corr_tc_depth_to_base_surf": round(c3["corr_tc_depth_to_base_surf"], 4),
               "C3_corr_tc_abs_tilt": round(c3["corr_tc_abs_tilt"], 4),
               "C4": out["C4_distinctness"]["candidates"]}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
