# 12GEMSDOE — Geothermal Fault Discovery & Submission Hub

> **Read this README every session.** Maximize P(Win): prioritize scientifically defensible discovery and validation over leaderboard churn. Own the Outcome: follow data, model, artifact and published result end to end. Line-by-line verification from official sources. Zero hallucinations.

[Workbench](https://buffedlizard55-lab.github.io/12GEMSDOE/) · [Executive Submission Guide](https://buffedlizard55-lab.github.io/12GEMSDOE/executive-summary.html) · [Evidence & Sibling Audit](docs/session-review.md) · [Round-1 Hypotheses](docs/hypotheses.md) · [Round-2 Hypotheses H6–H10](docs/hypotheses-round2.md) · [Round-3 H11–H14](docs/hypotheses-round3.md) · [Round-4 H15–H19](docs/hypotheses-round4.md) · [Round-5 Emission Geometry](docs/hypotheses-round5.md) · [Round-6 Seismic+Texture](docs/hypotheses-round6.md) · [Round-7 DEM Scarp H32–H36](docs/hypotheses-round7.md) · [**Round-8 H37–H41 (mass · lidar · graded · base-layer control)**](docs/hypotheses-round8.md) · [Sibling byte audit](docs/sibling-audit.md) · [Knowledge Base](docs/knowledge-base.md) · [Live leaderboard feed (JSON)](docs/leaderboard.json) · [Official Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

> **Latest status (2026-09-28, Round 8):** the frozen Round-8 gate **failed, so no new artifact was packaged and no weekly slot was spent** — the Round-7 file above is still the submission. The harness first reproduced Round 7 to full float64 precision (`abs_diff = 0.0` on both catalogue protocols: dense 0.24586, sparse 0.12732). Verdicts ([register and results](docs/hypotheses-round8.md) · [evidence](evidence/holdout_round8.json)): **H39** 1 m USGS 3DEP lidar scarp descriptors (fetched and hash-pinned via GitHub API from the public-domain USGS product built by sibling 7GEMSDOE) win the dense protocol 4/4 (0.24586 → 0.25326, +0.0074) but only 2/4 on the sparse protocol — catalogue-shaped skill, not new-fault skill; **H38** the metric's own marginal-inclusion mass splits the protocols in sign (3.2 % mass: dense +0.0312, sparse −0.0103), and the only real-board measurement of added mass (the sibling 0.1563 → 0.1560 pair, +10,668 px, −0.0003) sides with the sparse curve; **H40** graded emission −0.171 dense (negative, as predicted); **H37** catalogue base layer +0.515 dense but that is an artefact of a protocol whose truth *is* the catalogue — retired to a control. Leakage probe 0.0000 on every fold. Also new: a **byte-level sibling audit** ([docs/sibling-audit.md](docs/sibling-audit.md), [raw JSON](evidence/sibling-audit.json), 48 artifacts / 11 duplicate groups) that answers the two standing questions — the GEMSDOE and 5GEMSDOE sites hand out the *same* file (`7f00890a…`, 570,890 B, committed in six places across five repositories), and the 0.1560-vs-0.1563 gap is *measured* (GEMSDOE2's union added 9,430 chargeable pixels for −0.0003); plus a **metric algebra** ([evidence/metric-algebra.json](evidence/metric-algebra.json)) that turns each published score into a coverage locus and gives the marginal rule `ΔT/ΔE > 0.2·D/(1−0.2·D)` = 0.0323 at 0.1563. Leaderboard 2026-09-28: #1 DARD **0.3168**, #5 cutoff 0.2806, three rows at 0.1563 (#26–28). Irregularities still flagged: no upload receipts exist anywhere in the group, so byte → account attribution stays inference; the official `sample_submission.tif` is bit-for-bit the catalogue, not an empty raster.

---

## Direct Deliverable: Round-7 Thin-Trace + 10 m DEM Scarp Submission (Format-Validated, Not Yet Scored)

