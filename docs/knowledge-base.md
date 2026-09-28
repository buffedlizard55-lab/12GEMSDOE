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
| Known label irregularities | `tc` band is described as top-of-magnetic-source depth, not tilt; float32 sentinel −3.4028235e+38 inside footprint (3,073 px in `tc`); "Band 19" label string is a notebook bug | `evidence/data-inventory.json`; [thread 11529](https://community.drivendata.org/t/11529) | 2026-09-28 |
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
| 26–28 | extradr19 / SDCF9 / smashi34 | 0.1563 | identical scores; consistent with the group's byte-identical ens12 artifact — **account ownership not verified** |
| 33 | wbg1 | 0.1461 | 7GEMSDOE README claim — not verified |
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

Holdout numbers are **proxies** (catalogue traces held out spatially); nothing here is a
DrivenData score. The group's only scored artifacts: 0.1563 (ens12 emission), 0.1461, 0.1193.

## 4. External-data registry (free, official; obtainability checked)

| Dataset | Official source | Licence | Reachable from | Status in repo |
|---|---|---|---|---|
| USGS 3DEP 1/3″ (~10 m) DEM, tiles n38–n40 w118–w120 | `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/<tile>/USGS_13_<tile>.tif`; catalogue [ScienceBase 4f70aa9fe4b058caae3f8de5](https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5) | US public domain | GitHub-hosted runner (not sandbox) | **In use (H32)** — 13 channels built by GEMSDOE10 tag `ext/dem10-36343078537`, hashes in `evidence/dem10-fetch.json` |
| USGS 3DEP 1 m lidar DEM (`1m_DEM_links.csv`) | DrivenData data page → USGS | US public domain | runner only; ~tens of GB | H30 blocked (volume); not built |
| GeoDAWN airborne magnetics + **radiometrics** (K, eTh, eU, TC grids) | [ScienceBase 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI 10.5066/P93LGLVQ | US public domain | runner only | H35 registered, not fetched |
| INGENIOUS Quaternary Faults v2 (`qfaults_ingenious_nad83conus117_2023-06-27.zip`) | GDR submission 1391, DOI 10.15121/1881483 | CC BY 4.0 | runner only | GEMSDOE10 H21: identical to labels — no extra traces |
| USGS SGMC state geologic maps (bedrock faults) | https://mrdata.usgs.gov/geology/state/ | US public domain | runner only | H36 registered; not locally validatable |
| Sentinel-2 L2A | Copernicus Data Space | free, registration | blocked (registration + volume) | H31/H19 deferred |

## 5. Group inventory (sibling repositories under `buffedlizard55-lab`, read via GitHub API 2026-09-28)

GEMSDOE, GEMSDOE2/3/4, 5–8GEMSDOE, GEMSDOE9, GEMSDOE10, 11GEMSDOE, 13–15GEMSDOE (empty),
LEARNGEMSDOE. Ideas already tried somewhere in the group (do not relabel as novel): CNN
ensembles, pindrop/boosting, emission tuning, mag/grav coherence, conductive-basement
steps, strain tensors, inpainting, radiometric ratios, DEM scarp/hysteresis (GEMSDOE10 H20
= the 10 m channels reused here as H32). GEMSDOE10's audit: GEMSDOE1 = 5GEMSDOE = GEMSDOE2
byte-identical artifacts; 8GEMSDOE differs only on 54,533 masked catalogue pixels.

## 6. Open questions (answer = "unknown" until verified)

1. Do the group accounts on the leaderboard (extradr19 / SDCF9 / smashi34 / wbg1 /
   smrtdoog5 / GEMSDOE2's 0.1560) belong to one team? Rules eligibility depends on it.
2. What does a 12GEMSDOE NMS-3 artifact score on DrivenData? No R5/R6/R7 artifact has been
   uploaded; the holdout→leaderboard transfer is unmeasured.
3. Are the experts' new faults scarp-dominated (lidar-mapped) or geophysics-dominated?
   Staff decline to say. H32's holdout gain is on catalogue traces, not on the hidden truth.
4. Why does the sponsor's `det_elev_slope` correlate 0.97 with 10 m slope aggregated to
   100 m? Most likely it was itself derived from a high-resolution DEM; unverified.
