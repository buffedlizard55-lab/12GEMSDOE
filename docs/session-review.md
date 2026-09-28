# Evidence-Led Session Review • 27 September 2026

> **Core Values:** Maximize P(Win) · Own the Outcome · Zero Hallucinations · Line-by-Line Verification.

---

## 1. Executive Findings: Why Submissions Repeatedly Scored 0.1563

We conducted an independent, byte-level and pixel-by-pixel audit of historical group submissions (`gems1.tif`, `gems5.tif`, `gems8.tif`; see `evidence/identity.json`, recomputed NaN-safe by `scripts/audit_submissions.py`):

1. **GEMSDOE1 and 5GEMSDOE are Byte-for-Byte Identical (0 differing pixels):**
   - Both published TIFF files share the identical SHA-256 hash: `7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15`.
   - File size: exactly 570,890 bytes; positive pixel count: exactly 172,974; valid survey pixels: exactly 5,167,373.
   - **What this proves and does not prove:** GEMSDOE1 and 5GEMSDOE publish the same `ens12` artifact. If these published bytes were the submitted bytes, equal public-set scores necessarily follow. This audit has no DrivenData upload receipts, so it does **not** identify an account's uploaded file or explain the third 0.1563 row from score rounding.
2. **CORRECTED 2026-09-27: 8GEMSDOE's published file is unique and was never uploaded.**
   - The round-1 review claimed 8GEMSDOE "unioned masked labels onto the 0.1563 base, hence the same score." That claim is **withdrawn**. Measured facts: `gems8.tif` (SHA-256 `b83ea0e7…`) differs from `gems1.tif` at 563,092 pixels with off-label correlation of only 0.076 — it is not a union of the base with labels. 8GEMSDOE's own README logs it as `BUILT-UNIQUE-UNUPLOADED` with "no new DrivenData score verified, none claimed."
   - The `build_hedge_v2.py` "weakly dominant upgrade" rationale (emitting on catalogue pixels "can only add TP") is additionally vacuous: new faults are defined as pixels *not* captured by the catalogue ([11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2)), so catalogue pixels cannot coincide with new-fault truth.
   - **Irregularity retained:** the third 0.1563 row cannot be byte-attributed without an upload receipt. 8GEMSDOE reports that GEMSDOE2's recall arm matches `7f00890a`, while GEMSDOE2's reported 0.1560 differs by 0.0003. Both claims cannot describe the same fixed public-set upload; the underlying upload or reported score differs somewhere. It remains unresolved.
3. **Why Low Scores Occurred in 6GEMSDOE (0.0286), 4GEMSDOE (0.0343), 9GEMSDOE (0.0107), 11GEMSDOE (0.0202):**
   - 11GEMSDOE's repository reports a 6.6% binary mask (over 340,000 pixels). With sparse new-fault truth, a broad prediction field is **consistent with** a large DTI false-positive term; hidden labels are unavailable, so the exact false-positive count and causality cannot be verified here.
   - The DTI formula makes this a plausible diagnosis, not proof: a broad mask can accrue an $0.2\cdot FP_w$ denominator contribution.
   - **12GEMSDOE status:** the archived multi25 raster has 224,173 active pixels and is format-valid. Its private score and superiority to a strongest sibling baseline are unknown; it is not a release-authorized solution.

---

## 2. Root Cause of the Submission Form Rejection: "Predicted values must be in range [0, 1]"

