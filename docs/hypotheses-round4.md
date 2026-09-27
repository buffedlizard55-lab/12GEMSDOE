# Round-4 Candidate Register — Coincident Boundaries, Strain Gradients, Contact Topology, tc Lineaments

> **Status:** preregistered on 2026-09-27 **before** implementing Round-4 feature code,
> before running any Round-4 holdout, and before packaging any Round-4 artifact.
> A hypothesis is not a discovery. `PASS` on a source check means only that the
> source can be manually reviewed; it does not establish predictive value.
> The only release-eligible arm this round is the preregistered PRIMARY
> (`multi25+H15`), and only if it clears the frozen gate below — which still
> does not satisfy the standing strongest-sibling-baseline requirement.

## 0. Why this round exists, and what changed since Round 3

1. **Round-3 H11 failed** (multi25+H11 0.08650 vs multi25 0.09071, 1/4 folds,
   −0.00421). Drainage-deflection at 100 m is rejected as a multi25 upgrade.
2. **The leaderboard moved.** Re-fetched 2026-09-27:
   [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/):
   #1 DARD **0.3168** (was 0.3049), #2 0.2993, #3 0.2854. Three accounts tie at
   exactly **0.1563** (#26 `extradr19`, #27 `SDCF9`, #28 `smashi34`) — independently
   corroborated by GEMSDOE10's session-3 register. Score equality across accounts
   is consistent with same-bytes uploads but is not proof of them (no upload
   receipts exist in any audit). `#45 smrtdoog5 0.1193` and `#33 wbg1 0.1461`
   match the group's reported GEMSDOE3 and 7GEMSDOE scores; same caveat applies.
3. **Sibling intelligence (fresh 2026-09-27 reads) closes several doors:**
   - GEMSDOE10 H21 catalogue-version differencing: **decisive negative** — the
     provided label raster (60,988 px) *is* the current public catalogue
     (USGS QFFD 2020 + INGENIOUS v1/v2); no public trace is absent from it.
     Catalogue-lag ideas are retired, not re-proposed here.
   - GEMSDOE10 H20 3DEP 10 m scarp channels: **eligible and released**
     (+0.0147 dev / +0.0141 confirmation). DEM-stack ideas are sibling
     territory; not duplicated here. Lesson adopted: interaction features
     carry gain where univariate AUCs sit at 0.49–0.58.
   - GEMSDOE10 H19 thin-line emission: **not eligible** (dev win, confirmation
     loss −0.0211). Emission geometry is treacherous on sparse truth; this
     round keeps the frozen top-2% binary policy and does not sweep emission.
   - GEMSDOE10 H22 (raw ComCat event lineaments): **planned there, not built.**
     Avoided here to prevent a same-session collision.
   - GEMSDOE10 H15 (paleo/thermal point archives): data now in their hand,
     modelling deferred. Our H13/H14 stay deferred (same TLS block below);
     no thermal/paleo candidate is re-proposed here.
   - 11GEMSDOE H1 strain structure-tensor coherence: **rejected** (−0.0002);
     H4 trace-inpainting parked; H2/H3 structural bundled +0.0042 (n.s.).
     Strain-coherence and objective-surgery ideas are not re-proposed.
   - 7GEMSDOE H9 radiometric ratios as primary arm: **closed** (0–1/5 folds);
     H1 lidar scarp awaiting attributable upload.
4. **Round-2's lead (H6′) was never validated** — Round 3 tested H11 instead.
   This register preregisters H6′'s exact form (§5) as a *measurement* arm so
   the round-2 mechanism claim is tested prospectively, never promoted post hoc.
5. **Round-2's recorded limitation** (multi30 bundle rejected, single-channel
   ablations never run) is preregistered as diagnostic arms (§6): a bundle
   rejection does not imply each channel is useless.

## 1. Scope and non-duplication check

