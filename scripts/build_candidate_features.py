"""Build the auditable 30-channel candidate feature cube from pinned rasters.

Channels 0-18:  raw 19 supplied bands (see evidence/data-inventory.json).
Channels 19-22: H1 concealed basement step (docs/hypotheses.md).
  19: |grad(depth_to_base_surf)|          (B15, 0-based 14)
  20: laplacian(depth_to_base_surf)       (B15)
  21: |grad(iso_grav_anom_hg)|            (B18, 0-based 17)
  22: |grad(cond_surf)|                   (B17, 0-based 16)
Channels 23-24: H3 tilt edge + H2 strain dilation.
  23: |grad(tilt)|, tilt = atan2(tmi_vg, max(|tmi_hg|, eps))  (B9/B3)
  24: TDI = sqrt(max(shearrate,0)*max(dilaterate,0)) * (1+ieq) (B7/B8/B16)
Channels 25-29: NEW label-free candidates H8/H9/H7/H10 (docs/hypotheses-round2.md).
  25: H8  joint alteration = zplus(cond_surf) * zplus(-rtp)
  26: H9  cross-gradient |grad(iso_grav_anom) x grad(rtp)| (normalized)
  27: H9  intersection density = mean(crossgrad > p90) in 5px window
  28: H7  seismic strike-alignment = max over 8 strikes of
        (along-strike NCC - across-strike NCC) of ieq in 9px window
  29: H10 residual cover conductance = cond_surf - median_trend(depth_to_base)

NaN policy: gradients are computed on median-filled arrays; every output
channel is finite on all template-valid pixels (median-imputed, recorded).
No fault labels are used. No coordinates or catalogue distances.
"""
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import laplace, uniform_filter, shift

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data/training_features.tif"
TMPL = ROOT / "data/sample_submission.tif"
OUT = ROOT / "data/candidate-features-30.npy"
SIDECAR = ROOT / "evidence/feature-build.json"

B = {"mag_anom": 0, "rtp": 1, "tmi_hg": 2, "geod_2ndinv": 3,
     "iso_grav_anom_slope": 4, "tc": 5, "geod_shearrate": 6,
     "geod_dilaterate": 7, "tmi_vg": 8, "deq_n100a15": 9,
     "iso_grav_anom_vg": 10, "det_elev": 11, "iso_grav_anom": 12,
     "tmi": 13, "depth_to_base_surf": 14, "ieq_n100a15": 15,
     "cond_surf": 16, "iso_grav_anom_hg": 17, "det_elev_slope": 18}


def gradmag(a):
    gy, gx = np.gradient(a.astype("float64"))
    return np.sqrt(gx * gx + gy * gy)


def zplus(a, med, iqr):
    return np.clip((a - med) / (iqr + 1e-9), 0, None)


def local_ncc(a, b, size=9):
    ma = uniform_filter(a, size)
    mb = uniform_filter(b, size)
    va = np.maximum(uniform_filter(a * a, size) - ma * ma, 0)
    vb = np.maximum(uniform_filter(b * b, size) - mb * mb, 0)
    cov = uniform_filter(a * b, size) - ma * mb
    return cov / np.sqrt(va * vb + 1e-12)


