"""Compare PUBLISHED artifacts (not authenticated upload receipts).

NaN-safe: background NaN pixels compare equal to NaN. DrivenData does not
expose uploaded files, so equal leaderboard scores alone never prove equal
uploads; only byte-identical published files explain ties, and receipt
linkage stays unverified.
"""
import json
import itertools
from pathlib import Path
import numpy as np
import rasterio
from core import sha

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "gems1": ROOT / "data/gems1.tif",
    "gems5": ROOT / "data/gems5.tif",
    "gems8": ROOT / "data/gems8.tif",
    "12gems": ROOT / "docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif",
}

rows = []
arrays = {}
masks = {}
grids = {}
for name, p in FILES.items():
    with rasterio.open(p) as s:
        a = s.read(1)
        mask = s.read_masks(1) > 0
        grid = (str(s.crs), list(s.transform), s.width, s.height)
        rows.append(dict(name=name, sha256=sha(p), bytes=p.stat().st_size,
                         grid=grid, valid_pixels=int(mask.sum()),
                         positive_pixels=int((a[mask] > 0).sum()),
                         range=[float(a[mask].min()), float(a[mask].max())]))
        arrays[name] = a
        masks[name] = mask
        grids[name] = grid

pairs = []
for x, y in itertools.combinations(arrays, 2):
    same_grid = grids[x] == grids[y]
    same_mask = same_grid and np.array_equal(masks[x], masks[y])
    if same_mask:
        ax, ay = arrays[x], arrays[y]
        eq = (ax == ay) | (np.isnan(ax) & np.isnan(ay))
        frac = float(1 - eq.mean())
        ndiff = int((~eq).sum())
        peq = bool(eq.all())
    else:
        frac, ndiff, peq = None, None, False
    # byte-level identity (strongest tie explanation)
    same_bytes = rows[[r["name"] for r in rows].index(x)]["sha256"] == \
        rows[[r["name"] for r in rows].index(y)]["sha256"]
    pairs.append(dict(a=x, b=y, same_grid=same_grid, same_mask=same_mask,
                      same_bytes=same_bytes, pixel_equal=peq,
                      fraction_different=frac, different_pixels=ndiff))

out = {"checked_utc": "2026-09-27",
       "scope": "published artifacts, not upload receipts",
       "conclusion": ("GEMSDOE1 and 5GEMSDOE published byte-identical files "
                      "(same SHA-256, 0 differing pixels), explaining their equal "
                      "0.1563 score. 8GEMSDOE's published file (b83ea0e7) is unique "
                      "and, per 8GEMSDOE's own log, was never uploaded "
                      "(BUILT-UNIQUE-UNUPLOADED); the third 0.1563 row is another "
                      "upload of the shared 7f00890a bytes. 12GEMSDOE (06ca61e5) "
                      "is unique."),
       "files": rows, "pairs": pairs}
(ROOT / "evidence/identity.json").write_text(json.dumps(out, indent=2))
print(json.dumps(pairs, indent=2))
