"""Round-8 locks: preregistration, the sibling audit, the metric algebra, the frozen gate.

These tests encode the evidence contract of Round 8: the register existed before the run, the
gate is a pure function of the recorded numbers, the R7 incumbent reproduced exactly inside the
harness, and no artifact is shipped that a failed gate did not authorise.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _needs_data(*paths):
    for p in paths:
        if not Path(p).is_file():
            pytest.skip(f"requires git-ignored data file: {p} (run scripts/download_competition_data.sh)")


def test_register_preregisters_h37_to_h41_and_records_results():
    text = (ROOT / "docs/hypotheses-round8.md").read_text()
    for hid in ("H37", "H38", "H39", "H40", "H41"):
        assert hid in text, f"{hid} missing from the Round-8 register"
    assert "3.4 Register amendment" in text, "the dated amendment must be recorded, not silently edited in"
    assert "before the frozen run" in text
    # the marginal-inclusion rule must be stated in the register (symbol-for-symbol check)
    assert "0.2·D/(1−0.2·D)" in text or "0.2*D/(1-0.2*D)" in text
    assert "0.0323" in text and "0.0677" in text, "register must carry both derived thresholds"
    assert "gate" in text.lower() and "leakage probe" in text.lower()
    # the results section must be present once the frozen run has happened, with its verdict
    if (ROOT / "evidence/holdout_round8.json").is_file():
        assert "6. Frozen-run results" in text
        assert "no artifact was packaged and no DrivenData slot was spent" in text
        assert "0.24586" in text and "0.12732" in text, "results must quote the reproduced R7 numbers"


def test_sibling_audit_is_self_consistent():
    audit = json.loads((ROOT / "evidence/sibling-audit.json").read_text())
    assert audit["catalogue"]["sample_submission_is_catalogue_bit_for_bit"] is True
    assert audit["catalogue"]["catalogue_pixels"] == 60988
    assert audit["catalogue"]["existing_faults_identical_to_labels"] is True
    ens = "7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15"
    group = audit["duplicate_groups"][ens]
    repos = {entry.split(":")[0] for entry in group}
    assert {"GEMSDOE", "5GEMSDOE"} <= repos, "the ens12 file must be found in both sites' repos"
    assert len(group) >= 5
    for repo in ("GEMSDOE", "5GEMSDOE"):
        offers = audit["repos"][repo]["site_offers"]
        hits = [h for hs in offers.values() for h in hs if "ens12-adopted-floor0.1-w0" in h]
        assert hits, f"{repo} site must offer the ens12 artifact"


def test_metric_algebra_round_trips():
    alg = json.loads((ROOT / "evidence/metric-algebra.json").read_text())
    for name, row in alg["files"].items():
        E, dti = row["E_chargeable_bound"], row["score"]
        for n_t, cov in row["coverage_locus_lower_bound"].items():
            N = int(n_t)
            T = cov * N
            reconstructed = T / (0.2 * T + 0.2 * E + 0.8 * N)
            assert abs(reconstructed - dti) < 5e-4, (name, n_t, reconstructed, dti)
    assert abs(alg["thresholds"]["0.1563"] - 0.03227) < 1e-4
    assert abs(alg["thresholds"]["0.3168"] - 0.06765) < 1e-4


def _load_gate():
    path = ROOT / "evidence/holdout_round8.json"
    if not path.is_file():
        pytest.skip("evidence/holdout_round8.json not generated in this checkout")
    return json.loads(path.read_text())


def test_gate_is_a_pure_function_of_recorded_numbers():
    rep = _load_gate()
    g = rep["gate"]
    beats = (g["chosen_dense"] > g["incumbent_dense_2pct"]
             and g["chosen_sparse"] > g["incumbent_sparse_2pct"])
    expected = bool(g["leakage_probe_max"] == 0.0
                    and g["r7_reproduced_within"] < 5e-4
                    and (beats or g["chosen_budget"] != 0.02 or g["h39_passed"]))
    assert bool(g["passed"]) == expected
    assert g["chosen_arm"] in rep["arms"]
    assert g["chosen_budget"] in rep["budgets"]
    # the frozen decision rule: the chosen budget must be the sweep's argmax of min(dense, sparse)
    # whenever a non-2% budget beats 2% on >=3/4 folds on BOTH protocols; the recorded outcome
    # is that none did, so the frozen 2% stands.
    swept = {float(k): v for k, v in g["budget_sweep"].items()}
    ok = [b for b, row in swept.items() if b != 0.02
          and row["dense_fold_wins_vs_2pct"] >= 3 and row["sparse_fold_wins_vs_2pct"] >= 3]
    if ok:
        assert g["chosen_budget"] == max(ok, key=lambda b: swept[b]["min_mean"])
    else:
        assert g["chosen_budget"] == 0.02, "no budget cleared both protocols, so 2% must stand"
        # and the reason must be on the record: sign disagreement between the two protocols
        assert all(swept[b]["dense_mean"] > swept[0.02]["dense_mean"]
                   and swept[b]["sparse_mean"] < swept[0.02]["sparse_mean"] for b in (0.032, 0.05))


def test_harness_reproduced_round7_exactly():
    rep = _load_gate()
    for proto in ("dense_catalogue_truth", "sparse_thinned_20pct"):
        row = rep["r7_reproduction"][proto]
        assert row["abs_diff"] == 0.0, f"{proto}: harness did not reproduce R7 ({row})"
        assert row["recorded_r7"] == row["rerun_r8"]
    assert rep["protocols"]["dense_catalogue_truth"]["leakage_probe_max"] == 0.0
    assert rep["protocols"]["sparse_thinned_20pct"]["leakage_probe_max"] == 0.0
    assert rep["protocols"]["offset_adjacent_1_3px"]["leakage_probe_max"] == 0.0


def test_h37_control_dominates_in_its_own_protocols_only():
    """The catalogue base layer must gain in protocols whose truth is/derives from the catalogue.

    That is a property of the *harness*, not evidence about the hidden set; the register says so
    and the real-board evidence (staff ruling + the sibling max(ens12, catalogue) artifact) says
    the platform pays nothing for it.
    """
    rep = _load_gate()
    gains = rep["gate"]["h37_control_mean_gain"]
    assert gains["dense_catalogue_truth"] > 0.4
    assert gains["offset_adjacent_1_3px"] > 0.1     # offset truth sits inside the 300 m kernel
    assert gains["offset_far_4_6px_control"] < gains["offset_adjacent_1_3px"]
    assert rep["gate"]["h39_passed"] is False      # the preregistered sparse criterion was not met


def test_no_unfrozen_artifact_is_shipped():
    """A failed gate must leave docs/downloads without any Round-8 artifact."""
    rep = _load_gate()
    r8 = [p for p in (ROOT / "docs/downloads").glob("12GEMSDOE_r8-*")]
    if not rep["gate"]["passed"]:
        assert not r8, f"gate failed but an artifact exists: {[p.name for p in r8]}"
    else:
        assert r8, "gate passed but no artifact was packaged"


def test_docs_copy_matches_evidence():
    evidence = ROOT / "evidence/holdout_round8.json"
    docs = ROOT / "docs/holdout_round8.json"
    if evidence.is_file():
        assert docs.is_file(), "the site needs its own copy of the Round-8 evidence"
        assert docs.read_bytes() == evidence.read_bytes(), "docs copy drifted from evidence"
