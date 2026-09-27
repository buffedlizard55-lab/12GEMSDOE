"""Round-3 preregistered H11 validation against the current multi25 holdout best.

This script is intentionally narrow: it does not select a submission, write a
GeoTIFF, tune on a fold, or combine candidates post hoc.  It uses the frozen
spatial protocol from ``holdout_masked.py`` and tests exactly the arms named in
``docs/hypotheses-round3.md``:

* multi25 — current reproduced reference
* multi25_plus_h11 — same classifier and all settings plus the H11 feature
* h11_standalone — unsupervised top-2% H11 field
* random02 — density control

The catalogue is excluded from the false-positive term exactly as the staff
clarification specifies.  The feature builder reads no labels; labels are used
only to split, fit the known-fault proxy, and score the holdout.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, training_mask, sha
from holdout_masked import BUDGET, components_masked, topk_binary

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data/candidate-features-30.npy"
H11 = ROOT / "data/h11_drainage_deflection.npy"


def predict_classifier(clf: HistGradientBoostingClassifier, cube_flat: np.ndarray,
                       h11_flat: np.ndarray | None, testidx: np.ndarray) -> np.ndarray:
    """Chunked prediction, appending H11 only after all baseline columns."""
    out = np.empty(len(testidx), dtype="float32")
    for start in range(0, len(testidx), 100_000):
        ids = testidx[start:start + 100_000]
        x = cube_flat[ids, :25]
        if h11_flat is not None:
            x = np.column_stack((x, h11_flat[ids]))
        out[start:start + len(ids)] = clf.predict_proba(x)[:, 1]
    return out


def fit_and_score(name: str, n_features: int, flat: np.ndarray, h11_flat: np.ndarray,
                  idx: np.ndarray, y: np.ndarray, weights: np.ndarray, testidx: np.ndarray,
                  region: np.ndarray, test_truth: np.ndarray, catalogue: np.ndarray) -> dict:
    """Fit one fixed model and return the literal masked DTI components."""
    x_train = flat[idx, :n_features]
    if name == "multi25_plus_h11":
        x_train = np.column_stack((x_train, h11_flat[idx]))
    clf = HistGradientBoostingClassifier(
        max_iter=100, max_leaf_nodes=15, early_stopping=False,
        random_state=12027,
    )
    clf.fit(x_train, y, sample_weight=weights)
    prob = predict_classifier(clf, flat, h11_flat if name == "multi25_plus_h11" else None,
                              testidx)
    score = np.zeros(region.shape, dtype="float32")
    score.ravel()[testidx] = prob
    pred = topk_binary(score, region, BUDGET)
    return components_masked(pred, test_truth, region, catalogue)


def main() -> None:
    started = time.time()
    required = [CUBE, H11, ROOT / "data/sample_submission.tif", ROOT / "data/labels.tif",
                ROOT / "evidence/h11-feature-build.json"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("build verified inputs first: " + ", ".join(missing))

    with rasterio.open(ROOT / "data/sample_submission.tif") as ds:
        valid = ds.read_masks(1) > 0
        shape = ds.shape
    with rasterio.open(ROOT / "data/labels.tif") as ds:
        truth = (ds.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(CUBE), mode="r")
    if cube.shape != (*shape, 30):
        raise ValueError(f"unexpected candidate cube shape {cube.shape}")
    h11 = np.load(H11, mmap_mode="r", allow_pickle=False)
    if h11.shape != shape or not np.isfinite(h11[valid]).all():
        raise ValueError("invalid H11 feature")

    build = json.loads((ROOT / "evidence/h11-feature-build.json").read_text())
    flat = cube.reshape(-1, 30)
    h11_flat = h11.ravel()
    fmap = folds(truth)
    report: dict = {
        "protocol": "round3 preregistered masked spatial holdout; official pixel-exact "
                    "catalogue mask on FP; binary top-2% emission; 512px blocks; "
                    "12px collar; seed 12027",
        "preregistered_register": "docs/hypotheses-round3.md",
        "budget": BUDGET,
        "h11_feature_sha256": build["output"]["sha256"],
        "h11_feature_code_sha256": build["code_sha256"],
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "arms": {
            "multi25": "Existing current holdout reference: GBM on 25 channels.",
            "multi25_plus_h11": "Same GBM plus the label-free H11 feature.",
            "h11_standalone": "Unsupervised H11 score emitted at same 2% budget.",
            "random02": "Fixed-seed random equal-density control.",
        },
        "folds": [],
    }

    for fold in range(4):
        started_fold = time.time()
        train = training_mask(fmap, fold, valid)
        region = valid & (fmap == fold)
        test_truth = truth & region
        # No train pixels are scored.  This invariant prevents the known trace
        # itself from leaking into a 300m DTI kernel on the test region.
        if np.any(train & region):
            raise AssertionError("training/scoring overlap")
        rng = np.random.default_rng(12027 + fold)
        pos = np.flatnonzero(train & truth)
        neg_pool = np.flatnonzero(train & ~truth)
        neg = rng.choice(neg_pool, min(100_000, len(neg_pool)), replace=False)
        idx = np.concatenate((pos, neg))
        y = truth.ravel()[idx]
        weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(idx)
        testidx = np.flatnonzero(region)
        row: dict = {
            "fold": fold,
            "train_positive": int(len(pos)),
            "train_negative": int(len(neg)),
            "score_pixels": int(len(testidx)),
            "score_positive": int(test_truth.sum()),
            "arms": {},
        }
        probe = binary_dilation(truth & train, iterations=3).astype("float32")
        row["leakage_probe_dti"] = components_masked(probe, test_truth, region, truth)["dti"]
        row["arms"]["multi25"] = fit_and_score(
            "multi25", 25, flat, h11_flat, idx, y, weights, testidx, region, test_truth, truth)
        row["arms"]["multi25_plus_h11"] = fit_and_score(
            "multi25_plus_h11", 25, flat, h11_flat, idx, y, weights, testidx, region, test_truth, truth)

        h11_pred = topk_binary(np.asarray(h11), region, BUDGET)
        row["arms"]["h11_standalone"] = components_masked(h11_pred, test_truth, region, truth)
        random_score = np.zeros(shape, dtype="float32")
        n_emit = int(BUDGET * len(testidx))
        random_score.ravel()[rng.choice(testidx, n_emit, replace=False)] = 1.0
        row["arms"]["random02"] = components_masked(random_score, test_truth, region, truth)
        row["seconds"] = round(time.time() - started_fold, 2)
        report["folds"].append(row)
        print(
            f"fold {fold} ({row['seconds']}s) probe={row['leakage_probe_dti']:.4f} "
            f"multi25={row['arms']['multi25']['dti']:.5f} "
            f"plus_h11={row['arms']['multi25_plus_h11']['dti']:.5f} "
            f"h11={row['arms']['h11_standalone']['dti']:.5f} "
            f"random={row['arms']['random02']['dti']:.5f}",
            flush=True,
        )

    for arm in report["arms"]:
        report[f"mean_{arm}"] = float(np.mean([r["arms"][arm]["dti"] for r in report["folds"]]))
    paired = [float(r["arms"]["multi25_plus_h11"]["dti"] - r["arms"]["multi25"]["dti"])
              for r in report["folds"]]
    report["paired_multi25_plus_h11_vs_multi25"] = paired
    report["wins_multi25_plus_h11"] = int(sum(x > 0 for x in paired))
    passed = bool(np.mean(paired) > 0 and report["wins_multi25_plus_h11"] >= 3)
    report["release_allowed"] = False
    report["release_gate"] = {
        "predeclared": "positive mean paired DTI and >=3/4 fold wins over multi25",
        "passed": passed,
        "decision": ("PASS research gate only; strongest reproducible sibling baseline and "
                     "independent final gate still required" if passed else
                     "REJECT H11 as a submission upgrade; no weekly slot and no new submission artifact"),
    }
    report["total_seconds"] = round(time.time() - started, 2)
    for path in [ROOT / "evidence/holdout_round3_h11.json", ROOT / "docs/holdout_round3_h11.json"]:
        path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k.startswith("mean_") or
                      k in {"wins_multi25_plus_h11", "release_gate"}}, indent=2))


if __name__ == "__main__":
    main()
