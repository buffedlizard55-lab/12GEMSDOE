# Sibling Audit — Why the Same Score Keeps Coming Back

**Generated 2026-09-28.** Raw evidence: [`sibling-audit.json`](sibling-audit.json)
(25 MB of rasters hashed and compared; 48 unique published artifacts across 12 repositories).
Reproduce with `python scripts/audit_siblings.py` (read-only; GitHub API is the only egress
available in this environment).

---

## 1. The two questions the brief asks, answered from bytes

> "Why do 5GEMSDOE and GEMSDOE1 have the same score?"
> "Are we copying the same work over and over again?"

**Answer 1 — verified.** The GEMSDOE site and the 5GEMSDOE site hand out **the same file**.
Both `docs/index.html`, `docs/executive_summary.html` and `docs/how_to_submit.html` of both
repositories link one artifact only:

```
GEMSDOE  /docs/index.html  -> data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif
5GEMSDOE /docs/index.html  -> data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif
both SHA-256 7f00890a62878d612fb5eef67a9a364a2df819433dde74b6762ce4fc0fc4fe15
both 570,890 bytes, 172,974 positive pixels, binary {0,1}
```

Same bytes in, same score out: a fixed public test set can only produce one number for one
prediction raster. The 0.1563 identity is therefore *necessary*, not a coincidence.

**Answer 2 — verified, and it is worse than one pair.** That exact file is committed in
**six places across five repositories** (the seventh copy is this repo's own R5/R6/R7 chain,
which is different code and different bytes):

| Repository | Path | Bytes |
|---|---|---|
| GEMSDOE | `data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif` | 570,890 |
| 5GEMSDOE | `data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif` | 570,890 |
| 5GEMSDOE | `data/evidence/leaderboard_anchor/gemsdoe-ens12-adopted-7f00890a.tif` | 570,890 |
| GEMSDOE2 | `data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif` | 570,890 |
| GEMSDOE3 | `legacy/data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif` | 570,890 |
| GEMSDOE4 | `data/evidence/runs/ens12-adopted-floor0.1-w0/submission.tif` | 570,890 |

Three earlier experiment artifacts repeat the same pattern across four repositories
(`45d50773…`, `a5ae61d5…`, `b9f2bc4d…`), and 8 of the 11 duplicate groups in the audit are
cross-repository copies rather than independent reconstructions. This is the "copying the
same work over and over" the brief suspected: the repositories were forked from one another
(GEMSDOE4's own README says so: *"Copy the entire repo and site from GEMSDOE (the site that
scored 0.1563)"*), and each fork inherited the same offered artifact.

## 2. What the scored files actually are (measured, not quoted)

| Account | Score | SHA-256 (prefix) | Implied file | Emitted px | On catalogue | Off catalogue | Binary |
|---|---|---|---|---|---|---|---|
| extradr19 | 0.1563 | `7f00890a…` | ens12 CNN-ensemble floor-0.1 field | 172,974 | 6,455 | 166,519 | yes |
| smashi34 | 0.1560 | `f68e590f…` | GEMSDOE2 dual-family union | 183,642 | 7,693 | 175,949 | yes |
| smrtdoog5 | 0.1193 | `f347b70d…` | pindrop-v4 spaced nodes | 155,021 | 0 | 155,021 | yes |
| SDCF9 | 0.1152 | `4e03fc97…` | pindrop-v4 dense ridge control | 155,021 | 0 | 155,021 | yes |
| wbg1 | 0.0830 | `37f9d5b8…` | pindrop-v4 catalogue-gap discovery | 155,021 | 0 | 155,021 | yes |

Account attributions are copied verbatim from the sibling's own ledger
(`5GEMSDOE/scripts/leaderboard_anchor.py::SCORED`, generated 2026-09-26). **No DrivenData
upload receipt exists anywhere in this organisation**, so the table is evidence about
*files*, not proof about *uploads*; rows labelled CERTAIN in the source ledger are quoted as
such and the one PROBABLE row stays labelled PROBABLE.

Live board read for this audit (own HTTP read, 2026-09-28):
#26 `extradr19` 0.1563 (3 submissions) · #27 `SDCF9` 0.1563 (2) · #28 `smashi34` 0.1563 (2)
· #33 `wbg1` 0.1461 (3) · #48 `smrtdoog5` 0.1193 (2) · #17 `doegemsDrivendata` 0.1847.

## 3. The natural experiment that explains the plateau

`8GEMSDOE` published two artifacts whose positives **include every one of the 60,988
catalogue pixels**. Measured pixel-exact this session:

```
8GEMSDOE_Hedge-v2_submission.tif (SHA 052688ea…)  ==  max(ens12-7f00890a, catalogue)
    differing pixels: 0
    positives 227,507 = catalogue 60,988 + ens12's own off-catalogue 166,519
```

So a sibling independently derived **the exact "known-fault base layer" hypothesis**
(`docs/hypotheses-round8.md` H37) and published it. The brief records
`8GEMSDOE SCORE: 0.1563` — *identical* to the 0.1563 of the file it was derived from.

**What that establishes.** Adding the entire known-fault catalogue to a field that scored
0.1563 did not move the score. That is exactly what staff ruling
[11516/2](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2)
predicts — *"it should not matter whether these known faults are included with predictions or
not"* — and it settles the open question the repo carried: masked pixels are **neutral**,
neither charged as false positives nor credited as free true positives.

