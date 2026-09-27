# 12GEMSDOE — GEMS Prize research and submission workbench

> **Read this brief at the start of every work session.** The goal is to build an auditable, reproducible pipeline that finds plausible unmapped geologic faults, validates them without leakage, and exports a competition-valid GeoTIFF. Maximize the probability of a scientifically defensible win; own the outcome. A leaderboard score is evidence, not geological truth.

## Current state (2026-09-27)

This checkout contains only this README and no model, scripts, website, datasets, archived predictions, spatially blocked holdout, or experiment records. Therefore the claimed historical scores and methods below are user-supplied and cannot be independently verified from this repository. **No submission can currently be regenerated or compared, and no candidate can be holdout-validated.** No submission slot has been used or modified in this work.

The official public leaderboard currently displays a top public DW-Tversky score of **0.3049**. Our listed 0.1563 results tie, but that alone does not establish duplicated prediction rasters: metric rounding, a shared baseline, or genuinely identical files could all explain a tie. Compare prediction files by SHA-256, raster metadata, nodata mask, and pixelwise equality before concluding duplication. See [research and audit notes](docs/research-and-audit.md).

## What we are building

1. Data provenance inventory with source URL, retrieval date, license/terms, checksum, CRS, transform, dimensions, bands, nodata, and source attribution.
2. Deterministic preprocessing and experiment tracking; keep training labels separate from spatially blocked validation labels.
3. Distinct hypotheses with explicit physical signature, target layers, catalogue-gap rationale, competing explanations, and falsifiable tests.
4. Spatially blocked evaluation using the competition's metric and documented baselines. Do not use public leaderboard feedback as a substitute for validation.
5. One-click local export of a **single-band GeoTIFF** aligned exactly to the provided sample submission grid, with finite predictions in `[0,1]`, valid nodata handling, and preflight checks. Do not claim competition compatibility until tested against the actual sample file.
6. A simple public-facing site that makes the validated downloadable submission obvious, explains the submission steps, and links evidence and limitations.

## Non-negotiable experiment gate

A new idea must beat the current spatially blocked holdout best under a pre-registered, comparable split and metric before it is considered for a weekly submission slot. Report uncertainty and geographic coverage, not only one score. Do not select ideas based only on public leaderboard results. A candidate that depends on absent data is not viable until an official free source is verified obtainable and licensing is checked.

## Getting started each session

- Read this README and `docs/research-and-audit.md` first.
- Check `git status`, inspect data availability and provenance, then reproduce the current best baseline before changing it.
- Keep candidate code/results separate; record config, code revision, data checksums, validation blocks, metric, and submission checksum.
- If data is absent, do not fabricate results: state the precise blocker and proceed with useful, verifiable work.

## Competition and official references

- [Competition home and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description, datasets and scoring](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Data download page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — authenticated; unauthenticated access redirects to login.
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN metadata](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS GeoDAWN study area record](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [Submission instructions PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

## Access and limitations

Competition data is gated behind a DrivenData login. No credentials or data files were present in this checkout, and this agent cannot sign in as the user. Do not bypass access controls. The linked Dropbox items in the request are not official provenance by themselves; verify identity, checksums, terms, grid alignment, and that each file is authorized before use. GPU availability, package environment, competition deadline/round status, and historical outputs have not been verified. The official leaderboard is public and was accessible at review time.

## Historical scores supplied by the team (not independently verified)

| Name | Reported score | Evidence available in this checkout |
|---|---:|---|
| GEMSDOE1 | 0.1563 | User-provided only |
| GEMSDOE2 | 0.1560 | User-provided only |
| GEMSDOE3 | 0.1193 / 0.0830 / 0.1152 | User-provided only; multiple runs not identifiable |
| GEMSDOE4 | 0.0343 | User-provided only |
| 5GEMSDOE | 0.1563 | User-provided only |
| 6GEMSDOE | 0.0286 | User-provided only |
| 7GEMSDOE | 0.1461 | User-provided only |
| 8GEMSDOE | 0.1563 | User-provided only |
| 9GEMSDOE | 0.0107 | User-provided only |
| 10GEMSDOE | Not supplied | User-provided only |
| 11GEMSDOE | 0.0202 | User-provided only |
| 12GEMSDOE | Not supplied | User-provided only |

These are not verified against team pages or submission records. No inference about model quality or duplicate files should be made from this table alone.

## Work remaining

1. Obtain the competition-authorized files locally (`training_features.tif`, labels, sample submission, and DEM links); record hashes and metadata. The official download page currently requires login.
2. Recreate a fixed spatial holdout and baseline; independently implement/check the competition metric against the reference solution.
3. Test the research candidates listed in `docs/research-and-audit.md`; only promote candidates that beat the holdout baseline.
4. Add raster-safe inference, output validation, a submission manifest (unique name/comment/checksum), and the summary/export site only after verifying on actual official grid files.
5. Audit historic TIFs/runs where available. Identical SHA-256 is decisive file identity; equal displayed score is not.

## Arena operating principles

**Maximize P(Win):** choose work by expected evidence-based value, account for risk, avoid speculative submission churn. **Own the Outcome:** trace issues end-to-end, treat failures and successes as data, and make the final deliverable reproducible and reviewable.
