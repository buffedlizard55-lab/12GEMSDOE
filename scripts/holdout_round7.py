"""Round-7 frozen gate: NMS emission x H32 sub-100 m scarp channels, masked spatial holdout.

Preregistered in docs/hypotheses-round7.md section 3 BEFORE this file was written:
  * emission = NMS radius 2 (5x5), descending probability, deterministic tie-break
  * budget frozen at 0.02 (selected on folds 0-1 sparse in Round-5)
  * gate: multi25_h28_dem12 > multi25_h28 on >=3/4 folds on BOTH truth protocols
          AND mean paired gain > 0 on both (Round-7 addition, register section 3.4a)
  * leakage probe 0.0 every fold
  * distinctness reported per channel (evidence/round7-feature-build.json)

Arms
----
  multi25              reference (25-channel)
  multi25_h28          Round-6 incumbent (25 + H28 mag texture variance), retrained
  multi25_h28_dem12    H32 primary: incumbent + 12 DEM-10 m channels
  multi25_dem12        ablation: 25 + 12 DEM-10 m channels, no H28
  multi25_h28_dem3     distinct-only subset: incumbent + {steep_ratio_max, onesided, onesided3}

Every arm scored with BOTH emissions (topk @2% and NMS-3 @2%) and BOTH truth
protocols (dense catalogue truth; 20%-thinned sparse truth, seed 4242+f).
Protocol code (folds, collar, sampling, learner, DTI) is byte-for-byte the
Round-6 protocol; only the arm table changed.

No submission slot is spent. Output: evidence/holdout_round7.json + docs copy.
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
BUDGET = 0.02
RADIUS = 2
N_BASE = 25
H28_CH = 3            # channel 3 of data/round6_features.npy
DEM3 = [6, 10, 11]    # steep_ratio_max, onesided, onesided3 (register amendment)
DEM12 = list(range(12))

# (arm name, list of (source_key, channel) appended to the 25 base channels)
NEW_ARMS = [
    ("multi25_h28", [("r6", H28_CH)]),
    ("multi25_h28_dem12", [("r6", H28_CH)] + [("r7", c) for c in DEM12]),
    ("multi25_dem12", [("r7", c) for c in DEM12]),
    ("multi25_h28_dem3", [("r6", H28_CH)] + [("r7", c) for c in DEM3]),
]
INCUMBENT = "multi25_h28"
PRIMARY = "multi25_h28_dem12"


def dti_binary(pred, test_truth, region, weight_fp, coords):
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
            blocked[max(0, y - RADIUS):y + RADIUS + 1, max(0, x - RADIUS):x + RADIUS + 1] = True
            if n == max_sel:
                return sel
    return sel[:n]


def nms_pred(prob, idx, shape, frac):
    ordered = idx[np.lexsort((idx, -prob))]
    sel = nms_select(ordered, shape, int(frac * len(idx)))
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
    extra = {}
    r6p = ROOT / "data/round6_features.npy"
    r7p = ROOT / "data/round7_features.npy"
    if not r6p.exists():
        raise FileNotFoundError("data/round6_features.npy missing; run build_round6_features.py first")
    if not r7p.exists():
        raise FileNotFoundError("data/round7_features.npy missing; run build_round7_features.py first")
    extra["r6"] = np.lib.format.open_memmap(str(r6p), mode="r").reshape(-1, 5)
    extra["r7"] = np.lib.format.open_memmap(str(r7p), mode="r").reshape(-1, 12)

    r6build = json.loads((ROOT / "evidence/round6-feature-build.json").read_text())
    r7build = json.loads((ROOT / "evidence/round7-feature-build.json").read_text())
    if sha(r6p) != r6build["output"]["sha256"]:
        raise ValueError("round6_features.npy sha does not match evidence/round6-feature-build.json")
    if sha(r7p) != r7build["output"]["sha256"]:
        raise ValueError("round7_features.npy sha does not match evidence/round7-feature-build.json")

    fmap = folds(truth)

    report = {
        "protocol": "masked spatial holdout, official pixel-exact catalogue mask on FP; 512px blocks; 12px collar; seed 12027; NMS radius 2; budget 0.02",
        "preregistered_register": "docs/hypotheses-round7.md",
        "budget": BUDGET,
        "nms_radius": RADIUS,
        "budget_selection": "folds 0-1, sparse-truth protocol (register section 5 of Round-5, frozen)",
        "feature_cube_sha256": sha(ROOT / "data/candidate-features-30.npy"),
        "round6_feature_sha256": r6build["output"]["sha256"],
        "round7_feature_sha256": r7build["output"]["sha256"],
        "round7_feature_code_sha256": r7build["code_sha256"],
        "dem10_fetch_sidecar": "evidence/dem10-fetch.json",
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "arms": {name: cols for name, cols in NEW_ARMS},
        "incumbent": INCUMBENT,
        "primary": PRIMARY,
        "truth_protocols": {},
    }

    arm_names = ["multi25"] + [a for a, _ in NEW_ARMS]

    def matrix(ids, cols):
        parts = [flat[ids, :N_BASE]] + [extra[src][ids, ch] for src, ch in cols]
        return np.column_stack(parts)

    for protocol, thin in (("dense_catalogue_truth", False), ("sparse_thinned_20pct", True)):
        folds_rows, acc = [], {a: {"topk": [], "nms3": []} for a in arm_names}
        for fold in range(4):
            start = time.time()
            train = training_mask(fmap, fold, valid)
            region = valid & (fmap == fold)
            dense_truth = truth & region
            comp, ncomp = ndi_label(dense_truth, structure=np.ones((3, 3), int))
            rng_thin = np.random.default_rng(4242 + fold)
            keep = rng_thin.choice(np.arange(1, ncomp + 1), max(1, int(0.2 * ncomp)), replace=False)
            sparse_truth = dense_truth & np.isin(comp, keep)
            test_truth = sparse_truth if thin else dense_truth

            weight = np.minimum(distance_transform_edt(~test_truth) / 3, 1)
            weight_fp = (weight * (region & ~truth)).astype("float32")
            coords = np.nonzero(test_truth)
            testidx = np.flatnonzero(region)

            probe = binary_dilation(truth & train, iterations=3).astype("float32")
            row = {"fold": fold, "score_pixels": int(len(testidx)),
                   "score_positive": int(test_truth.sum()),
                   "leakage_probe_dti": dti_binary(probe, test_truth, region, weight_fp, coords)["dti"],
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
                    r = dti_binary(fn(prob, testidx, shape, BUDGET), test_truth, region, weight_fp, coords)
                    row["arms"][f"{name}_{emis}"] = r
                    acc[name][emis].append(r["dti"])

            cache_path = CACHE / f"prob-multi25-fold{fold}.npz"
            if cache_path.exists():
                data = np.load(cache_path)
                assert np.array_equal(data["idx"], testidx), "cache/region mismatch"
                score_arm("multi25", data["prob"])
            else:
                clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027)
                clf.fit(flat[tidx, :N_BASE], y, sample_weight=weights)
                prob = np.empty(len(testidx), dtype="float32")
                for s0 in range(0, len(testidx), 100000):
                    ids = testidx[s0:s0 + 100000]
                    prob[s0:s0 + len(ids)] = clf.predict_proba(flat[ids, :N_BASE])[:, 1]
                score_arm("multi25", prob)

            for name, cols in NEW_ARMS:
                clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027)
                clf.fit(matrix(tidx, cols), y, sample_weight=weights)
                prob = np.empty(len(testidx), dtype="float32")
                for s0 in range(0, len(testidx), 100000):
                    ids = testidx[s0:s0 + 100000]
                    prob[s0:s0 + len(ids)] = clf.predict_proba(matrix(ids, cols))[:, 1]
                score_arm(name, prob)

            row["seconds"] = round(time.time() - start, 2)
            folds_rows.append(row)
            print(f"[{protocol}] fold {fold} ({row['seconds']}s) probe={row['leakage_probe_dti']:.4f} "
                  + " ".join(f"{a}:{row['arms'][a + '_nms3']['dti']:.5f}" for a in arm_names), flush=True)

        means = {f"{a}_{e}": float(np.mean(acc[a][e])) for a in arm_names for e in ("topk", "nms3")}
        paired_ref = {a: [round(x - y, 6) for x, y in zip(acc[a]["nms3"], acc["multi25"]["nms3"])] for a in arm_names}
        paired_inc = {a: [round(x - y, 6) for x, y in zip(acc[a]["nms3"], acc[INCUMBENT]["nms3"])] for a in arm_names}
        report["truth_protocols"][protocol] = {
            "folds": folds_rows,
            "means": means,
            "paired_vs_multi25_nms3": paired_ref,
            "fold_wins_vs_multi25_nms3": {a: int(sum(d > 0 for d in paired_ref[a])) for a in arm_names},
            "paired_vs_incumbent_nms3": paired_inc,
            "fold_wins_vs_incumbent_nms3": {a: int(sum(d > 0 for d in paired_inc[a])) for a in arm_names},
            "mean_gain_vs_incumbent_nms3": {a: round(float(np.mean(paired_inc[a])), 6) for a in arm_names},
            "best_arm_nms3": max(arm_names, key=lambda a: means[f"{a}_nms3"]),
        }

    # Preregistered gate (register section 3, item 4a-b)
    gate = {}
    for protocol, blk in report["truth_protocols"].items():
        gate[protocol] = {
            "primary_wins_vs_incumbent": blk["fold_wins_vs_incumbent_nms3"][PRIMARY],
            "primary_mean_gain_vs_incumbent": blk["mean_gain_vs_incumbent_nms3"][PRIMARY],
            "leakage_probe_max": max(r["leakage_probe_dti"] for r in blk["folds"]),
        }
    passed = all(g["primary_wins_vs_incumbent"] >= 3 and g["primary_mean_gain_vs_incumbent"] > 0
                 and g["leakage_probe_max"] == 0.0 for g in gate.values())
    report["gate"] = {"rule": "primary > incumbent on >=3/4 folds AND mean paired gain > 0 on BOTH protocols; leakage probe 0.0",
                      "per_protocol": gate, "passed": bool(passed)}
    report["total_seconds"] = round(time.time() - t_all, 2)
    report["release_allowed"] = False
    report["release_reason"] = "Standing strongest-sibling-baseline gate unsatisfied; no sibling model reproduced; no DrivenData slot spent."
    (ROOT / "evidence/holdout_round7.json").write_text(json.dumps(report, indent=2))
    (ROOT / "docs/holdout_round7.json").write_text(json.dumps(report, indent=2))
    for protocol, blk in report["truth_protocols"].items():
        print(f"\n== {protocol}")
        for k, v in sorted(blk["means"].items(), key=lambda kv: -kv[1]):
            print(f"   {k:<24s} {v:.5f}")
        print("   fold wins vs incumbent (nms3):", blk["fold_wins_vs_incumbent_nms3"])
        print("   mean gain vs incumbent (nms3):", blk["mean_gain_vs_incumbent_nms3"])
    print("\nGATE:", json.dumps(report["gate"], indent=2))


if __name__ == "__main__":
    main()