**What it kills.** H37 was ranked first in this round's register on a dominance argument that
allowed for free true-positive credit at masked pixels. The field evidence says that credit
is not paid, at least not at a scale that moves a 4-decimal score. H37 is therefore
**demoted to a control arm, not a submission strategy** (see the register's results section).
The honest reading is: our best-known field is *saturated* on catalogue-adjacent geometry —
adding 60,988 zero-cost pixels recovered nothing.

## 4. Where the score is actually lost — the metric's own algebra

From the published formula, `TP_w + FN_w = N_t` exactly, so
`DTI = T / (0.2·T + 0.2·E + 0.8·N_t)`. Solving each scored file's equation for its
true-positive mass `T` gives the coverage the score implies, as a locus over the unknown
number of scored truth pixels `N_t` ([`../evidence/metric-algebra.json`](../evidence/metric-algebra.json)):

| File (score) | coverage implied if `N_t` = 20k | 30k | 40k | 60k |
|---|---|---|---|---|
| ens12 (0.1563) | ≤ 0.398 | ≤ 0.308 | ≤ 0.263 | ≤ 0.219 |
| union (0.1560) | ≤ 0.412 | ≤ 0.318 | ≤ 0.271 | ≤ 0.223 |
| nodes (0.1193) | ≤ 0.287 | ≤ 0.224 | ≤ 0.193 | ≤ 0.161 |
| ridge (0.1152) | ≤ 0.277 | ≤ 0.216 | ≤ 0.186 | ≤ 0.155 |
| discovery (0.0830) | ≤ 0.198 | ≤ 0.155 | ≤ 0.133 | ≤ 0.111 |

(Upper bounds on `E` make these lower bounds on coverage; the public split is unpublished, so
the true coverage is at least this high.)

And the first-order condition for adding mass at the group's current level:

```
include pixel  ⟺  ΔT/ΔE  >  0.2·DTI/(1 − 0.2·DTI)      = 0.0323 at DTI = 0.1563
                                                         0.0677 at the leader's 0.3168
```

With β/α = 4, coverage is four times as valuable as precision, and the rule says a pixel whose
chance of lying within the 300 m kernel exceeds ≈ 3.2 % should be emitted. Every artifact in
this family emits ≈ 3 % of the footprint (155k–173k px) — a number that was *frozen* in
Round 5 for comparability, never derived. **That is the open lever, and it is what Round 8
tests** (`scripts/holdout_round8.py`).

## 5. Irregularities flagged for review (not resolved here)

1. **The official sample submission is the catalogue.** `sample_submission.tif`
   (SHA-256 `2176d08e…`) is bit-for-bit `(labels.tif > 0)` — 60,988 positive pixels, values
   `{0,1}` — while the problem page describes it as *"a sample submission that predicts total
   fault absence"*. `labels.tif` and `existing_faults.tif` are the same bytes
   (`7ba308cc…`). Submitting the template as-is predicts only masked pixels.
   *Verified twice this session against the pinned rasters; independently corroborated by
   11GEMSDOE's README.*
2. **Third 0.1563 row is only consistent, not proven.** `SDCF9`'s and `smashi34`'s own
   published files score 0.1152 / 0.1560 in the ledger, yet both accounts display 0.1563, so
   both must hold a second submission that scored ≥ 0.1563; the only file in the family known
   to score exactly 0.1563 is `7f00890a`. Without upload receipts this stays an inference.
3. **`wbg1` 0.1461 has no file.** The board shows `wbg1` at 0.1461 (3 submissions) while the
   ledger attributes 0.0830 to its discovery arm. The 0.1461 file is unidentified.
4. **7GEMSDOE's and 8GEMSDOE's `downloads/` copies are unhashed duplicates** of their
   `docs/downloads/` counterparts (`90fb7dc0…`, `052688ea…`, `b83ea0e7…`) — harmless, but it
   means "which file did the site offer" cannot be answered by path alone for those repos.
5. **`8GEMSDOE`'s own README says its artifacts were never uploaded** (`BUILT-UNIQUE-UNUPLOADED`)
   while the brief records a 0.1563 score for that account. Both cannot describe the same
   event; one of the two records is stale.
6. **Repository naming.** `GEMSDOE1`, `9GEMSDOE` and `10GEMSDOE` are not repositories; the
   brief's "GEMSDOE1" page is `/GEMSDOE/docs/index.html` and the 9/10 sites live in
   `GEMSDOE9` / `GEMSDOE10`. `13/14/15GEMSDOE` are 11-byte README stubs with no artifacts.
7. **Knowledge-base citation error (ours, fixed this session).** `docs/knowledge-base.md`
   claimed the `tc` band "is described as top-of-magnetic-source depth" citing forum thread
   11529; that thread is about the *label* raster's band count. The in-file band description
   actually reads *"tc - Tilt angle or total curvature - magnetic field derivative for edge
   detection"*, and Round-5's C3 measurement (range 2.95–88.57, `corr(tc, |tilt|) = −0.0012`)
   is what rules the tilt reading out. The corrected wording is in the knowledge base.

## 6. What this audit cannot say

* It cannot attribute an upload to an account; no receipts exist in the organisation.
* It cannot measure the hidden truth, so it cannot say which of these files would win today.
* Every "score" in §2 is the sibling's own record of a public leaderboard row; §5 flags the
  three rows whose file identity is not first-party.
