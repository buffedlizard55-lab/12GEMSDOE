import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_round4_features as r4

ROOT = Path(__file__).resolve().parents[1]


def test_line_kernels_average_and_cover_four_orientations():
    ks = r4.line_kernels()
    assert len(ks) == 4
    for k in ks:
        assert k.shape == (9, 9)
        assert abs(k.sum() - 1.0) < 1e-12


def test_robust_unit_bounds_and_monotone():
    rng = np.random.default_rng(7)
    a = rng.normal(size=(40, 40))
    v = np.ones(a.shape, bool)
    out = r4.robust_unit(a, v)
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert (np.diff(np.sort(out.ravel())) >= -1e-12).all()


def test_h17_guard_rejects_magnitude_only_input():
    vg = np.abs(np.random.default_rng(3).normal(size=(30, 30))) + 0.5
    hg = np.random.default_rng(4).normal(size=(30, 30))
    v = np.ones(vg.shape, bool)
    with pytest.raises(ValueError, match="no VG sign change"):
        r4.build_h17(vg, hg, v)


def test_h17_detects_synthetic_vertical_contact():
    yy, xx = np.indices((60, 60))
    vg = (xx - 30).astype("float64")  # zero contour at x=30
    hg = np.exp(-((xx - 30) ** 2) / 8.0)  # ridge centered on the contour
    v = np.ones(vg.shape, bool)
    out = r4.build_h17(vg, hg, v)
    assert out[:, 28:33].mean() > out[:, :10].mean() + 0.2


def test_h15_rewards_aligned_fields_over_opposed_noise():
    rng = np.random.default_rng(11)
    yy, xx = np.indices((60, 60))
    step = (xx >= 30).astype("float64")
    aligned = [step + 0.01 * rng.normal(size=step.shape) for _ in range(4)]
    noise = [rng.normal(size=step.shape) for _ in range(4)]
    v = np.ones(step.shape, bool)
    a = r4.build_h15(*aligned, v)
    b = r4.build_h15(*noise, v)
    assert a[:, 27:34].mean() > b[:, 27:34].mean() + 0.1


def test_sidecar_labels_unused_when_built():
    p = ROOT / "evidence/round4-feature-build.json"
    if not p.exists():
        pytest.skip("round-4 features not built in this checkout")
    side = json.loads(p.read_text())
    assert side["labels_used"] is False
    assert side["preregistered_register"] == "docs/hypotheses-round4.md"
    arr = np.load(ROOT / "data/round4_features.npy", mmap_mode="r")
    assert arr.shape[2] == 4 and np.isfinite(arr).all()


def test_holdout_report_schema_when_present():
    p = ROOT / "evidence/holdout_round4.json"
    if not p.exists():
        pytest.skip("round-4 holdout not run in this checkout")
    rep = json.loads(p.read_text())
    assert rep["primary_arm"] == "multi25_plus_h15"
    assert rep["release_allowed"] is False
    assert len(rep["folds"]) == 4
    for row in rep["folds"]:
        assert row["leakage_probe_dti"] == pytest.approx(0.0, abs=1e-9)
        for arm in ("multi25", "multi25_plus_h15", "h6prime_hybrid",
                    "h15_standalone", "random02"):
            assert arm in row["arms"]
    assert "terminal_mechanism_check" in rep