Checked against the Round-2 mechanism inventory
([round 2](hypotheses-round2.md#what-is-already-taken)), Round-3 H11–H14,
local scripts, and the sibling registers listed in `evidence/review-scope.json`
plus the fresh reads above (GEMSDOE10/HYPOTHESES.md incl. session-3 results,
11GEMSDOE/docs/HYPOTHESES.md, 7GEMSDOE knowledge/next_session.md).
Deliberately excluded: raw/derived pixel classifiers, magnetic/gravity edges,
tilt/analytic-signal/curvature on magnetics (except the untouched `tc` band
quantity itself — see H18 verification), basement/conductivity gradients,
strain products and strain coherence, 1 m/10 m lidar scarps, radiometric
ratios, Hough/Frangi/Gabor ridges, tip rays/relays/splays (except preregistered
H6′ measurement), trace inpainting, emission-geometry sweeps, catalogue
differencing, upward continuation, texture restoration, thermal/paleo points,
ComCat events, and drainage topology. Inspection-bounded: two sibling trees
previously 404'd and remain unknown.

The public score target is **new fault pixels**, not geothermal vents. The
competition page states the test set is expert-identified faults absent from
the existing database; staff define a new fault as any fault pixel not already
captured, including new geometry of an existing system ([11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2)).
Nothing here claims to identify a proven geothermal resource.

## 2. Pre-registered input-identity checks (no labels, no scores)

These checks ran **before** this register was written, use no labels and no
model output, and exist only to prevent proposing a duplicate of H3:

| Check | Result | Consequence |
|---|---|---|
| `tc` (B6) vs tilt computed from B9/B3 | corr **0.0128**; \|tilt\| corr −0.0018 | `tc` is not the tilt angle |
| \|\|∇`tc`\|\| vs H3 \|\|∇tilt\|\| | corr **0.0213** | H3's feature and any `tc`-gradient are independent quantities |
| `tc` distribution | range 2.95–88.57, median 18.48 | consistent with a total-curvature-style magnitude, an untouched quantity |
| `iso_grav_anom_vg` (B11) sign | signed, median −0.07, 52% negative | zero-crossing topology well-defined |
| `iso_grav_anom_hg` (B18) sign | **signed** (−15.4…+12.9), median 0.04 | it is a directional gradient, not a magnitude; H17 uses \|hg\| |

External reachability from this sandbox (verified 2026-09-27, all HTTP 000 /
blocked): `sciencebase.gov`, `gdr.openei.org`, `s3.amazonaws.com`,
`earthquake.usgs.gov`, `tnmaccess.nationalmap.gov`. GitHub API works (bridge
verified). Any external-data candidate is therefore **deferred here**; the only
viable transport is the GitHub-runner pattern GEMSDOE10 demonstrated.

## 3. Ranked candidates H15–H19

Ranking is qualitative scientific judgment (expected DTI gain ÷ cost), not a
predicted score. All supplied-data transforms are label-free, coordinate-free,
and catalogue-distance-free.

| Rank / cost | Hypothesis: exact layers and source | Physical signature / proposed transform | Catalogue-gap rationale and competing null | Difference from work already implemented | Validation state |
|---|---|---|---|---|---|
| **1 / low** | **H15 — coincident multi-physics boundary alignment.** Supplied `depth_to_base_surf` (B15), `iso_grav_anom` (B13), `cond_surf` (B17), `rtp` (B2). | Per-field unit gradient orientations; pairwise **axial agreement** \|uᵢ·uⱼ\| over all 6 field pairs (parallel *or* antiparallel both count — a step may face either way per field); joint edge weight = min over the 4 robust edge strengths (AND logic: all four fields must break); lineament persistence via max over four oriented 9 px line kernels; robust [p50,p95]→[0,1] normalization. Targets places where four independent fields break along the **same** line. | A throughgoing basement fault offsets density, basement depth, conductivity, and magnetization together, so its gradients align even with zero surface scarp; a lithologic contact rarely offsets all four coherently. Null: fortuitous alignment of unrelated unit boundaries; survey-edge artifacts (mitigated by boundary zeroing). | H1 uses single-field gradient *magnitudes*; H9 uses the cross-product *magnitude* (perpendicular = transfer zones) — H15 is its complement (parallel = throughgoing faults); H8 is a magnitude-AND (alteration), H15 an orientation-AND (structure). No sibling computes cross-field gradient-orientation agreement. | **Viable now. PRIMARY.** `scripts/build_round4_features.py` channel 0; tested as `multi25_plus_h15` in `scripts/holdout_round4.py`. |
| **2 / low** | **H16 — active block-boundary strain-gradient ridges.** Supplied `geod_dilaterate` (B8), `geod_shearrate` (B7). | \|\|∇dilaterate\|\| + \|\|∇shearrate\|\| (robust per-field normalization), then max over four oriented 9 px line kernels, robust-normalized. Marks **boundaries** between differentially straining crustal blocks rather than straining interiors. | Geodetic strain accumulates on active faults with kyr recurrence and no Holocene rupture; the block boundary localizes the fault better than the block interior. Null: smooth interpolated strain with no resolvable edge; network artifacts. | H2 uses shear×dilation *products* (magnitudes); 11GEMSDOE-H1 used strain *coherence* (failed) — a gradient ridge is a different statistic (edge, not coherence). No sibling computes spatial gradients of the strain fields. | **Viable now.** Channel 1; secondary arm `multi25_plus_h16`. |
| **3 / low** | **H17 — gravity VG zero-contour ∩ HG ridge coincidence.** Supplied `iso_grav_anom_vg` (B11), `iso_grav_anom_hg` (B18). | Zero-crossing mask of VG (sign change in 3×3 neighborhood) × normalized \|HG\| ridge strength, aggregated as a 5 px mean (intersection-density style), robust-normalized. Near-vertical density-contact signature. Builder **fails loudly** if VG has no sign change in-footprint (guard against a magnitude-only input). | Steep range-bounding/intrabasin normal faults under alluvial fans have no scarp but a strong basement density contrast; VG-zero + HG-max is the textbook contact signature (Grauch & Hudson, 2002). Null: dipping contacts, intrusive edges. | H1 uses \|\|∇(hg)\|\| — the gradient of an already-derived gradient — a different quantity from \|hg\| strength at a VG zero. Nobody uses VG sign topology or zero-contour logic. GEMSDOE10-H14 attacks the same goal via upward continuation, a different method. | **Viable now.** Channel 2; secondary arm `multi25_plus_h17`. |
| **4 / low** | **H18 — total-curvature (`tc`) lineament topology.** Supplied `tc` (B6) only. | Robust-normalized `tc` → max over four oriented 9 px line kernels → robust normalization. Total curvature peaks over magnetic contacts **regardless of strike**, unlike directional derivatives that fade for parallel strikes. | Strike-independent detection catches faults parallel to the survey/derivative direction that directional transforms miss; magnetic contacts persist under non-magnetic cover. Null: lithologic/cultural magnetic relief; orientation persistence required. | H3 computes tilt from B9/B3 and takes its gradient — verified uncorrelated with `tc` (corr 0.013/0.021). No sibling derives topology from the `tc` band itself. (GEMSDOE10's computed tilt/curvature features are a related family; this claim is inspection-bounded.) | **Viable now.** Channel 3; secondary arm `multi25_plus_h18`. |
| **5 / high (external)** | **H19 — optical/SWIR alteration corridors (Sentinel-2 L2A).** ESA Copernicus Sentinel-2 L2A surface reflectance via AWS Open Data (`s3://sentinel-s2-l2a`, verified: license "free, full and open", [registry](https://registry.opendata.aws/sentinel-2/), L2A access with no AWS account required). | Clay ratio (B11/B12 SWIR) and ferric-oxide ratio (B4/B2) mosaicked over the footprint, cloud-masked (SCL), regridded to the 100 m template; alteration-corridor topology = linearly connected high-ratio patches intersected with fault-like magnetic boundaries (corridor topology as in H12, optical source). | Fault-related argillic/iron-oxide alteration can mark fluid pathways with no scarp. Null: pedogenic/lithologic clays, agriculture, burn scars. | No sibling uses optical/SWIR reflectance alteration; distinct from gamma radiometric ratios (different physics, different sensor). | **DEFERRED — not viable in this sandbox.** S3 HTTPS verified blocked (000) 2026-09-27. Viable only via GitHub-runner transport (GEMSDOE10 ext/* pattern) with per-scene hashes, license file, and footprint/coverage census. Do not make a submission claim from it. |

## 4. Frozen Round-4 release rule

`scripts/holdout_round4.py` uses the exact frozen spatial protocol (512 px
blocks, 12 px collar, seed 12027, pixel-exact catalogue mask on the FP term,
binary top-2% emission, leakage probe ≈ 0 required):

- **PRIMARY gate:** `multi25_plus_h15` passes iff mean paired DTI vs `multi25`
  is **> 0 AND** it wins **≥3/4** folds. A pass authorizes *further packaging
  consideration only* — the standing strongest-sibling-baseline gate, format
  validation, and provenance checks remain unsatisfied and are still required
  before any weekly slot is spent.
- **Secondary arms** (H16/H17/H18, ablations) are reported with paired deltas;
  ≥3/4 + mean>0 marks them "eligible for follow-up", never for release.
- **H6′ is a measurement arm** (§5): no release eligibility attaches to any
  geometric arm in Round 4 regardless of score.
- A loss, a 1–2 fold split, a missing source hash, a label-derived feature, or
  a format-valid TIFF is not a qualification. Do not tune thresholds on these
  folds afterward. No GeoTIFF is packaged from a failing arm; no weekly slot
  is spent in this session under any outcome.

## 5. H6′ exact preregistered form (prior lead, measurement only)

From **train traces only** per fold: endpoints = 8-connectivity degree-1
pixels; direction = centroid-away (endpoint minus window centroid of trace
pixels within 8 px Chebyshev; **straight — no magnetic fabric blending**),
reusing `straight_rays()` from `scripts/holdout_terminals.py` verbatim so the
geometry is exactly the Round-2 control arm; cast **5 px** rays with pixel
rounding, stopping at the grid edge or on a train trace. Emission: ray pixels
in the test region at 1.0, then virgin top-up — test-region pixels ranked by
the fold's `multi25` probability, excluding pixels within 3 px of any train
trace — filled to exactly 2% of the region, binary (deterministic tiebreak,
never triggered: if rays alone exceeded budget, keep the multi25-top-ranked
ray pixels). Evaluated (a) on the masked spatial holdout as `h6prime_hybrid`,
and (b) on the terminal-truncation simulator
(`scripts/holdout_terminals.py` protocol) against the equal-mass random
control. Success criterion for the *mechanism* (not for release): terminal
DTI clearly above random (>0.15 vs ~0.11) as in Round 2.

> **Erratum on preregistration wording (2026-09-27, before results were
> inspected for selection):** the first draft of this section said "PCA major
> axis"; the reused Round-2 function — and both Round-2 geometric arms — use
> the centroid-away vector, which is what the code computes. The wording is
> corrected here to match the implementation; the implementation was not tuned
> (it is the verbatim Round-2 control). Likewise the H15 joint edge weight is
> capped at 1.0 in the product (`clip(joint, 0, 1)`), an anti-dominance detail
> omitted from the §3 shorthand; it only down-weights, never re-ranks, extreme
> single-field edges.

## 6. Preregistered multi30 single-channel ablations (diagnostics)

Round 2 rejected the H8/H9/H7/H10 bundle (−0.00183, 2/4) without testing
channels singly. Each ablation trains the frozen GBM on 25+1 channels:
`multi25_h8` (ch25), `multi25_h9x` (ch26), `multi25_h9d` (ch27),
`multi25_h7` (ch28), `multi25_h10` (ch29). Reported as paired deltas vs
`multi25`; a passing single channel becomes a follow-up candidate, not a
release. This closes the recorded Round-2 limitation either way.

## 7. Official source ledger (manual review)

| Claim used above | Source | What was verified | Boundary |
|---|---|---|---|
| Competition target, supplied layers, external-data license rule | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Target = expert-identified faults absent from the database; lists conductivity, detrended elevation/slope, strain rates, gravity, magnetics, earthquake density; external data allowed iff licensed for challenge use and sharing with sponsor. | Does not endorse any transform. |
| Known catalogue pixels masked/excluded both rounds | [Staff 11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) | chrisk-dd (Staff): "Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from evaluation … Re-evaluation will also mask/exclude". | Geometry unspecified there; pixel-exact in 11516/4. |
| Mask is pixel-exact; near-catalogue predictions fully penalized; new truth may sit within 300 m of known traces | [Staff 11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) | chrisk-dd: "The mask is indeed pixel-exact … A new-fault ground truth pixel can indeed lie within 300m of a known fault trace." | Does not show hidden labels favor any mechanism. |
| New fault incl. new geometry of existing systems | [Staff 11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2) | "any fault pixel not already captured by USGS/INGENIOUS … can include newly mapped geometry of an existing fault system". | Same boundary. |
| Leaderboard snapshot 2026-09-27 | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | #1 DARD 0.3168; 0.1563 × 3 (#26–28 extradr19, SDCF9, smashi34). | Time-stamped snapshot, not a live claim. |
| Potential-field contact interpretation over Basin-and-Range faults | [USGS OFR 02-0400](https://pubs.usgs.gov/of/2002/ofr-02-0400/ofr-02-0400.pdf) | Grauch & Hudson: gravity/magnetic anomaly interpretation over faults (literature precedent). | Precedent only; does not validate H15/H17 detectors. |
| Tilt derivative for contact mapping | Verduzco et al. (2004), The Leading Edge | Tilt-derivative horizontal gradient peaks over vertical contacts (H3 precedent; contrast for H18). | Same boundary. |
| Geodetic strain / permeable conduits | Siler et al. (2019) framing via prior register | Modern strain on active faults (H16 motivation). | Same boundary. |
| Sentinel-2 L2A free/open, no-account S3 access | [AWS Open Data Registry](https://registry.opendata.aws/sentinel-2/) | License "free, full and open"; `s3://sentinel-s2-l2a`, `aws s3 ls --no-sign-request`. | Obtainable in principle; blocked in this sandbox (verified 000). |
| Sibling negatives/lessons adopted | GEMSDOE10/HYPOTHESES.md, 11GEMSDOE/docs/HYPOTHESES.md, 7GEMSDOE knowledge/next_session.md (read 2026-09-27 via GitHub API) | H21 decisive negative; H20 released; H19 rejected; H1-strain rejected; H9-radiometric closed. | Sibling self-reports, not independently reproduced here. |

## 8. Measured validation — 2026-09-27 (single frozen run, no tuning)

Features built after preregistration (`scripts/build_round4_features.py`,
output `6e3d48cc85d2…`, `labels_used: false`,
[`evidence/round4-feature-build.json`](../evidence/round4-feature-build.json)).
Channels are near-independent (max cross-corr 0.17). Frozen test run once via
`scripts/holdout_round4.py`; full report
[`evidence/holdout_round4.json`](../evidence/holdout_round4.json) (+ `docs/`
copy). Leakage probe 0.0000 all folds. `multi25` and `random02` reproduce
Rounds 2–3 to full precision on every fold (determinism check passed).

| Arm | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Mean | Paired vs multi25 |
|---|---:|---:|---:|---:|---:|---|
| multi25 reference | 0.07800 | 0.09197 | 0.06678 | 0.12611 | **0.09071** | — |
| **multi25+H15 (PRIMARY)** | 0.08128 | 0.09786 | 0.07588 | 0.11954 | **0.09364** | **+0.00293, 3/4** |
| multi25+H16 | 0.07800 | 0.09508 | 0.06593 | 0.12646 | 0.09137 | +0.00065, 2/4 |
| multi25+H17 | 0.07800 | 0.09671 | 0.06678 | 0.12611 | 0.09190 | +0.00119, 1/4 |
| multi25+H18 | 0.07672 | 0.08970 | 0.06080 | 0.11271 | 0.08498 | −0.00573, 0/4 |
| multi25+H8 (ablation) | 0.08318 | 0.09066 | 0.05332 | 0.13155 | 0.08968 | −0.00103, 2/4 |
| multi25+H9x (ablation) | 0.07800 | 0.09197 | 0.07334 | 0.12449 | 0.09195 | +0.00124, 1/4 |
| multi25+H9d (ablation) | 0.07729 | 0.08864 | 0.06098 | 0.12926 | 0.08904 | −0.00167, 1/4 |
| multi25+H7 (ablation) | 0.07909 | 0.09565 | 0.06678 | 0.12611 | 0.09191 | +0.00120, 2/4 |
| multi25+H10 (ablation) | 0.07295 | 0.08947 | 0.06397 | 0.11684 | 0.08581 | −0.00490, 0/4 |
| h6prime_hybrid | 0.07800 | 0.09197 | 0.06678 | 0.12611 | 0.09071 | 0.00000 (degenerate, see below) |
| h15_standalone | 0.02386 | 0.03977 | 0.01610 | 0.02656 | 0.02657 | weak standalone |
| random02 control | 0.13711 | 0.14331 | 0.14098 | 0.13011 | 0.13788 | calibration anchor |

PRIMARY paired deltas: +0.00328, +0.00589, +0.00910, −0.00657.

### Verdicts

- **PRIMARY H15: PASSED as a research signal only** (+0.00293 mean, 3/4 folds).
  Per the frozen rule this authorizes *further packaging consideration only*.
  No GeoTIFF was built from H15, no weekly slot was spent, and the standing
  strongest-sibling-baseline gate plus independent final gates remain
  unsatisfied. Gains concentrate on folds 0–2; fold 3 (densest truth) reverses
  (−0.00657) — recorded, not tuned.
- **H16/H17: follow-up eligible at best, not passing** (2/4 and 1/4; exact
  0.00000 ties on some folds mean the GBM ignored the channel there).
- **H18 REJECTED** (0/4, −0.00573): the `tc` quantity is independent of tilt
  (verified pre-registration) but its lineament topology hurts under this
  protocol. Independence ≠ skill.
- **Ablations close the Round-2 limitation:** no single multi30 channel passes
  (best: H9x +0.00124 1/4, H7 +0.00120 2/4). H8 is volatile (+0.005/−0.013
  across folds, mean −0.00103). **H10 is harmful on all 4 folds** (−0.00490)
  and should be dropped from any future bundle.
- **H15 standalone is weak (0.0266)** while H15+GBM gains (+0.00293): the gain
  is interaction-driven, matching GEMSDOE10-H20's lesson (univariate AUCs
  ~0.5, interaction gain real).
- **H6′ spatial arm is degenerate by construction (paired 0.00000, exact).**
  Post-hoc geometry audit: 5 px rays from endpoints ≥13 px (verified min
  endpoint distance 13.0) from any test region can never enter it
  (rays∩region = 0 on all folds), and the 3 px virgin exclusion provably never
  binds across the 12 px collar. So the hybrid ≡ multi25 top-2% exactly. This
  is a protocol-design finding, not a code bug: **no train-trace-derived
  geometry shorter than the collar can ever be tested on the collar-separated
  spatial holdout.** The mechanism test stands on the terminal simulator only.
- **Terminal mechanism check reproduces Round 2 bit-for-bit** on the mechanism
  arm: straight rays 0.2920284167756428 (exact, 16 decimals), 30,445 emitted,
  6,312 hidden, 831 components. The random control differs from Round 2
  (0.10447 vs 0.11333) because it is equal-mass to the *rays* here vs to the
  *gated H6 field* there — the correct comparator for this arm. Mechanism
  margin: **2.80× random**. The H6′ mechanism (short straight tip rays) is
  prospectively re-validated in its claimed regime; per preregistration it
  carries no release eligibility.
