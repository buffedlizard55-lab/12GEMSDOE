# Evidence-led review • 27 September 2026

## Executive findings

1. **GEMSDOE1 and 5GEMSDOE share an identical published artifact.** Independently downloaded both TIFFs and computed SHA-256 `7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15`. Both have identical grids, masks, and valid pixels. This supports reuse as the explanation for the team's matching scores, **conditional on these being the files actually uploaded**. Authenticated receipts were not inspected.
2. **8GEMSDOE is different.** Its published `submission.tif` differs at 10.897065% of valid pixels from that shared artifact. Equal four-decimal scores do not imply identical work. Byte hash and pixel comparison results: [identity.json](../evidence/identity.json).
3. **The local data blocker is cleared, not the provenance caveat.** Reassembled the 418,912,844-byte feature file and downloaded labels/template from the team's existing bridge at pinned GEMSDOE commit `cceebbdcf9a7d2890bb0665defcb54dfc66ae452`. All full-file and chunk hashes match the team's manifest. This is not an independent authenticated comparison with DrivenData. Files stay in ignored `data/`; [inventory](../evidence/data-inventory.json), [bridge manifest](../evidence/bridge-manifest.json).
4. **The checkout was not training-ready.** Before this session it held only README and a research note, not the scripts or holdout described in the request. CPU screening is now implemented. No GPU is needed for this test; a full deep-learning pipeline is not supplied or claimed complete.
5. **A new geological mechanism is being tested, not another emission reskin.** See the pre-implementation [three-candidate register](hypotheses.md). No candidate is eligible for a weekly slot until it beats the strongest reproduced baseline on identical splits. We do not promise a score above 0.3049.

## Primary official-source ledger

