"""Round-2 regression tests: masked metric, audit consistency, detectors.

No competition data required; all fixtures are synthetic.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from core import components
from holdout_masked import components_masked, topk_binary


def test_masked_metric_equals_unmasked_without_catalogue():
    rng = np.random.default_rng(3)
    p = rng.random((15, 15))
    t = rng.random((15, 15)) > 0.85
    region = np.ones(t.shape, bool)
    a = components(p, t, region)
    b = components_masked(p, t, region, np.zeros(t.shape, bool))
    assert b["tp"] == pytest.approx(a["tp"])
    assert b["fp"] == pytest.approx(a["fp"])
    assert b["fn"] == pytest.approx(a["fn"])
    assert b["dti"] == pytest.approx(a["dti"])


def test_masked_metric_catalogue_pixels_are_free():
    # Predicting exactly the catalogue (which contains the test truth plus
    # extra known traces) must not charge FP for the extra known pixels.
    truth = np.zeros((21, 21), bool)
    truth[10, 5:16] = True
    catalogue = truth.copy()
    catalogue[2, 2:19] = True  # extra known trace far from test truth
    region = np.ones(truth.shape, bool)
    p = catalogue.astype(float)
    got = components_masked(p, truth, region, catalogue)
    assert got["fp"] == pytest.approx(0.0)
    assert got["dti"] == pytest.approx(1.0)
    # Without the mask the same prediction would be heavily penalized.
    unmasked = components(p, truth, region)
    assert unmasked["fp"] > 10


def test_masked_metric_near_catalogue_still_penalized():
    # Staff 11516/4: a predicted pixel near a known trace but far from
    # new-fault truth is fully penalized (no buffer around known faults).
    truth = np.zeros((31, 31), bool)
    truth[25, 25] = True
    catalogue = np.zeros((31, 31), bool)
    catalogue[5, 5] = True
    region = np.ones(truth.shape, bool)
    p = np.zeros((31, 31))
    p[6, 5] = 1.0  # adjacent to known fault, far from test truth
    got = components_masked(p, truth, region, catalogue)
    assert got["fp"] == pytest.approx(1.0)
    assert got["dti"] == pytest.approx(0.0)


def test_topk_binary_exact_budget_and_deterministic_ties():
    score = np.zeros((10, 10), dtype="float32")
    score.ravel()[::2] = 0.5  # all ties
    region = np.ones((10, 10), bool)
    pred = topk_binary(score, region, 0.2)
    assert int(pred.sum()) == 20
    again = topk_binary(score, region, 0.2)
    assert np.array_equal(pred, again)


def test_identity_audit_self_consistent():
    root = Path(__file__).resolve().parents[1]
    ident = json.loads((root / "evidence/identity.json").read_text())
    assert ident["scope"] == "published artifacts, not upload receipts"
    by_name = {r["name"]: r for r in ident["files"]}
    for pair in ident["pairs"]:
        a, b = by_name[pair["a"]], by_name[pair["b"]]
        same_bytes = a["sha256"] == b["sha256"]
        assert pair["same_bytes"] == same_bytes
        if same_bytes:
            # Byte-identical files must compare pixel-equal (NaN-safe).
            assert pair["pixel_equal"] is True
            assert pair["different_pixels"] == 0
            assert pair["fraction_different"] == 0.0
        else:
            assert pair["different_pixels"] > 0
    tie = [p for p in ident["pairs"]
           if {p["a"], p["b"]} == {"gems1", "gems5"}][0]
    assert tie["same_bytes"] is True and tie["different_pixels"] == 0


def test_h6_h8_detectors_smoke_on_synthetic():
    from holdout_masked import h6_detector
    rng = np.random.default_rng(11)
    H, W = 60, 60
    traces = np.zeros((H, W), bool)
    traces[30, 10:40] = True  # one horizontal trace, two endpoints
    rtp = rng.normal(size=(H, W)).astype("float32")
    edge = np.zeros((H, W), dtype="float32")
    edge[30, 40:50] = 5.0  # unsupervised edge beyond the tip
    valid = np.ones((H, W), bool)
    region = np.ones((H, W), bool)
    score, diag = h6_detector(traces, rtp, edge, edge, edge, edge, region, valid)
    assert diag["endpoints"] == 2
    assert diag["gated_pixels"] > 0
    assert score[30, 41] > 0  # gated tip extension fires
    assert (score[traces] == 0).all()  # never emits on source traces


def test_feature_build_sidecar_contract():
    root = Path(__file__).resolve().parents[1]
    sidecar = root / "evidence/feature-build.json"
    if not sidecar.is_file():
        pytest.skip("feature cube not built in this checkout")
    spec = json.loads(sidecar.read_text())
    assert spec["labels_used"] is False
    assert spec["output"]["shape"][2] == 30
    assert len(spec["median_imputation"]) == 19
    assert spec["pixels_with_any_band_nan_inside_template"] > 0
