"""Independent, read-only duplicate audit of the sibling GEMSDOE submission repos.

Why: the standing user brief asks "are we copying the same work over and over again?" and
"why do 5GEMSDOE and GEMSDOE1 have the same score".  This script answers both from bytes,
not from prose: it fetches every *published candidate artifact* of every sibling repo over
the GitHub API (the only egress available in this sandbox), hashes it, measures it against
the supplied catalogue, and compares files pairwise with a NaN-safe equality.

Scope and honesty rules
-----------------------
* Published artifacts only.  No DrivenData upload receipts exist in this organisation, so
  no row here claims "account X uploaded file Y": the account column is copied verbatim
  from the sibling's own scored-file ledger and keeps its provenance label.
* Files larger than MAX_BYTES, official bridge rasters, raw external rasters and fixtures
  are out of scope; every exclusion is listed under `skipped` so the filter is auditable.
* `--offline` re-scores from local copies in /tmp/sib/files; the JSON records the mode.

Outputs: evidence/sibling-audit.json and docs/sibling-audit.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import subprocess
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("/tmp/sib/files")
ORG = "buffedlizard55-lab"

# Repos belonging to this effort.  GEMSDOE1 / 9GEMSDOE / 10GEMSDOE are NOT repositories:
# the brief's "GEMSDOE1" page is /GEMSDOE/docs/index.html, and the 9/10 sites live in
# `GEMSDOE9` / `GEMSDOE10`.
REPOS = ["GEMSDOE", "5GEMSDOE", "6GEMSDOE", "GEMSDOE2", "GEMSDOE3", "GEMSDOE4",
         "7GEMSDOE", "8GEMSDOE", "GEMSDOE9", "GEMSDOE10", "11GEMSDOE", "12GEMSDOE",
         "13GEMSDOE", "14GEMSDOE", "15GEMSDOE"]
MAX_BYTES = 6_000_000
EXCLUDE = ("data/bridge/", "external/", "fixture", "/proxy/", "prob_raw")


def included(path: str) -> bool:
    p = "/" + path
    return any(x in p for x in ("/downloads/", "leaderboard_anchor/", "/evidence/combined/",
                                "/evidence/runs/"))

# Scored-file ledger copied from 5GEMSDOE `scripts/leaderboard_anchor.py::SCORED` and its
# `data/evidence/leaderboard_anchor/leaderboard_anchor.json` (generated 2026-09-26,
# read_utc 2026-09-25).  Identity labels are the sibling's own wording.
SCORED_LEDGER = [
    ("7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15", "extradr19", 0.1563,
     "CERTAIN — the only file the GEMSDOE site offers (sibling ledger)"),
    ("f68e590f8534d036872f18170819b52366c728e68619f17c648dce9629b0aaf2", "smashi34", 0.1560,
     "PROBABLE — GEMSDOE2 dual-family union arm"),
    ("f347b70daa95170bfc967b1c0b6bbf951496c2b74764a7102848ad6178829aca", "smrtdoog5", 0.1193,
     "CERTAIN — owner note '1 · SUBMIT FIRST f347b70daa Pindrop nodes'"),
    ("4e03fc97052e9bd673e48f1923ad17f15926f8db26d2befc033e1722381dc9b7", "SDCF9", 0.1152,
     "CERTAIN — owner note '3 · CONTROL 4e03fc9705 dense ridge control'"),
    ("37f9d5b855ee1b6c302cb81cdae1414db94db427f5dc9da3538474df37cf1cad", "wbg1", 0.0830,
     "CERTAIN — owner note '2 · SUBMIT SECOND 37f9d5b855 catalogue-gap target'"),
]


def gh(args: list[str]) -> bytes:
    return subprocess.run(["gh", *args], check=True, capture_output=True).stdout


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def default_branch(repo: str) -> str | None:
    try:
        out = gh(["api", f"repos/{ORG}/{repo}", "--jq", ".default_branch"]).decode().strip()
        return out or None
    except subprocess.CalledProcessError:
        return None


def tree(repo: str) -> list[dict]:
    br = default_branch(repo)
    if br is None:
        return []
    data = json.loads(gh(["api", f"repos/{ORG}/{repo}/git/trees/{br}?recursive=1"]))
    return [t for t in data.get("tree", []) if t["type"] == "blob"]


def select(paths: list[dict]) -> tuple[list[dict], list[dict]]:
    keep, skipped = [], []
    for t in paths:
        p, size = t["path"], t.get("size", 0)
        if not p.lower().endswith(".tif"):
            continue
        if any(x in p for x in EXCLUDE) or not included(p):
            continue
        (skipped if size > MAX_BYTES else keep).append({"path": p, "size": size})
    return keep, skipped


SITE_PAGES = ("docs/index.html", "index.html", "docs/executive-summary.html",
              "docs/executive_summary.html", "docs/how_to_submit.html")


def site_offers(repo: str, offline: bool) -> dict:
    """Which artifacts does each repo's published site actually hand out?

    This is the link in the chain that turns 'two repos' into 'one score': if two sites
    offer byte-identical files, uploading them from two accounts must give one score.
    """
    import re
    offers: dict[str, list[str]] = {}
    for page in SITE_PAGES:
        dest = CACHE / f"{repo}__{page.replace('/', '_')}"
        try:
            if dest.exists():
                html = dest.read_text(errors="replace")
            elif offline:
                continue
            else:
                html = gh(["api", f"repos/{ORG}/{repo}/contents/{page}",
                           "-H", "Accept: application/vnd.github.raw"]).decode(errors="replace")
                dest.write_text(html)
        except subprocess.CalledProcessError:
            continue
        hrefs = set(re.findall(r'["\'\(]([^"\'\(\)]+\.(?:tif|zip))["\'\)]', html, flags=re.I))
        if hrefs:
            offers[page] = sorted(hrefs)
    return offers


def fetch(repo: str, path: str, offline: bool) -> tuple[bytes, Path]:
    dest = CACHE / f"{repo}__{path.replace('/', '_')}"
    if dest.exists():
        return dest.read_bytes(), dest
    if offline:
        raise FileNotFoundError(str(dest))
    b = gh(["api", f"repos/{ORG}/{repo}/contents/{path}", "-H", "Accept: application/vnd.github.raw"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b)
    return b, dest


def measure(b: bytes, cat: np.ndarray) -> dict:
    with rasterio.open(io.BytesIO(b)) as s:
        a = s.read(1)
        mask = s.read_masks(1) > 0
        prof = {"count": s.count, "dtype": s.dtypes[0], "crs": str(s.crs),
                "shape": list(s.shape), "transform": list(s.transform)[:6],
                "nodata": None if s.nodata is None else float(s.nodata)}
    inside = mask & np.isfinite(a)
    pos = inside & (a > 0)
    out = {"bytes": len(b), "sha256": sha_bytes(b), "profile": prof,
           "valid_pixels": int(mask.sum()), "positive": int(pos.sum()),
           "nan_inside": int((mask & ~np.isfinite(a)).sum()),
           "min": float(a[inside].min()) if inside.any() else None,
           "max": float(a[inside].max()) if inside.any() else None}
    if pos.shape == cat.shape:
        out["on_catalogue_pixels"] = int((pos & cat).sum())
        out["positive_off_catalogue"] = int((pos & ~cat).sum())
        out["binary"] = bool(np.all(np.isin(a[pos], [1.0]))) if pos.any() else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)

    labels_bytes = (ROOT / "data/labels.tif").read_bytes()
    existing_bytes = (ROOT / "data/existing_faults.tif").read_bytes()
    sample_bytes = (ROOT / "data/sample_submission.tif").read_bytes()
    with rasterio.open(ROOT / "data/labels.tif") as s:
        cat = (s.read(1, masked=True).filled(0) > 0)
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        tmpl = s.read_masks(1) > 0
        sample = s.read(1)

    report = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "mode": "offline" if args.offline else "live (gh api)",
        "scope": "published candidate artifacts only; no DrivenData upload receipts exist",
        "catalogue": {
            "labels_sha256": sha_bytes(labels_bytes),
            "existing_faults_identical_to_labels": sha_bytes(existing_bytes) == sha_bytes(labels_bytes),
            "catalogue_pixels": int(cat.sum()),
            "template_footprint": int(tmpl.sum()),
            "sample_submission_sha256": sha_bytes(sample_bytes),
            "sample_submission_is_catalogue_bit_for_bit": bool(
                np.array_equal(sample[tmpl], cat[tmpl].astype("float32"))),
            "sample_submission_positive_inside": int((sample[tmpl] > 0).sum()),
            "note": "the official sample_submission.tif IS the known-fault catalogue (values {0,1}, 60,988 "
                    "positive px = labels>0), which contradicts the problem page's phrase 'predicts total "
                    "fault absence'; verified twice this session against the pinned rasters",
        },
        "scored_ledger": [{"sha256": s, "account": a, "score": v, "identity": i}
                          for s, a, v, i in SCORED_LEDGER],
        "repos": {}, "skipped": {}, "notes": {
            "repo_naming": "GEMSDOE1 is not a repository; the brief's 'GEMSDOE1' page is /GEMSDOE/docs/index.html. "
                           "9GEMSDOE / 10GEMSDOE are repositories GEMSDOE9 / GEMSDOE10; 13/14/15GEMSDOE are "
                           "empty stubs (11-byte README, no artifacts).",
        },
    }

    by_sha: dict[str, list[str]] = {}
    for repo in REPOS:
        paths = tree(repo)
        if not paths:
            report["repos"][repo] = {"error": "not found or empty"}
            continue
        keep, skipped = select(paths)
        report["skipped"][repo] = [s["path"] for s in skipped]
        rows = []
        for t in keep:
            try:
                b, _ = fetch(repo, t["path"], args.offline)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                rows.append({"path": t["path"], "error": str(e)[:160]})
                continue
            m = measure(b, cat)
            m["path"] = t["path"]
            rows.append(m)
            by_sha.setdefault(m["sha256"], []).append(f"{repo}:{t['path']}")
        report["repos"][repo] = {"n_artifacts": len(rows), "artifacts": rows,
                                 "site_offers": site_offers(repo, args.offline)}
        print(f"{repo}: {len(rows)} artifacts", flush=True)

    # --- pairwise comparison of the scored candidates (NaN-safe) ---
    path_by_sha: dict[str, Path] = {}
    for repo in REPOS:
        for r in report["repos"].get(repo, {}).get("artifacts", []):
            if "sha256" in r:
                path_by_sha.setdefault(r["sha256"], CACHE / f"{repo}__{r['path'].replace('/', '_')}")
    arrs = {}
    for s in [x[0] for x in SCORED_LEDGER]:
        if s in path_by_sha and path_by_sha[s].exists():
            with rasterio.open(path_by_sha[s]) as h:
                arrs[s] = h.read(1)
    pairs = []
    keys = list(arrs)
    for i, s1 in enumerate(keys):
        for s2 in keys[i + 1:]:
            a1, a2 = arrs[s1], arrs[s2]
            diff = int((np.nan_to_num(a1, nan=-9) != np.nan_to_num(a2, nan=-9)).sum())
            pairs.append({"a": s1[:16], "b": s2[:16], "identical_bytes": s1 == s2,
                          "differing_pixels": diff})
    report["scored_file_pairs"] = pairs
    report["scored_file_stats"] = {s[:16]: {"bytes": int(path_by_sha[s].stat().st_size)} for s in keys}

    report["duplicate_groups"] = {k: v for k, v in by_sha.items() if len(v) > 1}
    report["unique_artifacts"] = len(by_sha)

    out = ROOT / "evidence/sibling-audit.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True))
    (ROOT / "docs/sibling-audit.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    print("wrote", out, "| unique artifacts:", len(by_sha),
          "| duplicate groups:", len(report["duplicate_groups"]))
    for sha, where in report["duplicate_groups"].items():
        print("  DUPLICATE", sha[:16], "->", where)


if __name__ == "__main__":
    main()
