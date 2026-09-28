"""Fetch the 13 label-free 10 m DEM scarp channels built by sibling GEMSDOE10 (H20).

Provenance chain (every link verifiable by a human):
  * Source product: USGS 3DEP 1/3 arc-second (~10 m) seamless DEM, public domain,
    tiles n38w118 … n41w120 from https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/
    (product catalogue https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5).
  * Built on a GitHub-hosted runner by sibling repo buffedlizard55-lab/GEMSDOE10 and stored
    as an immutable tag `ext/dem10-36343078537` (commit 91d6566ecc…) with a manifest that pins
    each channel's SHA-256, the template SHA-256 (official sample_submission.tif) and the
    vector order (np.nonzero(np.isfinite(sample_submission)), row-major).
  * This sandbox cannot reach USGS/S3 (TLS blocked); api.github.com is the only transport,
    so the tag is the only verified path to that data from here. Every byte is re-hashed
    against the manifest before use. Nothing here uses fault labels.

Output: data/dem10/<channel>.f32.npy (13 files) + data/dem10/manifest.json and an
evidence sidecar evidence/dem10-fetch.json with per-file hash results.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "dem10"
REPO = "buffedlizard55-lab/GEMSDOE10"
TAG = "ext/dem10-36343078537"
TAG_COMMIT = "91d6566ecc"  # prefix of the tag's commit, from `gh api repos/.../tags`
TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(path: str, dest: Path) -> None:
    cmd = ["gh", "api", f"repos/{REPO}/contents/{path}?ref={TAG}",
           "-H", "Accept: application/vnd.github.raw"]
    with dest.open("wb") as o:
        subprocess.run(cmd, stdout=o, check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tags = json.loads(subprocess.run(["gh", "api", f"repos/{REPO}/tags?per_page=100"],
                                     capture_output=True, check=True, text=True).stdout)
    match = [t for t in tags if t["name"] == TAG]
    if not match:
        sys.exit(f"tag {TAG} not found on {REPO}")
    commit = match[0]["commit"]["sha"]
    if not commit.startswith(TAG_COMMIT):
        sys.exit(f"tag {TAG} moved: {commit} does not start with {TAG_COMMIT}")

    man_path = OUT / "manifest.json"
    gh_raw("manifest.json", man_path)
    manifest = json.loads(man_path.read_text())
    if manifest.get("template_sha256") != TEMPLATE_SHA:
        sys.exit("manifest template sha does not match official sample_submission.tif pin")
    if manifest.get("footprint_pixels") != 5167373:
        sys.exit("manifest footprint pixel count is not 5,167,373")

    channels = manifest["channels"]
    stats = manifest["channel_stats"]

    def fetch(ch: str) -> dict:
        dest = OUT / f"{ch}.f32.npy"
        want = stats[ch]["sha256"]
        if dest.exists() and sha256_of(dest) == want:
            return {"channel": ch, "sha256": want, "status": "cached-verified"}
        gh_raw(f"{ch}.f32.npy", dest)
        got = sha256_of(dest)
        if got != want:
            dest.unlink(missing_ok=True)
            raise RuntimeError(f"{ch}: sha mismatch {got} != {want}")
        return {"channel": ch, "sha256": got, "bytes": dest.stat().st_size, "status": "fetched-verified"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(fetch, channels))

    sidecar = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_repo": REPO,
        "source_tag": TAG,
        "source_tag_commit": commit,
        "upstream_product": manifest["product"],
        "upstream_product_catalog": manifest["product_catalog"],
        "upstream_tiles": {k: {"url": v["url"], "sha256": v["sha256"], "bytes": v["bytes"]}
                           for k, v in manifest["tiles"].items()},
        "template_sha256": manifest["template_sha256"],
        "footprint_pixels": manifest["footprint_pixels"],
        "vector_order": manifest["vector_order"],
        "grid": manifest["grid"],
        "channels": results,
        "labels_used": False,
    }
    (ROOT / "evidence" / "dem10-fetch.json").write_text(json.dumps(sidecar, indent=2) + "\n")
    print(json.dumps({r["channel"]: r["status"] for r in results}, indent=1))


if __name__ == "__main__":
    main()