| | |
|---|---|
| **Primary GeoTIFF** | [`docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif`](docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif) (469,858 bytes) |
| **ZIP (one GeoTIFF)** | [`docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.zip`](docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.zip) |
| **All-finite fallback** | [`docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62_allfinite.tif`](docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62_allfinite.tif) — use only if primary rejected with `"Predicted values must be in range [0, 1]"` |
| **SHA-256** | `0c9199f14e625d7b2539a0a045803b74d6494ce568d185abecc193fe7e93c6f2` |
| **DrivenData note (paste verbatim)** | `12GEMSDOE R7 \| NMS-3 thin-trace on multi25+H28+H32 GBM; H32 = 12 USGS 3DEP 10 m DEM scarp channels (slope/gradient/micro-relief/one-sided asymmetry per 100 m cell) \| 5x5 exclusion 2.0% mass 103347 px \| sha256:0c9199f14e62` |
| **Provenance** | [`docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.json`](docs/downloads/12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.json) — includes the external-data declaration (USGS 3DEP tiles, SHA-256 each) |
| **Holdout evidence** | [`evidence/holdout_round7.json`](evidence/holdout_round7.json) — dense 0.24586 (4/4), sparse 0.12732 (4/4) vs incumbent multi25+H28 0.22143/0.11438 |
| **Previous archives** | [`docs/downloads/12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif`](docs/downloads/12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif) (R6, SHA-256 `8721329b55c7…`), [`docs/downloads/12GEMSDOE_r5-nms3-trace_055e9aac96b8.tif`](docs/downloads/12GEMSDOE_r5-nms3-trace_055e9aac96b8.tif) (R5) — still format-validated, superseded by R7 |

**What it is:** 103,347 predicted fault pixels — exactly 2.000 % of the 5,167,373-pixel
survey footprint — placed by greedy non-maximum suppression with a 5 × 5 exclusion
box over the multi25+H28+H32 probability field (H32 = 12 channels from the ~10 m USGS 3DEP DEM: slope max/mean/std, horizontal-gradient magnitude at 20/50/200 m, steep fraction, detrended micro-relief std/range, curvature, one-sided scarp asymmetry at two scales — per 100 m cell). Restricted to pixels the catalogue does not already capture. Values binary `{0,1}`.

**Local format verification:** one `float32` band, EPSG:32611, 100 m, 3,292 × 3,730, transform `(100, 0, 243350, 0, −100, 4508550)`, all 5,167,373 footprint pixels finite and in `[0.0, 1.0]`, all 7,111,787 outside pixels `NaN` — same convention as official `sample_submission.tif`. It
passes `core.validate()`; `tests/test_round7.py` locks the SHA-256, the value set,
the pixel count, the 5 × 5 exclusion invariant and that it differs from the R6 file.

**What it is not:** it has no DrivenData score. The standing
strongest-sibling-baseline gate is still unsatisfied, so it is not
"release-authorized"; spending a weekly slot is a human decision. The superseded
round-1..4 archive `06ca61e5` remains downloadable for comparison.


---

## The Founding Prompt & Project Directives (Read Every Session)

```text
Review the repo.     
    
Here are the results from our groups submissions, separated by ....:    
    
GEMSDOE1    
https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html    
GEMSDOE SCORE: 0.1563    
....    
https://buffedlizard55-lab.github.io/6GEMSDOE/    
6GEMSDOE SCORE: 0.0286    
....    
GEMSDOE3    
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html    
GEMSDOE3 SCORE: 0.1193    
1 · SUBMIT FIRST    
f347b70daa    
Pindrop nodes    
....    
GEMSDOE2    
https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html    
GEMSDOE2 SCORE: 0.1560    
....    
GEMSDOE3    
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html    
GEMSDOE3 SCORE: 0.0830    
2 · SUBMIT SECOND 37f9d5b855    
Pindrop catalogue-gap target SECOND SYSTEM    
....    
https://buffedlizard55-lab.github.io/GEMSDOE4/    
GEMSDOE 4 SCORE: 0.0343    
....    
GEMSDOE3    
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html    
GEMSDOE3 SCORE: 0.1152    
3 · CONTROL · UPLOAD LAST    
4e03fc9705    
Pindrop dense ridge control    
....    
https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html    
5GEMSDOE SCORE: 0.1563    
....    
7GEMSDOE SCORE: 0.1461    
....    
https://buffedlizard55-lab.github.io/8GEMSDOE/    
8GEMSDOESCORE: 0.1563    
....    
9GEMSDOE SCORE: 0.0107    
....    
10GEMSDOE SCORE:    
....    
11GEMSDOE SCORE: 0.0202    
....    
12GEMSDOE SCORE:    
....    
The following is the leaderboard for the competition:    
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/    
    
We need to figure out why we keep scoring 0.1563, are we copying the same work over and over again? we need to come up with different ideas, and not just the same idea tried a different way.    
Need to figure out why 5GEMSDOE and GEMSDOE1 have the same score. We should not be generating the same score submissions, they should all be unique.    
    
0.3049 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website. It should be unique, take unique approaches to generating a submission that can score higher than .3049.      
    
Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use. It should solve the problem of having to manually check everything ourselves and having an up to date current feed.    
    
Review the repo.     
    
The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.    
    
Our Core Values    
    
Maximize P(Win)    
“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.    
    
Own the Outcome    
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.    
    
Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.                          
    
Verify no hallucinations.        
The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.    
    
We need to focus on being able to generate a submission into the competition.      
The site should be able to generate a TIF file that is required for submission. It should be as easy as download to click a File to submit into the competition. This needs to be in the executive summary or the very beginning of the site. it should be obvious when you visit the site.    
    
I tried to submit the document that i downloaded from the site but it returned this error on the submission form:    
"Predicted values must be in range [0, 1]"    
    
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25    
    
Here is the submission page when i click submit file    
New submission    
File to submit: No file chosen    
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.    
Note (optional)    
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25    
    
Create a executive summary subpage that explains exactly how to make a submission into the contest.    
Work on the next steps from the previous sessions first.    
    
The goal of this project is to place top of the leaderboard in this competition:    
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/    
https://www.drivendata.org/competitions/306/competition-doe-gems/    
https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/    
https://www.drivendata.org/competitions/306/competition-doe-gems/data/    
Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution    
Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf    
Data source: https://gdr.openei.org/submissions/1391    
    
Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.    
    
Run this task through multiple passes.    
Pass 1: Implement the task completely and verify the result.    
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.    
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.    
    
Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project. It should be worked on in this next session or the next session. Work line by line verify everything no hallucinations.
```