When users encountered the error `"Predicted values must be in range [0, 1]"` on DrivenData:
- **Evidence limit:** the rejected file and DrivenData parser log were not retained, so the error text alone does not identify its exact cause. The official page requires one float32 band with values in $[0,1]$ and data outside bounds null or `NaN`; the local checks below catch common format violations but cannot prove why a past upload was rejected.
- **Enforced Invariants in 12GEMSDOE:**
  - Data type: strictly single-band 32-bit float (`float32`).
  - Spatial reference: EPSG:32611, 100 m resolution, 3,292 columns $\times$ 3,730 rows, transform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`.
  - Survey footprint: All 5,167,373 valid pixels are strictly finite and strictly in $[0.0, 0.95]$.
  - Outside survey footprint: All 7,111,787 background pixels are strictly `NaN`.
  - Re-read and verified from disk using `core.validate()`.

---

## 3. Top Candidate Validated on Spatially-Blocked Holdout

Under the frozen 4-fold spatially-blocked cross-validation protocol (512-px spatial blocks, 12-px collar exclusion, fixed seed 12027):

| Method / Arm | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Mean DTI | Paired Win Rate | Status |
|---|---|---|---|---|---|---|---|
| **Raw 19 Baseline** | 0.11201 | 0.11651 | 0.09938 | 0.12309 | 0.11275 | Baseline | Completed |
| **H1 Basement Step (23 feats)** | 0.11350 | 0.11489 | 0.11018 | 0.12921 | 0.11695 | 3 / 4 folds (75%) | Holdout Win (+0.00420) |
| **Multi-Physics 25 (H1+H2+H3)** | **0.11902** | **0.11871** | **0.10289** | **0.12916** | **0.11744** | **4 / 4 folds (100%)** | **Top Candidate (+0.00469)** |
| **Random 6% Control** | 0.22139 | 0.20798 | 0.19802 | 0.17541 | 0.20070 | Local artifact | Evaluated against full known labels |

**Historical diagnostic only:** Multi-Physics 25 beat raw19 in this *unmasked* known-fault screen, but the random 6% arm outperformed every learned arm. This screen therefore cannot authorize discovery or release. The archived `06ca61e5` field is locally format-validated, not a released submission; the masked protocol and strongest-sibling-baseline gates remain controlling.

---

## 4. Primary Official Source Ledger

| Assertion / Claim | Official Primary Source | Verification / Provenance |
|---|---|---|
| Target is faults indicative of geothermal resources, not proven vents | [DrivenData GEMS Problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Quoted directly; expert-labeled Quaternary fault dataset |
| Known USGS/INGENIOUS faults excluded from scoring and penalties | [DrivenData Forum Post 11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) | Chris K (Staff): "Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from evaluation" |
| DTI parameters: $\alpha=0.2, \beta=0.8, R=300\text{ m}$ triangular kernel | Same problem description page | Exact formula implemented and tested against brute-force verification |
| Single float32 band, EPSG:32611, 100 m, null or NaN outside bounds | Same problem description page | Verified locally against official `sample_submission.tif`; the repository selects NaN as a stricter local convention. |
| Total prize pool: $300,000 ($50k Phase 1 + $250k Phase 2) | [OSTI Rules PDF 96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Rules PDF states the split; it directs competitors to the competition website for the current timeline. |
| Leaderboard snapshot high: 0.3168 | [DrivenData Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Re-fetched 2026-09-27: Rank #1 DARD at 0.3168 (earlier same-day snapshot 0.3049); 0.1563 × 3 at #26–28. Time-stamped snapshot, not a live claim. |
| Great Basin geothermal structural context | [DOE GDR INGENIOUS compilation](https://gdr.openei.org/submissions/1391) | The public GDR page inventories relevant datasets. The numerical “over 70%” claim is not reasserted here because this session did not inspect the primary Faulds & Hinz text. |

---

## 5. Artifact Identity & Integrity Audit

- **12GEMSDOE format-validated candidate file (not release-authorized):** `docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif`
  - SHA-256: `06ca61e5c6a3e55eaf40228d97054a35af1187be9c98e0ef95d996f9919efc6b` (1,205,044 bytes)
  - Suggested note: `12GEMSDOE-v1 | Multiphysics Basement-Curvature + Tilt-Angle + Strain-Dilation | format-validated | sha256:06ca61e5c6a3`
  - Positive pixels: 224,173 (4.34% of survey footprint), of which 60,988 are known-catalogue pixels at 0.95 (masked, score-neutral) and 163,185 are off-catalogue structural predictions (3.16% of footprint); values in $[0.0, 0.95]$; NaN outside footprint.
- **Historical shared published artifact:** `7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15` (570,890 bytes, published by GEMSDOE1 and 5GEMSDOE). Upload-account linkage is not in the evidence set.
- **Pixel Difference (corrected 2026-09-27):** 12GEMSDOE differs from the historical shared artifact at **373,847 pixels (7.23% of valid footprint)** with off-label correlation 0.073 — genuinely novel field. (Round-1 docs stated 224,173/4.34%, which is the positive count, not the diff count.)

---

## 6. Round-2 Audit Corrections & Methodological Fixes (2026-09-27)

Recorded here rather than silently edited, so the review trail stays honest:

1. **`evidence/identity.json` pairs-table bug (FIXED):** the round-1 table compared full rasters with `!=`, where background `NaN != NaN` counted every one of the 7,111,787 background pixels as "different" — reporting byte-identical files as 57.9% different while the conclusion text correctly said 0.0%. `scripts/audit_submissions.py` now compares NaN-safely, adds `same_bytes`/`same_mask` fields and the `12gems` artifact; `tests/test_round2.py::test_identity_audit_self_consistent` locks the invariant (same bytes ⇒ pixel-equal, 0 diffs).
2. **8GEMSDOE "masked-labels" explanation (WITHDRAWN, see §1.2):** replaced with the verified unique-and-unuploaded account above.
3. **Missing feature-build script (CLOSED):** round-1 `experiment_v2.py` loaded `data/candidate-screen-features.npy`, whose generating code was never committed — the published +0.00469 was not reproducible from this repo. `scripts/build_candidate_features.py` now builds all 30 channels (19 raw + 6 round-1 + 5 round-2) from pinned rasters with exact definitions, median imputation of the 3,073 NaN-inside pixels, and a hash sidecar (`evidence/feature-build.json`). Round-1 numbers are kept as historical reports; all new claims use fresh cubes.
4. **Unmasked holdout selection signal (FIXED):** the round-1 screen scored against dense known faults without the official mask, so uniform random 6% (≈0.20) beat every learned arm (≈0.11) — an inverted selector that cannot rank discovery skill. `scripts/holdout_masked.py` emulates official scoring (pixel-exact catalogue mask on FP, leakage probe ≈ 0 required, binary top-2% emission). Consequence: round-1's "+0.00469, won 4/4 folds" gate is **demoted to a historical diagnostic**, not a release qualification; the archived submission file remains format-valid, but its skill gate must be re-earned on the masked protocol and against a strongest sibling baseline.
5. **Preregistration gate relaxation (DISCLOSED):** `evidence/preregistered-hypotheses.md` required beating the *strongest reproducible sibling baseline* before any release; round 1 released on beating *raw 19* only. No sibling baseline (e.g. re-trained `ens12`-class model or 11GEMSDOE structural arm) has been reproduced under our protocol. This gap is now explicit in the round-2 release rule, which additionally requires masked-protocol superiority.
6. **GEMSDOE2 0.1560 vs 0.1563 (UNRESOLVED):** 8GEMSDOE's byte audit says GEMSDOE2's recall arm matches `7f00890a`, yet the reported scores differ by 0.0003. Same bytes cannot score differently on a fixed public test set; either the uploaded file or the reported figure differs. Flagged for manual review, not papered over.
7. **`generate_submission_tif.py` comment overclaim (CORRECTED in docs):** setting known-catalogue pixels to 0.95 was described as potentially "increasing TP on catalogue revisions/splays." Catalogue pixels are pixel-exact masked ([11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)); the 0.95 values are score-neutral. Catching splays requires predicting pixels *adjacent* to traces (see H6), not on them.
8. **Round-1 H3 band-list typo (FIXED in round-2 docs):** the submission manifest listed tilt-derivative bands as "2, 8, 3, 6" (B8 is dilaterate); the transform uses B2/B9/B3 (rtp, tmi_vg, tmi_hg). Manifest JSON is preserved byte-identical for provenance; the correction lives here and in `docs/hypotheses-round2.md`.

---

## 7. Round-2 Validation Results (2026-09-27)

Five new mechanism-distinct candidates (H6–H10, [register](hypotheses-round2.md)) were preregistered, built from pinned rasters (`scripts/build_candidate_features.py` → 30-channel cube, sidecar `evidence/feature-build.json`), and tested without spending a submission slot:

- **Masked spatial holdout** (official pixel-exact mask, leakage probe 0.0000, binary top-2%): multi25 0.09071 beats raw19 0.08602 (+0.00469, 3/4 folds); multi30 (+H8/H9/H7/H10) 0.08889 does **not** beat multi25 (−0.00183, 2/4) → bundle rejected as an upgrade.
- **H6 geometric completion:** loses to equal-mass random on whole-component holdout (0.1127 vs 0.1882); gate ablation shows the p70 gate hurts (−0.014 vs ungated). Preregistered gated form **rejected**.
- **Terminal-truncation holdout** (direct extension simulator, 6,312 hidden terminal pixels): straight 5px rays 0.2920 (2.6× random) > ungated curved+splay 0.1773 (1.6×) > gated H6 0.1472 (1.3×) > random 0.1133. The *mechanism* validates in its claimed regime; the winning form was a control arm, so it becomes the **round-3 lead (H6′)** rather than a release — no post-hoc promotion.
- **Decision:** no new submission file; `06ca61e5` remains a format-validated archive, not a release authorization; multi25's masked win (+0.00469, 3/4) is only a partial gate. Full tables: [hypotheses-round2.md](hypotheses-round2.md#measured-results-2026-09-27).


---

## 8. Round-3 H11 result (2026-09-27)

Four new candidates were registered in [the Round-3 register](hypotheses-round3.md) before coding. H11 uses a label-free drainage tangent/bend/alignment transform on supplied `det_elev` and `det_elev_slope`; H12–H14 require official external resources that this sandbox could not transfer over HTTPS, so they are explicitly deferred rather than treated as available.

The frozen H11 test ran against multi25 with the same masked spatial protocol: multi25+H11 scored **0.08650** versus multi25 **0.09071**, winning 1/4 folds (mean paired difference **−0.00421**; leakage probe 0.0000 in all folds). It fails the preregistered gate; no H11 GeoTIFF and no DrivenData slot were used. See [`evidence/holdout_round3_h11.json`](../evidence/holdout_round3_h11.json) for all components.

---

## 9. Round-4 validation results (2026-09-27)

Five candidates H15–H19 were preregistered in [the Round-4 register](hypotheses-round4.md) before coding, with H19 (Sentinel-2 alteration) honestly deferred: its source is verified free/open ([AWS Open Data Registry](https://registry.opendata.aws/sentinel-2/), L2A no-account S3 access) but S3 HTTPS is blocked in this sandbox (verified 000), leaving GitHub-runner transport as the only viable path. Four label-free channels were built (`scripts/build_round4_features.py`, output `6e3d48cc85d2…`, cross-corr ≤ 0.17) and tested once on the frozen masked spatial holdout plus the terminal simulator:

- **PRIMARY H15 (coincident multi-physics boundary alignment): PASSED as a research signal** — multi25+H15 0.09364 vs multi25 0.09071 (**+0.00293, 3/4 folds**; deltas +0.00328/+0.00589/+0.00910/−0.00657; probe 0.0000). Gains concentrate on folds 0–2; fold 3 reverses. H15 standalone is weak (0.0266), so the gain is interaction-driven. No H15 GeoTIFF was built and no weekly slot was spent: the standing strongest-sibling-baseline gate and independent final gates remain unsatisfied.
- **H16 (+0.00065, 2/4) and H17 (+0.00119, 1/4): not passing.** H18 rejected (0/4, −0.00573) — `tc`'s verified independence from tilt did not translate to skill.
- **Round-2 limitation closed:** no single multi30 channel passes alone (best H9x +0.00124 1/4, H7 +0.00120 2/4); H8 volatile (2/4, mean −0.00103); **H10 harmful on all 4 folds (−0.00490)** — drop from future bundles.
- **H6′ spatial arm degenerate by construction** (paired 0.00000 exact): 5 px rays from endpoints ≥13 px from any test region can never enter it (verified 0/4 folds), and the 3 px virgin exclusion never binds across the 12 px collar. Lesson recorded: no sub-collar train-trace geometry can be tested on the collar-separated spatial holdout. The terminal simulator reproduces Round 2 bit-for-bit on the mechanism arm (rays 0.2920284167756428 exact; 2.80× the correctly-massed random control 0.10447), prospectively re-validating short straight tip rays with no release eligibility attached.
- **Leaderboard (re-fetched 2026-09-27):** #1 DARD **0.3168** (was 0.3049); 0.1563 × 3 (#26–28 `extradr19`, `SDCF9`, `smashi34`), corroborating the same-bytes diagnosis pattern without proving upload linkage. Sibling intelligence adopted: GEMSDOE10 H21 catalogue-diff decisive negative (labels *are* the current public catalogue), H20 10 m DEM released (+0.014), H19 thin-emission rejected, 11GEMSDOE-H1 strain coherence rejected, 7GEMSDOE-H9 radiometrics closed — none re-proposed here.

---

## 10. Round-5 session record (2026-09-27)

What was done, in order, with the command or file that proves each line.

1. **Data blocker closed.** `bash scripts/download_competition_data.sh` fetched all five
   `training_features.tif` parts plus `existing_faults.tif` and `example_submission.tif`
   from the pinned team bridge via the GitHub Contents API (revision
   `cceebbdcf9a7d2890bb0665defcb54dfc66ae452`) and `scripts/prepare_data.py` verified all
   three canonical rasters against their SHA-256 pins. `data/` stays git-ignored.
   **Correction to the previous sessions' standing note:** data placement is no longer a
   blocker in this environment; the earlier "run this on any unrestricted machine"
   instruction is superseded.
2. **Bit-exact reproduction of the frozen holdout** (`scripts/cache_fold_models.py`):
   raw19 `0.08602428869798472`, multi25 `0.09071277311870418`, multi30
   `0.08888636948563039`, random02 `0.1378794777374697` — every fold of every arm matches
   `evidence/holdout_masked.json` exactly. `build_candidate_features.py` and
   `build_round4_features.py` also regenerated their committed sidecars byte-identically
   (`git status` clean after each run).
3. **The reproduction exposed the defect.** random02 (0.13788) beats every learned arm on
   the protocol that gated rounds 2–4. Diagnosed analytically from the official metric
   (TP is a per-truth-pixel `max` over a 5 × 5 cell) and then measured
   (`scripts/round5_emission_probe.py`): 5 × 5 NMS emission beats top-*k* by 2.44×
   (dense), 2.49× (sparse) and 2.87× (off-catalogue, 4/4 folds).
4. **Identity checks before hypotheses** (`scripts/round5_identity_checks.py`): the
   float32 most-negative sentinel in `training_features.tif` (C1); B4/B17 are not a
   magnitude/component pair (C2); `tc` is a depth surface, not a tilt angle (C3); all four
   new candidates are mechanism-distinct (C4).
5. **Four geological candidates preregistered, built, tested, not adopted**
   (`docs/hypotheses-round5.md`, `scripts/build_round5_features.py`,
   `scripts/holdout_round5.py`). With the emission policy fixed, every arm is within
   ±0.0008 (dense) / ±0.0018 (sparse) of the multi25 reference. Leakage probe 0.0000 on
   every fold of every protocol.
6. **New format-validated artifact** (`scripts/generate_nms_submission.py`):
   `12GEMSDOE_r5-nms3-trace_055e9aac96b8.tif`, SHA-256
   `055e9aac96b89b9a1d8fca8005778733039ed79f1165bb8cdd46dcfc51d6f53d`, 103,347 emitted
   pixels (2.000 % of the footprint), binary `{0, 1}`, NaN outside, plus an all-finite
   fallback variant and a single-GeoTIFF zip. `core.validate()` passes; `pytest` is green
   at 36 tests.
7. **No DrivenData submission slot was spent**, and no claim in this document attributes a
   leaderboard score to an artifact.

### Limitations carried into the next session

* **No upload receipts exist**, so the byte-level duplicate finding for GEMSDOE1/5 still
  cannot be tied to a specific account's upload.
* **The strongest-sibling-baseline gate is still unsatisfied**: no sibling model has been
  reproduced under our protocol, so nothing here is "release-authorized".
* **Local truth is the known catalogue**, used as a proxy for expert-mapped new faults.
  The 20 %-thinned variant is a sensitivity check, not a reproduction of the real truth.
  Transfer magnitude of the emission gain is unknown until one scored submission.
* **Model class**: the official reference solution is a U-Net with Monte-Carlo CV; every
  arm here is a per-pixel GBM. Training one needs a GPU (this sandbox is 2 CPU).
* **External data** (3DEP 1 m/10 m DEMs, Sentinel-2, ComCat) is still unreachable from
  this sandbox; the GitHub-runner bridge pattern is the only demonstrated transport.
* **Budget transfer risk**: the 2 % emission mass was selected on folds 0–1 of a
  catalogue-density proxy. If the real new-fault truth is far sparser, the optimal mass is
  lower; the marginal condition `p > 0.2 · DTI` in the Round-5 register is the rule to
  re-derive it with, not a free parameter to sweep post hoc.

---

## 11. Round-6 session record (2026-09-28)

What was done, in order, with the command or file that proves each line.

1. **Preregistered five new mechanism-distinct hypotheses H25–H29 BEFORE coding** (`docs/hypotheses-round6.md`). Ranking by expected DTI gain ÷ cost: H25 seismic proximity (B10 first use), H26 gravity-slope curvature (B5+B12), H27 conductivity anisotropy (B17), H28 magnetic texture variance (B1), H29 grav-mag decorrelation (B13×B2). External H30 1m DEM (USGS 3DEP) and H31 Sentinel-2 L2A verified free/open via official registries but transport blocked.
   - Official sources re-verified: problem description https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (target = faults indicative of geothermal, not proven vents), about page https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/ (hidden faults require geophysics), leaderboard https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ (#1 DARD 0.3168 2026-09-28), rules PDF https://docs.nlr.gov/docs/fy26osti/96647.pdf ($300k), mask clarification https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2 (pixel-exact), new geometry https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2, Faulds & Hinz https://www.osti.gov/servlets/purl/1724109, QFFD https://www.usgs.gov/programs/earthquake-hazards/science/quaternary-fault-and-fold-database-united-states, GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and, GDR https://gdr.openei.org/submissions/1391, reference U-Net https://github.com/drivendataorg/gems-prize-reference-solution, 3DEP https://registry.opendata.aws/usgs-lidar/ + https://portal.opentopography.org/raster?opentopoID=OTNED.012021.4269.3, Sentinel-2 https://registry.opendata.aws/sentinel-2-l2a-cogs/.
2. **Built 5-channel cube** (`scripts/build_round6_features.py`, output SHA-256 `9ccc07d95d3128c3211df6c05633cc25d91a3712e41cd30d09bfc500b0f429eb`, shape 3730×3292×5, float32, label-free, median-imputed). Distinctness measured on 400k random valid pixels: H25 max|corr| 0.4301 vs geod_shearrate, H26 0.336 vs |grad iso_grav_anom_hg|, H27 0.339 vs |grad cond|, H28 0.384 vs tmi_hg, H29 0.120 vs intersection density — all <0.50 per preregistered rule. Initial H26 design correlated 0.86 with det_elev_slope and was revised to iso_grav_anom_slope curvature + relief to achieve distinctness.
3. **Re-cached fold models** (`scripts/cache_fold_models.py`): raw19 0.08602, multi25 0.09071, random02 0.13788 exact per fold vs `evidence/holdout_masked.json`; multi30 0.08728 vs 0.08889 (minor drift due to rebuild, not used as gate).
4. **Frozen masked holdout NMS-3 @2%** (`scripts/holdout_round6.py`): 4 folds, 512px blocks, 12px collar, seed 12027, official pixel-exact catalogue mask on FP, leakage probe 0.0000 every fold, both truth protocols (dense catalogue, sparse 20% thinned seed 4242+f). Results:
   - Dense: multi25 0.22138, H28 0.22143 (3/4), H27 0.22184 (2/4), H26 0.22067 (2/4), H25 0.21568 (1/4), H29 0.22138 (1/4), H15 0.22104 (1/4)
   - Sparse: multi25 0.11178, H28 0.11438 (3/4, +0.0026), H25 0.11179 (3/4), H26 0.11235 (1/4), H27 0.11149 (2/4), H29 0.11182 (1/4), H15 0.11241 (2/4)
   - Gate: H28 is the ONLY arm beating multi25+NMS on ≥3/4 folds on BOTH protocols. H25 passes sparse 3/4 but dense 1/4. Emission gate NMS vs topk passes both (dense 0.22085 vs 0.09644, sparse 0.10882 vs 0.04345).
5. **New artifact** (`scripts/generate_nms_submission_r6.py`): `12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif`, SHA-256 `8721329b55c72635803cca27414f3d0ffe4705f48285de0dc7c29d6fd3eb90d3`, 103,347 px (2.000% footprint), binary {0,1}, NaN outside (7,111,787 px), EPSG:32611 100m 3292×3730, 5×5 exclusion invariant, no catalogue pixel touched, plus all-finite fallback and zip. `core.validate()` passes.
6. **Site updated**: `docs/index.html` hero CTA now R6 (primary TIF, ZIP, fallback, archive R5), `docs/executive-summary.html` R6 guide, `README.md` R6 direct deliverable, `AGENTS.md` current round-6, `tests/test_site.py` expects R6 primary while R5 remains as archive. `tests/test_round6.py` locks distinctness <0.50, H28 gate, artifact conformance. Full suite 41 passed.
7. **No DrivenData slot spent**. Strongest-sibling-baseline gate still unsatisfied. Release not authorized, format-validated only.

### Limitations carried into next session (updated)

* **No upload receipts** — duplicate 0.1563 attribution still unresolved.
* **Strongest-sibling-baseline gate unsatisfied** — no sibling model reproduced under masked NMS protocol.
* **Local truth is known catalogue proxy** — sparse thinned variant is sensitivity check, not real new-fault truth; transfer magnitude of H28 gain (+0.0026 sparse) unknown until scored submission.
* **Model class gap U-Net vs GBM** — reference solution is U-Net with Monte-Carlo CV (GPU needed). Our arms are per-pixel GBM. This remains largest unexplored lever after emission geometry.
* **External data transport blocked** — 1m DEM (USGS 3DEP) and Sentinel-2 L2A verified free/open but S3 blocked in-sandbox; GitHub-runner bridge pattern is only viable path. 1m_DEM_links.csv not present in bridge; needs separate fetch from official data tab (requires login) or reconstruction via AWS listing.
* **Budget transfer risk** — 2% mass selected on folds 0–1 sparse proxy. If real new-fault truth is sparser, optimal mass lower per marginal condition p > 0.2·DTI.
* **H26 revised** — initial design correlated 0.86 with det_elev_slope, revised to gravity-slope curvature to achieve distinctness; this is recorded, not silently edited.

### Suggestions for next session

1. **Spend one weekly submission slot on R6 artifact** (`8721329b55c7`) to measure real transfer of H28 gain and emission policy. Note: primary NaN outside mirrors official sample; if rejected with `[0,1]` error, retry fallback all-finite once and record which check DrivenData runs — knowledge worth more than slot.
2. **Train U-Net reference architecture** (GPU) with NMS-3 emission: official reference is U-Net with Monte-Carlo CV; our GBM is per-pixel. Even a simple U-Net with same 25+1 features and NMS emission should beat GBM if spatial context matters.
3. **Fetch 1m DEM via GitHub runner**: use `1m_DEM_links.csv` from official data tab (requires DrivenData login) or list `s3://usgs-3dep` 1m tiles intersecting GeoDAWN footprint (EPSG:32611 bounds 243350,4508550,572550,4135250). Downsample curvature/openness to 100m and test H30.
4. **Fetch Sentinel-2 L2A clay/iron-oxide ratios** via `sentinel-cogs` bucket for H31 alteration halo.
5. **Reproduce strongest sibling baseline** (e.g., DARD 0.3168 or alexoktaba 0.2993) if code shared, or at least reproduce 11GEMSDOE structural arm under our masked NMS protocol to satisfy release gate.
6. **Budget sweep with marginal condition**: derive optimal mass for sparser truth using p > 0.2·DTI rule, not grid search post hoc.
7. **Forum posts**: raise `tc` band description mismatch and sentinel missing-data encoding as irregularities.


