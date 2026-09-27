"""Leakage-free MASKED spatial holdout: the official pixel-exact catalogue mask.

Why: DrivenData staff confirmed known USGS/INGENIOUS faults are pixel-exact
masked from scoring (11516/2, 11516/4). The earlier unmasked screen scored
against dense known faults, where random 6% beat every learned arm -- an
inverted selection signal. This protocol emulates official scoring:

- truth = test-block labels only; FP term excludes ALL catalogue pixels.
- leakage probe = 3px dilation of train traces scored vs test truth (must be ~0).
- binary top-2% emission within each score region (leaderboard-winning regime).

Arms: raw19 GBM | multi25 GBM | multi30 GBM (+H8/H9/H7/H10) |
       H6 standalone (tip/splay/relay + geophysical gate) |
       H8 standalone (joint alteration) | random 2% control.
"""
import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from scipy.ndimage import (distance_transform_edt, label as ndi_label,
                           uniform_filter)
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, training_mask, sha

ROOT = Path(__file__).resolve().parents[1]
BUDGET = 0.02


def components_masked(p, truth_test, region, catalogue):
    """DTI with official pixel-exact mask on the FP term only."""
    if p.shape != truth_test.shape:
        raise ValueError("shape")
    p = np.where(region, p, 0).astype("float64")
    t = truth_test & region
    yy, xx = np.nonzero(t)
    credit = np.zeros(len(yy), dtype="float64")
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            k = max(1 - np.hypot(dy, dx) / 3, 0)
            y = yy + dy
            x = xx + dx
            v = (y >= 0) & (x >= 0) & (y < p.shape[0]) & (x < p.shape[1])
            credit[v] = np.maximum(credit[v], p[y[v], x[v]] * k)
    tp = float(credit.sum())
    fn = float(len(yy) - tp)
    weight = np.minimum(distance_transform_edt(~t) / 3, 1) if t.any() else np.ones(t.shape)
    fpable = region & ~catalogue
    fp = float(np.sum(p * weight * fpable, dtype="float64"))
    return dict(tp=tp, fp=fp, fn=fn, dti=tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7))


def topk_binary(score, region, frac):
    idx = np.flatnonzero(region)
    order = np.lexsort((idx, -score.ravel()[idx]))
    k = int(frac * len(idx))
    pred = np.zeros(score.shape, dtype="float32")
    pred.ravel()[idx[order[:k]]] = 1.0
    return pred


def fabric_strike(rtp, y, x, win=7):
    h, w = rtp.shape
    y0, y1 = max(0, y - win), min(h, y + win + 1)
    x0, x1 = max(0, x - win), min(w, x + win + 1)
    patch = rtp[y0:y1, x0:x1].astype("float64")
    if patch.size < 9:
        return None
    gy, gx = np.gradient(patch)
    jxx, jyy, jxy = (gx * gx).mean(), (gy * gy).mean(), (gx * gy).mean()
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy)  # gradient orientation
    strike = ang + np.pi / 2  # fabric strike (perp of gradient)
    return np.array([np.sin(strike), np.cos(strike)])


