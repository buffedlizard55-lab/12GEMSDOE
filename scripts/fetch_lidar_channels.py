"""Fetch + verify the 1 m-lidar scarp descriptor cube (H39) through the GitHub bridge.

Source product (built by sibling 7GEMSDOE on GitHub-hosted runners, because this sandbox
cannot reach USGS hosts):

  repo   buffedlizard55-lab/7GEMSDOE, commit 2e7bf080270493f77286fd62f2db958805053ba5
  path   external/dem/lidar_scarp_features_u8.tif   (36,943,606 bytes)
  run    https://github.com/buffedlizard55-lab/7GEMSDOE/actions/runs/36266555805
  manifest external/dem/lidar_scarp_features.json (bands, quantisation, caveats, rights)

Official upstream: USGS 3DEP 1 m DEM tiles downloaded from the public bucket
`https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/<project>/TIFF/...`
(706 of 716 tiles `ok`, 10 `failed`), reduced at 2 m to 11 scarp descriptors plus a coverage
band and aggregated onto the competition 100 m grid.  USGS 3DEP is U.S. public domain.

Honest limits recorded by the producer and kept here:
  * an OCR-recovered inventory of the competition's `1m_DEM_links.csv`, not the login-walled CSV;
  * "uncalibrated terrain descriptors, not fault detections" — roads, channels, terraces and
    landslide/mine edges also produce steps;
  * ~1-2 m datum offset (NAD83(2011) tiles onto WGS84 UTM 11N), negligible at 100 m.

This script verifies the grid against the pinned template and pins the SHA-256 itself
(no hash is trusted from the sibling):  evidence/lidar-fetch.json
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/ext/lidar_scarp_u8.tif"
SIDE = ROOT / "evidence/lidar-fetch.json"
REPO = "buffedlizard55-lab/7GEMSDOE"
COMMIT = "2e7bf080270493f77286fd62f2db958805053ba5"
SRC = "external/dem/lidar_scarp_features_u8.tif"
MANIFEST = "external/dem/lidar_scarp_features.json"
EXPECT_BYTES = 36_943_606
# `valid` is the producer's coverage band (1 + round(254 * valid_frac)); it is dropped from
# the model inputs like Round-7 dropped the constant `valid_frac`, leaving 11 descriptors.
BANDS = ["ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
         "upface_max", "cross_max", "relief", "coh100", "strike"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if not DEST.exists() or DEST.stat().st_size != EXPECT_BYTES:
        with DEST.open("wb") as out:
            subprocess.run(["gh", "api", f"repos/{REPO}/contents/{SRC}?ref={COMMIT}",
                            "-H", "Accept: application/vnd.github.raw"],
                           stdout=out, check=True)
    manifest = json.loads(subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{MANIFEST}?ref={COMMIT}",
         "-H", "Accept: application/vnd.github.raw"],
        capture_output=True, check=True).stdout)

    with rasterio.open(ROOT / "data/sample_submission.tif") as t:
        tm = t.read_masks(1) > 0
        shape, crs, transform = t.shape, t.crs, t.transform
    with rasterio.open(DEST) as s:
        ok_grid = (s.shape == shape and s.crs == crs and s.transform == transform
                   and s.count == 12 and set(s.dtypes) == {"uint8"})
        a = s.read()
    zero_frac = {BANDS[i]: round(float((a[i][tm] == 0).mean()), 4) for i in range(len(BANDS))}
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "fetched-verified" if ok_grid else "grid-mismatch",
        "product": "USGS 3DEP 1 m DEM → 2 m scarp descriptors → 100 m competition grid (uint8)",
        "upstream_official_source": manifest.get("source"),
        "upstream_rights": manifest.get("rights"),
        "upstream_caveats": manifest.get("caveats"),
        "bridge": {"repo": REPO, "commit": COMMIT, "path": SRC, "manifest": MANIFEST,
                   "workflow_run": manifest.get("workflow_run"),
                   "tile_status": manifest.get("tile_status"),
                   "grid_cells_with_lidar": manifest.get("grid_cells_with_lidar")},
        "file": {"bytes": DEST.stat().st_size, "sha256": sha(DEST)},
        "grid": {"shape": list(shape), "crs": str(crs), "transform": list(transform)[:6],
                 "grid_matches_template": bool(ok_grid), "bands": 12, "dtype": "uint8",
                 "nodata": 0.0},
        "channels_used": BANDS,
        "channel_metadata": manifest.get("channels_2m"),
        "quantisation_rule": manifest.get("quantisation_rule"),
        "zero_fraction_inside_footprint": zero_frac,
        "labels_used": False,
        "sandbox_transport": "GitHub Contents API only (USGS hosts unreachable from this sandbox)",
    }
    SIDE.write_text(json.dumps(report, indent=1, sort_keys=True))
    print("grid ok:", ok_grid, "| sha256:", report["file"]["sha256"])
    print("zero fraction (no lidar) per channel:", zero_frac)
    print("wrote", SIDE)


if __name__ == "__main__":
    main()
