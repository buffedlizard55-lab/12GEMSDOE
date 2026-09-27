"""Round-5 regression tests: NMS emission geometry, artifact conformance, evidence.

These tests execute the code that produced the shipped Round-5 artifact:
  * scripts/generate_nms_submission.nms_select  (the emitter itself)
  * scripts/core.validate                        (the format gate)
  * the shipped GeoTIFF in docs/downloads/
and lock the invariants that the Round-5 claim depends on.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core import validate                                  # noqa: E402
from generate_nms_submission import RADIUS, nms_select     # noqa: E402

PRIMARY = "12GEMSDOE_r5-nms3-trace_055e9aac96b8"
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"


def _needs_data(*paths):
    for p in paths:
        if not Path(p).is_file():
            pytest.skip(f"requires git-ignored data file: {p} "
                        "(run scripts/download_competition_data.sh)")


def _ordered(score):
    idx = np.flatnonzero(score.ravel())
    return idx[np.lexsort((idx, -score.ravel()[idx]))]


def test_nms_select_enforces_the_five_by_five_exclusion():
    """No two selected pixels may share a (2*RADIUS+1)^2 credit cell."""
    rng = np.random.default_rng(7)
    shape = (120, 137)
    score = rng.random(shape).astype("float32")
    ordered = _ordered(score)
    budget = 200
    sel = nms_select(ordered, shape, budget)
    assert len(sel) == budget
    ys, xs = np.divmod(sel, shape[1])
    # every pair must differ by more than RADIUS in y or in x
    dy = np.abs(ys[:, None] - ys[None, :])
    dx = np.abs(xs[:, None] - xs[None, :])
    clash = (dy <= RADIUS) & (dx <= RADIUS)
    np.fill_diagonal(clash, False)
    assert not clash.any(), "two emitted pixels share one 300 m credit cell"


def test_nms_select_respects_score_order_and_is_deterministic():
    rng = np.random.default_rng(11)
    shape = (60, 60)
    score = rng.random(shape).astype("float32")
    ordered = _ordered(score)
    a = nms_select(ordered, shape, 50)
    b = nms_select(ordered, shape, 50)
    assert np.array_equal(a, b), "emission must be deterministic for a fixed field"
    # the first selection is the global maximum of the field
    assert a[0] == int(np.argmax(score))
    # scores along the selection order are non-increasing
    vals = score.ravel()[a]
    assert np.all(np.diff(vals) <= 0), "greedy NMS must follow descending score"


def test_nms_select_stops_early_when_budget_is_unreachable():
    """A fully blocked field cannot over-emit; the function returns what it made."""
    shape = (9, 9)
    score = np.ones(shape, dtype="float32")
    ordered = _ordered(score)
    sel = nms_select(ordered, shape, 10_000)
    assert 0 < len(sel) <= int(np.ceil(9 / (2 * RADIUS + 1))) ** 2 + 9


def test_shipped_artifact_matches_its_manifest_and_the_template():
    _needs_data(TEMPLATE, LABELS)
    tif = ROOT / "docs/downloads" / f"{PRIMARY}.tif"
    manifest = json.loads((ROOT / "docs/downloads" / f"{PRIMARY}.json").read_text())
    assert tif.is_file(), "shipped Round-5 artifact is missing"

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
    assert np.isfinite(arr[mask]).all(), "footprint pixels must be finite"
    assert np.isnan(arr[~mask]).all(), "outside the footprint must be strict NaN"
    emitted = int((arr[mask] > 0).sum())
    assert emitted == manifest["policy"]["emitted_pixels"] == 103347
    assert set(np.unique(arr[mask]).tolist()) == {0.0, 1.0}, "binary thin-trace emission"
    # the metric claim: no two emitted pixels inside one 5x5 credit cell.
    # Checked in O(N) with a 5x5 count filter instead of an O(N^2) pair scan.
    from scipy.ndimage import convolve
    counts = convolve((arr > 0).astype("int32"), np.ones((5, 5), "int32"),
                      mode="constant")
    assert counts[arr > 0].max() == 1, "two emitted pixels share one 300 m cell"

    with rasterio.open(LABELS) as s:
        labels = (s.read(1, masked=True).filled(0) > 0) & mask
    assert not (labels & (arr > 0)).any(), "a new fault cannot be a catalogue pixel"


def test_fallback_variant_is_finite_and_in_range_everywhere():
    _needs_data(TEMPLATE)
    fb = ROOT / "docs/downloads" / f"{PRIMARY}_allfinite.tif"
    assert fb.is_file()
    with rasterio.open(fb) as s:
        arr = s.read(1)
    assert np.isfinite(arr).all()
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert bool(np.all((arr >= 0) & (arr <= 1))) is True
    with rasterio.open(ROOT / "docs/downloads" / f"{PRIMARY}.tif") as s:
        prim = s.read(1)
    assert np.array_equal((prim > 0), (arr > 0)), "fallback must carry identical predictions"


def test_zip_contains_exactly_one_geotiff():
    z = ROOT / "docs/downloads" / f"{PRIMARY}.zip"
    assert z.is_file()
    with zipfile.ZipFile(z) as f:
        names = f.namelist()
    assert names == [f"{PRIMARY}.tif"], names
    with zipfile.ZipFile(z) as f, open(ROOT / "docs/downloads" / f"{PRIMARY}.tif", "rb") as g:
        assert hashlib.sha256(f.read(names[0])).hexdigest() == hashlib.sha256(
            g.read()).hexdigest()


def test_round5_evidence_records_the_preregistered_gate():
    ev = json.loads((ROOT / "evidence/holdout_round5.json").read_text())
    assert ev["budget"] == 0.02 and ev["nms_radius"] == 2
    assert ev["release_allowed"] is False
    for protocol, blk in ev["truth_protocols"].items():
        gate = blk["gate_a_folds23_nms3_vs_topk_multi25"]
        assert gate["passed"] is True, f"emission gate regressed on {protocol}"
        assert gate["nms3"] > 2 * gate["topk"]
        # every fold's leakage probe must stay at zero
        for row in blk["folds"]:
            assert row["leakage_probe_dti"] == 0.0
    # The preregistered adoption rule (register section 5c): a geological arm is
    # adopted only if it beats the same-emission multi25 reference on >=3/4 folds
    # on BOTH truth protocols. Record which arms would qualify; the Round-5
    # result is that none does, and the site says so.
    protocols = ev["truth_protocols"]
    arms = set(protocols["dense_catalogue_truth"]["fold_wins_vs_multi25_nms3"])
    qualifying = [a for a in arms if a != "multi25" and all(
        protocols[p]["fold_wins_vs_multi25_nms3"][a] >= 3 for p in protocols)]
    assert qualifying == [], (
        f"arms {qualifying} now pass the >=3/4-on-both-protocols rule: update "
        "docs/hypotheses-round5.md and the site before shipping this assertion")


def test_round5_identity_checks_are_present_and_label_free():
    ident = json.loads((ROOT / "evidence/round5-identity-checks.json").read_text())
    assert ident["labels_used"] is False
    c1 = ident["C1_sentinel_audit"]
    assert c1["any_band_with_sentinel_inside_footprint"] is True
    assert c1["unmasked_read_min_over_all_bands"] < -1e38
    assert ident["C3_tc_identity"]["tc_all_positive_inside_core"] is True
    assert abs(ident["C3_tc_identity"]["corr_tc_abs_tilt"]) < 0.05
    for name, row in ident["C4_distinctness"]["candidates"].items():
        if row["max_abs_corr"] == row["max_abs_corr"]:  # not NaN
            assert row["max_abs_corr"] < 0.50, f"{name} is not mechanism-distinct"


def test_round5_feature_sidecar_is_label_free_and_distinct():
    side = json.loads((ROOT / "evidence/round5-feature-build.json").read_text())
    assert side["labels_used"] is False
    for name, row in side["cross_correlation"].items():
        assert row["max_abs_corr"] < 0.50, f"{name} duplicates an existing channel"
