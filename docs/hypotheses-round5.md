# Round-5 Candidate Register — Emission Geometry, Magnetic-Basement Depth, Singularity, Step Asymmetry

> **Status:** preregistered on 2026-09-27 **before** implementing Round-5 feature code
> and before running the Round-5 gate. The emission-geometry **diagnostic**
> ([`evidence/round5-emission-probe.json`](../evidence/round5-emission-probe.json))
> and the input-identity checks
> ([`evidence/round5-identity-checks.json`](../evidence/round5-identity-checks.json))
> were run first and are reported verbatim in §2–§3; the decision rule in §5 was
> fixed from them **before** any Round-5 feature channel was built or scored.
> A hypothesis is not a discovery. `PASS` on a source check means only that the
> source can be manually reviewed.

## 0. Why this round exists, and what changed since Round 4

1. **The data blocker is closed in-sandbox.** `bash scripts/download_competition_data.sh`
   completed here on 2026-09-27 (all 5 bridge parts + 2 rasters fetched via the
   GitHub Contents API, reassembled, and SHA-256 verified by
   `scripts/prepare_data.py`). The full train → validate → format-check pipeline
   now runs end-to-end on CPU in this environment. The previous sessions'
   "single remaining blocker is data placement" statement is **no longer true**
   and has been corrected in the README.
2. **The Round-2/3/4 headline numbers reproduce bit-exactly here.**
   `scripts/cache_fold_models.py` re-trained raw19 / multi25 / multi30 /
   random02 under the frozen masked protocol and matched
   `evidence/holdout_masked.json` on **every fold of every arm to full float64
   precision** (multi25 mean 0.09071277311870418; random02 0.1378794777374697).
   Rounds 1–4 are therefore verified reproducible, not just reported.
3. **That verification exposed the real defect.** Under the frozen protocol the
   *uniform random 2 %* control (0.13788) beats every learned arm
   (multi25 0.09071, multi25+H15 0.09364). Four rounds of feature engineering
   were scored at an operating point where noise beats the model. The defect is
   not the features — it is the **emission policy** (top-*k* by probability),
   which every round inherited unchanged.
4. **A metric-geometry analysis explains it** (§1) and was then measured (§2):
   changing only the emission geometry, with the identical model and features,
   moves mean DTI from 0.09071 to 0.26303 on the dense-truth protocol and from
   0.04489 to 0.11178 on a sparse-truth protocol.
5. **`tc` (B5) has been misidentified for four rounds.** Identity check C3
   (§3) shows it is strictly positive with median 18.48 and maximum 88.57 and a
   correlation of −0.0012 with |tilt angle|. That is impossible for a tilt angle
   (bounded by ±π/2 radians). The official problem description lists
   "the **top-of-crustal magnetic source depth estimate**" among the supplied
   magnetics. Rounds 1–4 followed the raster band description
   ("Tilt angle or total curvature") instead, which is why H18 (`tc`
   lineaments) was rejected 0/4 folds. H20/H21 use `tc` as what it is: a second,
   independent basement-**depth** surface.

## 1. Metric geometry (derived from the official formula, not fitted)

Official metric ([problem description, "Performance metric"](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)):
distance-weighted Tversky index, α = 0.2 (false positives), β = 0.8 (false
negatives), triangular credit kernel of radius R = 300 m = **3 px** at the
100 m submission grid:

```
TP = Σ_{t ∈ T}  max_{|d| ≤ 3} ( P(t+d) · (1 − |d|/3) )
FP = Σ_{p}      P(p) · min(dist(p, T)/3, 1)
FN = |T| − TP
DTI = TP / (TP + 0.2·FP + 0.8·FN)
```

Three consequences that no previous round exploited:

* **TP is a per-truth-pixel maximum over a 5×5 neighbourhood.** Emitting a
  second predicted pixel inside the same 5×5 block adds FP and adds **zero** TP.
  Top-*k* emission (used by every round 1–4 arm and by the archived
  `06ca61e5` artifact) concentrates mass exactly where it is wasted.
* **The sparsest emission that can credit every truth pixel** is one whose
  predicted pixels are never within a 5×5 block of each other, i.e.
  non-maximum suppression with Chebyshev radius 2 → maximum density
  1/25 = **4 %**. This is the classical NMS/thinning step of lineament
  extraction, not a metric trick: a mapped fault *is* a 1-pixel-wide trace.