---

## Executive Audit: Why Submissions Repeatedly Scored 0.1563

1. **GEMSDOE1 & 5GEMSDOE are Byte-for-Byte Identical (0.0% Difference):**
   - Both published TIFF files share the identical SHA-256 hash: `7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15` (570,890 bytes).
   - The two repositories publish the same pinned `ens12` artifact. If those published bytes were the uploaded bytes, identical public-set scoring is necessary. **Upload receipts are not present in this audit**, so the audit does not assert who uploaded which file.
2. **CORRECTED 2026-09-27: 8GEMSDOE's published file is unique and was never uploaded:**
   - The earlier claim (8GEMSDOE "unioned masked labels → same 0.1563") is withdrawn. Measured: `gems8.tif` (`b83ea0e7…`) differs from `gems1.tif` at 563,092 pixels (off-label correlation 0.076), and 8GEMSDOE's own README logs it as `BUILT-UNIQUE-UNUPLOADED` with no score claimed.
   - Three public leaderboard rows showed 0.1563 in the 2026-09-27 snapshot. The byte audit establishes the GEMSDOE1/5 published duplicate, but **cannot attribute the third row without its upload receipt**. This is intentionally recorded as an irregularity, not inferred from score rounding.
   - Staff rulings used: pixel-exact catalogue mask ([11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2), [11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)); "new fault" includes new geometry of existing systems ([11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2)).
3. **Low-score interpretation is not platform-verified:** 9GEMSDOE and 11GEMSDOE reported 0.0107 and 0.0202. Their repositories describe broader binary masks; that is **consistent with** the DTI false-positive term, but neither hidden labels nor upload receipts are available here. It is a testable diagnosis, not a proven causal attribution.
   - The 12GEMSDOE artifact has 224,173 positive pixels (4.34% of the template footprint), 163,185 of them off-catalogue, and differs from the shared file at 373,847 valid pixels (7.23%). Its format status is verified; private-label performance is unknown.

---

## 4 Candidate Geological Hypotheses Matrix

