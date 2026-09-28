# Round 8 — preregistered hypotheses (H37–H41)

> **Written before any Round-8 code was executed.** Rounds 5–7 established the format:
> a hypothesis is registered here with its physical signature, the layer it consumes, the
> falsification rule and the cost; the frozen holdout then decides. A hypothesis that fails
> is recorded as failed and is not re-entered in a later round.
>
> Round-8 decisions were shaped by two things verified on 2026-09-28: the **staff scoring
> clarifications** (`docs/knowledge-base.md` §1) and the **sibling byte audit**
> (`docs/sibling-audit.md`). Both changed the ranking below relative to the first draft, and
> the change is recorded in §3.4 rather than hidden.

## 1. What Round 7 left us

| Item | Value | Where |
|---|---|---|
| Shipped artifact | `12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif` | `docs/downloads/` |
| Frozen holdout, dense catalogue truth | 0.24586 (incumbent `multi25_h28` 0.22143, +0.0244, 4/4) | `evidence/holdout_round7.json` |
| Frozen holdout, sparse 20 % truth | 0.12732 (incumbent 0.11438, +0.0129, 4/4) | same |
| DrivenData score | **none — no slot spent** | `README.md` |
| Group's best public score | 0.1563 (identical bytes published by GEMSDOE and 5GEMSDOE) | `docs/sibling-audit.md` |

The structural finding of the sibling audit is that the whole group has been re-scoring a
2–3 % thin emission of a 19–25 band model trained on the *catalogue*, and that two of the
three 0.1563 rows are literally the same 570,890-byte file. A new round that only retunes
that emission is not a new strategy.

## 2. What changed on 2026-09-28

1. **Known-fault pixels are masked from the metric** (staff, thread 11516): "Pixels
   corresponding to known USGS/INGENIOUS faults are masked / excluded from evaluation, so
   they do not count towards penalty terms." Predicting them is therefore neither rewarded
   nor punished *if the masking is pixel-exact as described*.
2. **"New fault" means any fault pixel not already captured by USGS/INGENIOUS, and may be
   newly mapped geometry of an existing fault system** (staff, thread 11536). So new truth
   can lie inside the 300 m kernel of a mapped trace.
3. **`sample_submission.tif` is the catalogue itself** (verified bit-for-bit this session):
   copying the official example cannot score on the private set.
4. **Metric algebra** (`evidence/metric-algebra.json`): with `D = T/(0.2T+0.2E+0.8N_t)` the
   marginal test for accepting a pixel is `ΔT/ΔE > 0.2·D/(1−0.2·D)` = **0.0323** at the
   group's 0.1563 and **0.0677** at the leader's 0.3168 — i.e. the metric pays for recall
   far more than the group's frozen 2 % budget implies.

## 3. Registered hypotheses, ranked by expected gain ÷ cost