* **The optimal emission mass scales with truth density.** With
  `DTI = TP/(0.2·S + 0.8·|T|)` (S = emitted mass), the marginal condition for
  adding a pixel with hit probability *p* is `p > 0.2·DTI`. Sparser truth ⇒
  lower optimal S. So the budget must be re-derived for the real test set
  (a sparse set of *new* faults), not carried over from a dense-catalogue
  screen.

## 2. Emission-geometry diagnostic (measured before this register was written)

Frozen masked spatial holdout, cached multi25 probabilities, no re-training, no
submission slot. Full report:
[`evidence/round5-emission-probe.json`](../evidence/round5-emission-probe.json).
Mean DTI over 4 folds; `f01`/`f23` are the two fold halves used by the §5 rule.

| Arm (multi25 model, same features) | mean | f01 | f23 |
|---|---:|---:|---:|
| **dense-truth protocol (truth = full catalogue)** | | | |
| nms3_model @ 4 % | **0.26303** | 0.27460 | 0.25145 |
| lattice 5×5 (no model at all) | 0.24385 | 0.25737 | 0.23033 |
| nms3_model @ 2 % | 0.22138 | 0.22190 | 0.22085 |
| nms3_random @ 4 % (geometry-only control) | 0.21804 | 0.22954 | 0.20654 |
| random @ 8 % | 0.20159 | 0.21623 | 0.18696 |
| random @ 2 % | 0.14188 | 0.14725 | 0.13652 |
| **top-k @ 2 % — the standing frozen policy** | **0.09071** | 0.08498 | 0.09644 |
| **sparse-truth protocol (20 % of truth components, seed 4242+f)** | | | |
| nms3_model @ 2 % | **0.11178** | 0.11473 | 0.10882 |
| nms3_model @ 1 % | 0.10117 | 0.10058 | 0.10175 |
| nms3_model @ 4 % | 0.10058 | 0.10669 | 0.09447 |
| lattice 5×5 | 0.08803 | 0.09419 | 0.08188 |
| nms3_random @ 2 % (geometry-only control) | 0.07036 | 0.07352 | 0.06719 |
| random @ 2 % | 0.06546 | 0.06846 | 0.06247 |
| **top-k @ 2 % — the standing frozen policy** | **0.04489** | 0.04633 | 0.04345 |

Mechanism, quantified (dense protocol, per fold): at the **same** emitted mass
(≈23 k pixels) top-k credits 7.6–15.0 % of truth pixels while NMS-3 credits
24.6–29.1 % — a per-fold coverage gain of 1.9–3.2× for the same FP bill. That is
the entire effect; nothing else changed.

Two honest caveats recorded now:
* The diagnostic printed per-fold values for all four folds, so the §5
  "confirm on folds 2–3" step is **not blind**. The policy has one scalar
  hyper-parameter (budget) chosen from a 4-value grid; the direction of the
  effect is identical on both folds halves and both truth variants.
* Local truth is the **known catalogue**, used as a proxy. The real test truth
  is a sparse set of expert-mapped *new* faults. The sparse-truth variant is a
  proxy for that, not a reproduction of it. Transfer magnitude is unknown and
  can only be settled by one scored submission.

## 3. Pre-registered input-identity checks (no labels, no scores, no model output)

Run by [`scripts/round5_identity_checks.py`](../scripts/round5_identity_checks.py);
results in [`evidence/round5-identity-checks.json`](../evidence/round5-identity-checks.json).

