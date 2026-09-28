# Session starting point

Read `README.md`, `docs/session-review.md`, the latest `docs/hypotheses-roundN.md` register and
the latest `evidence/holdout*.json` before changing models or the site (current: **Round-8
register `docs/hypotheses-round8.md` + `evidence/holdout_round8.json`**; `docs/knowledge-base.md`
is the verified-facts ledger; `screening.json` is a legacy unmasked diagnostic;
`holdout_masked.json` and `holdout_round4..7.json` are frozen references). README is the
standing user brief. Preregister hypotheses before coding them; do not silently reset the
holdout or re-label existing sibling ideas as novel.

## Standing rules

* **Emission convention:** NMS radius 2 (5×5) at the frozen 2 % budget. Top-k numbers are NOT
  comparable to NMS numbers — never mix them in one table.
* **Gate:** a new arm must beat the incumbent on ≥3/4 folds AND have a positive mean paired gain
  on BOTH catalogue protocols (dense, sparse-20 %), with a 0.0 leakage probe on every fold.
  Round-8 addition: any *emission-policy* change must also be disclosed before the run, and the
  shipped mass comes from the gate, not from a constant in the packaging script.
* **No artifact without a passed gate.** `tests/test_round8.py::test_no_unfrozen_artifact_is_shipped`
  enforces that a failed gate leaves `docs/downloads/` free of `12GEMSDOE_r8-*` files.
* **Round-8 outcome:** the gate FAILED, so the current deliverable is still
  `docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif` and the current incumbent arm
  is still `multi25_h28_dem12` (25 candidate channels + H28 + 12 USGS 3DEP 10 m channels).
  Measured this round: H39 (11 × 1 m-lidar scarp descriptors) wins dense 4/4 (+0.0074) but
  sparse only 2/4 → rejected; H38 mass sweep splits the protocols in sign (3.2 %: dense +0.0312,
  sparse −0.0103) → rejected; H40 graded −0.171 → rejected; H37 catalogue base layer is a
  **control**, not a strategy (staff ruling 11516 + the sibling `max(ens12, catalogue)` artifact).
* **The 2 % budget stands** until a *scored* measurement says otherwise. The metric's marginal
  rule (`ΔT/ΔE > 0.2·D/(1−0.2·D)`, 0.0323 at DTI 0.1563) is a cap, not a target.
* **Catalogue-shaped skill is not new-fault skill.** Gains that appear only on the dense
  protocol must be reported as such; the two catalogue protocols disagreeing in sign is a
  rejection, not noise to average away.
* **Feature cubes** must be rebuilt in order candidate-30 → round4 → round5 → round6 → round7;
  the deterministic candidate-30 cube SHA is `7eb403a2…` (the Round-6 session's `fc746d92…`
  drifted in channel 29 only).

## Data and bridges

* Sandbox has no internet beyond GitHub/PyPI: external data arrives through GitHub-runner-built
  `ext/*` products, hash-pinned locally.
  * 10 m DEM channels (H32): `data/round7_features.npy`, sidecar `evidence/round7-feature-build.json`.
  * 1 m lidar scarp descriptors (H39): `data/ext/lidar_scarp_u8.tif` (12 × uint8, SHA-256
    `d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568`), fetched by
    `scripts/fetch_lidar_channels.py`, sidecar `evidence/lidar-fetch.json`; upstream = USGS 3DEP
    1 m DEM tiles (public domain) reduced at 2 m by sibling 7GEMSDOE (706/716 tiles). Grid and
    hash are verified here; the reduction code is not re-executed here.
* Leaderboard comes from `.github/workflows/leaderboard-feed.yml`; if the htmx fragment changes
  the feed records `parse-failed` and the workflow fails visibly.
* Do not upload to DrivenData or publish an approved TIF without a passed gate, official
  provenance and a rules check (multiple accounts in one project family is a flagged compliance
  question). Unknown is an acceptable recorded result; invented evidence is not.