### H37 — catalogue base layer (p ← max(p, catalogue)) · **CONTROL, not an idea**
*Layer:* `data/labels.tif` (the USGS/INGENIOUS catalogue, = `existing_faults.tif`).
*Signature:* none; this is the specialisation of H28 to 100 % recall on known traces, and it
is the emission 8GEMSDOE published as `Hedge-v2`.
*Prediction:* on DrivenData it changes nothing (staff: masked; 8GEMSDOE's `max(ens12,
catalogue)` artifact is recorded at the same 0.1563 as the ens12 file it extends by 54,533
catalogue pixels). On the **dense catalogue truth** holdout it must dominate by construction,
so a dominance check is a *harness* test, not evidence about the hidden set.
*Falsification:* any protocol where the layer *lowers* the score means the mask/weighting in
our harness — or the platform's — is not what we think it is.
*Cost:* one `np.maximum`. *Rank: 5 (control).*

### H38 — marginal-rule mass instead of a frozen 2 % budget · rank 1 by algebra, 1st to test
*Layer:* the same model scores that produce the R7 emission; no new data.
*Signature:* none — this is a decision rule on the *rate* of emission. The algebra above says
the optimum is not "2 % of pixels" but "every pixel whose expected kernel-weighted true-positive
mass exceeds 0.2·D/(1−0.2·D) times its expected false-positive weight".
*Why it can find faults the catalogue misses:* it does not change the ranking at all; it
changes how far down the ranking we are willing to go. With β/α = 4, the tolerance for a wrong
pixel is high; every group artifact has emitted ~2 %, a budget inherited from Round 5 and never
re-derived from the metric.
*Falsification:* the sweep must beat the frozen 2 % on ≥3/4 folds with a positive mean on both
catalogue protocols; otherwise the 2 % budget stands.
*Cost:* one sweep over four pre-disclosed budgets. *Rank: 1.*

### H39 — USGS 3DEP 1 m lidar scarp descriptors (H32's sub-metre sibling) · rank 2
*Layers:* 11 quantised terrain descriptors + coverage, 100 m grid, from **USGS 3DEP 1 m DEM**
(official public bucket, 706/716 tiles), reduced at 2 m and aggregated per 100 m cell by
sibling 7GEMSDOE on GitHub runners (`evidence/lidar-fetch.json`; commit `2e7bf08`, build run
36266555805, SHA-256 pinned locally). Channels: `ex_max`, `ex_mean`, `step_max`, `lapneg_max`,
`lappos_max`, `downface_max`, `upface_max`, `cross_max`, `relief`, `coh100`, `strike` —
slope-excess, 10 m-vs-50 m step, ±Laplacian (crest/base), up/down-facing scarp asymmetry,
2 m micro-relief, 100 m coherence and strike.
*Physical signature:* the *scarp micro-morphology* of a fault trace at 1–2 m, which the
competition's 19 layers and our 10 m H32 channels cannot resolve. Ductile/oblique faults
without a sharp step are not expected to show here; fresh normal faults and the near-trace
geometry of reactivated systems are.
*Why it should catch catalogue gaps:* the catalogue is compiled from regional mapping at
coarser effective resolution, and the organisers' own cited reference (Hermant et al. 2025)
puts lidar-mapped traces up to ~400 m from catalogue traces — the lidar is the source that
*discovers* traces the compilation does not contain. Staff confirm a "new fault" may be newly
mapped geometry of an existing system.
*Distinctness (honest):* 7GEMSDOE built this product and pre-registered a lidar-vs-19-bands
test (claim: ridge skill ×2.33/1.81/1.47 at 0.5/1/2 %, 19 bands ×1.14/0.99/0.87 — a *sibling*
result, not re-verified here). It is new **to this repo** in the sense that 12GEMSDOE has never
tested it and never folded it into its frozen masked protocol or into the 25-channel
HistGradientBoosting spine. It is **not** a novel idea in the group, and 7GEMSDOE's own
lidar submission has still not been scored.
*Falsification:* must beat the Round-7 incumbent on ≥3/4 folds with positive mean gain on
**both** catalogue protocols, at the same budget. A win on the dense protocol alone is
insufficient (it would mean catalogue-shaped skill, not new-fault skill).
*Cost:* one 37 MB fetch (done, hash-pinned) + one extra arm per fold.
*Rank: 2 (highest expected gain, medium cost, external data already in hand).*

### H40 — graded emission instead of binarisation · rank 3
*Layer:* model scores again. The metric is linear in `p` (credit) and the FP term is linear in
`p` too, but the *ratio* is not: a pixel with `p = 0.4` costs 0.2·0.4·w and earns 0.4·k·1 in
unit terms. Kernel-weighted truth pixels usually have exactly one neighbour worth full credit,
so the optimum is generally a hard 0/1 field — **except** where a truth pixel sits between two
mutually exclusive candidate strands. H40 tests whether soft mass beats hard mass *at equal
expected FP*: `p' = clip((p − τ)/(1 − τ), 0, 1)`, τ ∈ {0.02, 0.032}.
*Falsification:* graded must beat its NMS counterpart on both protocols; the register expects
**no** gain (this is a negative result we want on the record).
*Cost:* trivial. *Rank: 3.*

### H41 — "gap proxy" target: distance-to-catalogue as an anti-target · rank 4
*Layer:* the catalogue alone. 5GEMSDOE reports its SGMC-gap proxy anti-ranks the real board
(ρ = −0.8) while the catalogue orders it at ρ = +0.9, and GEMSDOE10's H21 showed the INGENIOUS
QP v2 catalogue is *identical* to the labels — so "predict where the catalogue is absent" is
**refuted** as a target. H41 is therefore re-specified: use distance-to-catalogue *only* as an
FP-weight surrogate inside an emission rule, never as a label. Registered for completeness.
*Falsification:* already falsified as a label; do not spend a slot on it.
*Rank: 4.*

## 3.4 Register amendment (dated, before the frozen run)

Two changes were made after re-reading the staff answers and the audit, both **before** the
Round-8 harness was executed:

1. **H37 is a control, not a candidate strategy.** The first draft ranked it by its dense-protocol
   dominance; that dominance is an artefact of the dense protocol's truth *being* the catalogue.
   It is retained as a harness control and as the natural-experiment check.
2. **H38 is promoted to first test, H39 remains the primary scientific candidate.** Rationale:
   H38 is free and the algebra is decisive; if it works, the mint is the *budget*, and H39 stacks
   on top. Ranking is unchanged on the "primary arm" question (H39), changed on test order.

## 3.5 Decision rule (disclosed before the run)

* `chosen_arm` = the H39 arm **iff** it beats the Round-7 incumbent on ≥3/4 folds with positive
  mean paired gain on both catalogue protocols, at 2 %; otherwise the R7 incumbent.
* `chosen_budget` = over the pre-disclosed grid {0.02, 0.032, 0.05, 0.08}, the argmax of
  `min(mean dense, mean sparse)` for the chosen arm, accepted only if it beats 2 % on ≥3/4 folds
  on both protocols; otherwise 0.02.
* Shape of the shipped field: **no catalogue base layer** (metric-neutral by staff statement and
  by the 8GEMSDOE natural experiment; shipping it would only make the file look like a copy of
  the training labels to a human reviewer in Phase 2).