| Rank | Hypothesis & Layers | Physical Signature / Transform | Why Missing from USGS Catalogue | Holdout Result |
|---|---|---|---|---|
| **1** | **H1: Concealed Basement Step & Gravity Curvature**<br>`depth_to_base_surf` (B15), `iso_grav_anom_hg` (B18), `iso_grav_anom_vg` (B11), `cond_surf` (B17) | Normalized gradient $\|\nabla \text{dtb}\|$ and Laplacian curvature $\nabla^2 \text{dtb}$ coupled with horizontal gravity gradient ridges $\|\nabla \text{hg}\|$ and conductivity boundaries $\|\nabla \text{cond}\|$. | USGS catalogues rely on surface geomorphic scarps. Active extensional faults concealed under basin fill or playas have zero surface scarps, yet bound major geothermal grabens (e.g. McGinness Hills; Faulds & Hinz, 2015). | **+0.00420** vs baseline (won 3/4 folds) |
| **2** | **H3: Deep Magnetic Tilt-Angle Derivative**<br>`rtp` (B2), `tmi_vg` (B9), `tmi_hg` (B3), `tc` (B6) | Tilt angle $\theta = \arctan(\text{tmi\_vg} / \max(\|\text{tmi\_hg}\|, \epsilon))$ and horizontal derivative $\|\nabla \theta\|$. Peaks over vertical contact edges regardless of magnetization strength (Verduzco et al., 2004). | Hydrothermal fluid circulation along fault conduits destroys magnetite (pyritization/demagnetization) in basement rocks, preserving a subsurface magnetic boundary beneath non-magnetic alluvium. | Integrated into Multi-Physics 25 |
| **3** | **H2: Transtensional Strain Dilation Corridor**<br>`geod_2ndinv` (B4), `geod_shearrate` (B7), `geod_dilaterate` (B8), `ieq_n100a15` (B16) | Transtensional Dilation Index: $TDI = \sqrt{\text{geod\_shearrate} \cdot \max(\text{geod\_dilaterate}, 0)} \times (1 + \text{ieq\_n100a15})$. | Modern geodetic GPS strain accumulates on active crustal faults even when recurrence intervals are thousands of years and surface ruptures are absent (Siler et al., 2019). | Integrated into Multi-Physics 25 |
| **4** | **H4: Concealed Step-Over & Relay Transfer**<br>`labels.tif`, `det_elev_slope` (B19), H1 structural lineaments | Distance-dependent relay interaction tensor between overlapping en-echelon fault segments within 500 m to 2 km of mapped fault terminations. | Over 70% of Great Basin geothermal systems occur in structural stepovers / relay ramps (Faulds & Hinz, 2015). Catalogues regularly omit cross-faults in transfer zones. | Medium cost; follow-up candidate |
| **5** | **H5: 1m Lidar 3DEP Micro-Scarp Extraction (External)**<br>`1m_DEM_links.csv` (USGS 3DEP 1m DEMs) | Multiscale topographic openness, profile curvature, and 90th percentile slope downsampled from 1 m to 100 m. | Subtle alluvial scarps (<0.5 m height) are smoothed out in 100 m detrended elevation but clearly visible in 1 m lidar hillshades. | Source: USGS 3DEP AWS S3 (free/official). Deferred due to sandbox disk/egress. |

---

## 4-Fold Spatially-Blocked Holdout Validation Results

Protocol: 512-px spatial blocks, 12-px collar exclusion, fixed seed 12027, official Distance-Weighted Tversky metric ($DTI, \alpha=0.2, \beta=0.8, R=300\text{ m}$):

| Spatial Block Fold | Baseline Raw 19 | Candidate H1 (23 feats) | Candidate Multi-Physics 25 | Paired Gain (25 vs Baseline) |
|---|---|---|---|---|
| **Fold 0** | 0.11201 | 0.11350 | **0.11902** | <span style="color:#34d399; font-weight:700;">+0.00701</span> |
| **Fold 1** | 0.11651 | 0.11489 | **0.11871** | <span style="color:#34d399; font-weight:700;">+0.00220</span> |
| **Fold 2** | 0.09938 | **0.11018** | 0.10289 | <span style="color:#34d399; font-weight:700;">+0.00351</span> |
| **Fold 3** | 0.12309 | **0.12921** | 0.12916 | <span style="color:#34d399; font-weight:700;">+0.00607</span> |
| **Mean DTI Score** | **0.11275** | **0.11695** | **0.11744** | <span style="color:#34d399; font-weight:800;">+0.00469 (100% Fold Win Rate)</span> |

