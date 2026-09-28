"""Metric algebra on the five publicly scored files this organisation holds.

The official metric (page/967, fetched 2026-09-28) gives the exact identity
`TP_w + FN_w = N_t` (each scored truth pixel contributes credit <= 1), so

    DTI = T / (0.2*T + 0.2*E + 0.8*N_t)          (E = chargeable FP mass)

which is one linear equation per file in the two unknowns (T_i, N_t).  Solving for T_i
turns each published public score into a *coverage locus*: coverage_i(N_t) = T_i/N_t.

What this can and cannot say
----------------------------
* E_i is bounded by the measured count of positive off-catalogue pixels (a pixel within
  300 m of truth carries weight < 1), so the reported coverage is a *lower bound* on the
  coverage that the score implies.  Both bounds are reported.
* N_t (the number of scored, expert-mapped new-fault pixels on the public split) is NOT
  knowable from outside.  Nothing here invents it: every quantity is tabulated against a
  range of N_t, and the report states the locus, not a point.
* The scoring region is the *public split* of the GeoDAWN footprint, which is not
  published; E_i therefore also includes emitted pixels outside the split, which do not
  charge.  That inflates E_i and deflates the implied coverage.  Recorded, not hidden.

Outputs: evidence/metric-algebra.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALPHA, BETA = 0.2, 0.8

# measured this session (evidence/sibling-audit.json): positive pixels, of which the
# catalogue share is masked and cannot charge
FILES = {
    "ens12-7f00890a":       dict(score=0.1563, account="extradr19", positive=172974, on_catalogue=6455),
    "gemsdoe2-union-f68e590f": dict(score=0.1560, account="smashi34", positive=183642, on_catalogue=7693),
    "pindrop-nodes-f347b70daa": dict(score=0.1193, account="smrtdoog5", positive=155021, on_catalogue=0),
    "pindrop-ridge-4e03fc9705": dict(score=0.1152, account="SDCF9", positive=155021, on_catalogue=0),
    "pindrop-discovery-37f9d5b855": dict(score=0.0830, account="wbg1", positive=155021, on_catalogue=0),
}
LEADER = {"account": "DARD", "score": 0.3168}
N_T_GRID = [5_000, 10_000, 20_000, 30_000, 40_000, 60_000, 80_000, 100_000, 150_000, 200_000]


def implied_T(dti: float, E: float, N_t: float) -> float:
    """Solve DTI = T / (0.2T + 0.2E + 0.8 N_t) for T."""
    return (ALPHA * E + BETA * N_t) / (1.0 / dti - ALPHA)


def marginal_threshold(dti: float) -> float:
    """Include a pixel iff dT/dE > ALPHA*DTI/(1 - ALPHA*DTI)."""
    return ALPHA * dti / (1 - ALPHA * dti)


def main() -> None:
    report = {
        "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
        "identity": "DTI = T / (0.2*T + 0.2*E + 0.8*N_t), T = TP_w, E = FP_w, N_t = scored truth pixels",
        "marginal_rule": "include pixel iff dT/dE > 0.2*DTI/(1 - 0.2*DTI)",
        "thresholds": {f"{d:.4f}": round(marginal_threshold(d), 5) for d in (0.0830, 0.1152, 0.1193, 0.1563, 0.20, 0.3168)},
        "files": {},
        "caveats": [
            "E is bounded above by the count of positive off-catalogue pixels; pixels within 300 m of truth "
            "carry weight < 1, so implied coverage is a lower bound.",
            "The scored region is the unpublished public split; emitted pixels outside it do not charge, which "
            "inflates E and deflates implied coverage.",
            "N_t is unknown and is not guessed: every row is tabulated against a grid of N_t.",
            "Account -> file attribution comes from the sibling's own ledger (5GEMSDOE), not from upload receipts.",
        ],
    }
    for name, f in FILES.items():
        E = f["positive"] - f["on_catalogue"]
        row = {"score": f["score"], "account": f["account"], "E_chargeable_bound": E,
               "coverage_locus_lower_bound": {}}
        for N_t in N_T_GRID:
            T = implied_T(f["score"], E, N_t)
            row["coverage_locus_lower_bound"][str(N_t)] = round(T / N_t, 4) if N_t else None
        report["files"][name] = row

    # coverage needed to reach the current leader at the same emitted mass
    report["leader_requirement"] = {}
    for name, f in FILES.items():
        E = f["positive"] - f["on_catalogue"]
        row = {}
        for N_t in N_T_GRID:
            T = implied_T(LEADER["score"], E, N_t)
            row[str(N_t)] = {"coverage_needed": round(T / N_t, 4), "T": round(T, 1),
                             "feasible": bool(T <= N_t)}
        report["leader_requirement"][name] = row

    out = ROOT / "evidence/metric-algebra.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({"thresholds": report["thresholds"]}, indent=1))
    for name, row in report["files"].items():
        print(f"{name:30s} E<={row['E_chargeable_bound']:7d} coverage-locus(lower bound) "
              + " ".join(f"N{N}={v}" for N, v in list(row['coverage_locus_lower_bound'].items())[:6]))
    print("wrote", out)


if __name__ == "__main__":
    main()