## 12. Round-7 session record (2026-09-28)

What was done, in order, with the command or file that proves each line.

1. **Data placement autonomously reproduced** (`scripts/download_competition_data.py` → `scripts/prepare_data.py` → feature builds). Deterministic rebuild of `candidate-features-30.npy` gives SHA-256 `7eb403a2…` — identical to the Round-5 manifest, **not** to the Round-6 manifest (`fc746d92…`). Diff is confined to channel 29 (H10, used only by `multi30`), so no `multi25` gate is affected; the Round-5/6 sidecars (`round5/6-feature-build.json`) were regenerated in the correct order (r4 → r5 → r6) and only their `r12_ch29` correlations changed. Flagged as an irregularity in the register §5.3.
2. **Previous-session next steps executed first**: the GitHub-runner bridge for external data was found already built by sibling GEMSDOE10 (tag `ext/dem10-36343078537`, `STATUS.txt build=success run=36343078537`): 13 label-free 10 m-DEM scarp channels from 12 official USGS 3DEP 1/3″ tiles, per-tile SHA-256 pinned. `scripts/fetch_dem10_channels.py` pulled them through the GitHub API (the only egress this sandbox has), verified the tag commit, template SHA `2176d08e…`, footprint count 5,167,373 and every channel hash → `evidence/dem10-fetch.json` (all `fetched-verified`, `labels_used: false`).
3. **Preregistered H32–H36 BEFORE coding** (`docs/hypotheses-round7.md`), ranked by expected gain ÷ cost: H32 sub-100 m scarp signature (data in hand), H33 CPU U-Net spatial-context learner (deferred: PyTorch not installable here), H34 strike-integrated line contrast (Round-8), H35 GeoDAWN radiometrics K/eTh/eU/TC (ScienceBase 657e1d85…, public domain, runner bridge needed), H36 SGMC bedrock faults (not locally validatable). Gate tightened: ≥3/4 folds **and** positive mean paired gain on both protocols, because Round-6 had passed on 3/4 folds with a mean dense gain of +0.00005.
4. **Built the 12-channel cube** (`scripts/build_round7_features.py`, SHA-256 `4fcbb375…`, `valid_frac` dropped as constant). Distinctness on 400k random valid pixels: slope/gradient/micro-relief channels 0.80–0.97 vs `det_elev_slope` (B19); `steep_ratio_max` 0.41, `onesided` 0.26, `onesided3` 0.18. Recorded as a **register amendment before the gate ran**: the distinct-only arm `dem3` replaced the planned "core subset"; expected gain revised down.
5. **Frozen masked holdout, NMS-3 @2 %** (`scripts/holdout_round7.py`, 13.6 min): reference arms reproduced Round-6 exactly (multi25 0.22138/0.11178; multi25+H28 0.22143/0.11438). **H32 primary `multi25_h28_dem12`: dense 0.24586 (+0.02443 vs incumbent, 4/4), sparse 0.12732 (+0.01294, 4/4)**; ablation `multi25_dem12` 0.24658/0.12706 (4/4, 4/4); distinct-only `multi25_h28_dem3` 0.23533/0.12194 (4/4, 4/4). Leakage probe 0.0000 on every fold. `gate.passed = true` (`evidence/holdout_round7.json`).
6. **New artifact** (`scripts/generate_nms_submission_r7.py`, refuses to run unless the gate passed): `12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif`, SHA-256 `0c9199f14e625d7b2539a0a045803b74d6494ce568d185abecc193fe7e93c6f2`, 103,347 px (2.000 %), binary {0,1}, NaN outside, 0 catalogue pixels, 5×5 exclusion invariant; only 10,230 emitted pixels shared with R6 (186,234 differing pixels) — a genuinely different submission. Manifest carries the external-data declaration (tiles + hashes).
7. **Site / docs**: hero CTA on `index.html` and `executive-summary.html` now hand out R7 (R6/R5 archived); the guide's step 4/5 — which still named the R5 file and the Round-1 note — fixed; new live leaderboard card reading `docs/leaderboard.json`; new `docs/knowledge-base.md` (verified-facts ledger with sources and dates); README status/deliverable/reproduce sections, AGENTS.md brief updated.
8. **Leaderboard feed**: `scripts/fetch_leaderboard.py` (stdlib only, parser unit-tested on synthetic HTML) + `.github/workflows/leaderboard-feed.yml` (every 6 h + manual dispatch) commits `docs/leaderboard.json` and dated snapshots to `evidence/leaderboard/`. The seed feed is a hand-typed snapshot (status `manual-snapshot`); the live path can only be exercised on GitHub-hosted runners.
9. **Tests**: `tests/test_round7.py` (7 tests: register, provenance sidecar, distinctness honesty, holdout report + reference reproduction, memmap↔vector identity, parser, artifact conformance) + `tests/test_site.py` updated; full suite **48 passed**.
10. **No DrivenData slot spent.** Release still not "authorized" under the standing strongest-sibling-baseline rule; spending a slot is a human decision.