def main():
    with rasterio.open(TMPL) as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(FEAT) as s:
        raw = s.read(masked=True).filled(np.nan).astype("float32")  # (19,H,W)
    assert raw.shape == (19, *shape), raw.shape

    nan_inside = int((valid & ~np.isfinite(raw).all(axis=0)).sum())
    medians = {}
    for i in range(19):
        m = float(np.nanmedian(raw[i][valid]))
        medians[i] = m
        ch = raw[i]
        ch[~np.isfinite(ch)] = m  # in-place median fill (low-memory)
    filled = raw  # filled in place; no duplicate array
    del raw

    dtb = filled[B["depth_to_base_surf"]]
    grav_hg = filled[B["iso_grav_anom_hg"]]
    cond = filled[B["cond_surf"]]
    rtp = filled[B["rtp"]]
    tmi_vg = filled[B["tmi_vg"]]
    tmi_hg = filled[B["tmi_hg"]]
    shear = filled[B["geod_shearrate"]]
    dilate = filled[B["geod_dilaterate"]]
    ieq = filled[B["ieq_n100a15"]]
    isograv = filled[B["iso_grav_anom"]]

    f19 = gradmag(dtb).astype("float32")
    f20 = laplace(dtb).astype("float32")
    f21 = gradmag(grav_hg).astype("float32")
    f22 = gradmag(cond).astype("float32")

    tilt = np.arctan2(tmi_vg, np.maximum(np.abs(tmi_hg), 1e-9))
    f23 = gradmag(tilt).astype("float32")
    f24 = (np.sqrt(np.clip(shear, 0, None) * np.clip(dilate, 0, None))
            * (1.0 + ieq)).astype("float32")

    # H8: joint hydrothermal alteration (conductive HIGH x demagnetized LOW).
    mc, iqc = np.median(cond[valid]), np.subtract(*np.percentile(cond[valid], [75, 25]))
    mr, iqr_ = np.median(rtp[valid]), np.subtract(*np.percentile(rtp[valid], [75, 25]))
    f25 = (zplus(cond, mc, iqc) * zplus(-rtp, -mr, iqr_)).astype("float32")

    # H9: cross-gradient magnitude between gravity and magnetic gradients.
    gy_g, gx_g = np.gradient(isograv.astype("float64"))
    gy_m, gx_m = np.gradient(rtp.astype("float64"))
    cross = np.abs(gx_g * gy_m - gy_g * gx_m)
    cross /= (np.median(cross[valid]) + 1e-12)
    f26 = cross.astype("float32")
    thr = float(np.percentile(cross[valid], 90))
    f27 = uniform_filter((cross > thr).astype("float32"), 5)

    # H7: seismic strike-alignment correlogram on ieq (non-Frangi).
    z = ((ieq - np.median(ieq[valid]))
         / (np.subtract(*np.percentile(ieq[valid], [75, 25])) + 1e-9)).astype("float32")
    strikes = [(1, 0), (0, 1), (1, 1), (1, -1),
               (2, 1), (2, -1), (1, 2), (1, -2)]
    align = np.full(shape, -1.0, dtype="float32")
    for sy, sx in strikes:
        n = np.hypot(sy, sx)
        uy, ux = sy / n, sx / n
        v = (-ux, uy)
        a1 = shift(z, (2 * uy, 2 * ux), order=1, mode="nearest")
        a2 = shift(z, (-2 * uy, -2 * ux), order=1, mode="nearest")
        c1 = shift(z, (2 * v[0], 2 * v[1]), order=1, mode="nearest")
        c2 = shift(z, (-2 * v[0], -2 * v[1]), order=1, mode="nearest")
        score = local_ncc(a1, a2) - local_ncc(c1, c2)
        align = np.maximum(align, score.astype("float32"))
    f28 = align

    # H10: residual cover conductance (cond minus depth-trend).
    d = dtb[valid]
    c = cond[valid]
    qs = np.quantile(d, np.linspace(0, 1, 51))
    qs[0] -= 1e-6
    qs[-1] += 1e-6
    idx = np.clip(np.digitize(dtb.ravel(), qs) - 1, 0, 49)
    bin_med = np.array([np.median(c[(d >= qs[k]) & (d < qs[k + 1])]) for k in range(50)])
    trend = bin_med[idx].reshape(shape)
    f29 = (cond - trend).astype("float32")

    cube = np.lib.format.open_memmap(str(OUT), mode="w+", dtype="float32",
                                     shape=(*shape, 30))
    for i in range(19):
        cube[:, :, i] = filled[i]
    for j, f in enumerate([f19, f20, f21, f22, f23, f24, f25, f26, f27, f28, f29], start=19):
        cube[:, :, j] = np.where(valid, f, float(np.median(f[valid])))
    cube.flush()

    check = np.lib.format.open_memmap(str(OUT), mode="r")
    assert np.isfinite(check[valid]).all(), "non-finite inside footprint"
    del check

    SIDECAR.write_text(json.dumps({
        "built_by": "scripts/build_candidate_features.py",
        "code_sha256": sha(Path(__file__)),
        "inputs": {k: sha(ROOT / "data" / v) for k, v in
                   [("training_features", "training_features.tif"),
                    ("sample_submission", "sample_submission.tif")]},
        "output": {"file": "data/candidate-features-30.npy", "shape": [shape[0], shape[1], 30],
                   "dtype": "float32"},
        "channels": {"0-18": "raw 19 bands (median-imputed)",
                     "19": "|grad depth_to_base_surf|", "20": "laplacian depth_to_base_surf",
                     "21": "|grad iso_grav_anom_hg|", "22": "|grad cond_surf|",
                     "23": "|grad tilt|, tilt=atan2(tmi_vg,max(|tmi_hg|,eps))",
                     "24": "TDI=sqrt(max(shear,0)*max(dilate,0))*(1+ieq)",
                     "25": "H8 joint alteration zplus(cond)*zplus(-rtp)",
                     "26": "H9 cross-gradient |gx_g*gy_m-gy_g*gx_m| / median",
                     "27": "H9 intersection density mean(cross>p90) 5px",
                     "28": "H7 seismic strike-alignment max(along-across NCC)",
                     "29": "H10 residual cover conductance"},
        "median_imputation": {str(k): v for k, v in medians.items()},
        "template_valid_pixels": int(valid.sum()),
        "pixels_with_any_band_nan_inside_template": nan_inside,
        "labels_used": False,
    }, indent=2))
    print(f"wrote {OUT} shape={shape + (30,)} nan_inside={nan_inside}")


if __name__ == "__main__":
    main()