def h6_detector(train_traces, rtp, f21, f22, f23, f25, region, valid):
    """Curved tip extensions + splay fans + relay bridges, geophysically gated.

    Proposes geometry from TRAIN traces only; gates with unsupervised
    edge/alteration fields. Returns (score_field, diagnostics).
    """
    H, W = train_traces.shape
    # 8-connectivity neighbor count for endpoint detection.
    from scipy.ndimage import convolve
    nbr = convolve(train_traces.astype("int32"), np.ones((3, 3), "int32"),
                   mode="constant") - train_traces.astype("int32")
    endpoints = np.argwhere(train_traces & (nbr == 1))
    comp, ncomp = ndi_label(train_traces,
                            structure=np.ones((3, 3), dtype="int32"))

    score = np.zeros((H, W), dtype="float32")
    # Gate thresholds from unsupervised percentiles over valid area.
    g23 = f23[valid]
    g21 = f21[valid]
    g22 = f22[valid]
    g25 = f25[valid]
    t23, t21, t22 = (float(np.percentile(g23, 70)), float(np.percentile(g21, 70)),
                     float(np.percentile(g22, 70)))
    t25 = float(np.percentile(g25, 80))
    n23 = f23 / (t23 + 1e-12)
    n21 = f21 / (t21 + 1e-12)
    n22 = f22 / (t22 + 1e-12)
    n25 = f25 / (t25 + 1e-12)
    gate_pass = (f23 > t23) | (f21 > t21) | (f22 > t22) | (f25 > t25)
    strength = np.maximum.reduce([n23, n21, n22, n25]).astype("float32")

    def cast(y0, x0, direction, length):
        pts = []
        p = np.array([y0, x0], dtype="float64")
        d = direction / (np.linalg.norm(direction) + 1e-12)
        for _ in range(length):
            p = p + d
            y, x = int(round(p[0])), int(round(p[1]))
            if not (0 <= y < H and 0 <= x < W) or train_traces[y, x]:
                break
            pts.append((y, x))
            fab = fabric_strike(rtp, y, x)
            if fab is not None:
                if fab @ d < 0:
                    fab = -fab
                d = 0.6 * d + 0.4 * fab
                d = d / (np.linalg.norm(d) + 1e-12)
        return pts

    n_tip = n_splay = 0
    for (y0, x0) in endpoints:
        ys, xs = np.nonzero(train_traces[max(0, y0 - 8):y0 + 9, max(0, x0 - 8):x0 + 9])
        if len(ys) < 3:
            continue
        pts = np.stack([ys + max(0, y0 - 8), xs + max(0, x0 - 8)]).astype("float64")
        ctr = pts.mean(axis=1)
        away = np.array([y0, x0]) - ctr
        if np.linalg.norm(away) < 1e-9:
            continue
        away = away / np.linalg.norm(away)
        fab = fabric_strike(rtp, y0, x0)
        if fab is not None:
            if fab @ away < 0:
                fab = -fab
            away = 0.6 * away + 0.4 * fab
            away = away / np.linalg.norm(away)
        for (yy, xx) in cast(y0, x0, away, 15):
            n_tip += 1
            if gate_pass[yy, xx]:
                score[yy, xx] = max(score[yy, xx], strength[yy, xx])
        ca, sa = np.cos(np.deg2rad(20)), np.sin(np.deg2rad(20))
        for rot in (np.array([[ca, -sa], [sa, ca]]), np.array([[ca, sa], [-sa, ca]])):
            for (yy, xx) in cast(y0, x0, rot @ away, 8):
                n_splay += 1
                if gate_pass[yy, xx]:
                    score[yy, xx] = max(score[yy, xx], strength[yy, xx])

    # Relay bridges between distinct components 5-20px apart.
    n_bridge = 0
    if ncomp > 1 and len(endpoints) > 1:
        for i in range(len(endpoints)):
            d = np.abs(endpoints - endpoints[i]).sum(axis=1)
            cand = np.nonzero((d >= 5) & (d <= 20))[0][:4]
            for j in cand:
                a, b = endpoints[i], endpoints[j]
                if comp[tuple(a)] == comp[tuple(b)]:
                    continue
                steps = int(np.abs(b - a).max())
                for s in range(1, steps):
                    y = int(round(a[0] + (b[0] - a[0]) * s / steps))
                    x = int(round(a[1] + (b[1] - a[1]) * s / steps))
                    if train_traces[y, x]:
                        continue
                    n_bridge += 1
                    if gate_pass[y, x]:
                        score[y, x] = max(score[y, x], strength[y, x])
    diag = dict(endpoints=int(len(endpoints)), components=int(ncomp),
                tip_pixels=n_tip, splay_pixels=n_splay, bridge_pixels=n_bridge,
                gated_pixels=int((score > 0).sum()),
                gated_in_region=int(((score > 0) & region).sum()))
    return score, diag


