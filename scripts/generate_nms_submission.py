"""Build the Round-5 submission GeoTIFF: NMS-3 thin-trace emission on multi25.

What this is
------------
A single-band float32 GeoTIFF on the official submission grid, produced by the
policy preregistered in docs/hypotheses-round5.md section 5 and validated in
scripts/round5_emission_probe.py / scripts/round5_offcatalogue_check.py:

  * model     : the reproduced multi25 HistGradientBoostingClassifier
                (max_iter=100, max_leaf_nodes=15, early_stopping=False,
                 random_state=12027, balanced total class weight, 100k sampled
                 negatives) trained on the full catalogue;
  * emission  : greedy non-maximum suppression with Chebyshev radius 2 (5x5
                exclusion), descending probability, deterministic tie-break by
                pixel index, mass = 2 % of the valid footprint;
  * candidates: valid pixels that are NOT known-catalogue pixels, because a new
                fault is by definition a pixel the catalogue does not already
                capture (staff 11516/2, 11536/2).

Two files are written, because the DrivenData range check is not published:

  * primary  : NaN outside the survey footprint -- byte-for-byte the same
               convention as the official sample_submission.tif (verified
               locally: float32, nodata=NaN, 7,111,787 NaN pixels outside,
               5,167,373 valid pixels with values in {0, 1});
  * fallback : 0.0 outside the footprint, i.e. every pixel of the raster is
               finite and inside [0, 1]. Use this only if the primary file is
               rejected with "Predicted values must be in range [0, 1]"; that
               error is what a range check run on an unmasked read of a
               NaN-containing raster produces (see docs/session-review.md §2
               and evidence/round5-identity-checks.json C1).

Both files are score-neutral with respect to each other: pixels outside the
footprint contribute 0 to the false-positive term either way.

This command never contacts DrivenData and never consumes a submission slot.
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
    """Grid/CRS/dtype/range validation WITHOUT requiring mask equality.

    core.validate() (correctly) insists that the alpha mask equals the official
    template mask, which a fully-finite raster cannot satisfy. The submission
    form only states that the file "must match the submission format's CRS,
    shape, and geotransform", so the all-finite fallback variant is checked
    against exactly those properties plus the [0, 1] range, and the mask
    difference is reported rather than fatal.
    """
    with _rio.open(template) as t, _rio.open(path) as q:
        for name in ("crs", "transform", "width", "height"):
            if getattr(q, name) != getattr(t, name):
                raise ValueError("grid mismatch: " + name)
        if q.count != 1 or q.dtypes != ("float32",):
            raise ValueError("requires one float32 band")
        a = q.read(1)
        tv = t.read_masks(1) > 0
    if not np.isfinite(a).all() or a.min() < 0.0 or a.max() > 1.0:
        raise ValueError("all-finite variant must be finite and inside [0, 1] everywhere")
    return {"sha256": sha(path), "valid_pixels": int(tv.sum()),
            "min": float(a.min()), "max": float(a.max()),
            "mask_equals_template": bool(np.array_equal(~np.isnan(a), tv)),
            "validator": "relaxed (grid/CRS/dtype/range; mask reported, not enforced)"}

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"
CUBE = ROOT / "data/candidate-features-30.npy"
N_BASE = 25
BUDGET = 0.02
RADIUS = 2
SLUG = "r5-nms3-trace"


def nms_select(ordered_pixels, shape, max_sel):
    """Greedy NMS with a (2*RADIUS+1)^2 exclusion box, in descending score order."""
    width = shape[1]
    blocked_y = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    for s0 in range(0, len(ordered_pixels), 50000):
        cand = ordered_pixels[s0:s0 + 50000]
        ys, xs = np.divmod(cand, width)
        keep = ~blocked_y[ys, xs]
        for p, y, x in zip(cand[keep], ys[keep], xs[keep]):
            if blocked_y[y, x]:
                continue
            sel[n] = p
            n += 1
            blocked_y[max(0, y - RADIUS):y + RADIUS + 1,
                      max(0, x - RADIUS):x + RADIUS + 1] = True
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
    if cube.shape != (*shape, 30):
        raise ValueError(f"expected a 30-channel cube shaped {shape}; got {cube.shape}")
    flat = cube.reshape(-1, 30)

    rng = np.random.default_rng(12027)
    pos = np.flatnonzero(valid & labels)
    neg_all = np.flatnonzero(valid & ~labels)
    neg = rng.choice(neg_all, min(100000, len(neg_all)), replace=False)
    tidx = np.concatenate([pos, neg])
    y = labels.ravel()[tidx]
    weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(tidx)
    clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
                                         early_stopping=False, random_state=12027)
    clf.fit(flat[tidx, :N_BASE], y, sample_weight=weights)

    vidx = np.flatnonzero(valid)
    prob = np.empty(len(vidx), dtype="float32")
    for s0 in range(0, len(vidx), 200000):
        ids = vidx[s0:s0 + 200000]
        prob[s0:s0 + len(ids)] = clf.predict_proba(flat[ids, :N_BASE])[:, 1]
    info = {"model": "HistGradientBoostingClassifier",
            "model_parameters": {"max_iter": 100, "max_leaf_nodes": 15,
                                 "early_stopping": False, "random_state": 12027},
            "features": f"first {N_BASE} channels of data/candidate-features-30.npy",
            "training": {"positives": int(len(pos)), "sampled_negatives": int(len(neg)),
                         "class_weighting": "balanced total weight"}}
    return valid, labels, vidx, prob, info


def write_variant(values, path, outside):
    """Write one GeoTIFF variant. outside='nan' mirrors the official sample."""
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

    valid, labels, vidx, prob, model_info = train_and_predict()
    cand_mask = valid & ~labels
    in_cand = cand_mask.ravel()[vidx]
    cand_idx, cand_prob = vidx[in_cand], prob[in_cand]
    mass = int(BUDGET * int(valid.sum()))
    if len(cand_idx) < mass:
        raise RuntimeError("not enough off-catalogue candidates for the budget")
    ordered = cand_idx[np.lexsort((cand_idx, -cand_prob))]
    sel = nms_select(ordered, valid.shape, mass)

    values = np.zeros(valid.shape, dtype="float32")
    values.ravel()[sel] = 1.0
    on_catalogue = int(labels.ravel()[sel].sum())
    if on_catalogue:
        raise RuntimeError("emission touched catalogue pixels; candidates were restricted")

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
    assert np.isfinite(raw).all() and raw.min() >= 0.0 and raw.max() <= 1.0, \
        "fallback variant must be finite and inside [0,1] on every pixel"

    zip_path = args.out / f"{stem}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zip_path) as z:
        zip_names = z.namelist()
    if len(zip_names) != 1:
        raise RuntimeError(f"zip must contain exactly one GeoTIFF, got {zip_names}")

    note = (f"12GEMSDOE R5 | NMS-3 thin-trace emission (5x5 exclusion, 2.0% mass, "
            f"{len(sel)} px) on multi25 GBM | sha256:{v_primary['sha256'][:12]}")
    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "slug": SLUG,
        "policy": {
            "emission": "greedy non-maximum suppression, Chebyshev radius 2 (5x5), "
                        "descending probability, deterministic tie-break by pixel index",
            "budget_fraction_of_valid": BUDGET,
            "emitted_pixels": int(len(sel)),
            "valid_pixels": int(valid.sum()),
            "candidates": "valid & ~catalogue (a new fault is not a catalogue pixel)",
            "values": "1.0 on emitted pixels, 0.0 elsewhere inside the footprint",
            "preregistered_in": "docs/hypotheses-round5.md",
        },
        "model": model_info,
        "files": {
            "primary_tif": {"name": tif.name, "bytes": tif.stat().st_size,
                            "validation": v_primary,
                            "outside_footprint": "NaN (mirrors official sample_submission.tif)"},
            "fallback_tif": {"name": fallback.name, "bytes": fallback.stat().st_size,
                             "validation": v_fallback,
                             "outside_footprint": "0.0 (every pixel finite and in [0,1])",
                             "use_if": "the primary file is rejected with "
                                       "'Predicted values must be in range [0, 1]'"},
            "zip": {"name": zip_path.name, "bytes": zip_path.stat().st_size,
                    "contents": zip_names},
        },
        "suggested_note": note,
        "template_sha256": sha(TEMPLATE),
        "labels_sha256": sha(LABELS),
        "feature_cube_sha256": sha(CUBE),
        "holdout_evidence": ["evidence/round5-emission-probe.json",
                             "evidence/round5-offcatalogue-check.json",
                             "evidence/holdout_round5.json"],
        "drivendata_score": None,
        "release_status": ("Format-validated locally and holdout-validated on both truth "
                           "protocols. NOT scored by DrivenData in this evidence set, and "
                           "the standing strongest-sibling-baseline gate is unsatisfied. "
                           "Spending a weekly slot is a human decision."),
    }
    (args.out / f"{stem}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"primary": tif.name, "fallback": fallback.name, "zip": zip_path.name,
                      "emitted_pixels": int(len(sel)), "sha256": v_primary["sha256"],
                      "min": v_primary["min"], "max": v_primary["max"],
                      "valid_pixels": v_primary["valid_pixels"], "note": note}, indent=2))


if __name__ == "__main__":
    main()