* Leakage probe (truth∩training dilated 3 px) must be 0.0 on **every** fold of every protocol.
* No DrivenData slot is spent by this round. Uploading remains a human decision.

## 4. Protocols

Frozen protocol (unchanged from Rounds 5–7): 512-px blocks, 12-px collar, seed 12027,
pixel-exact catalogue mask on the FP weight, NMS radius 2 (5×5), DTI with the literal kernel
`k = max(1 − d/3, 0)`. Two catalogue protocols — `dense_catalogue_truth` and
`sparse_thinned_20pct` (seed 4242+f) — plus two new **offset** protocols that translate every
held-out component by 1–3 px (`offset_adjacent_1_3px`, inside the kernel: a proxy for "a
neighbouring parallel strand") or 4–6 px (`offset_far_4_6px_control`, outside the kernel:
the anti-proxy). The offset protocols measure the *mechanism* (how much free credit a field
gets from being near a mapped trace) and are reported as diagnostics, **not** as gate criteria.

## 5. Rejected before testing (do not re-propose)

* Catalogue-difference targets — refuted by GEMSDOE10 H21 (INGENIOUS v2 == labels).
* Radiometric lineament arm — 7GEMSDOE H9, failed its promotion rule.
* Strain-coherence arm — 11GEMSDOE H1, rejected (0.149795 vs 0.149986 control).
* Thin/blur emission retunes of the same 19–25 channel model — the group's 0.1563 plateau.
* Unmasked dense screen as a selector — uniform random 6 % (≈0.20) beats every learned arm;
  the diagnostic is retained but cannot authorise a submission (`docs/session-review.md`).

## 6. Frozen-run results (executed 2026-09-28) — `evidence/holdout_round8.json`

The harness first re-ran the **R7 incumbent inside this run** and reproduced
`evidence/holdout_round7.json` to full float64 precision (`r7_reproduced_within = 0.0` on both
catalogue protocols), so every number below is directly comparable to Round 7.

| Lever | dense | sparse | offset 1–3 px | offset 4–6 px | verdict |
|---|---|---|---|---|---|
| R7 incumbent `multi25_h28_dem12`, NMS @2 % | 0.24586 | 0.12732 | 0.21247 | 0.20266 | reference |
| H39 lidar12 arm, NMS @2 % | 0.25326 (4/4) | 0.13018 (2/4) | 0.21772 | 0.20802 | **fails** (sparse 2/4 folds) |
| H38 mass 3.2 % | 0.27705 (4/4) | 0.11705 (0/4) | 0.23933 | — | split, not accepted |
| H38 mass 5 % | 0.27995 (3/4) | 0.09821 (0/4) | 0.24124 | — | split, not accepted |
| H38 mass 8 % | 0.25106 (3/4) | 0.07332 (0/4) | 0.21393 | — | split, not accepted |
| H40 graded τ = 0.02 | −0.17100 vs NMS | −0.11028 | — | — | negative, as predicted |
| H37 catalogue base @2 % (control) | +0.51466 | +0.24990 | +0.20927 | +0.09980 | control only |

Leakage probe 0.0000 on every fold of all four protocols. `gate.passed = false`;
**no artifact was packaged and no DrivenData slot was spent.**

### Why the mass sweep is not a win, despite +0.031 on the dense protocol

The two catalogue protocols disagree in *sign*, and the disagreement is systematic: the dense
protocol's truth **is** the catalogue, so any pixel that re-traces a catalogue strand is paid
for; the sparse protocol keeps only 20 % of the components and therefore charges the same
pixels at the full FP weight. The only measurement of marginal mass that exists against the
**real** board is the sibling anchor's 0.1563 → 0.1560 pair: +10,668 emitted pixels (9,430 of
them off-catalogue and therefore chargeable) moved the public score by **−0.0003**. That is
≈ zero, and it is ~30× closer to the sparse protocol's elasticity (−0.0103 for +60 % mass) than
to the dense protocol's. Mass is therefore a coin-flip whose sign depends on the unknown
density of the hidden truth, and a coin-flip cannot authorise a submission.

### What survives, and what it changes

* **H37 is retired from the strategy list.** Its gain exists only in a protocol whose truth is
  the catalogue; the platform pays nothing for it (staff ruling 11516 plus the sibling
  `max(ens12, catalogue)` artifact that matches the score of the file it was derived from —
  inference flagged, no upload receipt). Shipping the catalogue layer would only make the
  field look like a copy of the training labels to the Phase-2 expert panel.
* **H39 is the best ranking improvement found this round** (dense 4/4, mean +0.0074) but fails
  the pre-registered sparse criterion. It stays the leading candidate for a future round — and
  the clean way to settle it is a *scored* upload of a lidar field pinned to the same budget,
  which is the one measurement this sandbox cannot make.
* **H38 survives as a cap, not a target**: the marginal rule `ΔT/ΔE > 0.2·D/(1−0.2·D)`
  (≈ 3.2 % at the group's level) says where the frontier lies, and the honest reading of the
  real-board pair is that the frontier is where the incumbent already stands.
* **H40 is negative** and stays negative.