def main():
    t_all = time.time()
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        truth = (s.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    assert cube.shape == (*shape, 30), cube.shape
    flat = cube.reshape(-1, 30)
    fmap = folds(truth)

    build = json.loads((ROOT / "evidence/feature-build.json").read_text())
    report = {
        "protocol": "masked spatial holdout, official pixel-exact catalogue mask on FP; "
                    "binary top-2% emission; 512px blocks; 12px collar; seed 12027",
        "budget": BUDGET,
        "feature_build_code_sha256": build["code_sha256"],
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "folds": [],
    }
    rtp = cube[:, :, 1]

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

        # Leakage probe: 3px dilation of train traces vs test truth.
        from scipy.ndimage import binary_dilation
        probe = binary_dilation(truth & train, iterations=3).astype("float32")
        row["leakage_probe_dti"] = components_masked(
            probe, test_truth, region, truth)["dti"]

        for name, n_feat in [("raw19", 19), ("multi25", 25), ("multi30", 30)]:
            clf = HistGradientBoostingClassifier(
                max_iter=100, max_leaf_nodes=15, early_stopping=False,
                random_state=12027)
            clf.fit(flat[idx, :n_feat], y, sample_weight=weights)
            prob = np.empty(len(testidx), dtype="float32")
            for s0 in range(0, len(testidx), 100000):
                ids = testidx[s0:s0 + 100000]
                prob[s0:s0 + len(ids)] = clf.predict_proba(flat[ids, :n_feat])[:, 1]
            score = np.zeros(shape, dtype="float32")
            score.ravel()[testidx] = prob
            row["arms"][name] = components_masked(
                topk_binary(score, region, BUDGET), test_truth, region, truth)

        h6, diag = h6_detector(truth & train, rtp, cube[:, :, 21], cube[:, :, 22],
                               cube[:, :, 23], cube[:, :, 25], region, valid)
        row["h6_diagnostics"] = diag
        row["arms"]["h6_geometric"] = components_masked(
            topk_binary(h6, region, BUDGET), test_truth, region, truth)
        h8 = np.zeros(shape, dtype="float32")
        h8.ravel()[testidx] = cube.reshape(-1, 30)[testidx, 25]
        row["arms"]["h8_alteration"] = components_masked(
            topk_binary(h8, region, BUDGET), test_truth, region, truth)
        pred = np.zeros(shape, dtype="float32")
        pred.ravel()[rng.choice(testidx, int(BUDGET * len(testidx)), replace=False)] = 1.0
        row["arms"]["random02"] = components_masked(pred, test_truth, region, truth)
        row["seconds"] = round(time.time() - start, 2)
        report["folds"].append(row)
        print(f"fold {fold} ({row['seconds']}s) probe={row['leakage_probe_dti']:.4f} " +
              " ".join(f"{a}={row['arms'][a]['dti']:.5f}" for a in
                       ["raw19", "multi25", "multi30", "h6_geometric",
                        "h8_alteration", "random02"]), flush=True)

    arms = ["raw19", "multi25", "multi30", "h6_geometric", "h8_alteration", "random02"]
    report["means"] = {a: float(np.mean([r["arms"][a]["dti"] for r in report["folds"]]))
                       for a in arms}
    for a in ["multi25", "multi30", "h6_geometric", "h8_alteration"]:
        report[f"paired_vs_raw19_{a}"] = [
            float(r["arms"][a]["dti"] - r["arms"]["raw19"]["dti"])
            for r in report["folds"]]
    report["paired_multi30_vs_multi25"] = [
        float(r["arms"]["multi30"]["dti"] - r["arms"]["multi25"]["dti"])
        for r in report["folds"]]
    report["total_seconds"] = round(time.time() - t_all, 2)
    report["release_allowed"] = False
    report["release_reason"] = ("Screening only. A submission requires beating the "
                                "current holdout best on this masked protocol plus "
                                "format/provenance gates; no weekly slot is spent here.")
    (ROOT / "evidence/holdout_masked.json").write_text(json.dumps(report, indent=2))
    (ROOT / "docs/holdout_masked.json").write_text(json.dumps(report, indent=2))
    print("means:", json.dumps(report["means"], indent=2))


if __name__ == "__main__":
    main()