**Round-1 gate (historical diagnostic, demoted 2026-09-27):** Multi-Physics Candidate 25 won across 4 out of 4 spatial folds (+0.00469 mean DTI improvement) on the *unmasked* screen. Because that screen scored against dense known faults without the official pixel-exact mask (uniform random 6% beat every learned arm), it cannot rank discovery skill. The archived TIFF is format-valid but **not release-authorized**: multi25 has a masked-protocol gain over raw19 (+0.00469, 3/4 folds, probe 0.0000), while reproduction of a strongest sibling baseline remains outstanding. H11 failed the next frozen test. See [Round 2](docs/hypotheses-round2.md), [Round 3](docs/hypotheses-round3.md), [masked results](docs/holdout_masked.json), and [audit corrections](docs/session-review.md#6-round-2-audit-corrections--methodological-fixes-2026-09-27).

---

## Round 5 — Emission Geometry, Corrected Layer Identity, and Four New Candidates

Full register: [`docs/hypotheses-round5.md`](docs/hypotheses-round5.md). Preregistered
before the feature code; identity checks and the emission diagnostic ran first and
are reported verbatim in the register.

### 5.1 Reproduction first (no hallucination check on our own repo)

`scripts/cache_fold_models.py` re-trained the frozen masked-holdout arms and matched
`evidence/holdout_masked.json` **exactly on every fold of every arm**:

| Arm | Reproduced mean DTI | Committed | Exact per fold |
|---|---|---|---|
| raw19 | 0.08602428869798472 | 0.08602 | yes |
| multi25 | 0.09071277311870418 | 0.09071 | yes |
| multi30 | 0.08888636948563039 | 0.08889 | yes |
| random02 | 0.1378794777374697 | 0.13788 | yes |

`multi25_h15` also reproduced the Round-4 value 0.09364 in `holdout_round5.py`, and
`build_round4_features.py` / `build_candidate_features.py` regenerated their committed
sidecars byte-identically.

### 5.2 The defect: top-*k* emission wastes most of its mass

The official metric credits a truth pixel with `max` over its 5 × 5 (300 m) cell, so a
second prediction inside that cell adds false-positive mass and **zero** true-positive
credit. Every round 1–4 arm used top-*k* by probability. Fixing only the emission
geometry — greedy non-maximum suppression, Chebyshev radius 2, deterministic
tie-break — with the identical model and features:

| Protocol (frozen masked spatial holdout, mean of 4 folds) | top-*k* @ 2 % | NMS-3 @ 2 % | Ratio |
|---|---:|---:|---:|
| Dense truth (truth = full catalogue) | 0.09071 | **0.22138** | 2.44× |
| Sparse truth (20 % of truth components, seed 4242+f) | 0.04489 | **0.11178** | 2.49× |
| Off-catalogue candidates only (strictest real-scoring analogue) | 0.06759 | **0.19380** | 2.87× (4/4 folds) |

Coverage at identical emitted mass (≈23 k px/fold): top-*k* credits 7.6–15.0 % of truth
pixels, NMS-3 credits 24.6–29.1 %. Evidence:
[`round5-emission-probe.json`](docs/round5-emission-probe.json),
[`round5-offcatalogue-check.json`](docs/round5-offcatalogue-check.json),
[`holdout_round5.json`](docs/holdout_round5.json).

### 5.3 Corrected layer identity: `tc` (B5) is a depth surface, not a tilt angle

Measured on the official raster: `tc` is **strictly positive**, median **18.479**, max
**88.57**, and correlates **−0.0012** with |tilt angle| computed from B8/B2. A tilt
angle is bounded by ±π/2 radians. The official problem description lists "the
**top-of-crustal magnetic source depth estimate**" among the supplied magnetics. Rounds
1–4 followed the raster band description ("Tilt angle or total curvature"), which is why
H18 (`tc` lineaments) was rejected 0/4 folds. Evidence:
[`round5-identity-checks.json`](docs/round5-identity-checks.json) (C3).

Also settled by C2: `iso_grav_anom_slope` (B4) is **not** the magnitude of a gradient
whose component is `iso_grav_anom_hg` (B17) — |B17| exceeds B4 at 387,553/400,000
sampled pixels — so no orthogonal gravity-gradient component is recoverable.

### 5.4 Four new geological candidates — preregistered, built, tested, not adopted

| Rank | Candidate | Layers | Signature | Gate result (with NMS-3 emission fixed) |
|---|---|---|---|---|
| 2 | **H20 magnetic-basement relief step** | `tc` (B5) | ‖∇(smooth₅ tc)‖ | 2/4 dense, 2/4 sparse — **not adopted** |
| 3 | **H21 two-depth-surface step coincidence** | `tc` (B5) × `depth_to_base_surf` (B14) | axial agreement of the two gradient directions × min of the two robust edge strengths | 0/4 dense, 2/4 sparse — **not adopted** |
| 4 | **H22 local singularity exponent** | `tc` (B5) | \|α − 2\| from log-mean vs log-window over w = 1…16 (Cheng-style multifractal singularity) | 3/4 dense, 2/4 sparse — **not adopted** (best of the four) |
| 5 | **H23 asymmetric-step (monocline) detector** | `depth_to_base_surf` (B14) | \|f − b\| / (\|f − c\| + \|b − c\|) along 4 axes — step polarity, which every symmetric gradient/curvature transform ignores | 2/4 dense, 2/4 sparse — **not adopted** |

All four are mechanism-distinct from every round-1..4 channel (max |corr| 0.153 /
0.342 / 0.388 / 0.014 per `evidence/round5-identity-checks.json` C4). With the emission policy fixed, **all arms land within ±0.0008
(dense) and ±0.0018 (sparse) of the multi25 reference** — an order of magnitude below
the emission effect. That is the actionable finding: the decision layer, not the
feature list, is where the score is being lost.

### 5.5 Irregularities flagged for manual review

1. **`tc` band description contradicts the official layer list** (§5.3). Worth a forum post.
2. **`training_features.tif` missing data is the float32 most-negative sentinel
   `−3.4028235e+38`, not NaN** (C1). An unmasked read puts `−3.4e+38` into model inputs
   and output rasters — a sufficient cause of the `"Predicted values must be in range
   [0, 1]"` rejection. Band `tc` alone carries 3,073 sentinel pixels inside the footprint.
3. **The dense-catalogue local protocol is an inverted selector** (random 2 % beats every
   learned arm). Rounds 1–4 rankings measured on it are weak evidence; recorded, not
   silently reinterpreted.
4. **GEMSDOE2 0.1560 vs 0.1563** remains unresolved; still no upload receipts anywhere.
5. **The official reference solution is a U-Net with Monte-Carlo CV** (verified from
   `drivendataorg/gems-prize-reference-solution` README), while every arm here is a
   per-pixel GBM. The model-class gap is the largest unexplored lever after emission
   geometry, and it needs a GPU.

## Reproduce Locally (CPU)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download and assemble competition rasters
bash scripts/download_competition_data.sh
python scripts/prepare_data.py

# 3. Build the auditable 30-channel feature cube (19 raw + 6 round-1 + 5 round-2)
python scripts/build_candidate_features.py

# 4. Run leakage-safe validation (no submission slot spent)
python scripts/holdout_masked.py
python scripts/holdout_trace.py
python scripts/build_h11_drainage_feature.py
python scripts/holdout_round3_h11.py

# 5. Round 5: cache the frozen fold models (also reproduces the round-2 numbers),
#    then measure emission geometry and run the preregistered gate
python scripts/cache_fold_models.py
python scripts/round5_identity_checks.py
python scripts/build_round5_features.py
python scripts/round5_emission_probe.py
python scripts/round5_offcatalogue_check.py
python scripts/holdout_round5.py

# 6. Generate the Round-5 format-validated submission GeoTIFF (cannot authorize release)
python scripts/generate_nms_submission.py

# 7. Round 6 (build order matters for the distinctness sidecars: r4 -> r5 -> r6)
python scripts/build_round4_features.py
python scripts/build_round6_features.py
python scripts/holdout_round6.py
python scripts/generate_nms_submission_r6.py

# 8. Round 7: fetch the hash-pinned 10 m DEM channels from the sibling tag (GitHub API only),
#    build the 12-channel cube + distinctness sidecar, run the gate, package
python scripts/fetch_dem10_channels.py        # needs `gh auth` (reads buffedlizard55-lab/GEMSDOE10 tag ext/dem10-36343078537)
python scripts/build_round7_features.py
python scripts/holdout_round7.py              # ~14 min on 2 CPUs; writes evidence/holdout_round7.json
python scripts/generate_nms_submission_r7.py  # refuses to run unless gate.passed is true

# 9. Leaderboard feed (network needed; runs on GitHub Actions twice daily, commits only on change)
python scripts/fetch_leaderboard.py

# 10. Run the full test suite
pytest
```

---

## Primary Official Sources

1. **DrivenData GEMS Challenge:** [https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)
2. **Problem & Metric Equations:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
3. **Official Rules (OSTI 96647):** [https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
4. **Scoring Clarification (Chris K, Staff):** [https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2)
5. **USGS GeoDAWN Survey:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
6. **DOE GDR Submission 1391 (INGENIOUS):** [https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)
7. **Faulds & Hinz (2015), GRC Transactions:** Structural Controls on Great Basin Geothermal Systems.
8. **Verduzco et al. (2004), The Leading Edge:** Tilt derivative for structural lineament mapping.
