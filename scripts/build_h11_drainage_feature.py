"""Build H11: a label-free drainage-deflection alignment feature.

H11 is preregistered in docs/hypotheses-round3.md before this file's
implementation.  It intentionally uses only the supplied detrended-elevation
and detrended-slope bands.  It does *not* read labels, fold assignments,
external data, model predictions, or absolute map coordinates as predictors.

The feature is a conservative proxy for repeated drainage bending:

1. At three local scales, use the Hessian of detrended elevation to find
   valley-like pixels and their axial valley tangent.
2. Compare tangent axes at +/- three pixels along the local tangent.  A large
   axial disagreement is a candidate bend, weighted by valley support.
3. Aggregate bend evidence in short horizontal, vertical and diagonal paths;
   this prefers collinear groups of bends over isolated local curvature.

It is not a hydrographic product and cannot establish a fault.  The paired
spatial-holdout script is the decision procedure, not this feature itself.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, convolve

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
FEATURES = ROOT / "data/training_features.tif"
OUT = ROOT / "data/h11_drainage_deflection.npy"
SIDECAR = ROOT / "evidence/h11-feature-build.json"

# 0-based positions in the official 19-band supplied raster.
DET_ELEV = 11
DET_ELEV_SLOPE = 18
SCALES_PX = (1.0, 2.0, 4.0)
TANGENT_OFFSET_PX = 3


def robust_unit(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Non-negative robust normalization, limited so one scale cannot dominate."""
    q50, q95 = np.percentile(a[valid], [50, 95])
    return np.clip((a - q50) / (q95 - q50 + 1e-12), 0.0, 1.0)


def line_kernels() -> list[np.ndarray]:
    """9-pixel line averaging kernels in four unoriented directions."""
    horizontal = np.zeros((9, 9), dtype="float64")
    horizontal[4, :] = 1 / 9
    vertical = horizontal.T.copy()
    diagonal_a = np.eye(9, dtype="float64") / 9
    diagonal_b = np.fliplr(diagonal_a)
    return [horizontal, vertical, diagonal_a, diagonal_b]


def valley_bend_alignment(det_elev: np.ndarray, det_slope: np.ndarray,
                           valid: np.ndarray) -> np.ndarray:
    """Return H11's finite, label-free multiscale bend-alignment score."""
    h, w = det_elev.shape
    # Detrended-slope is an independent supplied measure. It downweights flat
    # basins, where a numerically unstable tangent must not become evidence.
    slope_support = robust_unit(np.abs(det_slope), valid)
    scale_scores: list[np.ndarray] = []
    yy, xx = np.indices((h, w))

    for sigma in SCALES_PX:
        # Derivatives of the Gaussian-smoothed field.  Derivative scaling puts
        # the three scales on comparable dimensionless footing before robust
        # normalization; it does not use a fitted label-dependent parameter.
        hyy = gaussian_filter(det_elev, sigma=sigma, order=(2, 0), mode="nearest") * sigma**2
        hxx = gaussian_filter(det_elev, sigma=sigma, order=(0, 2), mode="nearest") * sigma**2
        hyx = gaussian_filter(det_elev, sigma=sigma, order=(1, 1), mode="nearest") * sigma**2
        trace = hxx + hyy
        disc = np.sqrt(np.maximum((hxx - hyy) ** 2 + 4 * hyx ** 2, 0.0))
        lambda_min = (trace - disc) / 2.0

        # A 2-D trough needs positive curvature in its least-curved direction.
        # The score remains a terrain proxy rather than an asserted valley map.
        valley = robust_unit(np.maximum(lambda_min, 0.0), valid) * slope_support

        # Eigenvector of the high-curvature direction is cross-valley normal;
        # rotate by 90 degrees for an *axial* (sign-insensitive) tangent.
        normal_angle = 0.5 * np.arctan2(2 * hyx, hxx - hyy)
        tangent_angle = normal_angle + np.pi / 2.0
        ty, tx = np.sin(tangent_angle), np.cos(tangent_angle)

        # Look ahead and behind along the locally inferred channel tangent.
        # Clipping is safe because a 4px boundary is zeroed below.
        y_plus = np.clip(np.rint(yy + TANGENT_OFFSET_PX * ty).astype(int), 0, h - 1)
        x_plus = np.clip(np.rint(xx + TANGENT_OFFSET_PX * tx).astype(int), 0, w - 1)
        y_minus = np.clip(np.rint(yy - TANGENT_OFFSET_PX * ty).astype(int), 0, h - 1)
        x_minus = np.clip(np.rint(xx - TANGENT_OFFSET_PX * tx).astype(int), 0, w - 1)
        # Axial orientation means a 180-degree reversal is unchanged.
        dot = np.abs(ty[y_plus, x_plus] * ty[y_minus, x_minus]
                     + tx[y_plus, x_plus] * tx[y_minus, x_minus])
        bend = 1.0 - np.clip(dot, 0.0, 1.0)
        local_support = np.minimum(valley, np.minimum(valley[y_plus, x_plus],
                                                       valley[y_minus, x_minus]))
        evidence = bend * local_support

        # Require a path-like arrangement of bends.  This is the alignment
        # stage that makes H11 different from a standalone curvature score.
        aligned = np.maximum.reduce([convolve(evidence, k, mode="nearest")
                                     for k in line_kernels()])
        scale_scores.append(robust_unit(aligned, valid))

    out = np.maximum.reduce(scale_scores).astype("float32")
    # Derivatives cannot be reliable near an image boundary or invalid survey
    # footprint. Do not let artificial border replication produce candidates.
    out[:4, :] = out[-4:, :] = out[:, :4] = out[:, -4:] = 0.0
    out[~valid] = 0.0
    if not np.isfinite(out[valid]).all():
        raise ValueError("H11 has non-finite values inside the template footprint")
    return out


def main() -> None:
    with rasterio.open(TEMPLATE) as ds:
        valid = ds.read_masks(1) > 0
        template_sha = sha(TEMPLATE)
    with rasterio.open(FEATURES) as ds:
        elev = ds.read(DET_ELEV + 1, masked=True).filled(np.nan).astype("float64")
        slope = ds.read(DET_ELEV_SLOPE + 1, masked=True).filled(np.nan).astype("float64")
        features_sha = sha(FEATURES)

    # Same documented within-footprint median policy as the existing feature
    # cube.  The values are recorded so this transform is reproducible.
    elev_median = float(np.nanmedian(elev[valid]))
    slope_median = float(np.nanmedian(slope[valid]))
    elev[~np.isfinite(elev)] = elev_median
    slope[~np.isfinite(slope)] = slope_median
    score = valley_bend_alignment(elev, slope, valid)
    np.save(OUT, score, allow_pickle=False)

    evidence = {
        "built_by": "scripts/build_h11_drainage_feature.py",
        "code_sha256": sha(Path(__file__)),
        "output": {"file": "data/h11_drainage_deflection.npy",
                   "sha256": sha(OUT), "shape": list(score.shape), "dtype": "float32"},
        "inputs": {"training_features.tif": features_sha,
                   "sample_submission.tif": template_sha},
        "official_band_indices_1_based": {"det_elev": DET_ELEV + 1,
                                          "det_elev_slope": DET_ELEV_SLOPE + 1},
        "parameters": {"scales_px": list(SCALES_PX),
                       "tangent_offset_px": TANGENT_OFFSET_PX,
                       "line_aggregation_pixels": 9,
                       "boundary_zero_pixels": 4},
        "within_footprint_median_imputation": {"det_elev": elev_median,
                                                 "det_elev_slope": slope_median},
        "labels_used": False,
    }
    SIDECAR.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
