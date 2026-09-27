"""Round-4 frozen validation: PRIMARY multi25+H15 plus secondaries (preregistered).

Register: docs/hypotheses-round4.md (written BEFORE this file). Frozen spatial
protocol identical to Round 3: 512px blocks, 12px collar, seed 12027,
pixel-exact catalogue mask on FP, binary top-2% emission, leakage probe ~0.

GBM arms (frozen hyper-params, frozen sampling): multi25 | multi25+H15..H18 |
  multi25+H8/H9x/H9d/H7/H10 single-channel ablations.
Measurement arms: h6prime_hybrid (preregistered exact form, train traces +
  virgin top-up to 2%) | h15_standalone | random02.
Terminal simulator: straight-5px-ray mechanism reproduction + random control.

No GeoTIFF is written. No weekly slot is spent. Nothing here can authorize
a release; the PRIMARY gate only marks follow-up eligibility.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, label as ndi_label
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, training_mask, sha
from holdout_masked import BUDGET, components_masked, topk_binary
from holdout_terminals import straight_rays

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data/candidate-features-30.npy"
R4 = ROOT / "data/round4_features.npy"

GBM = dict(max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027)

# (arm name, extra source, extra channel or None)
GBM_ARMS = [("multi25", None, None),
            ("multi25_plus_h15", "r4", 0),
            ("multi25_plus_h16", "r4", 1),
            ("multi25_plus_h17", "r4", 2),
            ("multi25_plus_h18", "r4", 3),
            ("multi25_h8", "cube", 25),
            ("multi25_h9x", "cube", 26),
            ("multi25_h9d", "cube", 27),
            ("multi25_h7", "cube", 28),
            ("multi25_h10", "cube", 29)]


def fit_predict(X_train, y, w, X_test) -> np.ndarray:
    clf = HistGradientBoostingClassifier(**GBM)
    clf.fit(X_train, y, sample_weight=w)
    out = np.empty(len(X_test), dtype="float32")
    for s in range(0, len(X_test), 100_000):
        out[s:s + 100_000] = clf.predict_proba(X_test[s:s + 100_000])[:, 1]
    return out


def h6prime_hybrid(train_traces, multi25_score, region, valid) -> np.ndarray:
    """Preregistered H6' form: straight 5px tip rays + virgin top-up to 2%."""
    rays = straight_rays(train_traces)
    ray_idx = np.flatnonzero((rays > 0) & region)
    budget = int(BUDGET * int(region.sum()))
    # Deterministic truncation if rays alone exceed budget (rank by multi25).
    if len(ray_idx) > budget:
        order = np.lexsort((ray_idx, -multi25_score.ravel()[ray_idx]))
        ray_idx = ray_idx[order[:budget]]
    pred = np.zeros(train_traces.shape, dtype="float32")
    pred.ravel()[ray_idx] = 1.0
    # Virgin top-up: multi25-ranked region pixels >3px from any train trace.
    virgin = region & ~binary_dilation(train_traces, iterations=3)
    cand = np.flatnonzero(virgin & (pred == 0))
    need = budget - int(pred.sum())
    if need > 0 and len(cand):
        order = np.lexsort((cand, -multi25_score.ravel()[cand]))
        pred.ravel()[cand[order[:need]]] = 1.0
    return pred


