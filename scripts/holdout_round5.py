"""Round-5 frozen gate: emission policy x feature arm, masked spatial holdout.

Preregistered in docs/hypotheses-round5.md section 5 BEFORE this file ran:
  * emission = non-maximum suppression, Chebyshev radius 2 (5x5 block),
    descending probability, deterministic tie-break by pixel index;
  * budget frozen at 0.02 (selected on folds 0-1 only, sparse-truth protocol);
  * gate (a) folds 2-3 sparse protocol: nms3 > top-k for the same model;
    (b) same inequality on the dense protocol;
    (c) a geological arm is adopted only if it beats the same-emission multi25
        reference on >=3/4 folds on BOTH protocols.

Arms
----
  multi25                 reference (cached probabilities, identical to
                          scripts/holdout_masked.py)
  multi25_h15             25 + round-4 H15 (best feature addition so far)
  multi25_h20 .. _h23     25 + one round-5 channel each
Every arm is scored with BOTH emissions (top-k @ 2 % and NMS-3 @ 2 %) and under
BOTH truth protocols (dense catalogue truth; 20 %-thinned sparse truth).

No submission slot is spent. Output: evidence/holdout_round5.json (+ docs copy).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, label as ndi_label
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, sha, training_mask

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
BUDGET = 0.02          # frozen by the preregistered rule (register section 5)
RADIUS = 2
N_BASE = 25
NEW_ARMS = [("multi25_h15", "r4", 0), ("multi25_h20", "r5", 0),
            ("multi25_h21", "r5", 1), ("multi25_h22", "r5", 2),
            ("multi25_h23", "r5", 3)]


def dti_binary(pred, test_truth, region, weight_fp, coords):
    t = test_truth & region
    yy, xx = coords
    credit = np.zeros(len(yy), dtype="float64")
    pv = pred.ravel()
    W = pred.shape[1]
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):
            k = max(1 - np.hypot(dy, dx) / 3, 0)
            y, x = yy + dy, xx + dx
            v = (y >= 0) & (x >= 0) & (y < pred.shape[0]) & (x < pred.shape[1])
            credit[v] = np.maximum(credit[v], pv[y[v] * W + x[v]] * k)
    tp = float(credit.sum())
    fn = float(len(yy) - tp)
    fp = float(np.sum(pred * weight_fp, dtype="float64"))
    return dict(tp=tp, fp=fp, fn=fn, coverage=tp / max(len(yy), 1),
                dti=tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7))


def topk_pred(prob, idx, shape, frac):
    order = np.lexsort((idx, -prob))
    k = int(frac * len(idx))
    pred = np.zeros(shape, dtype="float32")
    pred.ravel()[idx[order[:k]]] = 1.0
    return pred


def nms_select(ordered_pixels, shape, max_sel):
    W = shape[1]
    blocked = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    CHUNK = 50000
    for s0 in range(0, len(ordered_pixels), CHUNK):
        cand = ordered_pixels[s0:s0 + CHUNK]
        ys, xs = np.divmod(cand, W)
        keep = ~blocked[ys, xs]
        for p, y, x in zip(cand[keep], ys[keep], xs[keep]):
            if blocked[y, x]:
                continue
            sel[n] = p
            n += 1
            blocked[max(0, y - RADIUS):y + RADIUS + 1,
                    max(0, x - RADIUS):x + RADIUS + 1] = True
            if n == max_sel:
                return sel
    return sel[:n]


def nms_pred(prob, idx, shape, frac):
    ordered_pixels = idx[np.lexsort((idx, -prob))]
    sel = nms_select(ordered_pixels, shape, int(frac * len(idx)))
    pred = np.zeros(shape, dtype="float32")
    pred.ravel()[sel] = 1.0
    return pred


def main() -> None:
    t_all = time.time()
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        truth = (s.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    flat = cube.reshape(-1, cube.shape[2])
    extra = {"r4": np.lib.format.open_memmap(str(ROOT / "data/round4_features.npy"), mode="r").reshape(-1, 4),
             "r5": np.lib.format.open_memmap(str(ROOT / "data/round5_features.npy"), mode="r").reshape(-1, 4)}
    fmap = folds(truth)

    r5build = json.loads((ROOT / "evidence/round5-feature-build.json").read_text())
    report = {
        "protocol": "masked spatial holdout, official pixel-exact catalogue mask on FP; "
                    "512px blocks; 12px collar; seed 12027; NMS radius 2; budget 0.02",
        "preregistered_register": "docs/hypotheses-round5.md",
        "budget": BUDGET, "nms_radius": RADIUS,
        "budget_selection": "folds 0-1, sparse-truth protocol (register section 5)",
        "round5_feature_sha256": r5build["output"]["sha256"],
        "round5_feature_code_sha256": r5build["code_sha256"],
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "truth_protocols": {},
    }
    arm_names = ["multi25"] + [a for a, _, _ in NEW_ARMS]

    for protocol, thin in (("dense_catalogue_truth", False), ("sparse_thinned_20pct", True)):
        folds_rows, acc = [], {a: {"topk": [], "nms3": []} for a in arm_names}
        for fold in range(4):
            start = time.time()
            train = training_mask(fmap, fold, valid)
            region = valid & (fmap == fold)
            dense_truth = truth & region
            comp, ncomp = ndi_label(dense_truth, structure=np.ones((3, 3), int))
            rng_thin = np.random.default_rng(4242 + fold)
            keep = rng_thin.choice(np.arange(1, ncomp + 1), max(1, int(0.2 * ncomp)),
                                   replace=False)
            sparse_truth = dense_truth & np.isin(comp, keep)
            test_truth = sparse_truth if thin else dense_truth

            weight = np.minimum(distance_transform_edt(~test_truth) / 3, 1)
            weight_fp = (weight * (region & ~truth)).astype("float32")
            coords = np.nonzero(test_truth)
            testidx = np.flatnonzero(region)

            probe = binary_dilation(truth & train, iterations=3).astype("float32")
            row = {"fold": fold, "score_pixels": int(len(testidx)),
                   "score_positive": int(test_truth.sum()),
                   "leakage_probe_dti": dti_binary(probe, test_truth, region,
                                                   weight_fp, coords)["dti"],
                   "arms": {}}

            rng = np.random.default_rng(12027 + fold)
            pos = np.flatnonzero(train & truth)
            neg_all = np.flatnonzero(train & ~truth)
            neg = rng.choice(neg_all, min(100000, len(neg_all)), replace=False)
            tidx = np.concatenate([pos, neg])
            y = truth.ravel()[tidx]
            weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(tidx)

            def score_arm(name, prob):
                for emis, fn in (("topk", topk_pred), ("nms3", nms_pred)):
                    r = dti_binary(fn(prob, testidx, shape, BUDGET), test_truth,
                                   region, weight_fp, coords)
                    row["arms"][f"{name}_{emis}"] = r
                    acc[name][emis].append(r["dti"])

            data = np.load(CACHE / f"prob-multi25-fold{fold}.npz")
            assert np.array_equal(data["idx"], testidx), "cache/region mismatch"
            score_arm("multi25", data["prob"])

            for name, src, ch in NEW_ARMS:
                X = np.column_stack([flat[tidx, :N_BASE], extra[src][tidx, ch]])
                clf = HistGradientBoostingClassifier(
                    max_iter=100, max_leaf_nodes=15, early_stopping=False,
                    random_state=12027)
                clf.fit(X, y, sample_weight=weights)
                prob = np.empty(len(testidx), dtype="float32")
                for s0 in range(0, len(testidx), 100000):
                    ids = testidx[s0:s0 + 100000]
                    Xi = np.column_stack([flat[ids, :N_BASE], extra[src][ids, ch]])
                    prob[s0:s0 + len(ids)] = clf.predict_proba(Xi)[:, 1]
                score_arm(name, prob)
                del X
            row["seconds"] = round(time.time() - start, 2)
            folds_rows.append(row)
            print(f"[{protocol}] fold {fold} ({row['seconds']}s) "
                  f"probe={row['leakage_probe_dti']:.4f} " +
                  " ".join(f"{a}:{row['arms'][a + '_nms3']['dti']:.5f}" for a in arm_names),
                  flush=True)

        means = {f"{a}_{e}": float(np.mean(acc[a][e])) for a in arm_names for e in ("topk", "nms3")}
        paired = {a: [round(x - y, 6) for x, y in zip(acc[a]["nms3"], acc["multi25"]["nms3"])]
                  for a in arm_names}
        wins = {a: int(sum(d > 0 for d in paired[a])) for a in arm_names}
        report["truth_protocols"][protocol] = {
            "folds": folds_rows, "means": means,
            "paired_vs_multi25_nms3": paired, "fold_wins_vs_multi25_nms3": wins,
            "gate_a_folds23_nms3_vs_topk_multi25": {
                "nms3": float(np.mean(acc["multi25"]["nms3"][2:])),
                "topk": float(np.mean(acc["multi25"]["topk"][2:])),
                "passed": bool(np.mean(acc["multi25"]["nms3"][2:]) >
                               np.mean(acc["multi25"]["topk"][2:]))},
            "best_arm_nms3": max(arm_names, key=lambda a: means[f"{a}_nms3"]),
        }
    report["total_seconds"] = round(time.time() - t_all, 2)
    report["release_allowed"] = False
    report["release_reason"] = (
        "Standing strongest-sibling-baseline gate unsatisfied: no sibling model "
        "has been reproduced under this protocol. No DrivenData submission slot "
        "is spent by this script.")
    (ROOT / "evidence/holdout_round5.json").write_text(json.dumps(report, indent=2))
    (ROOT / "docs/holdout_round5.json").write_text(json.dumps(report, indent=2))
    for protocol, blk in report["truth_protocols"].items():
        print(f"\n== {protocol}")
        for k, v in sorted(blk["means"].items(), key=lambda kv: -kv[1]):
            print(f"   {k:<22s} {v:.5f}")
        print("   gate_a:", blk["gate_a_folds23_nms3_vs_topk_multi25"])
        print("   fold wins vs multi25_nms3:", blk["fold_wins_vs_multi25_nms3"])


if __name__ == "__main__":
    main()
