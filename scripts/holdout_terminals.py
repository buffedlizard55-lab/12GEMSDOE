"""Terminal-truncation holdout: the direct test of tip-extension claims.

Random-component holdout hides whole traces, most of which are not extensions
of visible ones. Here each connected component (>= 12px) is truncated: the
terminal 25% along its first principal axis is hidden, H6 extends from the
truncated remainder, and scoring is vs the hidden terminals with the official
mask semantics. Controls: equal-mass random in the near-field region, and
straight-ray extension (GEMSDOE3-style, 5px, ungated) as the prior-art baseline.
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
from holdout_masked import components_masked, h6_detector
from analyze_h6_regime import h6_ungated

ROOT = Path(__file__).resolve().parents[1]


def straight_rays(train_traces):
    H, W = train_traces.shape
    nbr = convolve(train_traces.astype("int32"), np.ones((3, 3), "int32"),
                   mode="constant") - train_traces.astype("int32")
    endpoints = np.argwhere(train_traces & (nbr == 1))
    out = np.zeros((H, W), dtype="float32")
    for (y0, x0) in endpoints:
        ys, xs = np.nonzero(train_traces[max(0, y0 - 8):y0 + 9, max(0, x0 - 8):x0 + 9])
        if len(ys) < 3:
            continue
        pts = np.stack([ys + max(0, y0 - 8), xs + max(0, x0 - 8)]).astype("float64")
        away = np.array([y0, x0]) - pts.mean(axis=1)
        n = np.linalg.norm(away)
        if n < 1e-9:
            continue
        away = away / n
        for s in range(1, 6):
            y, x = int(round(y0 + away[0] * s)), int(round(x0 + away[1] * s))
            if 0 <= y < H and 0 <= x < W and not train_traces[y, x]:
                out[y, x] = 1.0
    return out


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
    rng = np.random.default_rng(12027)
    # Truncate half the components (random half); hide terminal quartile.
    big = [c for c in range(1, ncomp + 1) if (comp == c).sum() >= 12]
    trunc = set(rng.choice(big, len(big) // 2, replace=False))
    hidden = np.zeros(shape, bool)
    for c in trunc:
        ys, xs = np.nonzero(comp == c)
        pts = np.stack([ys, xs]).astype("float64")
        ctr = pts.mean(axis=1)
        u, _, _ = np.linalg.svd(pts - ctr[:, None], full_matrices=False)
        t = (pts - ctr[:, None]).T @ u[:, 0]
        cut = np.quantile(t, 0.75)
        for y, x, v in zip(ys, xs, t):
            if v >= cut:
                hidden[y, x] = True
    hidden &= valid
    train_traces = (truth & ~hidden) & valid
    region = valid & (distance_transform_edt(~hidden) <= 25)
    h6, diag = h6_detector(train_traces, rtp, f21, f22, f23, f25, region, valid)
    pred = np.zeros(shape, dtype="float32")
    pred[(h6 > 0) & region] = 1.0
    geo = h6_ungated(train_traces, rtp, region)
    geop = np.zeros(shape, dtype="float32")
    geop[(geo > 0) & region] = 1.0
    rays = straight_rays(train_traces)
    idx = np.flatnonzero(region)
    ctrl = np.zeros(shape, dtype="float32")
    ctrl.ravel()[rng.choice(idx, min(int(pred.sum()), len(idx)), replace=False)] = 1.0
    out = {"protocol": "terminal-truncation (terminal quartile of half the "
                        ">=12px components hidden); official mask semantics",
           "script_sha256": sha(Path(__file__)),
           "truncated_components": len(trunc), "hidden_pixels": int(hidden.sum()),
           "region_pixels": int(region.sum()),
           "h6_emitted": int(pred.sum()), "geo_emitted": int(geop.sum()),
           "rays_emitted": int(rays.sum()),
           "h6_gated_dti": components_masked(pred, hidden, region, train_traces)["dti"],
           "geo_ungated_dti": components_masked(geop, hidden, region, train_traces)["dti"],
           "straight_rays_dti": components_masked(rays, hidden, region, train_traces)["dti"],
           "random_equal_mass_dti": components_masked(ctrl, hidden, region, train_traces)["dti"],
           "release_allowed": False,
           "release_reason": "Screening only; no weekly slot spent."}
    (ROOT / "evidence/holdout_terminals.json").write_text(json.dumps(out, indent=2))
    (ROOT / "docs/holdout_terminals.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v)
                      for k, v in out.items() if "dti" in k or "pixels" in k or "emitted" in k},
                     indent=1))


if __name__ == "__main__":
    main()
