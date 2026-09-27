# Round-2 Candidate Geological Hypotheses (H6–H10) — 12GEMSDOE

> Preregistered 2026-09-27 before the masked holdout finished. Falsifiable
> hypotheses, not discoveries. Ranking is qualitative scientific judgment, not a
> predicted DTI gain. No weekly submission slot is spent unless a candidate beats
> the current masked-holdout best on the same protocol.

## What is already taken (do not re-propose)

Mechanism-level inventory across this repo and inspected siblings (GEMSDOE,
GEMSDOE2/3/4, 5/6/7/8GEMSDOE, GEMSDOE9/10, 11GEMSDOE; 9GEMSDOE tree 404):

- Pixel classifiers on raw + derived bands (GBM, CNN ensembles incl. the 0.1563 `ens12` file)
- Magnetic edges / tilt / coherence / analytic signal; gravity gradients / coherence
- Basement gradient / Laplacian / relief / coherence; conductivity gradient / scalars
- Strain scalars / tensors / products; DEM scarp magnitude / curvature / slope (100 m and 1 m lidar)
- Radiometrics raw / ratios / derivatives (7GEMSDOE H9: FAILED 0–1/5 folds as primary arm)
- Seismic density scalars; displacement-restoration texture matching (this repo `core.restoration`, GEMSDOE10 H13)
- Upward-continuation edge tracking (GEMSDOE10 H14); Frangi/Gabor ridges (GEMSDOE10)
- Straight tip rays, halo exclusion, Hessian-NMS ridges, SGMC cross-catalogue targets (GEMSDOE3)
- Trace-inpainting objective (11GEMSDOE H4, parked); emission-geometry sweep; pindrop nodes/dense
- Odd-step topographic kernel (GEMSDOE10 H12, planned); interaction-zone cross-connectors (7GEMSDOE H10, protocol only)

## Ranked candidates

