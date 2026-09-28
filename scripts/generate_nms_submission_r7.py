"""Build Round-7 submission GeoTIFF: NMS-3 thin-trace emission on multi25 + H28 + H32 (DEM-10 m scarp channels).

H32 = 12 label-free channels derived from the USGS 3DEP 1/3 arc-second (~10 m) DEM
      (slope / gradient / micro-relief / one-sided scarp asymmetry per 100 m cell),
      provenance evidence/dem10-fetch.json + evidence/round7-feature-build.json.
      Preregistered primary arm multi25_h28_dem12 (docs/hypotheses-round7.md section 3);
      gate result recorded in evidence/holdout_round7.json and copied into the manifest.

Model: multi25 (first 25 channels of candidate-features-30.npy)
       + H28 (channel 3 of round6_features.npy)
       + H32 (all 12 channels of round7_features.npy)
Emission: greedy NMS Chebyshev radius 2 (5x5 exclusion), budget 2% of valid footprint
Candidates: valid & ~catalogue (new fault cannot be catalogue pixel)

Two files: primary NaN outside, fallback all-finite 0 outside.
The script refuses to run if evidence/holdout_round7.json does not record gate.passed == true.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha, validate
import rasterio as _rio

def validate_relaxed(path, template):
    with _rio.open(template) as t, _rio.open(path) as q:
        for name in ("crs", "transform", "width", "height"):
            if getattr(q, name) != getattr(t, name):
                raise ValueError("grid mismatch: " + name)
        if q.count != 1 or q.dtypes != ("float32",):
            raise ValueError("requires one float32 band")
        a = q.read(1)
        tv = t.read_masks(1) > 0
    if not np.isfinite(a).all() or a.min() < 0.0 or a.max() > 1.0:
        raise ValueError("all-finite variant must be finite and inside [0,1] everywhere")
    return {"sha256": sha(path), "valid_pixels": int(tv.sum()),
            "min": float(a.min()), "max": float(a.max()),
            "mask_equals_template": bool(np.array_equal(~np.isnan(a), tv)),
            "validator": "relaxed (grid/CRS/dtype/range; mask reported, not enforced)"}

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"
CUBE = ROOT / "data/candidate-features-30.npy"
R6 = ROOT / "data/round6_features.npy"
R7 = ROOT / "data/round7_features.npy"
N_BASE = 25
H28_CH = 3  # channel index in round6_features.npy
DEM_CH = list(range(12))  # all channels of round7_features.npy
BUDGET = 0.02
RADIUS = 2
SLUG = "r7-nms3-dem10-scarp"
ARM = "multi25_h28_dem12"

def nms_select(ordered_pixels, shape, max_sel):
    width = shape[1]
    blocked = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    for s0 in range(0, len(ordered_pixels), 50000):
        cand = ordered_pixels[s0:s0+50000]
        ys, xs = np.divmod(cand, width)
        keep = ~blocked[ys, xs]
        for p, y, x in zip(cand[keep], ys[keep], xs[keep]):
            if blocked[y, x]:
                continue
            sel[n] = p
            n += 1
            blocked[max(0, y-RADIUS):y+RADIUS+1, max(0, x-RADIUS):x+RADIUS+1] = True
            if n == max_sel:
                return sel
    return sel[:n]

def train_and_predict():
    with rasterio.open(TEMPLATE) as ds:
        valid = ds.read_masks(1) > 0
        shape = ds.shape
    with rasterio.open(LABELS) as ds:
        labels = (ds.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(CUBE), mode="r")
    r6 = np.lib.format.open_memmap(str(R6), mode="r")
    r7 = np.lib.format.open_memmap(str(R7), mode="r")
    assert cube.shape[:2] == shape
    assert r6.shape[:2] == shape
    assert r7.shape == (*shape, 12)
    r7build = json.loads((ROOT / "evidence/round7-feature-build.json").read_text())
    if sha(R7) != r7build["output"]["sha256"]:
        raise ValueError("round7_features.npy sha does not match evidence/round7-feature-build.json")
    flat_base = cube.reshape(-1, 30)[:, :N_BASE]
    flat_h28 = r6.reshape(-1, 5)[:, H28_CH]
    flat_dem = r7.reshape(-1, 12)[:, DEM_CH]
    flat = np.column_stack([flat_base, flat_h28, flat_dem])
    # training
    rng = np.random.default_rng(12027)
    pos = np.flatnonzero(valid & labels)
    neg_all = np.flatnonzero(valid & ~labels)
    neg = rng.choice(neg_all, min(100000, len(neg_all)), replace=False)
    tidx = np.concatenate([pos, neg])
    y = labels.ravel()[tidx]
    weights = np.where(y, 0.5/len(pos), 0.5/len(neg)) * len(tidx)
    clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027)
    clf.fit(flat[tidx], y, sample_weight=weights)

    vidx = np.flatnonzero(valid)
    prob = np.empty(len(vidx), dtype="float32")
    for s0 in range(0, len(vidx), 200000):
        ids = vidx[s0:s0+200000]
        prob[s0:s0+len(ids)] = clf.predict_proba(flat[ids])[:,1]

    info = {"model": "HistGradientBoostingClassifier",
            "model_parameters": {"max_iter": 100, "max_leaf_nodes": 15, "early_stopping": False, "random_state": 12027},
            "arm": ARM,
            "features": f"first {N_BASE} channels of candidate-features-30.npy + H28 (mag_anom local variance 11px) channel {H28_CH} of round6_features.npy + H32 channels {DEM_CH} of round7_features.npy (n_features={flat.shape[1]})",
            "training": {"positives": int(len(pos)), "sampled_negatives": int(len(neg)), "class_weighting": "balanced total weight"},
            "round6_feature_sha256": sha(R6),
            "round6_build": json.loads((ROOT / "evidence/round6-feature-build.json").read_text())["output"]["sha256"],
            "round7_feature_sha256": sha(R7),
            "round7_build": r7build["output"]["sha256"],
            "external_data": {
                "product": r7build["inputs"]["upstream_product"],
                "product_catalog": r7build["inputs"]["upstream_product_catalog"],
                "tiles": r7build["inputs"]["upstream_tiles"],
                "licence": "USGS 3DEP — U.S. public domain",
                "built_by": f"{r7build['inputs']['source_repo']} tag {r7build['inputs']['source_tag']} commit {r7build['inputs']['source_tag_commit']}",
                "fetch_provenance": "evidence/dem10-fetch.json",
            },
            }
    return valid, labels, vidx, prob, info, shape

def write_variant(values, path, outside):
    with rasterio.open(TEMPLATE) as t:
        profile = t.profile.copy()
        valid = t.read_masks(1) > 0
    a = values.copy()
    a[~valid] = np.nan if outside == "nan" else 0.0
    profile.update(count=1, dtype="float32", nodata=np.nan, compress="deflate")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(a, 1)
    return validate(path, TEMPLATE) if outside == "nan" else validate_relaxed(path, TEMPLATE)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/downloads")
    args = ap.parse_args()

    gate = json.loads((ROOT / "evidence/holdout_round7.json").read_text())
    if not gate.get("gate", {}).get("passed"):
        raise SystemExit("Round-7 gate did not pass (evidence/holdout_round7.json gate.passed != true); refusing to package.")
    if gate.get("primary") != ARM:
        raise SystemExit(f"holdout primary arm {gate.get('primary')} != packaging arm {ARM}")
    valid, labels, vidx, prob, model_info, shape = train_and_predict()
    cand_mask = valid & ~labels
    in_cand = cand_mask.ravel()[vidx]
    cand_idx, cand_prob = vidx[in_cand], prob[in_cand]
    mass = int(BUDGET * int(valid.sum()))
    ordered = cand_idx[np.lexsort((cand_idx, -cand_prob))]
    sel = nms_select(ordered, shape, mass)

    values = np.zeros(shape, dtype="float32")
    values.ravel()[sel] = 1.0

    args.out.mkdir(parents=True, exist_ok=True)
    digest_probe = args.out / f".tmp-{SLUG}.tif"
    v_primary = write_variant(values, digest_probe, "nan")
    digest = v_primary["sha256"][:12]
    stem = f"12GEMSDOE_{SLUG}_{digest}"
    tif = args.out / f"{stem}.tif"
    digest_probe.replace(tif)
    v_primary = validate(tif, TEMPLATE)

    fallback = args.out / f"{stem}_allfinite.tif"
    v_fallback = write_variant(values, fallback, "zero")
    with rasterio.open(fallback) as s:
        raw = s.read(1)
    assert np.isfinite(raw).all() and raw.min() >= 0.0 and raw.max() <= 1.0

    zip_path = args.out / f"{stem}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zip_path) as z:
        zip_names = z.namelist()
    assert len(zip_names) == 1

    dense = gate["truth_protocols"]["dense_catalogue_truth"]
    sparse = gate["truth_protocols"]["sparse_thinned_20pct"]
    gate_text = (f"{ARM} vs multi25_h28: dense {dense['fold_wins_vs_incumbent_nms3'][ARM]}/4 folds "
                 f"mean {dense['mean_gain_vs_incumbent_nms3'][ARM]:+.5f}, sparse {sparse['fold_wins_vs_incumbent_nms3'][ARM]}/4 folds "
                 f"mean {sparse['mean_gain_vs_incumbent_nms3'][ARM]:+.5f}")
    note = (f"12GEMSDOE R7 | NMS-3 thin-trace on multi25+H28+H32 GBM; H32 = 12 USGS 3DEP 10 m DEM scarp channels "
            f"(slope/gradient/micro-relief/one-sided asymmetry per 100 m cell) | "
            f"5x5 exclusion 2.0% mass {len(sel)} px | sha256:{v_primary['sha256'][:12]}")

    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "slug": SLUG,
        "policy": {
            "emission": "greedy NMS Chebyshev radius 2 (5x5), descending probability, deterministic tie-break",
            "budget_fraction_of_valid": BUDGET,
            "emitted_pixels": int(len(sel)),
            "valid_pixels": int(valid.sum()),
            "candidates": "valid & ~catalogue",
            "values": "1.0 on emitted pixels, 0.0 elsewhere inside footprint",
            "preregistered_in": "docs/hypotheses-round7.md",
            "gate_result": gate_text,
            "gate": gate["gate"],
        },
        "model": model_info,
        "files": {
            "primary_tif": {"name": tif.name, "bytes": tif.stat().st_size, "validation": v_primary, "outside_footprint": "NaN"},
            "fallback_tif": {"name": fallback.name, "bytes": fallback.stat().st_size, "validation": v_fallback, "outside_footprint": "0.0", "use_if": "primary rejected with 'Predicted values must be in range [0, 1]'"},
            "zip": {"name": zip_path.name, "bytes": zip_path.stat().st_size, "contents": zip_names},
        },
        "suggested_note": note,
        "template_sha256": sha(TEMPLATE),
        "labels_sha256": sha(LABELS),
        "feature_cube_sha256": sha(CUBE),
        "round6_feature_sha256": sha(R6),
        "round7_feature_sha256": sha(R7),
        "holdout_evidence": ["evidence/holdout_round7.json", "evidence/round7-feature-build.json", "evidence/dem10-fetch.json", "evidence/holdout_round6.json", "evidence/round5-emission-probe.json"],
        "drivendata_score": None,
        "release_status": f"Format-validated locally and holdout-validated ({gate_text}). NOT scored by DrivenData; no slot spent by the agent; strongest-sibling-baseline gate still unsatisfied. Uses external USGS 3DEP DEM (public domain) — disclose if asked.",
    }
    (args.out / f"{stem}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"primary": tif.name, "fallback": fallback.name, "zip": zip_path.name, "emitted_pixels": int(len(sel)), "sha256": v_primary["sha256"], "note": note}, indent=2))

if __name__ == "__main__":
    main()
