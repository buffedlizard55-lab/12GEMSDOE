"""Build Round-7 candidate features: H32 sub-100 m topographic scarp channels (preregistered).

Register: docs/hypotheses-round7.md (written BEFORE this file).

Input: 13 label-free channel vectors derived from the USGS 3DEP 1/3 arc-second
(~10 m) seamless DEM, built on a GitHub-hosted runner by the sibling repository
GEMSDOE10 (tag ext/dem10-36343078537) and fetched + SHA-256-verified into
data/dem10/ by scripts/fetch_dem10_channels.py (provenance: evidence/dem10-fetch.json).
Each vector holds one float32 value per finite pixel of sample_submission.tif in
row-major order np.nonzero(np.isfinite(sample_submission)).

This script
  1. re-hashes every vector against data/dem10/manifest.json,
  2. scatters 12 channels onto the (3730, 3292) grid (dem10_valid_frac is
     constant 1.0 on the footprint and is dropped; recorded in the sidecar),
  3. writes data/round7_features.npy  (float32, (H, W, 12), 0 outside footprint),
  4. computes distinctness (max |corr| vs every Round-1..6 channel on 400k random
     valid pixels) and writes evidence/round7-feature-build.json.

No labels, fold assignments, coordinates, catalogue distances or model outputs
are used. Channel order (0-based) in the output cube:
  0 slope_max        1 slope_mean       2 slope_std        3 hgm20_max
  4 hgm50_max        5 hgm200_mean      6 steep_ratio_max  7 resid_std
  8 resid_range      9 curv_absmax     10 onesided        11 onesided3
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
DEM_DIR = ROOT / "data/dem10"
MANIFEST = DEM_DIR / "manifest.json"
FETCH_SIDECAR = ROOT / "evidence/dem10-fetch.json"
OUT = ROOT / "data/round7_features.npy"
SIDECAR = ROOT / "evidence/round7-feature-build.json"

CHANNELS = [
    "dem10_slope_max", "dem10_slope_mean", "dem10_slope_std",
    "dem10_hgm20_max", "dem10_hgm50_max", "dem10_hgm200_mean",
    "dem10_steep_ratio_max", "dem10_resid_std", "dem10_resid_range",
    "dem10_curv_absmax", "dem10_onesided", "dem10_onesided3",
]
DROPPED = ["dem10_valid_frac"]  # constant 1.0 inside footprint (manifest p01 = p99 = 1.0)

# Core scarp subset used by the preregistered robustness arm (register section 3, item 3)
DEM4 = ["dem10_hgm20_max", "dem10_hgm50_max", "dem10_onesided3", "dem10_resid_std"]


def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError("data/dem10/manifest.json missing; run scripts/fetch_dem10_channels.py first")
    manifest = json.loads(MANIFEST.read_text())
    fetch = json.loads(FETCH_SIDECAR.read_text()) if FETCH_SIDECAR.exists() else {}

    with rasterio.open(TEMPLATE) as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    if sha(TEMPLATE) != manifest["template_sha256"]:
        raise ValueError("template sha mismatch: local sample_submission.tif != manifest template")
    footprint = np.flatnonzero(valid)
    if len(footprint) != int(manifest["footprint_pixels"]):
        raise ValueError(f"footprint count mismatch {len(footprint)} != {manifest['footprint_pixels']}")

    stats = manifest["channel_stats"]
    stack = np.zeros((*shape, len(CHANNELS)), dtype="float32")
    channel_rows = []
    for i, name in enumerate(CHANNELS):
        p = DEM_DIR / f"{name}.f32.npy"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != stats[name]["sha256"]:
            raise ValueError(f"{name}: sha256 {h[:12]} != manifest {stats[name]['sha256'][:12]}")
        vec = np.load(p)
        if vec.shape != (len(footprint),) or vec.dtype != np.float32:
            raise ValueError(f"{name}: unexpected shape/dtype {vec.shape} {vec.dtype}")
        if not np.isfinite(vec).all():
            raise ValueError(f"{name}: non-finite values inside footprint")
        plane = stack[:, :, i].ravel()
        plane[footprint] = vec
        stack[:, :, i] = plane.reshape(shape)
        channel_rows.append({
            "index": i, "name": name, "sha256": h,
            "p50": float(np.median(vec)), "p99": float(np.percentile(vec, 99)),
            "manifest_p50": stats[name].get("p50"),
        })
    for name in DROPPED:
        p = DEM_DIR / f"{name}.f32.npy"
        vec = np.load(p)
        channel_rows.append({"index": None, "name": name, "dropped": True,
                             "reason": "constant inside footprint",
                             "min": float(vec.min()), "max": float(vec.max())})

    np.save(OUT, stack)

    # Distinctness vs all prior channels (rounds 1-6), 400k random valid pixels, fixed seed.
    rng = np.random.default_rng(0)
    idx = rng.choice(footprint, 400000, replace=False)
    priors = {}
    cube30 = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    for j in range(cube30.shape[2]):
        priors[f"r12_ch{j:02d}"] = cube30[:, :, j].ravel()[idx].astype("float64")
    for key, fname, n in (("r4", "round4_features.npy", 4), ("r5", "round5_features.npy", 4), ("r6", "round6_features.npy", 5)):
        p = ROOT / "data" / fname
        if p.exists():
            arr = np.lib.format.open_memmap(str(p), mode="r")
            for j in range(n):
                priors[f"{key}_ch{j}"] = arr[:, :, j].ravel()[idx].astype("float64")
    # channel 29 of the cube can carry NaN outside footprint only; inside it is imputed. Guard anyway.
    cross, detail = {}, {}
    for i, name in enumerate(CHANNELS):
        cf = stack[:, :, i].ravel()[idx].astype("float64")
        row = {}
        for k, v in priors.items():
            ok = np.isfinite(v) & np.isfinite(cf)
            c = float(np.corrcoef(cf[ok], v[ok])[0, 1]) if ok.sum() > 1000 else float("nan")
            row[k] = round(c, 4)
        for j, other in enumerate(CHANNELS):
            if j != i:
                row[f"r7_{other}"] = round(float(np.corrcoef(cf, stack[:, :, j].ravel()[idx].astype("float64"))[0, 1]), 4)
        prior_only = {k: v for k, v in row.items() if not k.startswith("r7_")}
        best = max(prior_only.items(), key=lambda kv: abs(kv[1]) if np.isfinite(kv[1]) else -1)
        cross[name] = {"max_abs_corr_channel": best[0], "max_abs_corr": round(abs(best[1]), 4),
                       "distinct_lt_050": bool(abs(best[1]) < 0.50)}
        detail[name] = row

    band_names = {"r12_ch18": "det_elev_slope (B19)", "r12_ch11": "det_elev (B12)"}
    side = {
        "built_by": "scripts/build_round7_features.py",
        "code_sha256": sha(Path(__file__)),
        "register": "docs/hypotheses-round7.md",
        "hypothesis": "H32 sub-100 m topographic scarp signature (USGS 3DEP 1/3 arc-second DEM)",
        "inputs": {
            "template_sha256": sha(TEMPLATE),
            "dem10_manifest_sha256": sha(MANIFEST),
            "dem10_fetch_sidecar": str(FETCH_SIDECAR.relative_to(ROOT)),
            "source_repo": fetch.get("source_repo", manifest.get("github_sha")),
            "source_tag": fetch.get("source_tag"),
            "source_tag_commit": fetch.get("source_tag_commit"),
            "upstream_product": manifest.get("product"),
            "upstream_product_catalog": manifest.get("product_catalog"),
            "upstream_tiles": manifest.get("tiles"),
            "grid": manifest.get("grid"),
            "runner_code_sha256": manifest.get("code_sha256"),
            "runner_github_run_id": manifest.get("github_run_id"),
        },
        "output": {"file": str(OUT.relative_to(ROOT)), "shape": list(stack.shape), "sha256": sha(OUT), "dtype": "float32"},
        "channels": channel_rows,
        "dem4_core_subset": DEM4,
        "cross_correlation": cross,
        "cross_correlation_detail": detail,
        "prior_channel_names_of_interest": band_names,
        "distinctness_rule": "max |corr| vs every round-1..6 channel on 400k random valid pixels; <0.50 distinct. H32 is a resolution change, so channels >=0.50 are listed rather than hidden (register section 3, item 4c).",
        "labels_used": False,
    }
    SIDECAR.write_text(json.dumps(side, indent=2))
    print(json.dumps({"output_sha256": side["output"]["sha256"], "cross_correlation": cross}, indent=2))


if __name__ == "__main__":
    main()