| Rank / cost | Hypothesis and exact supplied layers | Physical signature / transform | Why it should catch a fault missing from the catalogue | Distinction from implemented work |
|---|---|---|---|---|
| **1 / low** | **H6: fabric-curved tip extension + splay fans + relay bridges, geophysically gated.** Layers: `labels.tif` skeleton (train folds only in holdout), `rtp` (B2) fabric orientation, gate fields `tmi_vg/tmi_hg` tilt gradient, `iso_grav_anom_hg` (B18), `cond_surf` (B17) | Endpoints from 8-connectivity degree-1 pixels; tangents from last-8px PCA blended 60/40 with local magnetic-fabric strike; curved 15px tip rays + ±20° 8px splay fans + 5–20px inter-component relay bridges. Emission only where an unsupervised gate passes (tilt/gravity/conductivity edge > p70 or alteration > p80). | Staff: "new fault means any fault pixel not already captured by USGS/INGENIOUS and can include newly mapped geometry of an existing fault system" ([11536/2](https://community.drivendata.org/t/where-do-you-draw-the-line/11536/2)); new truth may sit within 300 m of known traces ([11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)). Cartographers stop lines where surface expression fades; the fault continues. Competing explanation: rays may follow lithologic fabric, not slip planes — the gate and the holdout decide. | GEMSDOE3 rays are straight, 5px, ungated. 7GEMSDOE H10 covers cross-connectors only and explicitly excludes main-trace extensions; H6 does curved extensions + splays + relays with a two-stage propose-then-gate mechanism no sibling implements. |
| **2 / low** | **H8: hydrothermal alteration joint anomaly.** Layers: `cond_surf` (B17), `rtp` (B2) | `zplus(cond) × zplus(−rtp)`: multiplicative AND of conductivity HIGH with demagnetization LOW (robust median/IQR normalization). Rationale: the contest targets faults *indicative of geothermal resources*, i.e. fluid conduits; circulating fluids destroy magnetite while raising conductivity. | Blind geothermal conduits under basin fill have no scarp; the alteration halo is the only signature (cf. Faulds & Hinz 2015 on concealed Basin-and-Range systems). Competing explanation: conductive clays / lithologic magnetics with no fault. | All prior conductivity use is gradient/edge-based (H1) or scalar; no sibling implements a joint magnitude-AND alteration detector. |
| **3 / low** | **H9: gravity–magnetic cross-gradient transfer intersections.** Layers: `iso_grav_anom` (B13), `rtp` (B2) | Cross-gradient magnitude `\|∇g × ∇m\|` (median-normalized) + intersection density (fraction of >p90 pixels in 5px window). High-angle intersections of density and magnetic boundaries mark accommodation/transfer zones with peak fracture permeability. | Transfer faults are short, covered, systematically omitted from surface-biased maps. Competing explanation: intersecting lithologic contacts. | Siblings use gravity/magnetic features additively in classifiers; none computes an explicit multiplicative intersection field. |
| **4 / medium** | **H7: microseismic strike-alignment correlogram.** Layers: `ieq_n100a15` (B16) | Max over 8 strikes of (along-strike NCC − across-strike NCC) of earthquake density in 9px windows with ±200 m lag pairs. Detects *aligned* swarms, not density highs. | Blind seismogenic faults produce instrumental microseismicity with no Holocene scarp. Competing explanation: the `n100` smoothing radius may erase lineament-scale signal; quarry blasts / network artifacts. | Prior seismic use is scalar density (incl. our H2 multiplier). Hessian/Frangi ridges exist (GEMSDOE10) but a directional along-vs-across correlogram does not. |
| **5 / low** | **H10: residual cover conductance.** Layers: `cond_surf` (B17), `depth_to_base_surf` (B15) | `cond − median_trend(cond \| depth)`: conductivity residual after removing the 50-quantile cover-thickness trend. Positive residual = anomalously fluid/mineralized cover for its thickness. | Shallow reservoirs under thin cover vs deep conductors are indistinguishable in raw conductivity; the residual isolates the anomalous component. Competing explanation: clay-rich cover units. | Both layers were used only separately or via gradients; no residual-coupling transform exists in siblings. |

## External-data check

All five candidates use supplied bands + training labels only. No external dataset
is required. (Reference: GDR 1391 thermal/paleo-discharge archives are currently
not downloadable from this sandbox — GEMSDOE10 independently reports TLS failure —
so no thermal candidate is proposed as viable here. USGS 3DEP 1 m DEMs remain
obtainable via AWS PDS per 7GEMSDOE's 706-tile build, but H1-lidar attribution is
still pending there; no lidar candidate is proposed until that score is attributed.)

## Frozen validation protocol (`scripts/holdout_masked.py`)

1. Same 512px block folds + 12px collar + seed 12027 as round 1 (comparable geography).
2. **Official pixel-exact catalogue mask on the FP term** (staff 11516/2, 11516/4).
   Truth = test-block labels only.
3. Leakage probe: 3px dilation of train traces vs test truth; must be ≈ 0 or the
   split leaks through the 300 m kernel.
4. Binary top-2% emission inside each score region (leaderboard-winning density
   regime per 7GEMSDOE forensics: leader ≈ 4–5× random at 1–2%).
5. Arms: `raw19` GBM, `multi25` GBM (round-1 best, same hyper-parameters),
   `multi30` GBM (+H8/H9/H7/H10 channels), `h6_geometric` standalone,
   `h8_alteration` standalone, `random02` control.
6. Release rule: no submission file is built or published from round 2 unless a
   candidate beats `multi25` on this protocol. Results land in
   `evidence/holdout_masked.json` (mirrored to `docs/`).
7. H6 is additionally tested on two geometric simulators: whole-component
   holdout (`scripts/holdout_trace.py`) and terminal truncation
   (`scripts/holdout_terminals.py`), each with equal-mass random controls.

## Measured results (2026-09-27)

### Masked spatial holdout (`evidence/holdout_masked.json`, binary top-2%)

| Arm | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Mean | Paired vs multi25 |
|---|---|---|---|---|---|---|
| raw19 GBM | 0.08052 | 0.09113 | 0.05550 | 0.11695 | 0.08602 | — |
| **multi25 GBM (round-1 best)** | 0.07800 | 0.09197 | 0.06678 | 0.12611 | **0.09071** | — (+0.00469 vs raw19, 3/4 folds) |
| multi30 GBM (+H8/H9/H7/H10) | 0.07898 | 0.09874 | 0.06140 | 0.11643 | 0.08889 | −0.00183 (2/4 folds) |
| h6_geometric | 0.01024 | 0.01515 | 0.00281 | 0.01737 | 0.01139 | invalid test (only 43/95,212 gated px fall in test blocks) |
| h8_alteration standalone | 0.01576 | 0.02139 | 0.02866 | 0.03163 | 0.02436 | weak standalone |
| random02 control | 0.13711 | 0.14331 | 0.14098 | 0.13011 | 0.13788 | calibration anchor (dense-truth effect), not a promotion bar |

Leakage probe (3px train-trace dilation vs test truth): **0.0000 on all 4 folds** —
the split is leakage-free through the 300 m kernel.

### Trace-component holdout for H6 (`evidence/holdout_trace.json`)

| Arm | Mean DTI (4 folds) |
|---|---|
| h6_geometric (gated) | 0.11269 |
| random equal-mass | 0.18823 |
| train dilation 3px reference | 0.05678 |

H6 beats naive dilation 2× but loses to equal-mass random: randomly hidden whole
traces are mostly *not* extensions of visible ones, so this simulator is wrong
for an extension claim.

### Claimed-regime + gate ablation (`evidence/h6_regime.json`)

Hidden truth within 20px of train endpoints (78.9% of hidden pixels):
gated H6 0.12523 vs random 0.16577 vs **ungated geometry 0.13937**.
The p70 geophysical gate *hurts* (−0.014): under β = 0.8, recall loss outweighs
precision gain.

### Terminal-truncation holdout (`evidence/holdout_terminals.json`)

Terminal quartile of half the ≥12px components hidden (6,312 px — the direct
extension simulator):

| Arm | DTI | × random |
|---|---|---|
| **straight 5px tip rays (prior-art baseline)** | **0.29203** | 2.6× |
| curved 15px + splays, ungated | 0.17730 | 1.6× |
| h6 gated (preregistered) | 0.14723 | 1.3× |
| random equal-mass | 0.11333 | 1.0× |

## Verdicts

- **multi30 (H8/H9/H7/H10 bundle): REJECTED as an upgrade.** −0.00183 mean vs
  multi25, wins 2/4 folds. No release. (Individual-channel ablations not run;
  recorded as a limitation — a single channel may still carry skill.)
- **H6 gated (preregistered form): REJECTED in current form.** Loses to random on
  whole-component holdout and to its own ungated ablation in every geometric test.
- **H6 mechanism (near-catalogue tip geometry): VALIDATED in its claimed regime.**
  All geometric arms beat random on hidden terminals (1.3–2.6×). But the winning
  form (short straight rays) was a *control arm*, not the preregistered
  candidate — promoting it now would be post-hoc. It is recorded as the
  **round-3 lead (H6′)**: preregister short-ray + virgin-lineament hybrid at ~2%,
  validate on both holdouts, then consider release.
- **multi25 vs raw19 on the masked protocol: +0.00469, 3/4 folds.** The round-1
  feature family shows skill under official mask semantics — partial
  re-qualification of the standing artifact's skill gate (sibling-baseline
  reproduction still outstanding, see session-review §6.5).
- **No weekly submission slot spent.** Per the frozen rule, neither failed
  candidate is packaged. The standing `06ca61e5` file keeps format approval.

## Scientific grounding (precedent only — does not validate our detectors)

- Faulds, J.E. & Hinz, N.H. (2015): >70% of Great Basin geothermal systems in
  step-overs / relay ramps / fault tips — motivates H6 relay/splay geometry and
  H9 transfer intersections. ([GDR 1391](https://gdr.openei.org/submissions/1391))
- Verduzco et al. (2004), tilt derivative for contact mapping — H6 gate field.
- Grauch & Hudson (2002), [USGS OFR 02-0400](https://pubs.usgs.gov/of/2002/ofr-02-0400/ofr-02-0400.pdf):
  aeromagnetic/gravity anomaly interpretation over Basin-and-Range faults — H9.
- Siler et al. (2019), stress/kinematics and permeable conduits — H8 fluid-conduit framing.