| Claim | Source | Verification / limitation |
|---|---|---|
| Target is faults indicative of geothermal resources, not direct vent detections | [DrivenData problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Retrieved 2026-09-27; explicit problem statement |
| Test faults were expert mapped and absent from public inventory | Same problem page | Dataset description, not independently inspected hidden labels |
| DTI α=.2, β=.8, triangular support 300 m; probabilistic maximum credit | Same page, metric equations | Implemented directly; tested against independent brute-force equations; not claimed parity with hidden server code |
| Single float32 band, EPSG:32611, 100 m, aligned bounds, values [0,1] | Same page, submission format | Local tests reject out-of-range/NaN inside mask, changed CRS/transform/shape; outside mask encoded NaN |
| Known USGS/INGENIOUS pixels excluded from evaluation/penalties | [DrivenData staff reply](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) | Retrieved 2026-09-27; do not expand this statement into a free 300 m buffer |
| Leader displayed 0.3049 | [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Retrieved 2026-09-27, snapshot only; not a forecast or private score |
| External data requires license permitting contest use and sharing with sponsor | Problem page, external datasets | No new external geological dataset used in this experiment |

## Artifact evidence (team sources, not official scientific sources)

- [GEMSDOE ens12 TIFF](https://github.com/buffedlizard55-lab/GEMSDOE/blob/cceebbdcf9a7d2890bb0665defcb54dfc66ae452/data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif)
- [5GEMSDOE anchor TIFF](https://github.com/buffedlizard55-lab/5GEMSDOE/blob/main/data/evidence/leaderboard_anchor/gemsdoe-ens12-adopted-7f00890a.tif)
- [8GEMSDOE published TIFF](https://github.com/buffedlizard55-lab/8GEMSDOE/blob/main/docs/downloads/submission.tif)
- [11GEMSDOE prior holdout methods](https://github.com/buffedlizard55-lab/11GEMSDOE/blob/main/scripts/run_holdout_experiment.py)
- [5GEMSDOE context detector](https://github.com/buffedlizard55-lab/5GEMSDOE/blob/main/scripts/train_context_detector.py)
- [8GEMSDOE candidate register](https://github.com/buffedlizard55-lab/8GEMSDOE/blob/main/knowledge/10_hypotheses_ranked_2026-09-26.md)

The team tree audit found substantial shared legacy files and new branches of experiments. Shared code is not itself scientific misconduct or proof of identical outputs. Only the compared artifacts justify the identity conclusion. Other user-reported scores remain user-reported; no attribution to specific authenticated uploads is invented.

## Irregularities flagged

- The previous research note claimed both that the PDF had been parsed and that it had not been retrieved. Those contradictory statements are withdrawn; no detailed PDF rule compliance is certified here.
- The official problem page calls the example a total-absence prediction. The mirrored example actually contains positive values matching supplied labels. Treat it **only as a grid/mask template**, never as a model or unexamined submission. This discrepancy must be resolved against the authenticated source before final release.
- Sibling documents sometimes call spatial blocks “whole fault traces”; their split clips connected traces at block edges rather than assigning every connected system as a unit. Our experiment is described as **spatially blocked**, not independent whole-system validation.
- Re-scoring a historic raster trained on all known labels inside selected blocks is **not** an out-of-fold estimate. It cannot be the current holdout best.
- The old suggested cross-physics coherence, strain, basement-step and topographic ideas already overlap sibling work. They are retired as novelty claims.
- A low score does not prove an idea is geologically false; no causal explanation of every team's score is possible from the supplied summary.
- Direct raw.githubusercontent.com requests failed TLS in this sandbox; authenticated `gh api` read-only downloads succeeded. No credentials were requested or stored.
- Exact competition deadline, eligibility, team-sharing restrictions and full PDF rules need a separate verified compliance pass before any upload. No automated upload was attempted.

## Why the rejection occurred

“Predicted values must be in range [0,1]” means the server saw invalid prediction values, but the offending file was not identified here. Plausible causes include raw logits, integer/percent scaling, unmasked negative nodata, or infinities. We do **not** assert which caused that upload. The new writer rejects invalid values rather than silently clipping them; it uses the template mask, writes float32 NaN outside, then re-opens and validates the TIFF. It generates hash-based unique filenames and notes for research exports. A new filename does not make repeated predictions novel.

## Remaining release gates

1. Reproduce the strongest sibling model with the same frozen block assignment and complete training exclusion collar; compare nested or separately locked test performance. Catalogue labels remain a biased proxy for unknown faults.
2. Compare all candidate pixels and masks against an archive of submitted artifacts before release. Current audit covers three published artifacts only.
3. Authenticate data provenance / template discrepancy and read full contest rules including eligibility and data-sharing terms.
4. If a hypothesis wins robustly, retrain on all permissible labels, validate full-grid inference, and publish the actual approved TIF, note, checksum and gate evidence at the top of the site. Until then: **no approved submission download**.

## Completed experiment and three review passes

**Measured:** restoration 0.1184867 vs raw-band baseline 0.1191909; matched random-area control 0.2006984. Restoration loses overall and on two of four folds. **Rejected; no release.** See [results](screening.json). Pooled TP/FP/FN and paired fold differences are archived, not just a selected mean.

- **Pass 1 — implement and verify:** retrieved pinned data, compared three historical TIFFs, recorded hypotheses before code, implemented CPU screening and strict writer, built the site and submission guide.
- **Pass 2 — bug/assumption review:** synthetic constant-field test caught a nodata neighborhood artefact in displacement descriptors. A Manhattan-radius exclusion was insufficient for diagonal patch support; replaced it with a full square support mask. Stopped the initial run and reran all folds. Added exact duplicate rejection across differently named exports and explicit release refusal. Withdrew stale README-only and contradictory PDF claims.
- **Pass 3 — end-to-end requirements review:** checked source/claim distinctions, added synthetic displaced-fabric and brute-force metric tests, exercised the writer on the actual 3,730 × 3,292 template, independently found the sample/labels discrepancy, archived all fold scores including failed candidate and random control, and left the submission button disabled. Missing strongest-baseline reproduction, complete rules review, broader history audit and live feed are documented rather than claimed finished.

No list of confirmed newly discovered faults or vents is produced: that would require expert validation not available here. No “hallucination-free” certification is asserted; instead every consequential claim has its evidence class and unresolved limitations recorded.
