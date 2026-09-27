# 12GEMSDOE — evidence before submission

> **Read this README every session.** Maximize P(Win): prioritize scientifically defensible discovery and validation over leaderboard churn. Own the Outcome: follow data, model, artifact and published result end to end. Do not invent observations, results, source verification or access.

[Workbench](https://buffedlizard55-lab.github.io/12GEMSDOE/) · [Executive submission guide](docs/executive-summary.html) · [Evidence and irregularities](docs/session-review.md) · [New hypotheses](docs/hypotheses.md)

## Executive summary — 2026-09-27

**There is no approved new submission download.** Do not spend a slot until the candidate beats the current strongest reproducible model on the same frozen spatial holdout. Valid TIFF formatting alone is insufficient.

- **Duplicate confirmed:** compared GEMSDOE1 and 5GEMSDOE published ens12 TIFFs are byte- and pixel-identical, SHA-256 `7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15`. Their matching reported 0.1563 scores plausibly reflect reuse; exact upload receipts remain inaccessible.
- **Not all ties are duplicates:** 8GEMSDOE's published TIFF differs at 10.897065% of valid pixels. [Machine-readable audit](evidence/identity.json).
- **Data placement completed:** assembled and checked all three raster files via the team's pinned public bridge. [Inventory](evidence/data-inventory.json). Direct official provenance still needs authentication. The example's pixel contents match labels, contradicting the official page's all-absence description; use it as grid/mask only.
- **New CPU experiment:** four spatial folds compare raw 19 bands against eight displacement-restoration descriptors. [Frozen protocol](docs/hypotheses.md); [results](evidence/screening.json). **Rejected:** 0.11849 versus raw baseline 0.11919 and random-area control 0.20070. This is screening, not a certified leaderboard gain or strongest-baseline win.
- **Strict raster writer:** tests enforce one float32 band, exact template alignment/mask, finite [0,1] inside and NaN outside. Unique hash-based research filenames/comments; repeat artifact rejection. Production release is fail-closed.
- The official [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed **0.3049** at review time. This is a snapshot, not an automatically updated claim.

## Standing user prompt / project requirements

The following is a **deduplicated operational transcription**, not a claim to preserve the repeated original wording verbatim. It is the starting brief for future work:

1. Review the repo and prior-session next steps first. Investigate why group submissions keep scoring 0.1563, especially GEMSDOE1 and 5GEMSDOE, using actual artifact identity rather than score ties. Strategies must differ scientifically, not merely by name or tuning.
2. Before implementation generate **3–5 new geological hypotheses**, each naming layers, physical transform/signature, catalogue-gap rationale, differences from existing work, expected DTI test priority and implementation cost. Validate the top one on spatially blocked holdout. **Never spend a weekly slot unless it beats the current holdout best.**
3. For external data, name a free official source, verify obtainability and usage/sharing rights before treating an idea as viable. Store scientific knowledge, provenance, calculations, results and official review links for reuse. Think independently while remaining grounded in research.
4. Work autonomously; no routine manual input. Never invent evidence. Verify claims against primary trusted sources, label team-reported claims, flag irregularities and state limitations. A stated goal above 0.3049 is not a result or guarantee. The competition target is faults indicative of geothermal resources, not proven geothermal vents.
5. Build an auditable pipeline: download/prepare data, train, infer, validate and package the required single-band GeoTIFF aligned exactly with the sample. Fix the “[0,1]” rejection without silently masking model bugs. Use a unique filename and short comment, and keep exact uploaded hashes and receipts.
6. Provide a clean GitHub Pages site with an executive-summary subpage explaining the submission process. Put the approved TIF download at the beginning **when the gate passes**, otherwise make the blocker obvious. Maintain freshness honestly; never call a static snapshot a live feed.
7. Keep **Maximize P(Win)** and **Own the Outcome** central. Run three passes: implement/verify; review bugs, assumptions and edge cases; re-check against this brief and fix residual issues.
8. Open a pull request and merge it after checks. Save remaining work/access limitations for the next session. Do not request or store credentials. No competition uploads without the validation/rules gate.

### Team-supplied historical results (not authenticated receipts)

| Project | Reported public score |
|---|---:|
| GEMSDOE1 | 0.1563 |
| GEMSDOE2 | 0.1560 |
| GEMSDOE3 nodes `f347b70daa` | 0.1193 |
| GEMSDOE3 catalogue-gap `37f9d5b855` | 0.0830 |
| GEMSDOE3 ridge `4e03fc9705` | 0.1152 |
| GEMSDOE4 | 0.0343 |
| 5GEMSDOE | 0.1563 |
| 6GEMSDOE | 0.0286 |
| 7GEMSDOE | 0.1461 |
| 8GEMSDOE | 0.1563 |
| 9GEMSDOE | 0.0107 |
| 10GEMSDOE | Not supplied |
| 11GEMSDOE | 0.0202 |
| 12GEMSDOE | Not supplied |

## Reproduce locally (CPU)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
bash scripts/download_competition_data.sh  # gh CLI; fixed revision, checked chunks/full hashes
python scripts/prepare_data.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python scripts/experiment.py
python -m pytest -q
```

Use ~3 GB free disk and several GB RAM; data/ is ignored. Data downloader is rerunnable and reuses verified chunks. No GPU is required for this screening model. It is not the previous project's full CNN train→inference pipeline.

`python scripts/package_submission.py probabilities.npy --name fabric-offset-v1` creates **research-only** TIFF/JSON in ignored `data/research-exports/`. Arrays must already be aligned probabilities. `--release` is deliberately rejected until a robust strongest-baseline release gate exists. The site does not link research artifacts as approved submissions.

`python scripts/fetch_history.py` retrieves pinned historical TIFFs; `python scripts/audit_submissions.py` compares `data/gems1.tif`, `data/gems5.tif`, `data/gems8.tif`; see the exact source URLs in the session review. These are team artifacts, not official challenge inputs.

## Official starting sources

- [Competition and rules entry](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem, features, DTI equations and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/), [authenticated data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — full compliance review outstanding
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR 1391](https://gdr.openei.org/submissions/1391) — lead supplied by team, not used as a newly validated dataset here

## Next session / release blockers

1. Diagnose why the spatial screening model underperforms a matched random-area control; do not promote a weak baseline win. Reproduce the strongest sibling OOF model, including auxiliary provenance, on the frozen split before any release decision.
2. Resolve mirrored sample/label content discrepancy against authenticated official files. This session has no DrivenData login or submission receipts and cannot establish identity with hidden labels.
3. Expand source/code and uploaded-artifact audit to all projects; 9GEMSDOE and 10GEMSDOE tree access returned 404. Do not assert global novelty over inaccessible work.
4. Check the complete official rules PDF, current deadline, team eligibility, sharing policy, and licensing before upload. No terms acceptance on the user's behalf.
5. Add a truly automated source-refresh pipeline with timestamps, source-change alerts, archived responses and failure/staleness indicators. Today's site is explicitly a snapshot.
6. Only after a robust holdout win: fit full data, export and verify the unique TIF, publish the approved download and note, then retain the actual upload receipt and score. Private-test improvement and winning a prize cannot be guaranteed.
