# New experiment register — 2026-09-27

Written before candidate implementation. These are falsifiable hypotheses, not discovered faults or predicted numeric gains. Priority ranks expected DTI value qualitatively; no defensible numerical improvement forecast exists.

The checkout initially had no implementation. Sibling source inspections found CNN ensembles, boosting/pindrop, emission tuning, magnetic/gravity coherence, conductive-basement steps, strain tensors, inpainting, radiometric ratios, and DEM scarp/hysteresis work. Those are **not new proposals**. The old research-and-audit list is superseded. Novelty is bounded by the inspected source inventory, not a guarantee about unpublished team work. 9GEMSDOE and 10GEMSDOE tree requests returned 404; novelty there remains unknown.

| Priority / cost rank | Hypothesis and exact supplied layers | Physical signature / transform | Why potentially missing, and competing explanation | Distinction |
|---|---|---|---|---|
| 1 / 1 (medium) | **Displaced magnetic fabric:** `rtp`, `mag_anom` | Across four trial boundary orientations, compare local squared mismatch of magnetic textures on opposite sides; measure improvement when one side is shifted along strike by ±200 or ±400 m. This is a displacement-restoration score, not gradient strength. | A buried lateral offset may interrupt otherwise matching magnetic fabric without a mapped surface scarp. Sedimentary/igneous contacts and periodic texture can mimic a restoration match; it is not proof of slip. | No displacement-restoration descriptor found in inspected sibling feature code; unlike coherence, it asks whether two separated textures can be re-aligned. |
| 2 / 2 (medium-high) | **Depth-dependent edge migration:** `rtp`, `tmi`, `iso_grav_anom` | Upward-continuation scale-space followed by edge tracking; measure systematic lateral migration of an edge with continuation height rather than persistence alone. | Dipping buried contacts may project away from the strongest shallow edge and so mark an unmapped surface continuation. Magnetic remanence and nonfaulted dipping contacts are alternatives. | Existing multiscale magnitude/coherence does not estimate the signed edge trajectory with observation height. Requires careful padding/taper and synthetic dip controls; not yet implemented. |
| 3 / 3 (high) | **Drainage deflection consistency:** `det_elev`, `det_elev_slope` | Extract valley network from local curvature, then detect repeated signed bends where multiple valleys cross a candidate line; use bend-direction consistency, not a scarp score. | Repeated stream deflection could identify an unmapped strike-slip lineament without a clear scarp. Lithology, fan channels, and detrending artefacts are major nulls. | Uses network crossing topology and repeated kinematics, not independent pixel relief/curvature. 100 m detrended elevation may be insufficient; stop if synthetic/visual tests fail. |

All three use already downloaded supplied bands. No external dataset is assumed viable or required. External 1 m DEM work is deferred, not silently claimed obtainable.

## Scientific grounding and boundaries of evidence

- [USGS magnetic mapping examples](https://pubs.usgs.gov/of/2002/ofr-02-0400/ofr-02-0400.pdf) describes magnetic patterns and gradients supporting fault interpretation and extrapolation; it does **not** validate our proposed descriptor or claim every magnetic edge is a fault.
- [USGS aeromagnetic interpretation](https://pubs.usgs.gov/of/1983/0170c/report.pdf) discusses possible fault offsets and ambiguous correlations. This motivates testing restored correspondence, including null controls, rather than asserting unique structural interpretations.
- [Official challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) defines the target as geological faults, not a directly observed list of geothermal vents. Physical mechanisms in the table remain hypotheses.

## Frozen screening protocol

Use the sibling 11GEMSDOE block assignment: 512-pixel blocks ranked by positive count with stable index tie-break, dealt among four folds. Exclude a 12-pixel collar from **all** training samples; hold out every pixel in test blocks, not random pixels. Features do not use fault labels. Refitting occurs per fold; no coordinates or catalogue distance are predictors. This spatial protocol is not whole-system geological independence.

Compare raw 19-band gradient boosting to raw bands plus restoration features. Fixed seed 12027; 100,000 randomly sampled training negatives plus all training positives; HistGradientBoosting, 100 iterations, 15 leaves, early stopping disabled. Fit sample weights balance classes. Fixed 6% emission area selected from preceding sibling work, not tuned on this experiment's holdout. Report each fold, pooled components, and matched random 6% control. No weekly submission regardless of screening result until the **current strongest reproducible sibling model** is retrained under this same protocol. Scores from different protocols cannot serve as that gate. No historic full-fit raster is accepted as an out-of-fold baseline.

## Measured result (after preregistration and implementation)

| Fold | Raw 19 | Restoration 27 | Matched random 6% |
|---|---:|---:|---:|
| 0 | 0.11703 | 0.12098 | 0.22139 |
| 1 | 0.12869 | 0.13337 | 0.20798 |
| 2 | 0.09729 | 0.09261 | 0.19802 |
| 3 | 0.13376 | 0.12698 | 0.17541 |
| Mean | **0.11919** | **0.11849** | **0.20070** |

**Reject candidate 1 for submission.** Mean paired delta −0.000704, only two of four folds won. The stronger random-area control makes promotion even less defensible. This is evidence against this descriptor/model/emission combination, not a proof that magnetic offsets have no geological value. No holdout threshold sweep or submission was performed. Do not submit the random control either: metric coverage alone is not geological discovery.

[Complete components and descriptive uncertainty](screening.json). The preregistration content hash from execution is retained there; this results section was appended afterwards. Both magnetic inputs are related fields, not independent physical corroboration. NaN support may reveal data coverage to the model; an eventual positive claim would require a support-matched ablation and independent physics. Candidates 2 and 3 remain unimplemented and unvalidated.
