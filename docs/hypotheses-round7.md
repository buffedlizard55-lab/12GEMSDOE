# Round-7 Candidate Register — Sub-100 m Topography, Spatial-Context Learning, Strike-Integrated Lineaments, Radiometrics, Geologic-Map Faults

> **Status:** preregistered on 2026-09-28 **before** `scripts/build_round7_features.py` and
> `scripts/holdout_round7.py` were written or run. Emission policy is frozen from Round-5
> (greedy NMS, Chebyshev radius 2, budget 2 % of the valid footprint, deterministic
> tie-break). No DrivenData slot is spent in this session under any outcome. A hypothesis is
> not a discovery. Every source link below is for manual review; `PASS` on a source means
> only that the page was opened and the quoted text was found.

## 0. Why this round exists — and why it is a different *kind* of idea

Rounds 1–6 tested **29 per-pixel feature transforms of the 19 supplied 100 m bands** on the
same HistGradientBoosting learner. Round-5 showed the emission geometry, not the feature
list, was the bottleneck (top-*k* → NMS-3: 0.0907 → 0.2214 dense). With emission fixed,
every one of the 29 transforms lands within ±0.001 (dense) / ±0.003 (sparse) of `multi25`
(`evidence/holdout_round6.json`). Continuing to add 100 m-band transforms is the definition
of "the same idea tried a different way". Round-7 therefore changes one of three things:

1. **the input resolution** (H32: 10 m topography — sub-pixel relative to the supplied grid),
2. **the learner's receptive field** (H33: spatial-context CNN instead of a per-pixel GBM), or
3. **the data domain** (H35 radiometrics, H36 pre-Quaternary geologic-map faults — layers no
   supplied band represents).

H34 is the only new transform of supplied bands, and it is included because it targets a
statistic (long-baseline strike integration) that no 3×3 / 9-px kernel in rounds 1–6 can
express; it is ranked below the resolution/domain changes.

### Official facts that shape this round (re-verified 2026-09-28)