### Limitations carried into next session (updated)

* **Holdout truth is the catalogue proxy.** H32's +0.024/+0.013 is measured on held-out *catalogue* traces; the hidden truth is expert-mapped new faults whose sources staff will not disclose. If experts mapped from lidar, H32 should transfer well; if the new faults are geophysics-only, it may not. Unknown until a slot is spent.
* **`det_elev_slope` overlap.** Nine of twelve DEM channels are near-duplicates of B19; the repo does not claim them as new information. Whether the sponsor derived B19 from 10 m/30 m topography is unverified.
* **Sibling-built channels.** The DEM reduction code lives in GEMSDOE10; this repo verified hashes and template alignment, not that code line by line.
* **Leaderboard feed unexercised on the network.** Parser tested only on synthetic HTML; the first Actions run must be checked (`gh run list --workflow leaderboard-feed.yml`). If DrivenData's table markup differs, the feed will record `parse-failed` and the workflow fails visibly.
* **No upload receipts; strongest-sibling-baseline gate unsatisfied; U-Net model-class gap; 1 m DEM / Sentinel-2 / GeoDAWN radiometrics need the runner bridge** — unchanged from §11.
* **Budget frozen at 2 %.** With a sharper probability field the marginal condition p > 0.2·DTI may favour a different mass; not re-swept (preregistration kept the budget fixed for comparability).

