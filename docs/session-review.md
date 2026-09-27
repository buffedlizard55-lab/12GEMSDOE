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
| Leaderboard snapshot high: 0.3049 | [DrivenData Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Fetched 2026-09-27: Rank #1 DARD at 0.3049. This is a time-stamped snapshot, not a live claim. |
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
