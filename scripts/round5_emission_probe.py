"""Round-5 emission-policy probe on the frozen masked spatial holdout.

Question this answers
---------------------
The official metric is a distance-weighted Tversky index with a 300 m (=3 px at
100 m) triangular credit kernel (drivendata.org competition 306, "Performance
metric"). For a binary prediction P and truth T:

    TP = sum over truth pixels of max_{|d|<=3} ( P(p+d) * (1-|d|/3) )
    FP = sum over predicted pixels of w(p) * min(dist(p,T)/3, 1)
    FN = |T| - TP
    DTI = TP / (TP + 0.2*FP + 0.8*FN)

Because TP is a per-truth-pixel MAXIMUM over a 5x5 neighbourhood, emitting
several predicted pixels inside one 5x5 neighbourhood adds FP without adding TP.
The sparsest emission that still credits every truth pixel is therefore a set of
predicted pixels with **no two within a 5x5 block** -- i.e. non-maximum
suppression with Chebyshev radius 2, density 1/25 = 4%.

This probe measures, on the frozen protocol and with the already-cached multi25
probability fields (no re-training, no new labels, no submission slot):

  * top-k emission (the policy every previous round used) over a budget sweep;
  * uniform random emission over the same budgets;
  * NMS-3 emission ordered by the model (model decides *where*, metric geometry
    decides *how spread*);
  * NMS-3 emission ordered randomly (geometry-only control);
  * a fixed 5x5 lattice (coverage-only reference, no model at all).

It also re-runs the same comparison on a thinned-truth variant (20% of truth
connected components kept, deterministic seed) as a sensitivity check for the
real test set, whose new-fault truth is much sparser than the dense catalogue
used as local truth.

This is a DIAGNOSTIC of emission geometry. It does not train anything and does
not authorize a release; see docs/hypotheses-round5.md for the preregistered
decision rule.

Output: evidence/round5-emission-probe.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, label as ndi_label

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, sha, training_mask

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
BUDGETS = (0.005, 0.01, 0.02, 0.04, 0.08, 0.16)
NMS_BUDGETS = (0.005, 0.01, 0.02, 0.04)
RADIUS = 2  # Chebyshev radius of the credit kernel (300 m at 100 m pixels)


def dti_binary(pred, truth_test, region, weight_fp, truth_coords):
    """DTI for a binary prediction, matching holdout_masked.components_masked."""
    t = truth_test & region
    yy, xx = truth_coords
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


def nms_select(order, shape, max_sel):
    """Greedy non-maximum suppression in `order` (descending score)."""
    W = shape[1]
    blocked = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    ys = xs = None
    CHUNK = 50000
    for s0 in range(0, len(order), CHUNK):
        cand = order[s0:s0 + CHUNK]
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


def main() -> None:
    t0 = time.time()
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        truth = (s.read(1, masked=True).filled(0) > 0) & valid
    fmap = folds(truth)

    report = {
        "purpose": "measure emission geometry (top-k vs NMS-3 vs random vs lattice) "
                   "on the frozen masked spatial holdout using cached multi25 "
                   "probabilities; no training, no submission slot",
        "metric": "DTI = TP/(TP + 0.2*FP + 0.8*FN), triangular kernel radius 3 px",
        "credit_kernel_radius_px": RADIUS,
        "max_nms_density": 1.0 / (2 * RADIUS + 1) ** 2,
        "model": "multi25 (cached, identical to scripts/holdout_masked.py arm)",
        "core_sha256": sha(ROOT / "scripts/core.py"),
        "script_sha256": sha(Path(__file__)),
        "truth_variants": {},
    }

    for variant, thin in (("full_catalogue_truth", False), ("thinned_20pct_truth", True)):
        arms: dict[str, list[float]] = {}
        detail: dict[str, list[dict]] = {}
        for fold in range(4):
            start = time.time()
            train = training_mask(fmap, fold, valid)
            region = valid & (fmap == fold)
            test_truth = truth & region
            if thin:
                comp, ncomp = ndi_label(test_truth, structure=np.ones((3, 3), int))
                rng = np.random.default_rng(4242 + fold)
                keep = rng.choice(np.arange(1, ncomp + 1),
                                  max(1, int(0.2 * ncomp)), replace=False)
                test_truth = test_truth & np.isin(comp, keep)
            data = np.load(CACHE / f"prob-multi25-fold{fold}.npz")
            idx, prob = data["idx"], data["prob"]

            weight = np.minimum(distance_transform_edt(~test_truth) / 3, 1)
            weight_fp = (weight * (region & ~truth)).astype("float32")
            yy, xx = np.nonzero(test_truth)
            coords = (yy, xx)

            def add(name, pred):
                r = dti_binary(pred, test_truth, region, weight_fp, coords)
                r["fold"] = fold
                detail.setdefault(name, []).append(r)
                arms.setdefault(name, []).append(r["dti"])
                return r

            for b in BUDGETS:
                k = int(b * len(idx))
                order = np.lexsort((idx, -prob))
                p = np.zeros(shape, dtype="float32")
                p.ravel()[idx[order[:k]]] = 1.0
                add(f"topk_{b:g}", p)
            for b in BUDGETS:
                rng = np.random.default_rng(12027 + fold)
                k = int(b * len(idx))
                p = np.zeros(shape, dtype="float32")
                p.ravel()[rng.choice(idx, k, replace=False)] = 1.0
                add(f"random_{b:g}", p)
            for b in NMS_BUDGETS:
                k = int(b * len(idx))
                ordered_pixels = idx[np.lexsort((idx, -prob))]
                sel = nms_select(ordered_pixels, shape, k)
                p = np.zeros(shape, dtype="float32")
                p.ravel()[sel] = 1.0
                add(f"nms3_model_{b:g}", p)
                del ordered_pixels
            for b in NMS_BUDGETS:
                rng = np.random.default_rng(777 + fold)
                k = int(b * len(idx))
                order = idx[rng.permutation(len(idx))]
                sel = nms_select(order, shape, k)
                p = np.zeros(shape, dtype="float32")
                p.ravel()[sel] = 1.0
                add(f"nms3_random_{b:g}", p)
                del order
            # coverage-only reference: fixed lattice, spacing 2*RADIUS+1 = 5 px
            lat = np.zeros(shape, dtype=bool)
            lat[::2 * RADIUS + 1, ::2 * RADIUS + 1] = True
            p = np.zeros(shape, dtype="float32")
            p[lat & region] = 1.0
            add("lattice5x5", p)
            print(f"[{variant}] fold {fold} ({time.time()-start:.1f}s) "
                  f"truth={int(test_truth.sum())} "
                  f"topk_0.02={arms['topk_0.02'][-1]:.5f} "
                  f"nms3_model_0.02={arms['nms3_model_0.02'][-1]:.5f} "
                  f"lattice={arms['lattice5x5'][-1]:.5f}", flush=True)

        means = {k: float(np.mean(v)) for k, v in arms.items()}
        report["truth_variants"][variant] = {
            "means": means,
            "per_fold": detail,
            "best_arm": max(means, key=means.get),
            "ranking": sorted(means.items(), key=lambda kv: -kv[1])[:12],
        }
    report["total_seconds"] = round(time.time() - t0, 2)
    (ROOT / "evidence/round5-emission-probe.json").write_text(json.dumps(report, indent=2))
    for variant, blk in report["truth_variants"].items():
        print(f"\n== {variant} (mean DTI over 4 folds)")
        for k, v in blk["ranking"]:
            print(f"   {k:<18s} {v:.5f}")


if __name__ == "__main__":
    main()
