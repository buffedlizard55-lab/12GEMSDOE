"""Round-7 regression tests: H32 provenance + distinctness ledger, gate report, leaderboard feed parser.

These tests lock the invariants that Round-7 claims depend on. Data-dependent
checks skip when the git-ignored rasters / feature cubes are absent (CI).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_leaderboard import WATCH, build_feed, parse_leaderboard  # noqa: E402

REGISTER = ROOT / "docs/hypotheses-round7.md"
DEM_FETCH = ROOT / "evidence/dem10-fetch.json"
R7_BUILD = ROOT / "evidence/round7-feature-build.json"
R7_HOLDOUT = ROOT / "evidence/holdout_round7.json"


def _needs_data(*paths):
    for p in paths:
        if not Path(p).is_file():
            pytest.skip(f"requires git-ignored data file: {p}")


def test_round7_register_preregisters_arms_and_gate():
    text = REGISTER.read_text()
    for token in ("H32", "H33", "H34", "H35", "H36", "multi25_h28_dem12", "multi25_dem12",
                  "multi25_h28_dem3", "mean paired gain > 0", "No slot is spent"):
        assert token in text, f"register missing preregistered element: {token}"
    # The register must not claim the sibling-built channels as novel data.
    assert "GEMSDOE10" in text and "ext/dem10-36343078537" in text


def test_dem10_provenance_sidecar_is_complete_and_label_free():
    side = json.loads(DEM_FETCH.read_text())
    assert side["labels_used"] is False
    assert side["source_repo"] == "buffedlizard55-lab/GEMSDOE10"
    assert side["source_tag"] == "ext/dem10-36343078537"
    assert side["source_tag_commit"].startswith("91d6566ecc")
    assert side["template_sha256"] == "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
    assert side["footprint_pixels"] == 5167373
    tiles = side["upstream_tiles"]
    assert len(tiles) == 12
    for name, t in tiles.items():
        assert t["url"].startswith("https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/")
        assert name in t["url"] and len(t["sha256"]) == 64 and t["bytes"] > 100_000_000
    chans = side["channels"]
    assert len(chans) == 13
    assert all(c["status"] == "fetched-verified" and len(c["sha256"]) == 64 for c in chans)


def test_round7_feature_sidecar_reports_distinctness_honestly():
    side = json.loads(R7_BUILD.read_text())
    assert side["labels_used"] is False
    assert side["output"]["shape"] == [3730, 3292, 12]
    cross = side["cross_correlation"]
    assert len(cross) == 12
    # The register amendment fixed the distinct-only subset from this table.
    distinct = sorted(k for k, v in cross.items() if v["distinct_lt_050"])
    assert distinct == ["dem10_onesided", "dem10_onesided3", "dem10_steep_ratio_max"], distinct
    # Slope-type channels must be flagged as near-duplicates of det_elev_slope (B19 = r12_ch18),
    # i.e. the sidecar must not hide the overlap.
    for k in ("dem10_slope_mean", "dem10_hgm50_max", "dem10_hgm20_max"):
        assert cross[k]["max_abs_corr_channel"] == "r12_ch18" and cross[k]["max_abs_corr"] > 0.9
    dropped = [c for c in side["channels"] if c.get("dropped")]
    assert [c["name"] for c in dropped] == ["dem10_valid_frac"]
    # per-channel hashes must match the fetch sidecar
    fetched = {c["channel"]: c["sha256"] for c in json.loads(DEM_FETCH.read_text())["channels"]}
    for c in side["channels"]:
        if not c.get("dropped"):
            assert fetched[c["name"]] == c["sha256"]


def test_round7_holdout_report_gate_and_protocol():
    ev = json.loads(R7_HOLDOUT.read_text())
    assert ev["budget"] == 0.02 and ev["nms_radius"] == 2
    assert ev["release_allowed"] is False
    assert ev["incumbent"] == "multi25_h28" and ev["primary"] == "multi25_h28_dem12"
    r7 = json.loads(R7_BUILD.read_text())
    assert ev["round7_feature_sha256"] == r7["output"]["sha256"]
    for protocol, blk in ev["truth_protocols"].items():
        for row in blk["folds"]:
            assert row["leakage_probe_dti"] == 0.0
            # dense/sparse truth counts must be positive on every fold
            assert row["score_positive"] > 0
        # multi25 reference must reproduce the frozen Round-6 numbers exactly (protocol unchanged)
    r6 = json.loads((ROOT / "evidence/holdout_round6.json").read_text())
    for protocol in ("dense_catalogue_truth", "sparse_thinned_20pct"):
        a = ev["truth_protocols"][protocol]["means"]["multi25_nms3"]
        b = r6["truth_protocols"][protocol]["means"]["multi25_nms3"]
        assert abs(a - b) < 1e-9, f"multi25 reference drifted on {protocol}: {a} vs {b}"
        a = ev["truth_protocols"][protocol]["means"]["multi25_h28_nms3"]
        b = r6["truth_protocols"][protocol]["means"]["multi25_h28_nms3"]
        assert abs(a - b) < 1e-9, f"incumbent drifted on {protocol}: {a} vs {b}"
    gate = ev["gate"]
    computed = all(g["primary_wins_vs_incumbent"] >= 3 and g["primary_mean_gain_vs_incumbent"] > 0
                   and g["leakage_probe_max"] == 0.0 for g in gate["per_protocol"].values())
    assert gate["passed"] == computed


def test_round7_features_memmap_matches_vectors():
    _needs_data(ROOT / "data/round7_features.npy", ROOT / "data/dem10/dem10_onesided3.f32.npy",
                ROOT / "data/sample_submission.tif")
    import rasterio
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
    cube = np.lib.format.open_memmap(str(ROOT / "data/round7_features.npy"), mode="r")
    vec = np.load(ROOT / "data/dem10/dem10_onesided3.f32.npy")
    plane = cube[:, :, 11]
    assert np.array_equal(plane[valid], vec)
    assert not plane[~valid].any()


def test_leaderboard_parser_and_feed_shape():
    html = """<table><tr><th>x</th></tr><tr><td>1</td></tr></table>
    <table class="leaderboard"><thead><tr><th>Rank</th><th>Name</th><th>Score</th><th>Submissions</th><th>Last Submission</th></tr></thead>
    <tbody><tr><td>1</td><td><a href="/users/DARD/">DARD</a></td><td>0.3168</td><td>11</td><td>Sept. 27, 2026</td></tr>
    <tr><td>2</td><td>Team X</td><td>0.2993</td><td>7</td><td>Sept. 26, 2026</td></tr></tbody></table>"""
    rows = parse_leaderboard(html)
    assert [(r["rank"], r["name"], r["score"]) for r in rows] == [(1, "DARD", 0.3168), (2, "Team X", 0.2993)]
    assert rows[0]["submissions"] == 11 and rows[0]["profile"] == "/users/DARD/"
    assert parse_leaderboard("<html><p>no table</p></html>") == []
    feed = build_feed(rows, "2026-09-28T00:00:00+00:00", "test", "ok")
    assert feed["watched"]["DARD"]["rank"] == 1 and feed["watched"]["alexoktaba"]["rank"] is None
    assert set(WATCH) >= {"DARD", "doegemsDrivendata", "extradr19"}
    # the committed feed must parse and carry a status the site can display
    committed = json.loads((ROOT / "docs/leaderboard.json").read_text())
    assert committed["status"] in {"ok", "manual-snapshot", "fetch-failed", "parse-failed"}
    assert committed["rows"] and committed["rows"][0]["rank"] == 1


def test_shipped_r7_artifact_matches_manifest_and_template():
    import zipfile
    import hashlib
    import rasterio
    from core import validate  # noqa: E402

    stem = "12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62"
    tif = ROOT / "docs/downloads" / f"{stem}.tif"
    manifest = json.loads((ROOT / "docs/downloads" / f"{stem}.json").read_text())
    assert tif.is_file(), "shipped Round-7 artifact missing"
    assert manifest["policy"]["gate"]["passed"] is True
    assert manifest["model"]["arm"] == "multi25_h28_dem12"
    assert manifest["drivendata_score"] is None
    z = ROOT / "docs/downloads" / f"{stem}.zip"
    with zipfile.ZipFile(z) as f:
        names = f.namelist()
        assert names == [f"{stem}.tif"]
        assert hashlib.sha256(f.read(names[0])).hexdigest() == manifest["files"]["primary_tif"]["validation"]["sha256"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == manifest["files"]["primary_tif"]["validation"]["sha256"]
    # The note the site hands out must match the manifest and name the SHA prefix.
    assert manifest["suggested_note"].endswith("sha256:0c9199f14e62")
    assert manifest["suggested_note"] in (ROOT / "docs/index.html").read_text()

    _needs_data(ROOT / "data/sample_submission.tif", ROOT / "data/labels.tif")
    report = validate(tif, ROOT / "data/sample_submission.tif")
    assert report["valid_pixels"] == 5167373 and report["min"] >= 0.0 and report["max"] <= 1.0
    with rasterio.open(tif) as s:
        assert s.count == 1 and s.dtypes == ("float32",) and s.crs.to_string() == "EPSG:32611"
        arr = s.read(1)
        mask = s.read_masks(1) > 0
    assert np.isnan(arr[~mask]).all() and np.isfinite(arr[mask]).all()
    assert int((arr[mask] > 0).sum()) == manifest["policy"]["emitted_pixels"] == 103347
    from scipy.ndimage import convolve
    counts = convolve((arr > 0).astype("int32"), np.ones((5, 5), "int32"), mode="constant")
    assert counts[arr > 0].max() == 1, "two emitted pixels share one 300 m cell"
    with rasterio.open(ROOT / "data/labels.tif") as s:
        labels = (s.read(1, masked=True).filled(0) > 0) & mask
    assert not (labels & (arr > 0)).any(), "new fault cannot be catalogue pixel"
    # Must be a genuinely different submission from the Round-6 file.
    with rasterio.open(ROOT / "docs/downloads/12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif") as s:
        prev = s.read(1)
    assert int(((arr > 0) != (prev > 0)).sum()) > 100000