| Check | Measured result | Consequence |
|---|---|---|
| **C1** missing-data encoding in `training_features.tif` | Sentinel = float32 most-negative **−3.4028235e+38**; `tc` carries 3,073 sentinel pixels *inside* the survey footprint; unmasked read of the stack has min −3.4028235e+38 | Any pipeline that reads the stack **unmasked** propagates −3.4e+38 into predictions. That is a concrete, sufficient cause of the DrivenData rejection `"Predicted values must be in range [0, 1]"`. See §7. |
| **C2** is `iso_grav_anom_slope` (B4) the magnitude containing `iso_grav_anom_hg` (B17)? | corr(B4, \|B17\|) = **0.7998**; \|B17\| > B4 at **387,553 / 400,000** pixels (96.9 %) | They are **not** magnitude and component of one gradient field. No orthogonal component is recoverable; any hypothesis assuming one is invalid. |
| **C3** what is `tc` (B5)? | all-positive; median **18.479**; max **88.57**; corr(tc, depth_to_base_surf) = **0.2069**; corr(tc, \|tilt\|) = **−0.0012**; lag-1 autocorrelation 0.998-class smooth | Not a tilt angle (impossible range, zero tilt correlation). Consistent with a **depth-to-magnetic-source** surface in km, matching the official layer list; weakly related to (i.e. largely independent of) the MT conductive-base depth. |
| **C4** Round-5 candidate vs every round-1..4 channel | H20 max \|r\| = **0.153** (vs raw `tc` band); H21 max \|r\| = **0.342** (vs \|∇depth_to_base_surf\|); H22 max \|r\| = **0.388** (vs raw `tc` band); H23 max \|r\| = **0.014** (vs \|∇depth_to_base_surf\|) | All four below the 0.50 distinctness rule → mechanism-distinct from everything already implemented. |

## 4. Ranked candidates

Ranking is expected DTI gain ÷ implementation cost, i.e. qualitative scientific
judgement, not a predicted score.