### Suggestions for next session

1. **Decide on spending one slot on R7 (`0c9199f14e62`)** — first artifact with a material holdout gain; the transfer measurement is worth more than any further proxy result. Record upload receipt + score in the knowledge base.
2. **Verify the leaderboard feed's first run** (`gh workflow run leaderboard-feed.yml`, then `gh run watch`); fix the parser against the real markup if `parse-failed`.
3. **H33 U-Net on a GitHub runner** (CPU, 6 h job limit): same fold masks, 19+12 channels, Tversky loss, NMS-3 emission on the averaged field; bridge per-fold probability vectors back via an `ext/*` tag and score them with `holdout_round7.py`'s DTI code.
4. **H35 GeoDAWN radiometrics** via the runner bridge (ScienceBase item 657e1d85d34e23d3533209f7): K, eTh, eU, TC grids → K/eTh ratio anomaly, |∇TC| lineaments; preregister first.
5. **H34 strike-integrated line contrast** on B3/B18/B19 + `dem10_hgm50_max` (12 orientations, 15/25 px baselines, flank subtraction).
6. **Budget sweep under the marginal rule** for the R7 field (1.5 %, 2 %, 2.5 %, 3 %) on folds 0–1 sparse only, confirm on 2–3.
7. **Forum posts** on the `tc` description and sentinel encoding; **account-ownership check** for the 0.1563 trio before any upload.
