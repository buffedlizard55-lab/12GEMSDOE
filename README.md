# 12GEMSDOE — Geothermal Fault Discovery & Submission Hub

> **Read this README every session.** Maximize P(Win): prioritize scientifically defensible discovery and validation over leaderboard churn. Own the Outcome: follow data, model, artifact and published result end to end. Line-by-line verification from official sources. Zero hallucinations.

[Workbench](https://buffedlizard55-lab.github.io/12GEMSDOE/) · [Executive Submission Guide](https://buffedlizard55-lab.github.io/12GEMSDOE/executive-summary.html) · [Evidence & Sibling Audit](docs/session-review.md) · [Round-1 Hypotheses](docs/hypotheses.md) · [Round-2 Hypotheses H6–H10](docs/hypotheses-round2.md) · [Round-3 H11–H14](docs/hypotheses-round3.md) · [Round-4 H15–H19](docs/hypotheses-round4.md) · [Official Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

> **Latest status (2026-09-27, Round 4):** Five candidates H15–H19 were preregistered before coding ([register](docs/hypotheses-round4.md)); H19 (Sentinel-2 alteration) deferred — source verified free/open but S3 blocked in-sandbox. The PRIMARY **H15 coincident multi-physics boundary alignment passed as a research signal**: multi25+H15 = 0.09364 vs multi25 = 0.09071 (**+0.00293, 3/4 folds**, probe 0.0000). H16/H17 not passing; H18 rejected (0/4); H10 harmful all folds (−0.00490, drop it); H6′ spatial arm proven degenerate-by-construction while its terminal mechanism re-validated at 2.80× random. **No H15 GeoTIFF was built and no weekly slot was spent** — the strongest-sibling-baseline gate is still outstanding. Leaderboard re-fetched: #1 DARD **0.3168**.

---

## Direct Deliverable: Format-Validated Candidate (Release Gate Pending)

- **GeoTIFF File:** [`docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif`](docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif) (1,205,044 bytes, 1.20 MB)
- **ZIP File:** [`docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.zip`](docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.zip) (1,131,737 bytes, 1.13 MB)
- **SHA-256 Hash:** `06ca61e5c6a3e55eaf40228d97054a35af1187be9c98e0ef95d996f9919efc6b`
- **Pre-formatted DrivenData Note:**  
  `12GEMSDOE-v1 | Multiphysics Basement-Curvature + Tilt-Angle + Strain-Dilation | format-validated | sha256:06ca61e5c6a3`
- **Format verification (local):** Single-band `float32`, EPSG:32611, 100 m resolution, 3,292 × 3,730, finite in $[0.0, 0.95]$ inside the 5,167,373-pixel template footprint and `NaN` outside the 7,111,787-pixel footprint. It passes `core.validate()` against the downloaded official template. This is not a claim that DrivenData has accepted or scored the file.

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

# 5. Generate a format-validated research GeoTIFF (this cannot authorize release)
python scripts/generate_submission_tif.py --name multi25-repro

# 6. Run the full test suite
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
