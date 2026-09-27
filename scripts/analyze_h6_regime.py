"""H6 claimed-regime analysis: hidden truth near visible-trace endpoints.

The full trace holdout mixes H6-catchable truth (hidden components adjacent
to visible traces) with truth H6 cannot catch by design (isolated hidden
components). This scores H6 vs equal-mass random on the claimed regime only
(hidden pixels within 20px of a train endpoint) and reports the regime share.
Also ablates the geophysical gate (geometry-only vs gated).
"""
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import (label as ndi_label, convolve,
                           distance_transform_edt)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha
from holdout_masked import components_masked, h6_detector, fabric_strike

ROOT = Path(__file__).resolve().parents[1]


def h6_ungated(train_traces, rtp, region):
    H, W = train_traces.shape
    nbr = convolve(train_traces.astype("int32"), np.ones((3, 3), "int32"),
                   mode="constant") - train_traces.astype("int32")
    endpoints = np.argwhere(train_traces & (nbr == 1))
    score = np.zeros((H, W), dtype="float32")

    def cast(y0, x0, direction, length):
        p = np.array([y0, x0], dtype="float64")
        d = direction / (np.linalg.norm(direction) + 1e-12)
        for _ in range(length):
            p = p + d
            y, x = int(round(p[0])), int(round(p[1]))
            if not (0 <= y < H and 0 <= x < W) or train_traces[y, x]:
                break
            score[y, x] = 1.0
            fab = fabric_strike(rtp, y, x)
            if fab is not None:
                if fab @ d < 0:
                    fab = -fab
                d = 0.6 * d + 0.4 * fab
                d = d / (np.linalg.norm(d) + 1e-12)

    for (y0, x0) in endpoints:
        ys, xs = np.nonzero(train_traces[max(0, y0 - 8):y0 + 9, max(0, x0 - 8):x0 + 9])
        if len(ys) < 3:
            continue
        pts = np.stack([ys + max(0, y0 - 8), xs + max(0, x0 - 8)]).astype("float64")
        away = np.array([y0, x0]) - pts.mean(axis=1)
        if np.linalg.norm(away) < 1e-9:
            continue
        away = away / np.linalg.norm(away)
        cast(y0, x0, away, 15)
        ca, sa = np.cos(np.deg2rad(20)), np.sin(np.deg2rad(20))
        for rot in (np.array([[ca, -sa], [sa, ca]]), np.array([[ca, sa], [-sa, ca]])):
            cast(y0, x0, rot @ away, 8)
    return score


def main():
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        truth = (s.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    rtp = np.asarray(cube[:, :, 1])
    f21, f22, f23, f25 = (np.asarray(cube[:, :, i]) for i in (21, 22, 23, 25))
    del cube
    comp, ncomp = ndi_label(truth, structure=np.ones((3, 3), dtype="int32"))
    sizes = np.bincount(comp.ravel())
    big = sorted([c for c in range(1, ncomp + 1) if sizes[c] >= 3],
                 key=lambda c: -sizes[c])
    comp_fold = np.zeros(ncomp + 1, dtype="int8")
    for rank, c in enumerate(big):
        comp_fold[c] = rank % 4

    out = {"protocol": "claimed-regime (hidden truth within 20px of train "
                        "endpoints) + gate ablation; seed 12027",
           "script_sha256": sha(Path(__file__)), "folds": []}
    for fold in range(4):
        test_truth = np.isin(comp, [c for c in big if comp_fold[c] == fold]) & valid
        train_traces = (truth & ~test_truth) & valid
        nbr = convolve(train_traces.astype("int32"), np.ones((3, 3), "int32"),
                       mode="constant") - train_traces.astype("int32")
        endpoints = train_traces & (nbr == 1)
        near_end = distance_transform_edt(~endpoints) <= 20
        regime_truth = test_truth & near_end
        region = valid & (distance_transform_edt(~test_truth) <= 25)
        h6, _ = h6_detector(train_traces, rtp, f21, f22, f23, f25, region, valid)
        pred = np.zeros(shape, dtype="float32")
        pred[(h6 > 0) & region] = 1.0
        n_emit = int(pred.sum())
        rng = np.random.default_rng(12027 + fold)
        idx = np.flatnonzero(region)
        ctrl = np.zeros(shape, dtype="float32")
        ctrl.ravel()[rng.choice(idx, min(n_emit, len(idx)), replace=False)] = 1.0
        geo = h6_ungated(train_traces, rtp, region)
        geop = np.zeros(shape, dtype="float32")
        geop[(geo > 0) & region] = 1.0
        row = {"fold": fold,
               "hidden_pixels": int(test_truth.sum()),
               "regime_pixels": int(regime_truth.sum()),
               "regime_share": float(regime_truth.sum() / test_truth.sum()),
               "h6_emitted": n_emit,
               "geo_only_emitted": int(geop.sum()),
               "full_h6_dti": components_masked(pred, test_truth, region, train_traces)["dti"],
               "regime_h6_dti": components_masked(pred, regime_truth, region, train_traces)["dti"],
               "regime_random_dti": components_masked(ctrl, regime_truth, region, train_traces)["dti"],
               "regime_geo_only_dti": components_masked(geop, regime_truth, region, train_traces)["dti"]}
        out["folds"].append(row)
        print(f"fold {fold} hidden={row['hidden_pixels']} regime_share={row['regime_share']:.3f} "
              f"full_h6={row['full_h6_dti']:.4f} regime_h6={row['regime_h6_dti']:.4f} "
              f"regime_rand={row['regime_random_dti']:.4f} geo_only={row['regime_geo_only_dti']:.4f}",
              flush=True)
    for k in ["regime_share", "full_h6_dti", "regime_h6_dti", "regime_random_dti",
              "regime_geo_only_dti"]:
        out[f"mean_{k}"] = float(np.mean([r[k] for r in out["folds"]]))
    out["paired_regime_h6_vs_random"] = [
        float(r["regime_h6_dti"] - r["regime_random_dti"]) for r in out["folds"]]
    out["paired_regime_gated_vs_geo"] = [
        float(r["regime_h6_dti"] - r["regime_geo_only_dti"]) for r in out["folds"]]
    (ROOT / "evidence/h6_regime.json").write_text(json.dumps(out, indent=2))
    (ROOT / "docs/h6_regime.json").write_text(json.dumps(out, indent=2))
    print("means:", {k: round(v, 5) for k, v in out.items() if k.startswith("mean_")})


if __name__ == "__main__":
    main()