def terminal_check(truth, valid) -> dict:
    """Reproduce the Round-2 terminal truncation exactly (seed 12027)."""
    shape = truth.shape
    comp, ncomp = ndi_label(truth, structure=np.ones((3, 3), dtype="int32"))
    rng = np.random.default_rng(12027)
    big = [c for c in range(1, ncomp + 1) if (comp == c).sum() >= 12]
    trunc = set(rng.choice(big, len(big) // 2, replace=False))
    hidden = np.zeros(shape, bool)
    for c in trunc:
        ys, xs = np.nonzero(comp == c)
        pts = np.stack([ys, xs]).astype("float64")
        ctr = pts.mean(axis=1)
        u, _, _ = np.linalg.svd(pts - ctr[:, None], full_matrices=False)
        t = (pts - ctr[:, None]).T @ u[:, 0]
        cut = np.quantile(t, 0.75)
        for y, x, v in zip(ys, xs, t):
            if v >= cut:
                hidden[y, x] = True
    hidden &= valid
    train_traces = (truth & ~hidden) & valid
    region = valid & (distance_transform_edt(~hidden) <= 25)
    rays = straight_rays(train_traces)
    idx = np.flatnonzero(region)
    ctrl = np.zeros(shape, dtype="float32")
    ctrl.ravel()[rng.choice(idx, min(int((rays > 0).sum()), len(idx)),
                            replace=False)] = 1.0
    return {
        "truncated_components": len(trunc),
        "hidden_pixels": int(hidden.sum()),
        "region_pixels": int(region.sum()),
        "rays_emitted": int((rays > 0).sum()),
        "straight_rays_dti": components_masked(rays, hidden, region, train_traces)["dti"],
        "random_equal_mass_dti": components_masked(ctrl, hidden, region, train_traces)["dti"],
    }


def main() -> None:
    t0 = time.time()
    for p in (CUBE, R4, ROOT / "data/sample_submission.tif",
              ROOT / "data/labels.tif", ROOT / "evidence/round4-feature-build.json"):
        if not p.exists():
            raise FileNotFoundError(f"build verified inputs first: {p}")
    with rasterio.open(ROOT / "data/sample_submission.tif") as ds:
        valid = ds.read_masks(1) > 0
        shape = ds.shape
    with rasterio.open(ROOT / "data/labels.tif") as ds:
        truth = (ds.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(CUBE), mode="r")
    r4 = np.load(R4, mmap_mode="r", allow_pickle=False)
    assert cube.shape == (*shape, 30) and r4.shape == (*shape, 4)
    assert np.isfinite(np.asarray(r4)[valid]).all()
    build = json.loads((ROOT / "evidence/round4-feature-build.json").read_text())
    flat, flat4 = cube.reshape(-1, 30), r4.reshape(-1, 4)
    fmap = folds(truth)
    report: dict = {
        "protocol": "round4 preregistered masked spatial holdout; official pixel-exact "
                    "catalogue mask on FP; binary top-2% emission; 512px blocks; "
                    "12px collar; seed 12027",
        "preregistered_register": "docs/hypotheses-round4.md",
        "budget": BUDGET,
        "round4_feature_sha256": build["output"]["sha256"],
        "round4_feature_code_sha256": build["code_sha256"],
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "primary_arm": "multi25_plus_h15",
        "folds": [],
    }
    for fold in range(4):
        fs = time.time()
        train = training_mask(fmap, fold, valid)
        region = valid & (fmap == fold)
        test_truth = truth & region
        if np.any(train & region):
            raise AssertionError("training/scoring overlap")
        rng = np.random.default_rng(12027 + fold)
        pos = np.flatnonzero(train & truth)
        neg = rng.choice(np.flatnonzero(train & ~truth), 100_000, replace=False)
        idx = np.concatenate((pos, neg))
        y = truth.ravel()[idx]
        w = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(idx)
        testidx = np.flatnonzero(region)
        row: dict = {"fold": fold, "train_positive": int(len(pos)),
                     "train_negative": int(len(neg)),
                     "score_pixels": int(len(testidx)),
                     "score_positive": int(test_truth.sum()), "arms": {}}
        probe = binary_dilation(truth & train, iterations=3).astype("float32")
        row["leakage_probe_dti"] = components_masked(probe, test_truth, region, truth)["dti"]
        multi25_score = None
        for name, src, ch in GBM_ARMS:
            Xtr = flat[idx, :25]
            Xte = flat[testidx, :25]
            if src == "r4":
                Xtr = np.column_stack((Xtr, flat4[idx, ch]))
                Xte = np.column_stack((Xte, flat4[testidx, ch]))
            elif src == "cube":
                Xtr = np.column_stack((Xtr, flat[idx, ch]))
                Xte = np.column_stack((Xte, flat[testidx, ch]))
            prob = fit_predict(Xtr, y, w, Xte)
            score = np.zeros(shape, dtype="float32")
            score.ravel()[testidx] = prob
            if name == "multi25":
                multi25_score = score
            row["arms"][name] = components_masked(
                topk_binary(score, region, BUDGET), test_truth, region, truth)
        assert multi25_score is not None
        row["arms"]["h6prime_hybrid"] = components_masked(
            h6prime_hybrid(truth & train, multi25_score, region, valid),
            test_truth, region, truth)
        row["arms"]["h15_standalone"] = components_masked(
            topk_binary(np.asarray(r4[:, :, 0]), region, BUDGET),
            test_truth, region, truth)
        rs = np.zeros(shape, dtype="float32")
        rs.ravel()[rng.choice(testidx, int(BUDGET * len(testidx)), replace=False)] = 1.0
        row["arms"]["random02"] = components_masked(rs, test_truth, region, truth)
        row["seconds"] = round(time.time() - fs, 2)
        report["folds"].append(row)
        d = {a: round(row["arms"][a]["dti"], 5) for a, _, _ in GBM_ARMS}
        print(f"fold {fold} ({row['seconds']}s) probe={row['leakage_probe_dti']:.4f} "
              + " ".join(f"{a}={v}" for a, v in d.items())
              + f" h6p={row['arms']['h6prime_hybrid']['dti']:.5f}"
              + f" h15s={row['arms']['h15_standalone']['dti']:.5f}"
              + f" rnd={row['arms']['random02']['dti']:.5f}", flush=True)

    arms = [a for a, _, _ in GBM_ARMS] + ["h6prime_hybrid", "h15_standalone", "random02"]
    report["means"] = {a: float(np.mean([r["arms"][a]["dti"] for r in report["folds"]]))
                       for a in arms}
    base = [r["arms"]["multi25"]["dti"] for r in report["folds"]]
    for a in arms:
        if a in ("multi25", "random02"):
            continue
        paired = [float(r["arms"][a]["dti"] - b) for r, b in zip(report["folds"], base)]
        report[f"paired_{a}_vs_multi25"] = paired
        report[f"wins_{a}"] = int(sum(x > 0 for x in paired))
    pkey, wkey = "paired_multi25_plus_h15_vs_multi25", "wins_multi25_plus_h15"
    passed = bool(np.mean(report[pkey]) > 0 and report[wkey] >= 3)
    report["terminal_mechanism_check"] = terminal_check(truth, valid)
    report["release_allowed"] = False
    report["release_gate"] = {
        "predeclared": "PRIMARY multi25_plus_h15: positive mean paired DTI and >=3/4 wins",
        "passed": passed,
        "decision": ("PRIMARY gate passed as a research signal; strongest sibling "
                     "baseline + independent final gates still required; no slot spent"
                     if passed else
                     "PRIMARY rejected as a submission upgrade; no weekly slot and no "
                     "new submission artifact"),
    }
    report["total_seconds"] = round(time.time() - t0, 2)
    for p in (ROOT / "evidence/holdout_round4.json", ROOT / "docs/holdout_round4.json"):
        p.write_text(json.dumps(report, indent=2) + "\n")
    print("means:", json.dumps(report["means"], indent=2))
    print("PRIMARY:", json.dumps(report["release_gate"], indent=2))
    print("terminal:", json.dumps(report["terminal_mechanism_check"], indent=2))


if __name__ == "__main__":
    main()
