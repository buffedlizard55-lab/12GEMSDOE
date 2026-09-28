"""Round-8 frozen run: H37 control, H38 mass sweep, H39 1 m-lidar scarp arm, H40 graded.

Preregistered in `docs/hypotheses-round8.md` (sections 3, 3.4, 3.5, 4) before this run.

Protocol is the frozen Round-5..7 protocol: 512-px blocks, 12-px collar, seed 12027,
pixel-exact catalogue mask on the FP weight, NMS radius 2, literal DTI kernel
`k = max(1 - d/3, 0)`; truth protocols `dense_catalogue_truth`, `sparse_thinned_20pct`
(seed 4242+f) plus two diagnostics `offset_adjacent_1_3px` and `offset_far_4_6px_control`.

The R7 incumbent arm is retrained here with the *identical* learner configuration and sampling
seed, so its numbers must reproduce `evidence/holdout_round7.json` to the last digit; that
reproduction is asserted, not assumed.

Nothing is uploaded. Output: evidence/holdout_round8.json + docs copy.
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
RADIUS = 2
N_BASE = 25
H28_CH = 3
DEM12 = list(range(12))
LIDAR_ALL = list(range(12))          # 11 descriptors + `valid` coverage; 0 = no lidar
BUDGETS = [0.02, 0.032, 0.05, 0.08]
GRADED_TAUS = [0.02, 0.032]
REFERENCE = "multi25"
INCUMBENT = "multi25_h28_dem12"
LIDAR_ARM = "multi25_h28_dem12_lidar12"
ARMS = {
    REFERENCE: {"r6": [], "r7": [], "lidar": []},
    INCUMBENT: {"r6": [H28_CH], "r7": DEM12, "lidar": []},
    LIDAR_ARM: {"r6": [H28_CH], "r7": DEM12, "lidar": LIDAR_ALL},
}
# emissions produced per fold and per arm (name -> kind)
EMISSIONS = {INCUMBENT: [*(f"nms{b:.3f}" for b in BUDGETS),
                         *(f"graded{t:.3f}" for t in GRADED_TAUS),
                         "nms0.020+cat"],
             LIDAR_ARM: [*(f"nms{b:.3f}" for b in BUDGETS),
                         *(f"graded{t:.3f}" for t in GRADED_TAUS),
                         "nms0.020+cat"],
             REFERENCE: ["nms0.020"]}


def dti_binary(pred, truth_coords, weight_fp):
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
    fp = float(np.sum(pred.astype("float32") * weight_fp, dtype="float64"))
    return dict(tp=tp, fp=fp, fn=fn, coverage=tp / max(len(yy), 1), truth_px=int(len(yy)),
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
        for p_, y, x in zip(cand[keep], ys[keep], xs[keep]):
            if blocked[y, x]:
                continue
            sel[n] = p_
            n += 1
            blocked[max(0, y - RADIUS):y + RADIUS + 1, max(0, x - RADIUS):x + RADIUS + 1] = True
            if n == max_sel:
                return sel
    return sel[:n]


def int_median(values_u8):
    counts = np.bincount(values_u8, minlength=256)
    c = np.cumsum(counts)
    return int(np.searchsorted(c, c[-1] / 2.0))


def offset_truth(truth, catalogue, region, seed, lo, hi):
    comp, ncomp = ndi_label(truth, structure=np.ones((3, 3), int))
    out = np.zeros_like(truth)
    h, w = truth.shape
    rng = np.random.default_rng(seed)
    for c in range(1, ncomp + 1):
        ys, xs = np.nonzero(comp == c)
        if len(ys) == 0:
            continue
        r = int(rng.integers(lo, hi + 1))
        th = float(rng.uniform(0, 2 * np.pi))
        dy, dx = int(round(r * np.sin(th))), int(round(r * np.cos(th)))
        ny, nx = ys + dy, xs + dx
        keep = (ny >= 0) & (nx >= 0) & (ny < h) & (nx < w)
        out[ny[keep], nx[keep]] = True
    return out & region & ~catalogue


def main() -> None:
    t_all = time.time()
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        valid = s.read_masks(1) > 0
        shape = s.shape
    with rasterio.open(ROOT / "data/labels.tif") as s:
        catalogue = (s.read(1, masked=True).filled(0) > 0) & valid

    cube = np.lib.format.open_memmap(str(ROOT / "data/candidate-features-30.npy"), mode="r")
    flat = cube.reshape(-1, cube.shape[2])
    r6p, r7p = ROOT / "data/round6_features.npy", ROOT / "data/round7_features.npy"
    r6build = json.loads((ROOT / "evidence/round6-feature-build.json").read_text())
    r7build = json.loads((ROOT / "evidence/round7-feature-build.json").read_text())
    lidarbuild = json.loads((ROOT / "evidence/lidar-fetch.json").read_text())
    for path, sidecar in ((r6p, r6build), (r7p, r7build)):
        if sha(path) != sidecar["output"]["sha256"]:
            raise ValueError(f"{path.name} sha does not match {sidecar['output']['sha256']}")
    lidar_path = ROOT / "data/ext/lidar_scarp_u8.tif"
    if sha(lidar_path) != lidarbuild["file"]["sha256"]:
        raise ValueError("lidar cube sha does not match evidence/lidar-fetch.json")
    extra = {"r6": np.lib.format.open_memmap(str(r6p), mode="r").reshape(-1, 5),
             "r7": np.lib.format.open_memmap(str(r7p), mode="r").reshape(-1, 12)}
    with rasterio.open(lidar_path) as s:
        assert s.shape == shape and s.count == 12 and set(s.dtypes) == {"uint8"}
        assert tuple(s.transform)[:6] == tuple(rasterio.open(ROOT / "data/sample_submission.tif").transform)[:6]
        lidar_u8 = np.ascontiguousarray(s.read().transpose(1, 2, 0).reshape(-1, 12))

    fmap = folds(catalogue)
    report = {
        "protocol": "masked spatial holdout; 512 px blocks; 12 px collar; seed 12027; "
                    "pixel-exact catalogue mask on FP; NMS radius 2; literal kernel k=max(1-d/3,0)",
        "preregistered_register": "docs/hypotheses-round8.md (sections 3, 3.4, 3.5, 4)",
        "budgets": BUDGETS, "graded_taus": GRADED_TAUS,
        "arms": ARMS, "reference": REFERENCE, "incumbent": INCUMBENT, "primary_candidate": LIDAR_ARM,
        "feature_cube_sha256": sha(ROOT / "data/candidate-features-30.npy"),
        "round6_feature_sha256": sha(r6p), "round7_feature_sha256": sha(r7p),
        "lidar_feature_sha256": sha(lidar_path),
        "lidar_source": {"product": "USGS 3DEP 1 m DEM -> 2 m scarp descriptors -> 100 m grid (uint8)",
                         "upstream_official_source": lidarbuild["upstream_official_source"],
                         "bridge_repo": lidarbuild["bridge"]["repo"], "bridge_commit": lidarbuild["bridge"]["commit"],
                         "build_run": lidarbuild["bridge"]["workflow_run"],
                         "sidecar": "evidence/lidar-fetch.json", "labels_used": False},
        "core_sha256": sha(ROOT / "scripts/core.py"), "script_sha256": sha(Path(__file__)),
        "catalogue_pixels": int(catalogue.sum()),
        "decision_rule": "chosen_arm = H39 arm iff it beats the R7 incumbent on >=3/4 folds with positive mean "
                         "paired gain on BOTH catalogue protocols at 2%; else the R7 incumbent. chosen_budget = "
                         "argmax over {0.02,0.032,0.05,0.08} of min(mean dense, mean sparse) for the chosen arm, "
                         "accepted only if it beats 2% on >=3/4 folds on both protocols; else 0.02.",
        "folds": [], "protocols": {},
    }
    PROTO_ORDER = ["dense_catalogue_truth", "sparse_thinned_20pct",
                   "offset_adjacent_1_3px", "offset_far_4_6px_control"]

    for fold in range(4):
        start = time.time()
        train = training_mask(fmap, fold, valid)
        region = valid & (fmap == fold)
        dense_truth = catalogue & region
        comp, ncomp = ndi_label(dense_truth, structure=np.ones((3, 3), int))
        keep = np.random.default_rng(4242 + fold).choice(
            np.arange(1, ncomp + 1), max(1, int(0.2 * ncomp)), replace=False)
        truths = {
            "dense_catalogue_truth": dense_truth,
            "sparse_thinned_20pct": dense_truth & np.isin(comp, keep),
            "offset_adjacent_1_3px": offset_truth(dense_truth, catalogue, region, 9001 + fold, 1, 3),
            "offset_far_4_6px_control": offset_truth(dense_truth, catalogue, region, 9001 + fold, 4, 6),
        }
        truth_coords, weight_fp = {}, {}
        for name, t in truths.items():
            truth_coords[name] = np.nonzero(t)
            weight = np.minimum(distance_transform_edt(~t) / 3, 1)
            weight_fp[name] = (weight * (region & ~catalogue)).astype("float32")
        testidx = np.flatnonzero(region)
        probe = binary_dilation(catalogue & train, iterations=3).astype("float32")

        row = {"fold": fold, "score_pixels": int(len(testidx)),
               "truth_px": {k: int(v.sum()) for k, v in truths.items()},
               "leakage_probe_dti": {n: dti_binary(probe, truth_coords[n], weight_fp[n])["dti"]
                                     for n in PROTO_ORDER},
               "arms": {}}

        # --- training set (identical to Rounds 5-7) ---
        rng = np.random.default_rng(12027 + fold)
        pos = np.flatnonzero(train & catalogue)
        neg = rng.choice(np.flatnonzero(train & ~catalogue), 100000, replace=False)
        tidx = np.concatenate([pos, neg])
        y = np.concatenate([np.ones(len(pos), int), np.zeros(len(neg), int)])
        weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(tidx)
        train_flat = (train & valid).ravel()
        lidar_med = np.array([int_median(lidar_u8[train_flat, c]) for c in LIDAR_ALL], dtype="float32")

        def matrix(ids, cols):
            parts = [flat[ids, :N_BASE]]
            for src in ("r6", "r7"):
                if cols[src]:
                    parts.append(extra[src][np.ix_(ids, cols[src])])
            if cols["lidar"]:
                v = lidar_u8[ids][:, cols["lidar"]].astype("float32")
                imp = np.where(v == 0.0, lidar_med[cols["lidar"]], v)
                # keep the coverage channel raw (0 genuinely means "no lidar") when present
                if 11 in cols["lidar"]:
                    imp[:, cols["lidar"].index(11)] = v[:, cols["lidar"].index(11)]
                parts.append(imp)
            return np.column_stack(parts)

        for arm, cols in ARMS.items():
            cache_path = CACHE / f"prob-{arm}-fold{fold}.npz"
            if cache_path.exists():
                prob = np.load(cache_path)["prob"]
            else:
                clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
                                                     early_stopping=False, random_state=12027)
                clf.fit(matrix(tidx, cols), y, sample_weight=weights)
                prob = np.empty(len(testidx), dtype="float32")
                for s0 in range(0, len(testidx), 100000):
                    ids = testidx[s0:s0 + 100000]
                    prob[s0:s0 + len(ids)] = clf.predict_proba(matrix(ids, cols))[:, 1]
            ordered = testidx[np.lexsort((testidx, -prob))]
            cat32 = catalogue.astype("float32")
            for emis in EMISSIONS[arm]:
                if emis.startswith("nms"):
                    frac = float(emis.split("+")[0][3:])
                    pred = np.zeros(shape, dtype="float32")
                    pred.ravel()[nms_select(ordered, shape, int(frac * len(testidx)))] = 1.0
                    if emis.endswith("+cat"):
                        pred = np.maximum(pred, cat32)
                elif emis.startswith("graded"):
                    tau = float(emis[6:])
                    pred = np.zeros(shape, dtype="float32")
                    pred.ravel()[testidx] = np.clip((prob - tau) / (1.0 - tau), 0.0, 1.0)
                else:
                    raise ValueError(emis)
                row["arms"].setdefault(arm, {})[emis] = {
                    n: dti_binary(pred, truth_coords[n], weight_fp[n]) for n in PROTO_ORDER}
                del pred
            row["arms"][arm]["_reproduced_from_cache"] = bool(cache_path.exists())
        row["seconds"] = round(time.time() - start, 1)
        report["folds"].append(row)
        best = {n: max(row["arms"][a][e][n]["dti"] for a in ARMS for e in EMISSIONS[a]) for n in PROTO_ORDER}
        print(f"[fold {fold}] {row['seconds']}s probe={max(row['leakage_probe_dti'].values()):.4f} "
              f"dense={row['arms'][INCUMBENT]['nms0.020']['dense_catalogue_truth']['dti']:.5f} "
              f"sparse={row['arms'][INCUMBENT]['nms0.020']['sparse_thinned_20pct']['dti']:.5f} "
              f"lidar_dense={row['arms'][LIDAR_ARM]['nms0.020']['dense_catalogue_truth']['dti']:.5f} "
              f"best_dense={best['dense_catalogue_truth']:.5f}", flush=True)

    # ---------------- aggregation ----------------
    def mean_dti(arm, emis, proto):
        return float(np.mean([f["arms"][arm][emis][proto]["dti"] for f in report["folds"]]))

    def wins(arm, emis, proto, base="nms0.020"):
        return int(sum(f["arms"][arm][emis][proto]["dti"] > f["arms"][arm][base][proto]["dti"]
                       for f in report["folds"]))

    protos = {}
    for n in PROTO_ORDER:
        means = {f"{a}|{e}": mean_dti(a, e, n) for a in ARMS for e in EMISSIONS[a]}
        protos[n] = {"means": means,
                     "leakage_probe_max": max(f["leakage_probe_dti"][n] for f in report["folds"]),
                     "best_key": max(means, key=means.get)}
    report["protocols"] = protos

    # R7 reproduction check (harness validation, asserted below)
    r7_evidence = json.loads((ROOT / "evidence/holdout_round7.json").read_text())
    repro = {}
    for proto in ("dense_catalogue_truth", "sparse_thinned_20pct"):
        recorded = r7_evidence["truth_protocols"][proto]["means"].get(f"{INCUMBENT}_nms3")
        if recorded is None:
            recorded = next(v for k, v in r7_evidence["truth_protocols"][proto]["means"].items()
                            if k.startswith(INCUMBENT))
        repro[proto] = {"recorded_r7": recorded, "rerun_r8": mean_dti(INCUMBENT, "nms0.020", proto)}
        repro[proto]["abs_diff"] = abs(repro[proto]["recorded_r7"] - repro[proto]["rerun_r8"])
    report["r7_reproduction"] = repro

    d, s = protos["dense_catalogue_truth"]["means"], protos["sparse_thinned_20pct"]["means"]
    h39_d = [f["arms"][LIDAR_ARM]["nms0.020"]["dense_catalogue_truth"]["dti"]
             - f["arms"][INCUMBENT]["nms0.020"]["dense_catalogue_truth"]["dti"] for f in report["folds"]]
    h39_s = [f["arms"][LIDAR_ARM]["nms0.020"]["sparse_thinned_20pct"]["dti"]
             - f["arms"][INCUMBENT]["nms0.020"]["sparse_thinned_20pct"]["dti"] for f in report["folds"]]
    h39_pass = (sum(x > 0 for x in h39_d) >= 3 and sum(x > 0 for x in h39_s) >= 3
                and float(np.mean(h39_d)) > 0 and float(np.mean(h39_s)) > 0)
    chosen_arm = LIDAR_ARM if h39_pass else INCUMBENT

    sweep = {}
    for b in BUDGETS:
        e = f"nms{b:.3f}"
        sweep[f"{b:.3f}"] = {
            "dense_mean": mean_dti(chosen_arm, e, "dense_catalogue_truth"),
            "sparse_mean": mean_dti(chosen_arm, e, "sparse_thinned_20pct"),
            "offset_adjacent_mean": mean_dti(chosen_arm, e, "offset_adjacent_1_3px"),
            "dense_fold_wins_vs_2pct": wins(chosen_arm, e, "dense_catalogue_truth"),
            "sparse_fold_wins_vs_2pct": wins(chosen_arm, e, "sparse_thinned_20pct"),
            "min_mean": min(mean_dti(chosen_arm, e, "dense_catalogue_truth"),
                            mean_dti(chosen_arm, e, "sparse_thinned_20pct")),
        }
    best_budget = max(BUDGETS, key=lambda b: sweep[f"{b:.3f}"]["min_mean"])
    chosen_budget = best_budget if (
        best_budget != 0.02
        and sweep[f"{best_budget:.3f}"]["dense_fold_wins_vs_2pct"] >= 3
        and sweep[f"{best_budget:.3f}"]["sparse_fold_wins_vs_2pct"] >= 3) else 0.02

    h37 = {p: [f["arms"][INCUMBENT]["nms0.020+cat"][p]["dti"] - f["arms"][INCUMBENT]["nms0.020"][p]["dti"]
               for f in report["folds"]] for p in PROTO_ORDER}
    e_chosen = f"nms{chosen_budget:.3f}"
    gate = {
        "rule": report["decision_rule"],
        "h37_control_mean_gain": {p: float(np.mean(h37[p])) for p in PROTO_ORDER},
        "h37_control_catalogue_protocol_folds_won": {
            p: int(sum(x > 0 for x in h37[p])) for p in ("dense_catalogue_truth", "sparse_thinned_20pct")},
        "h39_passed": bool(h39_pass),
        "h39_paired_dense": [round(x, 6) for x in h39_d],
        "h39_paired_sparse": [round(x, 6) for x in h39_s],
        "h39_fold_wins_dense": int(sum(x > 0 for x in h39_d)),
        "h39_fold_wins_sparse": int(sum(x > 0 for x in h39_s)),
        "h40_graded_gain_dense": mean_dti(chosen_arm, "graded0.020", "dense_catalogue_truth")
                                 - mean_dti(chosen_arm, "nms0.020", "dense_catalogue_truth"),
        "h40_graded_gain_sparse": mean_dti(chosen_arm, "graded0.020", "sparse_thinned_20pct")
                                  - mean_dti(chosen_arm, "nms0.020", "sparse_thinned_20pct"),
        "chosen_arm": chosen_arm,
        "budget_sweep": sweep,
        "chosen_budget": chosen_budget,
        "incumbent_dense_2pct": mean_dti(INCUMBENT, "nms0.020", "dense_catalogue_truth"),
        "incumbent_sparse_2pct": mean_dti(INCUMBENT, "nms0.020", "sparse_thinned_20pct"),
        "chosen_dense": mean_dti(chosen_arm, e_chosen, "dense_catalogue_truth"),
        "chosen_sparse": mean_dti(chosen_arm, e_chosen, "sparse_thinned_20pct"),
        "chosen_offset_adjacent": mean_dti(chosen_arm, e_chosen, "offset_adjacent_1_3px"),
        "chosen_offset_far": mean_dti(chosen_arm, e_chosen, "offset_far_4_6px_control"),
        "leakage_probe_max": max(v["leakage_probe_max"] for v in protos.values()),
        "r7_reproduced_within": max(v["abs_diff"] for v in repro.values()),
    }
    beats_incumbent = (gate["chosen_dense"] > gate["incumbent_dense_2pct"]
                       and gate["chosen_sparse"] > gate["incumbent_sparse_2pct"])
    gate["passed"] = bool(
        gate["leakage_probe_max"] == 0.0
        and gate["r7_reproduced_within"] < 5e-4
        and (beats_incumbent or chosen_budget != 0.02 or h39_pass))
    report["gate"] = gate
    report["seconds_total"] = round(time.time() - t_all, 1)
    report["release_allowed"] = bool(gate["passed"])
    report["release_reason"] = ("gate passed: chosen arm/budget beats the R7 incumbent on both catalogue "
                                "protocols with a 0.0 leakage probe" if gate["passed"] else
                                "gate failed: no lever beat the R7 incumbent on both catalogue protocols")

    text = json.dumps(report, indent=1, sort_keys=True)
    (ROOT / "evidence/holdout_round8.json").write_text(text)
    (ROOT / "docs/holdout_round8.json").write_text(text)
    print(json.dumps({k: gate[k] for k in ("chosen_arm", "chosen_budget", "incumbent_dense_2pct",
                                           "incumbent_sparse_2pct", "chosen_dense", "chosen_sparse",
                                           "h39_passed", "h39_fold_wins_dense", "h39_fold_wins_sparse",
                                           "h40_graded_gain_dense", "leakage_probe_max",
                                           "r7_reproduced_within", "passed")}, indent=1))
    print("wrote evidence/holdout_round8.json", f"({report['seconds_total']}s)")


if __name__ == "__main__":
    main()
