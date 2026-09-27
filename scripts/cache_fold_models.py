"""Re-train the frozen masked-holdout GBM arms and cache their probability fields.

Purpose (session 2026-09-27, round 5):
  1. Independent reproduction check of the committed headline numbers in
     evidence/holdout_masked.json (raw19 / multi25 / multi30 / random02) using
     the *same* protocol code path as scripts/holdout_masked.py, without
     overwriting that committed evidence file.
  2. Cache each fold's per-pixel probability field for the downstream round-5
     experiments (emission-policy sweep, new geological arms) so the GBM is
     trained once instead of once per experiment.

The training recipe below is copied deliberately from scripts/holdout_masked.py
(same seed, same negative subsample size, same class weights, same estimator
hyper-parameters, same chunked prediction, same RNG call order) so that the
DTI values are directly comparable and the random02 control is bit-identical.

Outputs (all under data/, which is git-ignored):
  data/cache/prob-<arm>-fold<k>.npz   keys: idx (int64), prob (float32)
  data/cache/reproduction.json        reproduction report vs committed evidence
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, training_mask, sha

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
BUDGET = 0.02
ARMS = [("raw19", 19), ("multi25", 25), ("multi30", 30)]


def components_masked(p, truth_test, region, catalogue):
    """DTI with the official pixel-exact catalogue mask on the FP term."""
    p = np.where(region, p, 0).astype("float64")
    t = truth_test & region
    yy, xx = np.nonzero(t)
    credit = np.zeros(len(yy), dtype="float64")
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            k = max(1 - np.hypot(dy, dx) / 3, 0)
            y, x = yy + dy, xx + dx
            v = (y >= 0) & (x >= 0) & (y < p.shape[0]) & (x < p.shape[1])
            credit[v] = np.maximum(credit[v], p[y[v], x[v]] * k)
    tp = float(credit.sum())
    fn = float(len(yy) - tp)
    weight = np.minimum(distance_transform_edt(~t) / 3, 1) if t.any() else np.ones(t.shape)
    fpable = region & ~catalogue
    fp = float(np.sum(p * weight * fpable, dtype="float64"))
    return dict(tp=tp, fp=fp, fn=fn, dti=tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7))


def topk_binary(score, region, frac):
    """Verbatim copy of holdout_masked.topk_binary (deterministic tie-break)."""
    idx = np.flatnonzero(region)
    order = np.lexsort((idx, -score.ravel()[idx]))
    k = int(frac * len(idx))
    pred = np.zeros(score.shape, dtype="float32")
    pred.ravel()[idx[order[:k]]] = 1.0
    return pred


def main() -> None:
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        truth = (s.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    assert cube.shape == (*shape, 30), cube.shape
    flat = cube.reshape(-1, 30)
    fmap = folds(truth)

    report = {
        "purpose": "reproduce evidence/holdout_masked.json arms and cache per-fold "
                   "probability fields for round-5 experiments",
        "protocol": "masked spatial holdout, official pixel-exact catalogue mask on FP; "
                    "binary top-2% emission; 512px blocks; 12px collar; seed 12027",
        "budget": BUDGET,
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "feature_build_code_sha256": json.loads(
            (ROOT / "evidence/feature-build.json").read_text())["code_sha256"],
        "folds": [],
    }

    for fold in range(4):
        start = time.time()
        train = training_mask(fmap, fold, valid)
        region = valid & (fmap == fold)
        test_truth = truth & region
        rng = np.random.default_rng(12027 + fold)
        pos = np.flatnonzero(train & truth)
        neg_all = np.flatnonzero(train & ~truth)
        neg = rng.choice(neg_all, min(100000, len(neg_all)), replace=False)
        idx = np.concatenate([pos, neg])
        y = truth.ravel()[idx]
        weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(idx)
        testidx = np.flatnonzero(region)
        row = {"fold": fold, "train_positive": int(len(pos)),
               "train_negative": int(len(neg)), "score_pixels": int(len(testidx)),
               "score_positive": int(test_truth.sum()), "arms": {}}

        probe = binary_dilation(truth & train, iterations=3).astype("float32")
        row["leakage_probe_dti"] = components_masked(probe, test_truth, region, truth)["dti"]

        for name, n_feat in ARMS:
            clf = HistGradientBoostingClassifier(
                max_iter=100, max_leaf_nodes=15, early_stopping=False,
                random_state=12027)
            clf.fit(flat[idx, :n_feat], y, sample_weight=weights)
            prob = np.empty(len(testidx), dtype="float32")
            for s0 in range(0, len(testidx), 100000):
                ids = testidx[s0:s0 + 100000]
                prob[s0:s0 + len(ids)] = clf.predict_proba(flat[ids, :n_feat])[:, 1]
            np.savez_compressed(CACHE / f"prob-{name}-fold{fold}.npz",
                                idx=testidx, prob=prob)
            score = np.zeros(shape, dtype="float32")
            score.ravel()[testidx] = prob
            row["arms"][name] = components_masked(
                topk_binary(score, region, BUDGET), test_truth, region, truth)

        # random02 control: same RNG call order as holdout_masked.py.
        pred = np.zeros(shape, dtype="float32")
        pred.ravel()[rng.choice(testidx, int(BUDGET * len(testidx)), replace=False)] = 1.0
        row["arms"]["random02"] = components_masked(pred, test_truth, region, truth)
        row["seconds"] = round(time.time() - start, 2)
        report["folds"].append(row)
        print(f"fold {fold} ({row['seconds']}s) probe={row['leakage_probe_dti']:.4f} "
              + " ".join(f"{a}={row['arms'][a]['dti']:.5f}"
                         for a in ["raw19", "multi25", "multi30", "random02"]),
              flush=True)

    names = ["raw19", "multi25", "multi30", "random02"]
    report["means"] = {a: float(np.mean([r["arms"][a]["dti"] for r in report["folds"]]))
                       for a in names}
    committed = json.loads((ROOT / "evidence/holdout_masked.json").read_text())
    diffs = {}
    for a in names:
        mine = report["means"][a]
        theirs = committed["means"][a]
        per_fold = [round(r["arms"][a]["dti"] - c["arms"][a]["dti"], 12)
                    for r, c in zip(report["folds"], committed["folds"])]
        diffs[a] = {"reproduced_mean": mine, "committed_mean": theirs,
                    "abs_mean_delta": abs(mine - theirs),
                    "per_fold_delta": per_fold,
                    "exact_per_fold": all(d == 0.0 for d in per_fold)}
    report["reproduction_vs_committed"] = diffs
    report["total_seconds"] = round(time.time() - t0, 2)
    (CACHE / "reproduction.json").write_text(json.dumps(report, indent=2))
    print("reproduction:", json.dumps({a: diffs[a]["exact_per_fold"] for a in names}))
    print("means:", json.dumps(report["means"]))


if __name__ == "__main__":
    main()
