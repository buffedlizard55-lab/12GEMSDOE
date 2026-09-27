"""Trace-component holdout for H6 (near-catalogue geometric completion).

A geographic block holdout cannot validate H6: test-block traces sit km away
from train traces, so any near-catalogue predictor scores ~0 by construction.
This protocol instead hides whole connected trace components (a proxy for
"newly mapped geometry of existing systems", staff 11536/2) and asks H6 to
recover them from the remaining components.

Protocol:
- connected components (8-connectivity) of the catalogue with >= 3 pixels;
  components dealt round-robin into 4 folds by descending size.
- score region = valid pixels within 25px (2.5 km) of a hidden test component
  (near-field: the regime H6 claims), minus a 3px kernel guard around train
  traces is NOT applied (official mask handles train pixels; near-train FPs
  are legitimately penalized per staff 11516/4).
- truth = hidden test components; catalogue mask = train components (visible).
- arms: h6_geometric (fixed natural emission, no top-up), random equal-mass
  control (same pixel count, uniform in region), train-dilation 3px reference.
- metric: components_masked (official pixel-exact mask semantics).
"""
import json
import time
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import label as ndi_label, binary_dilation, distance_transform_edt

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha
from holdout_masked import components_masked, h6_detector

ROOT = Path(__file__).resolve().parents[1]


def main():
    t_all = time.time()
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
    big = [c for c in range(1, ncomp + 1) if sizes[c] >= 3]
    big.sort(key=lambda c: -sizes[c])
    comp_fold = np.zeros(ncomp + 1, dtype="int8")
    for rank, c in enumerate(big):
        comp_fold[c] = rank % 4
    small = truth & (comp_fold[comp] == 0) & ~np.isin(comp, big)
    print(f"components: {ncomp} total, {len(big)} with >=3px; "
          f"small(<3px) px always-train: {int(small.sum())}", flush=True)

    report = {"protocol": "trace-component holdout; near-field region 25px; "
                           "official mask semantics; seed 12027",
              "script_sha256": sha(Path(__file__)),
              "folds": []}
    for fold in range(4):
        start = time.time()
        test_comp = np.isin(comp, [c for c in big if comp_fold[c] == fold])
        test_truth = test_comp & valid
        train_traces = (truth & ~test_comp) & valid
        near = distance_transform_edt(~test_truth) <= 25
        region = valid & near
        rng = np.random.default_rng(12027 + fold)
        h6, diag = h6_detector(train_traces, rtp, f21, f22, f23, f25, region, valid)
        pred = np.zeros(shape, dtype="float32")
        pred[(h6 > 0) & region] = 1.0
        n_emit = int(pred.sum())
        row = {"fold": fold, "hidden_components": int(sum(1 for c in big if comp_fold[c] == fold)),
               "hidden_pixels": int(test_truth.sum()), "region_pixels": int(region.sum()),
               "h6_emitted": n_emit, "h6_diagnostics": diag, "arms": {}}
        row["arms"]["h6_geometric"] = components_masked(pred, test_truth, region, train_traces)
        idx = np.flatnonzero(region)
        ctrl = np.zeros(shape, dtype="float32")
        ctrl.ravel()[rng.choice(idx, min(n_emit, len(idx)), replace=False)] = 1.0
        row["arms"]["random_equal_mass"] = components_masked(
            ctrl, test_truth, region, train_traces)
        ref = binary_dilation(train_traces, iterations=3).astype("float32")
        row["arms"]["train_dilation_3px"] = components_masked(
            ref, test_truth, region, train_traces)
        row["seconds"] = round(time.time() - start, 2)
        report["folds"].append(row)
        print(f"fold {fold} ({row['seconds']}s) hidden={row['hidden_pixels']} "
              f"emit={n_emit} h6={row['arms']['h6_geometric']['dti']:.5f} "
              f"rand={row['arms']['random_equal_mass']['dti']:.5f} "
              f"ref3px={row['arms']['train_dilation_3px']['dti']:.5f}", flush=True)

    for a in ["h6_geometric", "random_equal_mass", "train_dilation_3px"]:
        report[f"mean_{a}"] = float(np.mean([r["arms"][a]["dti"] for r in report["folds"]]))
    report["paired_h6_vs_random"] = [
        float(r["arms"]["h6_geometric"]["dti"] - r["arms"]["random_equal_mass"]["dti"])
        for r in report["folds"]]
    report["total_seconds"] = round(time.time() - t_all, 2)
    report["release_allowed"] = False
    report["release_reason"] = ("Screening only. H6 must beat the equal-mass random "
                                "control on hidden components before any submission "
                                "use; no weekly slot is spent here.")
    (ROOT / "evidence/holdout_trace.json").write_text(json.dumps(report, indent=2))
    (ROOT / "docs/holdout_trace.json").write_text(json.dumps(report, indent=2))
    print("means:", {k: v for k, v in report.items() if k.startswith("mean_")})


if __name__ == "__main__":
    main()
