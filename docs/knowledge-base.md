# 12GEMSDOE Knowledge Base — verified facts, open questions, and where each came from

> Purpose: one page a new session can read in two minutes instead of re-deriving the
> competition from scratch. Every row says **how** it was verified and **when**. "Unknown"
> is a valid entry; an invented value is not. Update this file whenever a fact changes.
> Machine-readable companions: `docs/leaderboard.json` (auto-updated by the leaderboard
> feed), `evidence/*.json` (holdout results, provenance sidecars).

## 1. Competition facts (official)

| Fact | Value | Source | Last verified |
|---|---|---|---|
| Competition | DrivenData "Geothermal Energy Mapping (GEMS) Prize" — DOE, competition id 306 | https://www.drivendata.org/competitions/306/competition-doe-gems/ | 2026-09-28 |
| Target | Pixels of **new** faults — expert-mapped, not in the current USGS/INGENIOUS catalogue | [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | 2026-09-28 |
| "New fault" definition | Any fault pixel not already captured by USGS/INGENIOUS, incl. newly mapped geometry of existing systems | [Staff, thread 11536 post 2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2) | 2026-09-28 |
| Scoring mask | Known catalogue pixels are masked **pixel-exact** in both rounds; only new-fault truth is scored; a prediction near a known trace but far from new truth is fully penalized; new truth may lie within 300 m of known traces | [Staff, thread 11516 post 4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) | 2026-09-28 |
| Metric | Distance-weighted Tversky index, α = 0.2 (FP), β = 0.8 (FN), triangular kernel k(d) = max(1 − d/300 m, 0); TP is per-truth-pixel max over the credit cell | Problem description, "Performance metric" | 2026-09-28 |
| Submission format | Single float32 band, EPSG:32611, 100 m, same bounds as `sample_submission.tif` (3730 × 3292), values in [0, 1], NaN outside footprint (5,167,373 valid pixels) | Problem description, "Submission format"; verified against the pinned template SHA `2176d08e…` | 2026-09-28 |
| Prizes | Phase 1: top 5 on the public leaderboard × $10k; Phase 2: $100k / 70k / 40k / 25k / 15k after expert review of **all** Phase-1 submissions | Problem description; [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | 2026-09-28 (rules carried from Round-5) |
| Submission allowance | 3 per week, **rolling window** (not calendar reset) | [Staff, thread 11524 post 2](https://community.drivendata.org/t/weekly-submissions/11524/2) | 2026-09-28 |
| Test-fault sources | **Undisclosed** by staff (sources, fault types, spatial coverage) | [Staff, thread 11527 post 7](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527/7) | 2026-09-28 |
| Provided layers | 19 bands (`training_features.tif`): conductivity, depth-to-conductive-base, detrended elevation + slope, strain-rate invariants, isostatic gravity + slope, magnetics (RTP, TMI, gradients, source depth), earthquake density. **No radiometrics; no sub-100 m topography.** `1m_DEM_links.csv` supplied separately | Problem description, "Provided features" | 2026-09-28 |
| Known label irregularities | float32 sentinel −3.4028235e+38 inside footprint (3,061 px/band, 3,073 in `tc`; 7,110,247 px outside); "Band 19" printed for the single-band label TIF is a notebook summary-string bug | measured in `evidence/round5-identity-checks.json`; [thread 11529 post 2](https://community.drivendata.org/t/11529/2) | 2026-09-28 |
| `tc` identity | The **in-file band description** is "tc - Tilt angle or total curvature - magnetic field derivative for edge detection", i.e. *not* a depth. Reading it as the problem description's "top-of-crustal magnetic source depth estimate" is an **inference** (that bullet is otherwise unassigned among the 19 bands) reinforced by measurement: strictly positive, 2.95–88.57, `corr(tc, |tilt|) = −0.0012`. Earlier sessions cited forum 11529 for the depth claim; that thread is about the label raster's band count, so the citation was corrected here. | band descriptions read from `data/training_features.tif` 2026-09-28; `evidence/round5-identity-checks.json` C3 | 2026-09-28 |
| `sample_submission.tif` | **Is the known-fault catalogue, not an empty raster**: bit-for-bit `(labels.tif > 0)` on the footprint (60,988 positive px, values {0,1}; SHA `2176d08e…`). `labels.tif` and `existing_faults.tif` are the same bytes (`7ba308cc…`). The problem page's "predicts total fault absence" wording is wrong. Copying the template would score on masked pixels only. | measured twice 2026-09-28 (`scripts/audit_siblings.py`, `evidence/sibling-audit.json`); independently corroborated by 11GEMSDOE's README | 2026-09-28 |
| Known-fault pixels in a prediction | **Neutral**: not charged as FP and no measurable free TP credit. Staff: "it should not matter whether these known faults are included with predictions or not" (11516/2); natural experiment: 8GEMSDOE's published `max(ens12, catalogue)` (0 differing pixels from that union) scored the same 0.1563 as ens12. | [thread 11516 post 2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2); `docs/sibling-audit.md` §3 | 2026-09-28 |
| Reference solution | U-Net (resnet18, ImageNet init), 19 bands min-max scaled, 128-px patches, Tversky loss (0.2, 0.8), 5 random 50/50 splits, 5 epochs, averaged soft output | [gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) | 2026-09-28 |
| External data | Allowed if free and publicly available; USGS products are public domain | Problem description, "External datasets" | 2026-09-28 |

## 2. Leaderboard (public DTI) — snapshot 2026-09-28, see `docs/leaderboard.json` for the live feed

| Rank | Account | Score | Note |
|---|---|---|---|
| 1 | DARD | 0.3168 | 11 submissions |
| 2 | alexoktaba | 0.2993 | |
| 3 | HardcoreTechGod | 0.2854 | |
| 4 | mzoorob | 0.2843 | |
| 5 | joeyfezster | 0.2806 | **Phase-1 top-5 cutoff** |
| 6 | GrigorSargsyan | 0.2742 | |
| 17 | doegemsDrivendata | 0.1847 | name suggests the organizer's reference U-Net — **not verified** |
| 26–28 | extradr19 / SDCF9 / smashi34 | 0.1563 | identical scores. extradr19 = the ens12 file (CERTAIN per the sibling ledger); SDCF9 and smashi34 were 0.1152 / 0.1560 on 2026-09-25, so they re-submitted — **account ownership not verified**, no upload receipts exist |
| 33 | wbg1 | 0.1461 | the ledger attributes 0.0830 (discovery arm) to this account; the 0.1461 file is unidentified — flagged |
| — | 0.1560 explanation | measured | GEMSDOE2's union added 10,668 px (9,430 chargeable) to the 0.1563 field and moved the score −0.0003 (sibling ledger D2) |
| 48 | smrtdoog5 | 0.1193 | GEMSDOE3 README claim — not verified |

Automation: `.github/workflows/leaderboard-feed.yml` runs `scripts/fetch_leaderboard.py`
twice daily (05:17 / 17:17 UTC) on a GitHub-hosted runner (the development sandbox cannot reach drivendata.org),
commits `docs/leaderboard.json` and a dated snapshot in `evidence/leaderboard/`, and the
site renders it. If the page structure changes the feed records `status: parse-failed`
and the workflow fails visibly. **Verified live 2026-09-28** (run 36365801815): the page shell has no
`<table>`; the table arrives as an htmx fragment from `…/leaderboard_partial/?page=1` (50 rows,
headers `Rank / Team members / Participant / Best public DW-Tversky / Links`, no submission count).

## 3. Local holdout ledger (frozen protocol — 512-px blocks, 12-px collar, seed 12027, pixel-exact mask, NMS-3 @ 2 %)

| Round | Arm | Dense DTI | Sparse DTI | Verdict | Evidence |
|---|---|---|---|---|---|
| 5 | multi25, top-k @2 % | 0.09071 | — | emission baseline | `evidence/holdout_round5.json` |
| 5 | multi25, NMS-3 @2 % | 0.22138 | 0.11178 | reference | `evidence/holdout_round5.json` |
| 6 | multi25 + H28 | 0.22143 (3/4, mean +0.00005) | 0.11438 (3/4, +0.0026) | passed on a technicality — noise-level | `evidence/holdout_round6.json` |
| 7 | multi25 + H28 + **H32 dem12** | see `evidence/holdout_round7.json` | see `evidence/holdout_round7.json` | recorded in `docs/session-review.md` §Round-7 | `evidence/holdout_round7.json` |

| 8 | H38 mass sweep / H39 1 m lidar / H40 graded / H37 control | 0.24586 → 0.27705 dense at 3.2 % mass but 0.12732 → 0.11705 sparse | 0.25326 dense (H39, 4/4) / 0.13018 sparse (2/4) | **gate failed — no artifact, no slot spent**; verdicts in `docs/hypotheses-round8.md` §6 | `evidence/holdout_round8.json` |

Holdout numbers are **proxies** (catalogue traces held out spatially); nothing here is a
DrivenData score. The group's only scored artifacts: 0.1563 (ens12 emission), 0.1560, 0.1461,
0.1193, 0.1152, 0.0830.

**Round-8 outcome (2026-09-28).** The frozen gate **failed**, so the shipped artifact is still
`12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif` and no weekly slot was spent. The harness
reproduced Round 7 exactly (`abs_diff = 0.0`, both protocols), then: H39 (1 m USGS 3DEP lidar
scarp descriptors, hash-pinned from sibling 7GEMSDOE) won the dense protocol 4/4
(0.24586 → 0.25326) but only 2/4 on sparse; the H38 mass sweep moved dense +0.0312 and sparse
−0.0103 at 3.2 % — sign disagreement, and the one real-board measurement of extra mass
(−0.0003 for +10,668 px) sides with sparse; H40 graded −0.171 dense; H37 catalogue base layer
+0.515 dense but provably a harness artefact of a catalogue-truth protocol. Leakage probe
0.0000 everywhere. Reading: mass and catalogue-shaped skill are not the levers; detector
quality is (the real board's break-even marginal hit rate at 0.156 is ≈ 3.3 %, versus ≈ 6.5 %
for a 0.30 detector).

**Metric algebra (2026-09-28, `evidence/metric-algebra.json`).** Because `TP_w + FN_w = N_t`
exactly, a public score fixes the file's true-positive mass as a function of the unknown
`N_t`: `T = (0.2E + 0.8N_t)/(1/DTI − 0.2)`. At the group's best (0.1563) the implied coverage
is ≤ 0.31 if `N_t` = 30k, ≤ 0.22 at 60k. The marginal-inclusion threshold derived from the
same algebra is `ΔT/ΔE > 0.2·DTI/(1 − 0.2·DTI)` = **0.0323** at DTI 0.1563 (0.0677 at the
leader's 0.3168) — i.e. with β/α = 4 the metric rewards recall far above precision, and every
artifact in this family has emitted a frozen ≈3 % of the footprint rather than the mass the
rule implies.

## 4. External-data registry (free, official; obtainability checked)

| Dataset | Official source | Licence | Reachable from | Status in repo |
|---|---|---|---|---|
| USGS 3DEP 1/3″ (~10 m) DEM, tiles n38–n40 w118–w120 | `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/<tile>/USGS_13_<tile>.tif`; catalogue [ScienceBase 4f70aa9fe4b058caae3f8de5](https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5) | US public domain | GitHub-hosted runner (not sandbox) | **In use (H32)** — 13 channels built by GEMSDOE10 tag `ext/dem10-36343078537`, hashes in `evidence/dem10-fetch.json` |
| USGS 3DEP 1 m lidar DEM (`1m_DEM_links.csv`) | official bucket `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/<project>/TIFF/…` (706/716 tiles of the OCR-recovered inventory) | US public domain | built on runner by sibling 7GEMSDOE; product fetched here via GitHub API | **H39 tested** — 12-channel 2 m scarp descriptor raster on the 100 m grid, SHA-256 pinned in `evidence/lidar-fetch.json`; gate failed on the sparse protocol (see §3) |
| GeoDAWN airborne magnetics + **radiometrics** (K, eTh, eU, TC grids) | [ScienceBase 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI 10.5066/P93LGLVQ | US public domain | runner only | H35 registered, not fetched |
| INGENIOUS Quaternary Faults v2 (`qfaults_ingenious_nad83conus117_2023-06-27.zip`) | GDR submission 1391, DOI 10.15121/1881483 | CC BY 4.0 | runner only | GEMSDOE10 H21: identical to labels — no extra traces |
| USGS SGMC state geologic maps (bedrock faults) | https://mrdata.usgs.gov/geology/state/ | US public domain | runner only | H36 registered; not locally validatable |
| Sentinel-2 L2A | Copernicus Data Space | free, registration | blocked (registration + volume) | H31/H19 deferred |

## 5. Group inventory (sibling repositories under `buffedlizard55-lab`, read via GitHub API 2026-09-28)

GEMSDOE, GEMSDOE2/3/4, 5–8GEMSDOE, GEMSDOE9, GEMSDOE10, 11GEMSDOE, 13–15GEMSDOE (empty stubs),
LEARNGEMSDOE. Ideas already tried somewhere in the group (do not relabel as novel): CNN
ensembles, pindrop/boosting, emission tuning, mag/grav coherence, conductive-basement
steps, strain tensors, inpainting, radiometric ratios, DEM scarp/hysteresis (GEMSDOE10 H20
= the 10 m channels reused here as H32), self-training, catalogue-gap targets.

**Byte-level audit 2026-09-28 (`scripts/audit_siblings.py`, 48 unique artifacts, 11 duplicate
groups, `docs/sibling-audit.md`):** the GEMSDOE site and the 5GEMSDOE site offer the *same*
file — `7f00890a…`, 570,890 B, 172,974 positive px — and that exact file is committed in six
places across five repositories; three earlier run artifacts repeat across four repositories.
`8GEMSDOE_Hedge-v2_submission.tif` (`052688ea…`) is pixel-exactly `max(ens12-7f00890a,
catalogue)` (0 differing pixels) and is recorded at the same 0.1563. Working account→file
ledger (5GEMSDOE first-party, no upload receipts anywhere): extradr19 0.1563 = `7f00890a`;
smashi34 0.1560 = `f68e590f` (union); smrtdoog5 0.1193 = `f347b70d` (nodes); SDCF9 0.1152 =
`4e03fc97` (ridge control); wbg1 0.0830 = `37f9d5b8` (discovery). `wbg1`'s board row of 0.1461
has no identified file.

## 6. Open questions (answer = "unknown" until verified)

1. Do the group accounts on the leaderboard (extradr19 / SDCF9 / smashi34 / wbg1 /
   smrtdoog5 / GEMSDOE2's 0.1560) belong to one team? Rules eligibility depends on it.
2. What does a 12GEMSDOE NMS-3 artifact score on DrivenData? No R5/R6/R7 artifact has been
   uploaded; the holdout→leaderboard transfer is unmeasured.
3. Are the experts' new faults scarp-dominated (lidar-mapped) or geophysics-dominated?
   Staff decline to say. H32's holdout gain is on catalogue traces, not on the hidden truth.
4. Why does the sponsor's `det_elev_slope` correlate 0.97 with 10 m slope aggregated to
   100 m? Most likely it was itself derived from a high-resolution DEM; unverified.