| Rank / cost | Candidate: exact layers and transform | Physical signature | Why it should catch a fault absent from USGS/INGENIOUS | Difference from anything in this repo or the sibling registers | Validation state |
|---|---|---|---|---|---|
| **1 / low** | **H24 — DTI-geometry thin-trace emission (policy, not geology).** Model: unchanged `multi25` probabilities. Emission: greedy non-maximum suppression with Chebyshev radius 2 (5×5 block) in descending probability order, budget fixed by §5. | Not a geological signature: it is the decision layer that converts a probability field into a submitted raster. Enforces the physical fact that a mapped fault is a 1-px-wide trace and the metric fact that two predicted pixels in one 5×5 credit cell cannot both earn TP. | Orthogonal to catalogue completeness: it improves *recall per emitted pixel* on **any** truth geometry, so it also helps on faults that are missing because they are concealed under basin fill. | Every round 1–4 arm and the archived artifact used top-*k*. No sibling register in `evidence/review-scope.json` reports an NMS/coverage emission policy; the sibling GEMSDOE10-H19 result (thin-line emission **rejected**) used a different construction (dev-set win, confirmation loss) and did not enforce a 5×5 exclusion or re-derive the budget. | **Measured** (§2). PRIMARY. |
| **2 / low** | **H20 — magnetic-basement relief step.** `tc` (B5), re-identified in C3 as top-of-crustal magnetic source depth. Transform: ‖∇(5-px-smoothed `tc`)‖. | A normal fault offsets the magnetic basement; the source-depth surface shows a **step** even where the alluvial cover hides every surface expression. | USGS QFFD/INGENIOUS map surface-rupture evidence. A fault buried under 300–500 m of basin fill has no scarp but does offset the magnetic basement, which is exactly what a source-depth step records. Competing null: intrusions and lithologic contacts also perturb source depth (mitigated by ranking, not masking). | H18 used `tc` as a curvature/lineament field (rejected 0/4). H1 used ‖∇depth_to_base_surf‖ — the *MT* surface, a different layer. Nobody has taken the gradient of `tc` as a depth surface. Max \|r\| vs all existing channels = 0.153. | Viable now; arm `multi25+h20`. |
| **3 / low** | **H21 — two-depth-surface step coincidence.** `tc` (B5) × `depth_to_base_surf` (B14). Axial agreement of the two gradient directions × min of the two robust edge strengths (AND logic). | Both an independently derived **magnetic** basement and an independently derived **conductive** (MT) basement break along the same line. Two unrelated surveys agreeing on one line is strong evidence of a through-going structure. | A concealed range-front or intrabasin fault must offset both the magnetic and the conductive basement; a shallow lithologic contact or a data artifact perturbs one. C3 measured corr(tc, dtb) = 0.21, so the two surfaces are genuinely independent — agreement is informative, not redundant. | H15 aligned **four** fields but included `tc` only implicitly and treated it as curvature; H15's layer set was dtb/iso-grav/cond/rtp. H21 is the 2-field version built on the corrected `tc` identity, and it is the only arm that combines the two *basement-depth* surfaces. Max \|r\| = 0.342. | Viable now; arm `multi25+h21`. |
| **4 / medium** | **H22 — local singularity (multifractal) exponent of the magnetic-source depth.** `tc` (B5). α from log(mean over dyadic windows w = 1,2,4,8,16) vs log w; feature = \|α − 2\|. | Faults and fracture zones are scale-invariant singular structures; a 1-D singularity embedded in a 2-D field has local exponent α ≈ 1, a smooth background α ≈ 2. This measures **how the field scales**, which no gradient, curvature or tilt transform does. | Catalogue gaps concentrate where fault geometry is fragmented and self-similar (relay zones, distributed shear) rather than a single clean scarp; the singularity exponent responds to that fragmentation directly. | No repo channel and no sibling register computes a multi-scale scaling exponent. The nearest existing work is H9's cross-gradient magnitude (single scale, two fields). Max \|r\| = 0.388. | Viable now; arm `multi25+h22`. |
| **5 / medium** | **H23 — asymmetric-step (monocline) detector on basement depth.** `depth_to_base_surf` (B14), later `tc`. Along the four principal axes, compare the forward and backward lag-2/4 means and normalise: `\|f − b\| / (\|f − c\| + \|b − c\|)`, max over axes. | A fault **step** is antisymmetric (up on one side, down on the other); a ridge, valley or dome is symmetric. Every transform in rounds 1–4 is symmetric in profile and cannot tell the two apart. | Half-graben growth-fault flexure produces exactly this asymmetric cover profile; symmetric topography produces false positives in every gradient/curvature detector used so far. Competing null: tilted blocks and drainage asymmetry. | No repo channel encodes step **polarity/asymmetry**; H1 used ‖∇dtb‖ and ∇²dtb, both symmetric. (First implementation attempt used array-valued `scipy.ndimage.shift`, which is not supported and produced a constant field — recorded in §6 and fixed before scoring.) | Viable now; arm `multi25+h23`. |
| — | **Rejected before coding** | | | | |
| — | Recover the orthogonal gravity-gradient component from B4 and B17 | — | — | Identity check C2 falsifies the premise (\|B17\| > B4 at 96.9 % of pixels) | **Not viable.** |
| — | `tc` as a tilt/curvature lineament field | — | — | Already implemented as H18 and rejected (0/4 folds, −0.00573) | **Duplicate.** |
| — | 3DEP 10 m / 1 m DEM scarps; ComCat event lineaments; radiometric ratios; catalogue-version differencing | — | — | Sibling territory: GEMSDOE10-H20 (released), H22 (planned there), 7GEMSDOE-H9 (closed), GEMSDOE10-H21 (decisive negative) | **Not duplicated here.** |
| — | Sentinel-2 alteration (Round-4 H19) | — | — | Source verified free/open ([AWS Open Data Registry](https://registry.opendata.aws/sentinel-2/)) but S3 HTTPS is still blocked from this sandbox | **Deferred again** (transport, not licence). |

## 5. Preregistered decision rule (fixed before any Round-5 arm is scored)

1. **Emission policy for every Round-5 arm:** NMS radius 2 (5×5), descending
   probability, deterministic tie-break by pixel index.
2. **Budget:** the value of `b ∈ {0.005, 0.01, 0.02, 0.04}` with the highest
   mean DTI on **folds 0–1 only**, under the **sparse-truth** protocol
   (the real test truth is a sparse set of new faults, per the official problem
   description). From §2 that value is **b = 0.02** (f01 = 0.11473). This value
   is now frozen; it will not be re-chosen after seeing folds 2–3.
3. **Gate (must pass all three):**
   a. on folds 2–3, sparse-truth protocol, `nms3_model @ 2 %` > standing frozen
   policy `top-k @ 2 %`;
   b. the same inequality on the dense-truth protocol;
   c. a geological arm is adopted only if it beats the *same-emission*
   multi25 reference on ≥3/4 folds on both protocols.
4. **A pass authorises packaging a GeoTIFF for the site. It does not authorise
   release.** The standing strongest-sibling-baseline requirement
   ([`evidence/preregistered-hypotheses.md`](../evidence/preregistered-hypotheses.md))
   is still unsatisfied: no sibling model has been reproduced under our
   protocol. No weekly submission slot is spent in this session under any
   outcome.
5. **Leakage probe** must remain 0.0000 on every fold; every Round-5 channel
   must be label-free, coordinate-free and catalogue-distance-free.

## 6. Known irregularities flagged for manual review

1. **`tc` band description contradicts the official layer list** (§0.5, C3).
   The raster says "Tilt angle or total curvature"; the official feature list
   says "top-of-crustal magnetic source depth estimate"; the data supports the
   latter. Worth raising on the competition forum.
2. **`training_features.tif` missing-data sentinel** is the float32 most-negative
   value, not NaN (C1). Any competitor (including this group's earlier sites)
   that reads the stack unmasked gets −3.4e+38 in the model inputs.
3. **GEMSDOE2 0.1560 vs 0.1563** remains unresolved (round-2 §6.6); still no
   upload receipts in any audit.
4. **The dense-catalogue local protocol is an inverted selector** (random 2 %
   beats every learned arm). Rounds 1–4 rankings measured on it are weak
   evidence. Recorded, not silently reinterpreted.
5. **No DrivenData upload receipts** exist anywhere in this repo, so no claim
   in this document attributes a leaderboard score to a specific artifact.

## 7. Official source ledger (manual review links)

| Claim used above | Source | What was verified | Boundary |
|---|---|---|---|
| Target = expert-identified faults absent from the public USGS database; two-round structure; single submission chosen for both rounds | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fetched 2026-09-27. Quotes in §0/§1 are from that page. | Does not endorse any transform. |
| Supplied magnetics include "the top-of-crustal magnetic source depth estimate" | Same page, "Provided features" | Fetched 2026-09-27; the phrase appears verbatim in the layer list. | The page does not name the raster band; the mapping to `tc` is supported by C3 (range + zero tilt correlation), not stated officially. |
| DTI parameters α = 0.2, β = 0.8, R = 300 m, triangular kernel | Same page, "Performance metric" | Fetched 2026-09-27; `scripts/core.py` implements it and `tests/test_core.py` checks it against a brute-force reference. | — |
| Submission format: single-band GeoTIFF or a zip with one GeoTIFF; must match CRS, shape, geotransform | [New submission form text](https://www.drivendata.org/competitions/306/competition-doe-gems/) and the official `sample_submission.tif` (verified locally: float32, EPSG:32611, 3730×3292, nodata = NaN, inside values {0,1}, 5,167,373 valid px, 7,111,787 NaN px) | Verified by direct inspection of the downloaded official file on 2026-09-27. | The form's server-side range check implementation is not published; §7 of `docs/session-review.md` states what is and is not provable about the past rejection. |
| Known catalogue pixels masked/excluded from scoring, pixel-exact | [Staff 11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2), [11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) | Carried from Round 2/4 verification. | Mask geometry is pixel-exact; new truth may lie within 300 m of a known trace. |
| "New fault" includes newly mapped geometry of an existing system | [Staff 11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2) | Carried from Round 2 verification. | — |
| Leaderboard snapshot 2026-09-27 (this session) | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Re-fetched this session: #1 DARD **0.3168**, #2 alexoktaba 0.2993, #3 HardcoreTechGod 0.2854, #4 mzoorob 0.2843, #5 joeyfezster 0.2806, #6 GrigorSargsyan 0.2742; **0.1563 × 3** at #26 `extradr19`, #27 `SDCF9`, #28 `smashi34`; #33 `wbg1` 0.1461; #46 `smrtdoog5` 0.1193. A new row #45 `mtrpdx` 0.1219 appeared relative to the Round-4 snapshot. | Time-stamped snapshot, not a live claim; no upload linkage is asserted. |
| Non-maximum suppression / thinning as the canonical lineament-extraction step | Standard edge/lineament detection literature (e.g. Canny's NMS stage); the 5×5 exclusion radius here is derived from the competition's own 300 m kernel, not from a citation. | Radius is a function of the official metric only. | NMS is a geometric operation; it makes no geological claim by itself. |
| Reference solution architecture (context for "spatial models matter") | [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) README (fetched 2026-09-27 via the GitHub API) | It is a **U-Net with Monte-Carlo CV** by Prof. John Lipor, GPU/MPS/CPU selectable. | Our arms are per-pixel GBMs; a U-Net was not trained here (2 CPU sandbox). Recorded as the main model-class gap. |
| Sentinel-2 L2A free/open, no-account S3 access | [AWS Open Data Registry](https://registry.opendata.aws/sentinel-2/) | Licence and bucket confirmed. | Not reachable from this sandbox; deferred. |
