"""Build the Round-8 submission GeoTIFF from the frozen Round-8 gate result.

Reads `evidence/holdout_round8.json` and refuses to package anything unless the frozen gate
passed.  The arm and the emission budget come from that file, not from constants here, so the
artifact can only be reproduced from the evidence that authorised it.

  arm      multi25_h28_dem12         = 25 candidate channels + H28 + 12 USGS 3DEP-10 m channels
           multi25_h28_dem12_lidar12 = the same + 12 USGS 3DEP-1 m lidar scarp descriptors
  emission NMS radius 2, budget = gate.chosen_budget of the valid footprint
  layer    no catalogue base layer (H37 measured score-neutral; see the register section 3.5)

Outputs: <name>.tif (+ .zip, + _allfinite.tif fallback, + provenance .json) in docs/downloads/.
Nothing is uploaded; spending a weekly slot stays a human decision.
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

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"
CUBE = ROOT / "data/candidate-features-30.npy"
R6 = ROOT / "data/round6_features.npy"
R7 = ROOT / "data/round7_features.npy"
LIDAR = ROOT / "data/ext/lidar_scarp_u8.tif"
RADIUS = 2
N_BASE = 25
H28_CH = 3
DEM12 = list(range(12))
LIDAR12 = list(range(12))
ARM_EXTRA = {
    "multi25_h28_dem12": {"r6": [H28_CH], "r7": DEM12, "lidar": []},
    "multi25_h28_dem12_lidar12": {"r6": [H28_CH], "r7": DEM12, "lidar": LIDAR12},
}


def validate_relaxed(path, template):
    with rasterio.open(template) as t, rasterio.open(path) as q:
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


def nms_select(ordered_pixels, shape, max_sel):
    width = shape[1]
    blocked = np.zeros(shape, dtype=bool)
    sel = np.empty(max_sel, dtype=np.int64)
    n = 0
    for s0 in range(0, len(ordered_pixels), 50000):
        cand = ordered_pixels[s0:s0 + 50000]
        ys, xs = np.divmod(cand, width)
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


def int_median(values_u8):
    counts = np.bincount(values_u8, minlength=256)
    c = np.cumsum(counts)
    return int(np.searchsorted(c, c[-1] / 2.0))


def build_matrix(ids, cols, flat, extra, lidar_u8, lidar_med):
    parts = [flat[ids, :N_BASE]]
    for src in ("r6", "r7"):
        if cols[src]:
            parts.append(extra[src][np.ix_(ids, cols[src])])
    if cols["lidar"]:
        v = lidar_u8[ids][:, cols["lidar"]].astype("float32")
        imp = np.where(v == 0.0, lidar_med[cols["lidar"]], v)
        if 11 in cols["lidar"]:
            imp[:, cols["lidar"].index(11)] = v[:, cols["lidar"].index(11)]
        parts.append(imp)
    return np.column_stack(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/downloads")
    ap.add_argument("--budget", type=float, default=None, help="override the gate's budget")
    ap.add_argument("--arm", default=None, help="override the gate's chosen arm")
    ap.add_argument("--slug", default=None)
    args = ap.parse_args()

    gate_doc = json.loads((ROOT / "evidence/holdout_round8.json").read_text())
    gate = gate_doc["gate"]
    if not gate.get("passed"):
        raise SystemExit("Round-8 gate did not pass (evidence/holdout_round8.json) — refusing to package.")
    arm = args.arm or gate["chosen_arm"]
    if arm not in ARM_EXTRA:
        raise SystemExit(f"unknown arm {arm!r}")
    budget = args.budget if args.budget is not None else float(gate["chosen_budget"])
    slug = args.slug or f"r8-nms3-dem10-lidar-b{int(round(budget * 1000)):03d}"

    with rasterio.open(TEMPLATE) as ds:
        valid = ds.read_masks(1) > 0
        shape = ds.shape
    with rasterio.open(LABELS) as ds:
        labels = (ds.read(1, masked=True).filled(0) > 0) & valid

    cube = np.lib.format.open_memmap(str(CUBE), mode="r")
    assert cube.shape == (*shape, 30), cube.shape
    flat = cube.reshape(-1, 30)
    r7build = json.loads((ROOT / "evidence/round7-feature-build.json").read_text())
    if sha(R7) != r7build["output"]["sha256"]:
        raise ValueError("round7_features.npy sha does not match its sidecar")
    extra = {"r6": np.lib.format.open_memmap(str(R6), mode="r").reshape(-1, 5),
             "r7": np.lib.format.open_memmap(str(R7), mode="r").reshape(-1, 12)}
    cols = ARM_EXTRA[arm]
    lidar_med = None
    if cols["lidar"]:
        lidar_doc = json.loads((ROOT / "evidence/lidar-fetch.json").read_text())
        if sha(LIDAR) != lidar_doc["file"]["sha256"]:
            raise ValueError("lidar cube sha does not match evidence/lidar-fetch.json")
        with rasterio.open(LIDAR) as s:
            assert s.shape == shape
            lidar_u8 = np.ascontiguousarray(s.read().transpose(1, 2, 0).reshape(-1, 12))
    else:
        lidar_u8 = None

    rng = np.random.default_rng(12027)
    pos = np.flatnonzero(valid & labels)
    neg = rng.choice(np.flatnonzero(valid & ~labels), 100000, replace=False)
    tidx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(len(pos), int), np.zeros(len(neg), int)])
    weights = np.where(y, 0.5 / len(pos), 0.5 / len(neg)) * len(tidx)
    if cols["lidar"]:
        lidar_med = np.array([int_median(lidar_u8[tidx, c]) for c in LIDAR12], dtype="float32")

    X = build_matrix(tidx, cols, flat, extra, lidar_u8, lidar_med)
    clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
                                         early_stopping=False, random_state=12027)
    clf.fit(X, y, sample_weight=weights)
    del X
    vidx = np.flatnonzero(valid & ~labels)
    prob = np.empty(len(vidx), dtype="float32")
    for s0 in range(0, len(vidx), 200000):
        ids = vidx[s0:s0 + 200000]
        prob[s0:s0 + len(ids)] = clf.predict_proba(
            build_matrix(ids, cols, flat, extra, lidar_u8, lidar_med))[:, 1]

    mass = int(budget * int(valid.sum()))
    ordered = vidx[np.lexsort((vidx, -prob))]
    sel = nms_select(ordered, shape, mass)
    values = np.zeros(shape, dtype="float32")
    values.ravel()[sel] = 1.0
    emitted = int((values > 0).sum())
    on_catalogue = int(values.ravel()[np.flatnonzero(labels.ravel())].sum())

    def write_variant(vals, path, outside):
        with rasterio.open(TEMPLATE) as t:
            profile = t.profile.copy()
            v = t.read_masks(1) > 0
        a = vals.copy()
        a[~v] = np.nan if outside == "nan" else 0.0
        profile.update(count=1, dtype="float32", nodata=np.nan, compress="deflate")
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(a, 1)

    args.out.mkdir(parents=True, exist_ok=True)
    probe = args.out / f".tmp-{slug}.tif"
    write_variant(values, probe, "nan")
    digest = sha(probe)[:12]
    stem = f"12GEMSDOE_{slug}_{digest}"
    tif = args.out / f"{stem}.tif"
    probe.replace(tif)
    v_primary = validate(tif, TEMPLATE)

    fallback = args.out / f"{stem}_allfinite.tif"
    write_variant(values, fallback, "zero")
    v_fallback = validate_relaxed(fallback, TEMPLATE)
    with rasterio.open(fallback) as s:
        raw = s.read(1)
        assert np.isfinite(raw).all() and raw.min() >= 0.0 and raw.max() <= 1.0
        assert np.array_equal(raw > 0, values > 0)

    zip_path = args.out / f"{stem}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.namelist() == [tif.name]

    note = (f"12GEMSDOE R8 | NMS-3 thin trace on {'+'.join(['multi25', 'H28', 'H32-dem12'] + (['H39-lidar12'] if cols['lidar'] else []))}"
            f" GBM | {emitted} px = {100 * emitted / int(valid.sum()):.3f}% of footprint | "
            f"budget {budget:.3f} from the Round-8 marginal-rule gate | sha256:{digest}")
    manifest = {
        "artifact": tif.name,
        "sha256": v_primary["sha256"],
        "bytes": tif.stat().st_size,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "slug": slug,
        "suggested_note": note,
        "emitted_pixels": emitted,
        "emitted_fraction_of_footprint": emitted / int(valid.sum()),
        "emitted_fraction_of_valid_pixels": emitted / int(valid.sum()),
        "budget_from_gate": budget,
        "nms_radius": RADIUS,
        "catalogue_pixels_predicted": on_catalogue,
        "round8_gate": {
            "passed": bool(gate["passed"]), "chosen_arm": arm, "chosen_budget": budget,
            "h39_passed": gate.get("h39_passed"), "incumbent_dense_2pct": gate.get("incumbent_dense_2pct"),
            "incumbent_sparse_2pct": gate.get("incumbent_sparse_2pct"),
            "chosen_dense": gate.get("chosen_dense"), "chosen_sparse": gate.get("chosen_sparse"),
            "leakage_probe_max": gate.get("leakage_probe_max"),
            "r7_reproduced_within": gate.get("r7_reproduced_within"),
        },
        "holdout_evidence": "evidence/holdout_round8.json",
        "preregistered_register": "docs/hypotheses-round8.md",
        "model": {
            "estimator": "HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, "
                         "early_stopping=False, random_state=12027)",
            "arm": arm,
            "features": ["first 25 channels of candidate-features-30.npy",
                         "H28: channel 3 of round6_features.npy",
                         "H32: all 12 channels of round7_features.npy (USGS 3DEP ~10 m DEM)"]
                        + (["H39: 12 channels of lidar_scarp_u8.tif (USGS 3DEP 1 m DEM, "
                            "sibling-built; zeros imputed with training-sample medians except "
                            "the coverage channel, which stays raw)"] if cols["lidar"] else []),
            "n_features": 25 + 1 + 12 + (12 if cols["lidar"] else 0),
            "training": {"positives": int(len(pos)), "sampled_negatives": int(len(neg)),
                         "class_weighting": "balanced total weight"},
            "external_data": {
                "dem10": {"product": r7build["inputs"]["upstream_product"],
                          "tiles": r7build["inputs"]["upstream_tiles"],
                          "licence": "USGS 3DEP — U.S. public domain",
                          "sidecar": "evidence/dem10-fetch.json"},
                **({"lidar_1m": {"product": "USGS 3DEP 1 m DEM → 2 m scarp descriptors → 100 m grid",
                                 "bridge_repo": json.loads((ROOT / 'evidence/lidar-fetch.json').read_text())["bridge"]["repo"],
                                 "build_run": json.loads((ROOT / 'evidence/lidar-fetch.json').read_text())["bridge"]["workflow_run"],
                                 "licence": "USGS 3DEP — U.S. public domain",
                                 "sidecar": "evidence/lidar-fetch.json"}} if cols["lidar"] else {}),
            },
        },
        "files": {"primary": tif.name, "all_finite_fallback": fallback.name, "zip": zip_path.name},
        "format": {"crs": "EPSG:32611", "resolution_m": 100, "shape": list(shape),
                   "dtype": "float32", "count": 1,
                   "values": "binary {0,1} inside the footprint, NaN outside"},
        "release_status": "format-validated only — no DrivenData slot spent; uploading is a human decision",
    }
    (args.out / f"{stem}.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    print(json.dumps({k: manifest[k] for k in ("artifact", "sha256", "bytes", "emitted_pixels",
                                               "emitted_fraction_of_footprint",
                                               "catalogue_pixels_predicted", "budget_from_gate")}, indent=1))
    print("note:", note)
    print("all-finite fallback:", fallback.name, "| zip:", zip_path.name)


if __name__ == "__main__":
    main()