| Fact | Source (opened this session) |
|---|---|
| Test truth = faults "manually identified by fault experts … not contained within the current public USGS database"; a `1m_DEM_links.csv` of 1 m DEM download links is part of the official data | [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Supplied `training_features.tif` layers: conductivity, depth-to-conductive-base, detrended elevation + slope, strain rates, isostatic gravity + slope, magnetics (RTP, TMI, gradients, source depth), earthquake density — **no radiometric layer, no sub-100 m topography** | same page, "Provided features" |
| Mask is pixel-exact = training labels; a prediction near a known trace but far from new-fault truth is fully penalized; new truth may lie within 300 m of known traces ("corrections") | [Staff 11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) |
| "New fault" = any fault pixel not already captured by USGS/INGENIOUS, incl. new geometry of existing systems | [Staff 11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2) |
| Staff will not disclose the data sources, fault types or coverage behind the test faults; Phase-2 truth is expanded by expert review of all Phase-1 submissions | [Staff 11527/7](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527/7) |
| Submission allowance resets on a rolling window | [Staff 11524/2](https://community.drivendata.org/t/weekly-submissions/11524/2) |
| Reference solution = U-Net (resnet18 encoder, ImageNet init), 128-px patches, Tversky loss α=0.2 β=0.8, 5 Monte-Carlo splits, 5 epochs, soft-probability average | [`unet-mc-cv-reference-solution.ipynb`](https://github.com/drivendataorg/gems-prize-reference-solution/blob/main/unet-mc-cv-reference-solution.ipynb) (cells 0, 16 read via GitHub API) |
| Leaderboard 2026-09-28: #1 DARD 0.3168 (11 subs), #2 alexoktaba 0.2993, #3 HardcoreTechGod 0.2854, #4 mzoorob 0.2843, #5 joeyfezster 0.2806; #26–28 extradr19 / SDCF9 / smashi34 all 0.1563; #33 wbg1 0.1461; #48 smrtdoog5 0.1193 | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) |
| GeoDAWN is an airborne **magnetic and radiometric** survey; the data release includes "geoTIFF images of geophysical grids" and a radiometric ternary map; public-domain USGS data release, DOI 10.5066/P93LGLVQ | [ScienceBase 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) |

## 1. Metric geometry reminder (frozen)

Official DTI: α = 0.2, β = 0.8, triangular kernel R = 300 m = 3 px; TP is a per-truth-pixel
`max` over the 5 × 5 credit cell ([problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
Marginal emission condition derived in Round-5: emit a pixel iff its hit probability
exceeds 0.2 × DTI. Budget 2 % and NMS radius 2 remain frozen so Round-7 numbers are
directly comparable with Rounds 5–6.

## 2. Ranked candidates (expected DTI gain ÷ implementation cost)

| Rank / cost | Candidate: exact layers and transform | Physical signature | Why it should catch a fault absent from USGS/INGENIOUS | Difference from anything in this repo or sibling registers | Validation state |
|---|---|---|---|---|---|
| **1 / low (data already obtainable)** | **H32 — sub-100 m topographic scarp signature.** External: USGS 3DEP 1/3 arc-second (~10 m) seamless DEM, 12 tiles n38w118…n41w120, public domain, reduced to 13 label-free channels per 100 m cell: `slope_max`, `slope_mean`, `slope_std`, `hgm20_max`, `hgm50_max`, `hgm200_mean` (horizontal-gradient magnitude at 20/50/200 m), `steep_ratio_max`, `resid_std`, `resid_range` (detrended micro-relief), `curv_absmax`, `onesided`, `onesided3` (scarp-facing asymmetry), `valid_frac`. Arm = `multi25 + H28 + dem12` (`valid_frac` is constant and dropped). | A 1–10 m fault scarp is a step in elevation over 20–100 m. On the supplied 100 m grid it is sub-pixel and averaged away in `det_elev`/`det_elev_slope`; at 10 m posting it is a resolved, one-sided gradient ridge. | The USGS catalogue is stated to be incomplete ([problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)); Quaternary-fault mapping in the Great Basin predates lidar for most quadrangles, and the organizers ship `1m_DEM_links.csv`, i.e. high-resolution topography is the one external data class the sponsor explicitly points at. Small, degraded scarps in alluvium are exactly what such mapping adds. Null: erosional terraces, shorelines (pluvial Lake Lahontan), roads, and canal banks are also 1–10 m steps. | 12GEMSDOE has never used any topography finer than the 100 m `det_elev` band (H11 drainage, H26 relief were 100 m). Sibling GEMSDOE10 built these 13 channels (H20) and measured +0.0147 under **its own** protocol (stripe folds, 4 km exclusion, `thin10_binary`); they have never been tested under the 12GEMSDOE frozen masked NMS-3 protocol nor together with H28. | **Viable now.** Fetched and hash-verified this session (`scripts/fetch_dem10_channels.py`, `evidence/dem10-fetch.json`). Tested in `scripts/holdout_round7.py`. |
| **2 / high** | **H33 — spatial-context learner.** Layers: all 19 raw bands (+ dem13 if H32 passes). Model: compact U-Net (4 levels, 16–128 filters), 128-px patches, Tversky loss α=0.2 β=0.8, spatially-blocked folds identical to the GBM protocol, NMS-3 emission on the averaged probability field. | Faults are continuous, oriented lines; a per-pixel learner cannot use continuity, strike coherence, or the relationship between a pixel and its 1–6 km neighbourhood. A CNN's receptive field learns these. | Faint scarps/lineaments whose per-pixel signal is below noise but whose along-strike continuity is unmistakable — the way a human mapper sees them on a hillshade. | Every 12GEMSDOE arm is a per-pixel HistGradientBoosting model. The official reference solution is a U-Net ([notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/main/unet-mc-cv-reference-solution.ipynb)); the model-class gap was flagged in Rounds 5–6 as the largest unexplored lever and never acted on. | **Deferred to Round-8.** Needs PyTorch: the PyPI default `torch` wheel is a CUDA build far too large for this sandbox; the CPU wheel index (download.pytorch.org) is blocked here. Plan: build the wheel cache or train on a GitHub-hosted runner (2-core, 7 GB) using the same fold masks, then bridge the per-fold probability fields back via an `ext/*` tag. |
| **3 / medium** | **H34 — strike-integrated line contrast (Radon-style).** Supplied `tmi_hg` (B3), `iso_grav_anom_hg` (B18), `det_elev_slope` (B19) + `dem10_hgm50_max`. For 12 orientations θ and lengths L ∈ {15, 25} px: mean of the robust-normalized edge field along a centred line segment minus the mean of two parallel flanking segments 3 px either side; feature = max over θ, L. | A long, straight, faint lineament integrates coherently along strike while noise averages out; local 3×3 / 9-px kernels cannot distinguish a 2 km lineament from speckle. | Concealed range-front and intrabasin faults produce faint but long gradient lineaments; mappers omit them where no single scarp segment is convincing. Null: flight-line levelling artefacts (E–W lines at 400 m spacing), roads, fences. | H15–H18 and H26 use 9-px oriented kernels (≤ 900 m); H7 is a correlogram of earthquake density; H6 extends known tips. None integrates evidence over 1.5–2.5 km baselines with flank subtraction. | **Round-8 candidate**; not built this session (compute ~1–2 h CPU; ranked below H32 by expected gain and below H33 by mechanism novelty). |
| **4 / medium-high (external, transport blocked)** | **H35 — GeoDAWN airborne radiometrics: potassium alteration and lithologic-contrast lineaments.** External: K (%), eTh, eU, total count grids from the GeoDAWN data release; transforms: K/eTh ratio anomaly, |∇(total count)| lineaments, K-high ∩ magnetic-low (H8-style AND). | Hydrothermal fluids along fault conduits produce potassic alteration (K enrichment, K/Th high) and destroy magnetite; radiometrics sense the top ~30 cm, so they map surface expression of conduits and lithologic contacts offset by faults. | Radiometrics are half of the GeoDAWN survey, the problem page shows a radiometric map, yet **no radiometric band is in `training_features.tif`** — most competitors will not add it. Blind conduits with surface leakage have K anomalies but no scarp. Null: agricultural potash, granite outcrops, playa evaporites. | The sibling inventory lists "radiometric ratios" (source not verified this session); 12GEMSDOE has never used radiometrics; H8 used conductivity × magnetics, H31/H19 optical SWIR — different sensors and physics. | **Source verified free/official** ([ScienceBase 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI 10.5066/P93LGLVQ, USGS public domain; JSON API answered). **Not obtainable from this sandbox** (sciencebase.gov TLS blocked); needs the GitHub-runner bridge (`ext/*` tag pattern). Not scored here. |
| **5 / medium (external; not locally validatable)** | **H36 — pre-Quaternary geologic-map faults as a catalogue-gap prior.** External: USGS State Geologic Map Compilation (SGMC) fault lines for Nevada and California, public domain. Transform: rasterize, remove any pixel within 300 m of a label, use the residual as a prior channel. | Bedrock faults mapped on 1:100k–1:500k geologic maps that are not Quaternary-active and therefore absent from QFFD/INGENIOUS. | Sibling GEMSDOE10 H21 measured that the labels are exactly the QFFD + INGENIOUS v2 catalogue; geologic-map faults are a strictly different set. Whether the experts' "new faults" include such structures is **unknown** (staff decline to describe sources). | No repo in the group uses geologic-map faults. | **Not viable for a holdout decision**: no local truth can score it (the catalogue proxy excludes it by construction), so only a submission or the Phase-2 expert review can test it. Source: [USGS SGMC](https://mrdata.usgs.gov/geology/state/) (blocked from sandbox). Recorded, not proposed for a slot. |

## 3. Preregistered decision rule (fixed before any Round-7 arm is scored)

1. **Emission for every arm:** NMS radius 2 (5 × 5), descending probability, deterministic
   tie-break by pixel index, budget 2 % (unchanged since Round-5).
2. **Protocol:** frozen masked spatial holdout — 512-px blocks, 12-px collar, seed 12027,
   official pixel-exact catalogue mask on the FP term, leakage probe must read 0.0000 on every
   fold, both truth protocols (dense catalogue truth; sparse 20 % component-thinned truth,
   seed 4242+f).
3. **Arms:** `multi25` (reference), `multi25_h28` (Round-6 incumbent, retrained),
   `multi25_h28_dem12` (**H32 primary**: all DEM channels except the constant
   `valid_frac`), `multi25_dem12` (ablation: is the gain from topography alone?),
   `multi25_h28_dem3` (**distinct-only subset** = the DEM channels whose max |corr| against
   every prior channel is < 0.50; fixed by the distinctness table in
   `evidence/round7-feature-build.json` *before* any arm was scored — see the amendment
   note below).
4. **Gate (must pass all):** (a) `multi25_h28_dem12` > `multi25_h28` on ≥ 3/4 folds on
   **both** truth protocols **and** mean paired gain > 0 on both (Round-6 lesson: 3/4 folds
   with a mean gain of +0.00005 is not a material improvement, see §5.2); (b) leakage probe
   0.0000; (c) distinctness reported per channel (max |corr| vs all 43 prior channels on
   400 k random valid pixels). Because H32 is a **resolution** change, some channels are
   expected to correlate with `det_elev_slope`; channels ≥ 0.50 are listed, not hidden, and
   the distinct-only arm `multi25_h28_dem3` is not formed from them.
5. **A pass authorizes packaging a Round-7 GeoTIFF for the site.** It does **not** authorize
   release: the standing strongest-sibling-baseline requirement
   (`evidence/preregistered-hypotheses.md`) is still unsatisfied and spending a slot is a
   human decision. No slot is spent in this session under any outcome.
6. **External arms H35/H36 and the model-class arm H33** are recorded with verified sources
   and obtainability; they are not scored this session.

**Amendment (2026-09-28, after `build_round7_features.py`, before `holdout_round7.py` was
written or run).** The distinctness table came back far stronger than expected: the 10 m
slope / gradient / micro-relief channels correlate **0.80–0.97** with the supplied
`det_elev_slope` (B19) — `slope_mean` 0.966, `hgm50_max` 0.952, `hgm20_max` 0.943,
`slope_max` 0.905, `resid_range` 0.853, `hgm200_mean` 0.852, `resid_std` 0.838,
`curv_absmax` 0.797, `slope_std` 0.640. Only the scarp-**asymmetry** and steep-fraction
channels are distinct: `onesided3` 0.177, `onesided` 0.259, `steep_ratio_max` 0.411.
Interpretation: the sponsor's `det_elev_slope` is evidently already computed from
high-resolution topography and aggregated to 100 m, so "sub-100 m slope" is *not* new
information at the 100 m cell level; the genuinely new content of H32 is the *one-sided*
scarp signature. Consequences, fixed before scoring: (i) the primary arm keeps all 12
channels as preregistered; (ii) the preregistered "core subset" arm is replaced by the
distinct-only subset `dem3` = {`steep_ratio_max`, `onesided`, `onesided3`}, which is what
item 4c required; (iii) `valid_frac` is constant 1.0 on the footprint and dropped, so the
arm is `dem12`, not `dem13`. Expected gain is revised **down** from the sibling's +0.0147
(their stack did not contain B19-derived transforms in the same form) to "small, possibly
zero"; the gate is unchanged.

## 4. Provenance of the H32 data (how a reviewer can check every byte)

* Product: USGS 3DEP 1/3 arc-second seamless DEM, "current" staged TIFFs, e.g.
  `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n40w118/USGS_13_n40w118.tif`
  (12 tiles; per-tile SHA-256 and byte counts are in `data/dem10/manifest.json` →
  `evidence/dem10-fetch.json`). Product catalogue:
  [ScienceBase 4f70aa9fe4b058caae3f8de5](https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5).
  USGS data are public domain, so the licence permits contest use and sharing with the
  sponsor ([External datasets](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#external-datasets)).
* Built on a GitHub-hosted runner by `buffedlizard55-lab/GEMSDOE10` and frozen as tag
  `ext/dem10-36343078537` (commit `91d6566ecc…`; `STATUS.txt` = `build=success
  run=36343078537`). Channel vectors are in footprint order
  `np.nonzero(np.isfinite(sample_submission))`, template SHA-256
  `2176d08e…` = the official `sample_submission.tif` pinned in this repo.
* This session re-hashed all 13 channels against the manifest before use
  (`evidence/dem10-fetch.json`, every channel `fetched-verified`). No fault labels were used
  in the build (`labels_used: false`).
* Boundary: the build script itself lives in the sibling repository; this repo verifies the
  hashes and the template alignment, not the sibling's code line by line.

## 5. Irregularities flagged this session (for manual review)

1. **Three leaderboard accounts at exactly 0.1563 (#26 extradr19, 3 subs; #27 SDCF9, 2 subs;
   #28 smashi34, 2 subs) alongside GEMSDOE1 = 5GEMSDOE byte-identical published files.**
   Consistent with the same artifact being uploaded from three accounts. Ownership of those
   accounts is **not** established by this repo (no upload receipts); if they are group
   accounts, note that the [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
   governs team/account eligibility — check before any further upload.
2. **Round-6 "pass" was noise-level.** `multi25_h28` beat `multi25` on 3/4 folds, but the
   paired dense deltas were [+0.00067, +0.00010, +0.00331, −0.00386] (mean **+0.00005**);
   sparse mean +0.0026. The Round-7 gate therefore adds "mean paired gain > 0 on both
   protocols" so a 3/4 split with a negative or zero mean cannot pass again.
3. **Feature-cube SHA drift between sessions.** The Round-5 manifest pins
   `candidate-features-30.npy` = `7eb403a2…`; the Round-6 manifest pins `fc746d92…`; this
   session's deterministic rebuild from the pinned rasters gives `7eb403a2…` again. The
   difference is confined to channel 29 (H10, used only by `multi30`); `multi25` arms are
   unaffected, but the Round-6 distinctness sidecar was computed against the drifted cube.
   The sidecar is regenerated here in the correct build order (round-4 → round-5 → round-6).
4. **`tc` band description vs official layer list** and **float32 sentinel missing data**
   (Round-5 C1/C3) remain open — worth a forum post.
5. **Leaderboard account `doegemsDrivendata` at 0.1847 (5 subs)** — plausibly the
   organizers' reference U-Net, but that is an inference from the name only and is not
   asserted as fact.

## 6. Source ledger (manual review links)

| Claim | Source | Verified |
|---|---|---|
| Target, competition structure, provided layers, metric, submission format | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | opened 2026-09-28, quotes in §0 |
| Pixel-exact mask, full penalty near known traces, corrections within 300 m | https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4 | opened 2026-09-28 (JSON API) |
| "New fault" definition | https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2 | opened 2026-09-28 |
| Test-fault sources undisclosed; Phase-2 truth expanded by expert review | https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527/7 | opened 2026-09-28 |
| Rolling submission window | https://community.drivendata.org/t/weekly-submissions/11524/2 | opened 2026-09-28 |
| Reference solution architecture | https://github.com/drivendataorg/gems-prize-reference-solution | notebook read via GitHub API 2026-09-28 |
| Leaderboard snapshot | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | opened 2026-09-28 (top-50 table) |
| GeoDAWN data release (mag + rad, GeoTIFF grids, public domain) | https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7 | opened 2026-09-28 (HTML + JSON) |
| 3DEP 1/3 arc-second product catalogue | https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5 | URL from the runner manifest; not re-opened this session |
| SGMC state geologic maps | https://mrdata.usgs.gov/geology/state/ | not reachable from sandbox; not opened this session |
| Rules, prize split, eligibility | https://docs.nlr.gov/docs/fy26osti/96647.pdf | carried from Round-5 verification |
| Sibling H20 result (+0.0147 dev / +0.0141 confirmation) | https://github.com/buffedlizard55-lab/GEMSDOE10 README, tag `ext/dem10-36343078537` | README + manifest read via GitHub API 2026-09-28 |
