"""Round-3 regression tests — no competition raster required."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_h11_drainage_feature import line_kernels, valley_bend_alignment


def test_h11_feature_is_finite_and_uses_no_implicit_labels():
    # A smooth synthetic trough is enough to exercise every Hessian, tangent,
    # offset and line-aggregation branch. This is a numerical smoke test, not
    # a claim that the transform identifies a real fault.
    yy, xx = np.indices((48, 48))
    elevation = ((yy - 24) ** 2 + 0.02 * xx).astype("float64")
    slope = np.abs(yy - 24).astype("float64")
    valid = np.ones(elevation.shape, dtype=bool)
    feature = valley_bend_alignment(elevation, slope, valid)
    assert feature.shape == elevation.shape
    assert feature.dtype == np.float32
    assert np.isfinite(feature).all()
    assert (feature >= 0).all() and (feature <= 1).all()
    for kernel in line_kernels():
        assert kernel.shape == (9, 9)
        assert np.isclose(kernel.sum(), 1.0)


def test_round3_result_is_a_rejected_preregistered_candidate():
    report = json.loads((ROOT / "evidence/holdout_round3_h11.json").read_text())
    build = json.loads((ROOT / "evidence/h11-feature-build.json").read_text())
    assert build["labels_used"] is False
    assert report["preregistered_register"] == "docs/hypotheses-round3.md"
    assert len(report["folds"]) == 4
    assert all(r["leakage_probe_dti"] == 0.0 for r in report["folds"])
    deltas = report["paired_multi25_plus_h11_vs_multi25"]
    assert report["wins_multi25_plus_h11"] == sum(d > 0 for d in deltas) == 1
    assert report["mean_multi25_plus_h11"] < report["mean_multi25"]
    assert report["release_allowed"] is False
    assert report["release_gate"]["passed"] is False


def test_round3_register_records_data_access_boundary_and_results():
    register = (ROOT / "docs/hypotheses-round3.md").read_text()
    assert "H11" in register and "H12" in register and "H13" in register and "H14" in register
    assert "SSL_ERROR_SYSCALL" in register
    assert "reject H11 as a submission upgrade" in register
    assert "no GeoTIFF was packaged from H11" in register
