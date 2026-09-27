"""Round-6 regression tests: H25-H29 distinctness, H28 gate, R6 artifact conformance.

These tests lock the invariants that Round-6 claims depend on.
"""

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core import validate  # noqa: E402
from generate_nms_submission_r6 import RADIUS, nms_select  # noqa: E402

PRIMARY_R6 = "12GEMSDOE_r6-nms3-h28-texture_8721329b55c7"
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"


def _needs_data(*paths):
    for p in paths:
        if not Path(p).is_file():
            pytest.skip(f"requires git-ignored data file: {p} (run scripts/download_competition_data.sh)")


def test_round6_feature_sidecar_is_label_free_and_distinct():
    side = json.loads((ROOT / "evidence/round6-feature-build.json").read_text())
    assert side["labels_used"] is False
    assert side["output"]["shape"][2] == 5
    for name, row in side["cross_correlation"].items():
        # max_abs_corr must be <0.50 per preregistered rule
        assert row["max_abs_corr"] is not None
        assert row["max_abs_corr"] < 0.50, f"{name} duplicates existing channel: {row}"


def test_round6_holdout_gate_h28_passes_both_protocols():
    ev = json.loads((ROOT / "evidence/holdout_round6.json").read_text())
    assert ev["budget"] == 0.02 and ev["nms_radius"] == 2
    assert ev["release_allowed"] is False
    # gate_a must pass (NMS beats topk)
    for protocol, blk in ev["truth_protocols"].items():
        gate = blk["gate_a_folds23_nms3_vs_topk_multi25"]
        assert gate["passed"] is True, f"emission gate regressed on {protocol}"
        for row in blk["folds"]:
            assert row["leakage_probe_dti"] == 0.0

    # H28 must be the only arm that wins >=3/4 on BOTH protocols
    protocols = ev["truth_protocols"]
    dense_wins = protocols["dense_catalogue_truth"]["fold_wins_vs_multi25_nms3"]
    sparse_wins = protocols["sparse_thinned_20pct"]["fold_wins_vs_multi25_nms3"]
    # H28 should have >=3 on both
    assert dense_wins.get("multi25_h28", 0) >= 3, f"H28 dense wins {dense_wins.get('multi25_h28')}"
    assert sparse_wins.get("multi25_h28", 0) >= 3, f"H28 sparse wins {sparse_wins.get('multi25_h28')}"
    # No other new arm should have >=3 on both except H28
    for arm in ["multi25_h25", "multi25_h26", "multi25_h27", "multi25_h29"]:
        if dense_wins.get(arm, 0) >= 3 and sparse_wins.get(arm, 0) >= 3:
            raise AssertionError(f"Unexpected arm {arm} also passes both protocols: dense {dense_wins[arm]}, sparse {sparse_wins[arm]} — update register")


def test_shipped_r6_artifact_matches_manifest_and_template():
    _needs_data(TEMPLATE, LABELS)
    tif = ROOT / "docs/downloads" / f"{PRIMARY_R6}.tif"
    manifest = json.loads((ROOT / "docs/downloads" / f"{PRIMARY_R6}.json").read_text())
    assert tif.is_file(), "shipped Round-6 artifact missing"

    report = validate(tif, TEMPLATE)
    assert report["sha256"] == manifest["files"]["primary_tif"]["validation"]["sha256"]
    assert report["valid_pixels"] == 5167373
    assert 0.0 <= report["min"] and report["max"] <= 1.0

    with rasterio.open(tif) as s:
        assert s.count == 1 and s.dtypes == ("float32",)
        assert s.crs.to_string() == "EPSG:32611"
        assert s.shape == (3730, 3292)
        arr = s.read(1)
        mask = s.read_masks(1) > 0
    assert np.isfinite(arr[mask]).all()
    assert np.isnan(arr[~mask]).all()
    emitted = int((arr[mask] > 0).sum())
    assert emitted == manifest["policy"]["emitted_pixels"] == 103347
    assert set(np.unique(arr[mask]).tolist()) == {0.0, 1.0}

    from scipy.ndimage import convolve
    counts = convolve((arr > 0).astype("int32"), np.ones((5, 5), "int32"), mode="constant")
    assert counts[arr > 0].max() == 1, "two emitted pixels share one 300 m cell"

    with rasterio.open(LABELS) as s:
        labels = (s.read(1, masked=True).filled(0) > 0) & mask
    assert not (labels & (arr > 0)).any(), "new fault cannot be catalogue pixel"


def test_r6_fallback_is_finite_and_matches_primary():
    _needs_data(TEMPLATE)
    fb = ROOT / "docs/downloads" / f"{PRIMARY_R6}_allfinite.tif"
    assert fb.is_file()
    with rasterio.open(fb) as s:
        arr = s.read(1)
    assert np.isfinite(arr).all()
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    with rasterio.open(ROOT / "docs/downloads" / f"{PRIMARY_R6}.tif") as s:
        prim = s.read(1)
    assert np.array_equal((prim > 0), (arr > 0)), "fallback must carry identical predictions"


def test_r6_zip_contains_one_geotiff():
    import hashlib
    z = ROOT / "docs/downloads" / f"{PRIMARY_R6}.zip"
    assert z.is_file()
    with zipfile.ZipFile(z) as f:
        names = f.namelist()
    assert names == [f"{PRIMARY_R6}.tif"]
    with zipfile.ZipFile(z) as f, open(ROOT / "docs/downloads" / f"{PRIMARY_R6}.tif", "rb") as g:
        assert hashlib.sha256(f.read(names[0])).hexdigest() == hashlib.sha256(g.read()).hexdigest()
