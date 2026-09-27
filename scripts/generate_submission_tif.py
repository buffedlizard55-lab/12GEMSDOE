"""Create a format-validated *research* GeoTIFF from the reproduced multi25 model.

This command deliberately cannot mark an artifact as an approved leaderboard
release.  A valid GeoTIFF only proves format conformance; it does not demonstrate
private-label skill or satisfy the project's strongest-baseline release gate.

The archived site artifact ``06ca61e5`` remains downloadable and independently
validates against the official template.  Its historical training script referred
to a missing feature file, so this script does **not** claim byte reproduction of
that archive.  Instead it creates a separately named, fully provenance-recorded
research export.  It never contacts DrivenData and never consumes a submission
slot.
"""
from __future__ import annotations

import argparse
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import sha, write_prediction

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
LABELS = ROOT / "data/labels.tif"
CUBE = ROOT / "data/candidate-features-30.npy"


def build_prediction() -> tuple[np.ndarray, dict]:
    """Fit exactly the reproducible multi25 model class and emit a sparse field."""
    with rasterio.open(TEMPLATE) as ds:
        valid = ds.read_masks(1) > 0
        shape = ds.shape
    with rasterio.open(LABELS) as ds:
        labels = (ds.read(1, masked=True).filled(0) > 0) & valid
    cube = np.lib.format.open_memmap(str(CUBE), mode="r")
    if cube.shape != (*shape, 30):
        raise ValueError(f"expected 30-channel cube shaped {shape}; got {cube.shape}")
    flat = cube.reshape(-1, 30)

    # Full-grid equivalent of the current multi25 holdout reference.  The
    # sampling seed/configuration is pinned in the provenance manifest.
    rng = np.random.default_rng(12027)
    positives = np.flatnonzero(valid & labels)
    negatives = np.flatnonzero(valid & ~labels)
    sampled_negatives = rng.choice(negatives, min(250_000, len(negatives)), replace=False)
    train_idx = np.concatenate((positives, sampled_negatives))
    y = labels.ravel()[train_idx]
    weights = np.where(y, 0.5 / len(positives), 0.5 / len(sampled_negatives)) * len(train_idx)
    clf = HistGradientBoostingClassifier(
        max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027,
    )
    clf.fit(flat[train_idx, :25], y, sample_weight=weights)

    valid_idx = np.flatnonzero(valid)
    probabilities = np.empty(len(valid_idx), dtype="float32")
    for start in range(0, len(valid_idx), 100_000):
        idx = valid_idx[start:start + 100_000]
        probabilities[start:start + len(idx)] = clf.predict_proba(flat[idx, :25])[:, 1]

    # This emission density belongs to the historical archive's protocol. It
    # is deliberately recorded, not advertised as private-score-optimal.
    fraction = 0.035
    selected_rank = np.lexsort((valid_idx, -probabilities))[:int(fraction * len(valid_idx))]
    selected_idx = valid_idx[selected_rank]
    selected_prob = probabilities[selected_rank]
    lo, hi = float(selected_prob.min()), float(selected_prob.max())
    values = np.zeros(shape, dtype="float32")
    values.ravel()[selected_idx] = (0.25 + 0.70 * (selected_prob - lo) / (hi - lo + 1e-7)).astype("float32")

    # Staff says existing catalogue pixels are masked from evaluation. Keeping
    # them in this research raster is score-neutral under that stated rule, and
    # they are labelled explicitly here so nobody treats them as discoveries.
    values[labels] = 0.95
    values[~valid] = np.nan
    metadata = {
        "model": "HistGradientBoostingClassifier",
        "model_parameters": {"max_iter": 100, "max_leaf_nodes": 15,
                             "early_stopping": False, "random_state": 12027},
        "training": {"positive_count": int(len(positives)),
                     "negative_sample_count": int(len(sampled_negatives)),
                     "class_weighting": "balanced total weight"},
        "emission": {"top_fraction_of_valid": fraction,
                     "selected_value_range": [0.25, 0.95],
                     "catalogue_value": 0.95,
                     "catalogue_semantics": "known pixels are included for format completeness; staff says they are masked from evaluation"},
    }
    return values, metadata


def generate(out_dir: Path, slug: str) -> dict:
    if not slug or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug):
        raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
    missing = [str(p) for p in (TEMPLATE, LABELS, CUBE) if not p.is_file()]
    if missing:
        raise FileNotFoundError("run download, prepare, and feature build first: " + ", ".join(missing))
    out_dir.mkdir(parents=True, exist_ok=True)
    values, model_info = build_prediction()
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    temporary = out_dir / f".tmp-{utc}.tif"
    validation = write_prediction(temporary, values, TEMPLATE)
    digest = validation["sha256"]
    name = f"12gems-{slug}-research-{digest[:12]}.tif"
    tif = out_dir / name
    temporary.replace(tif)
    zip_path = tif.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(tif, arcname=tif.name)
    manifest = {
        "submission_eligible": False,
        "reason": "research export only; H11 did not beat multi25 and the strongest sibling baseline gate remains unresolved",
        "generated_utc": utc,
        "file": tif.name,
        "zip": zip_path.name,
        "sha256": digest,
        "bytes_tif": tif.stat().st_size,
        "bytes_zip": zip_path.stat().st_size,
        "template_sha256": sha(TEMPLATE),
        "feature_cube_sha256": sha(CUBE),
        "labels_sha256": sha(LABELS),
        "validation": validation,
        "suggested_note": f"12GEMSDOE research | {slug} | format-validated | sha256:{digest[:12]}",
        "model": model_info,
    }
    tif.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data/research-exports")
    parser.add_argument("--name", default="multi25")
    parser.add_argument("--release", action="store_true",
                        help="always rejected: an artifact cannot self-authorize a leaderboard release")
    args = parser.parse_args()
    if args.release:
        raise SystemExit("Release blocked: research exports never authorize a DrivenData submission.")
    result = generate(args.out, args.name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
