# Research and audit log

**Reviewed:** 2026-09-27 (UTC)  
**Repository revision at review:** `c48589c` (initial commit; shallow checkout)
**Purpose:** separate sourced facts, reported claims, hypotheses, and unverified items. This is a research backlog, not a claim that any candidate has improved results.

## 1. Scope and verified facts

| Statement | Evidence and verification | Status |
|---|---|---|
| The challenge predicts geologic faults indicative of geothermal resources. | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), fetched 2026-09-27. | Verified from official competition page. |
| Existing public fault labels may be incomplete or inaccurate; test labels are expert-identified faults absent from the public USGS dataset. | Same official problem description. | Verified as the competition's stated setup; not an independent geological assessment. |
| The provided feature raster is described as UTM 11N / EPSG:32611 at 100 m and includes conductivity, detrended elevation/slope, strain, gravity, magnetic, and earthquake-density features. | Same official problem description, “Provided features.” | Verified description only; the actual raster and band names are unavailable here. |
| A 1 m DEM link CSV is part of the described data. | Same official problem description. | Verified page description. Availability/content not checked. |
| Metric is distance-weighted Tversky (DW-Tversky), with alpha 0.2, beta 0.8, and a linear triangular distance kernel of 300 m support (3 pixels at 100 m). | Official [problem description, performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), fetched 2026-09-27. | Verified stated metric; still reproduce against official reference implementation before relying on a local scorer. |
| Public leaderboard top score was 0.3049. | Official leaderboard fetched 2026-09-27; first entry displayed 0.3049. | Verified at fetch time; dynamic and can change. |
| Data page access is gated. | Unauthenticated fetch of official [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected to DrivenData login. | Verified for this access attempt only. |
| There are no project artifacts beyond README in the checkout. | `find` and `git status` inspection at review. | Verified locally. |
| The team’s listed 0.1563 scores are the same prediction. | No raster files, hashes, metadata, or experiment records supplied. | **Not verified; cannot conclude.** |
| Required submission raster format: EPSG:32611, 100 m, same bounds as training data, outside bounds null/NaN, one float32 band with values in `[0,1]`. | Official [problem description, submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), fetched 2026-09-27. | Verified as page requirements; exact alignment must be tested against the official sample raster. |
| Official rules PDF title/date: “Geologic Enhanced Mapping System (GEMS) Prize Official Rules,” September 2026. | [NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), fetched 2026-09-27; PDF parsed. | Verified title/date. The full rules still need careful review before contest entry.

### Score tie investigation

The supplied list reports 0.1563 for GEMSDOE1, 5GEMSDOE, and 8GEMSDOE. Equal four-decimal public scores are not proof of identical predictions. To investigate, obtain original output TIFs and submitted-file records, then compare:

1. SHA-256 of the exact uploaded bytes (exact identity).
2. Raster dimensions, CRS, affine transform, dtype, nodata, and mask.
3. Pixelwise exact equality and correlation after aligning grids; report fraction equal and differing values.
4. Predictions after clipping/nodata handling and any quantization, if known.
5. Code/config/data hashes and timestamps for each run.

A high or perfect raster match would support repeated outputs; merely similar score would not. Scores may be rounded, and the benchmark can assign equal metric values to different predictions.

## 2. Candidate hypotheses (not yet tested)

**Important:** The provided checkout contains no features/labels, no holdout split, and no previous implementation. Consequently no claim that these are absent from past work can be made. They are novel relative to the *contents of this checkout* (which implements no method), not proven novel relative to the submitted external projects. Before coding, compare them to retrieved historical notebooks/scripts. Estimated rank is qualitative; a score gain cannot responsibly be predicted without data. “Expected DTI improvement” ranks test priority, not a promised amount.

| Rank | Candidate and involved layers | Signature / physical idea | Catalogue-gap mechanism (testable, not fact) | Difference from this repo | Cost / expected value |
|---|---|---|---|---|---|
| 1 | **Cross-physics edge concordance:** TMI / RTP magnetic, isostatic gravity anomaly, conductivity (plus detrended elevation as an independent surface layer). | Multi-scale horizontal gradient magnitude and directional edge-coherence; reward spatially coincident, persistent lineaments across independent physical fields, not raw high values. | Faults can juxtapose rocks or alter fluid pathways and may create aligned contrasts; coincident edges outside mapped fault traces could flag unrepresented structures. Contrasts can also be lithologic/contact boundaries, so require spatial holdout and map-near exclusion analysis. | No feature engineering/model exists in this repo; distinct from a “pindrop” point/cluster or a single dense-ridge score as described in user-provided notes. Historical implementations unavailable, so external novelty is unverified. | Medium implementation; **highest priority to test** because source layers are described as already provided and it requires no new external data. Validation still blocked pending data. |
| 2 | **Scale-space curvature / ridge persistence:** detrended elevation, slope of detrended elevation, and (if available) 1 m DEM derivatives. | Multiscale profile/plan curvature, Laplacian/ ridge-valley response, and persistence across smoothing scales; directional lineamentness rather than point peaks. | Subtle scarps/linear drainage or topographic breaks missed by mapped inventories may persist across scales. Nevada aridity/erosion and roads can create false positives. | Transform-based morphology, not point sampling or catalogue proximity; not implemented here. Prior project strategy cannot be verified. | Medium-high; promising and existing base DEM-derived layers require no extra download; fine DEM optional only after provenance/access check. |
| 3 | **Strain-tensor regime boundaries:** dilatation, shear strain rate, second invariant. | Gradients, sign transitions, anisotropy/orientation and coherent boundary segments, then test against faults rather than simply favoring high strain magnitude. | A mapped fault may be missing where a coherent deformation-domain boundary localizes strain; gradients may trace broad tectonic boundaries unrelated to local faults. | Uses tensor relations and boundary geometry rather than magnetic ridge/pindrop detection. No code in this checkout; previous use unverified. | Medium; use existing stated layers, no extra source. Expected value moderate, needs careful spatial null tests. |
| 4 | **Earthquake-density lineament with scale-aware background correction:** earthquake density plus strain layers; no raw event data assumed. | Local density residual against a broad-scale kernel, anisotropic connected-component/line orientation and cross-check to independent strain evidence. | Seismicity may illuminate active unmapped structures, while raw density alone favors known active faults and clusters; broad-background subtraction may expose secondary lineaments. | A spatial residual/line-network approach, different from magnetic/topographic transforms. Earthquake-density raster is described as provided; temporal source/event provenance not established. | Low-medium; no external data if provided band is confirmed. Likely higher confounding and lower expected value. |
| 5 | **1 m DEM micro-geomorphology:** linked fine-resolution DEM tiles from the competition CSV. | Tile-level multiscale scarp/curvature/roughness and lineament continuity, aggregated to the 100 m target grid with uncertainty. | Small scarps absent from 100 m regional derivatives could expose unmapped near-surface fault traces, particularly where geophysics is ambiguous. | Resolves a different scale and uses source DEM rather than only supplied 100 m predictors. | High: obtain and mosaic official-listed DEMs, inspect coverage/vertical datum/resampling and validate. Do not propose as viable until exact links are checked and downloads/licensing verified. |

### Top candidate and validation gate

Candidate 1 is top-ranked for feasibility because the competition page says the relevant geophysical feature bands are supplied; it does not require obtaining an external dataset. **It has not been validated and no test score is claimed.** The data page requires login, and local files are absent, so it cannot be evaluated in this session. Do not spend a submission slot on it. Required next test: create a spatial-block holdout before tuning; compare the current reproducible baseline, each single-layer edge, and concordance ablation with identical training coverage, competition metric, and inference mask. Report fold-level results, bootstrap uncertainty by spatial block, lineament overlap with known labels, and performance in areas buffered away from known fault inventory. Only proceed if it beats current holdout best robustly and improves independent blocks.

No external source is needed for candidates 1–4 beyond authenticated challenge data. Candidate 5 requires the exact DEM URLs in `1m_DEM_links.csv`; that file is unavailable, so a specific DEM endpoint, coverage, availability, and terms cannot be verified yet. The official entry point is the gated [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). The [USGS GeoDAWN dataset metadata](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and its [ScienceBase record](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) are official leads, but no additional downloadable layer is asserted here as available or licensed for this contest.

## 3. Official references for review

1. [DrivenData competition home / rules](https://www.drivendata.org/competitions/306/competition-doe-gems/) — primary rules and overview.
2. [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — task, provided layers, labels, external data allowance, scoring explanation.
3. [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) — competition context.
4. [DrivenData data download page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — authenticated data source; access redirected to login in this review.
5. [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — dynamic public ranking; queried 2026-09-27.
6. [DrivenData reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) — baseline implementation and setup.
7. [USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — official survey metadata.
8. [USGS ScienceBase GeoDAWN study-area record](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7).
9. [Great Basin Center INGENIOUS project](https://gbcge.org/current-projects/ingenious/).
10. [NLR/DOE GEMS submission guidance PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — link supplied by team; contents not independently retrieved in this review, so exact procedural claims are not attributed to it.

## 4. Irregularities and limitations flagged

- User-supplied team score pages/submission descriptions cannot be verified from this repository; no submitted file names or checksums are present.
- Repeated 0.1563 values may result from shared outputs, same default/baseline, or rounding; current evidence cannot distinguish them.
- User named target scores and older reports; leaderboard is dynamic, and snapshot at review shows 0.3049 leader. No claim that this will remain current.
- The repo has no code, README only, data, test suite, or GitHub Pages site despite prior request describing such assets. The statement that a pipeline was “ready” is unsupported by the present checkout.
- Data access, actual GeoTIFF submission validity, current competition deadline/round, free external-data access, GPU, and local package support remain unverified.
- A leaderboard score is not proof that a predicted lineament is geologically a fault; final-round expert review is relevant to the challenge design. See competition structure on official problem page.

## 5. Next-session checklist

1. Securely obtain authorized challenge data through the user's DrivenData access, place in ignored `data/`, and retain no credentials. Record file hashes and raster metadata.
2. Inspect official reference notebook, actual metric implementation, label prevalence, prediction mask, grid, and nodata conventions.
3. Define immutable spatial blocks and holdout before feature/model choices; establish baseline and reproducible scoring tests.
4. Obtain historical submissions/runs from team archives to resolve same-score question using hashes and pixel comparisons.
5. Implement candidate 1 as a separate experiment, run ablations and block-level validation; reject if it fails gate.
6. Only then implement a submission builder that aligns to sample submission exactly, enforces finite `[0,1]` values, tags experiment identity, and writes a unique descriptive name/comment plus provenance manifest.
7. Create the web summary/export interaction when a valid generated raster can be demonstrated; test output against the official sample grid before exposing a download button.
