"""Round-5 honesty check: emission restricted to OFF-catalogue pixels.

Why this exists
---------------
In the frozen local protocol the truth *is* the known catalogue (labels.tif).
So a predicted pixel that lands ON a catalogue pixel earns TP locally, while the
FP term excludes catalogue pixels. On the real test set that cannot happen:
new-fault truth excludes catalogue pixels by construction (staff 11516/2,
11536/2), so any local TP earned on a catalogue pixel is an artefact of using
the catalogue as a truth proxy.

This script re-scores the two emission policies with the candidate set
restricted to `valid & ~catalogue`, i.e. the model may only predict pixels that
could legally be a new fault. Locally, TP then comes only from predicted pixels
that fall within the 3 px credit radius of a known trace -- which is exactly the
regime staff describe for new geometry of existing systems (11516/4: "A
new-fault ground truth pixel can indeed lie within 300m of a known fault
trace").

It is the strictest of the three protocols and the closest local analogue of
the real scoring geometry. Diagnostic only; no submission slot.

Output: evidence/round5-offcatalogue-check.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import folds, sha, training_mask

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
BUDGET = 0.02
RADIUS = 2


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


def nms_select(ordered_pixels, shape, max_sel):
    W = shape[1]
    blocked = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    for s0 in range(0, len(ordered_pixels), 50000):
        cand = ordered_pixels[s0:s0 + 50000]
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
    out = {"protocol": "masked spatial holdout; candidates restricted to valid & ~catalogue; "
                       "budget 0.02; NMS radius 2; cached multi25 probabilities",
           "budget": BUDGET, "script_sha256": sha(Path(__file__)),
           "core_sha256": sha(ROOT / "scripts/core.py"), "folds": [], "arms": {}}
    acc = {"topk_offcatalogue": [], "nms3_offcatalogue": [],
           "topk_allcandidates_oncatalogue_tp_fraction": []}
    for fold in range(4):
        train = training_mask(fmap, fold, valid)   # noqa: F841 (protocol parity)
        region = valid & (fmap == fold)
        test_truth = truth & region
        cand_region = region & ~truth              # legally predictable pixels
        weight = np.minimum(distance_transform_edt(~test_truth) / 3, 1)
        weight_fp = (weight * (region & ~truth)).astype("float32")
        coords = np.nonzero(test_truth)
        data = np.load(CACHE / f"prob-multi25-fold{fold}.npz")
        idx, prob = data["idx"], data["prob"]
        k = int(BUDGET * len(idx))

        # restrict to off-catalogue candidates, keep the validated mass k
        in_cand = ~truth.ravel()[idx]
        idx_o, prob_o = idx[in_cand], prob[in_cand]
        order = np.lexsort((idx_o, -prob_o))
        p_top = np.zeros(shape, dtype="float32")
        p_top.ravel()[idx_o[order[:k]]] = 1.0
        sel = nms_select(idx_o[order], shape, k)
        p_nms = np.zeros(shape, dtype="float32")
        p_nms.ravel()[sel] = 1.0

        # how much of the unrestricted top-k arm's TP came from catalogue pixels?
        order_all = np.lexsort((idx, -prob))
        p_all = np.zeros(shape, dtype="float32")
        p_all.ravel()[idx[order_all[:k]]] = 1.0
        on_cat = float((p_all.ravel()[np.flatnonzero(truth.ravel())] > 0).sum())

        r_top = dti_binary(p_top, test_truth, region, weight_fp, coords)
        r_nms = dti_binary(p_nms, test_truth, region, weight_fp, coords)
        acc["topk_offcatalogue"].append(r_top["dti"])
        acc["nms3_offcatalogue"].append(r_nms["dti"])
        acc["topk_allcandidates_oncatalogue_tp_fraction"].append(on_cat)
        out["folds"].append({"fold": fold, "region_pixels": int(region.sum()),
                             "offcatalogue_candidates": int(cand_region.sum()),
                             "emitted_mass": k,
                             "topk_offcatalogue": r_top,
                             "nms3_offcatalogue": r_nms,
                             "unrestricted_topk_pixels_landing_on_catalogue": int(on_cat)})
        print(f"fold {fold}: topk_off={r_top['dti']:.5f} (cov {r_top['coverage']:.3f}) "
              f"nms3_off={r_nms['dti']:.5f} (cov {r_nms['coverage']:.3f}) "
              f"unrestricted_topk_on_catalogue_px={int(on_cat)}", flush=True)
    out["arms"] = {k: float(np.mean(v)) for k, v in acc.items()}
    out["per_fold"] = {k: [float(x) for x in v] for k, v in acc.items()}
    out["total_seconds"] = round(time.time() - t0, 2)
    (ROOT / "evidence/round5-offcatalogue-check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out["arms"], indent=2))


if __name__ == "__main__":
    main()
