"""The registered bars for D2e, printed from what `drift_separates.py` scored.

WHAT: The command. Takes clones, scores each, pools them, and prints the tertile comparison and the
      churn-stratified one — B2 and B3 of
      `docs/plans/preregistrations/ranker/drift-preregistration.md`.
WHY:  **SPLIT FROM THE SCORER AT THE 200-LINE CAP, AND THE SEAM IS REAL.** What `drift` IS and what
      the bars SAY about it are two decisions, and only the second moves when a pre-registration is
      amended. Keeping them apart means an amendment cannot quietly change the measurement.

      **THE STRATIFIED TABLE IS PRINTED WHETHER OR NOT THE HEADLINE PASSES.** B3 is the bar that
      decides, and a report that showed it only on a win would be the shape of every result this
      project has had to withdraw.
IMPORTS: scripts/measure/graph/drift_separates.py.
CONSUMED BY: run by hand; its output is the evidence in
      `docs/findings/graph/D2E_DRIFT_DOES_NOT_SEPARATE_2026-08.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from drift_separates import MIN_CHURN, Scored, score


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clones", type=Path, nargs="+")
    args = parser.parse_args(argv[1:])

    rows: list[Scored] = []
    for clone in args.clones:
        found = score(clone)
        print(f"[drift] {clone.name}: {len(found)} file(s) with churn >= {MIN_CHURN}", flush=True)
        rows.extend(found)

    print(f"\n[drift] {len(rows)} file(s) across {len(args.clones)} repositor(y/ies)")
    if not rows:
        print("[drift] nothing to score")
        return 1

    ranked = sorted(rows, key=lambda r: r.drift)
    third = len(ranked) // 3
    low, high = ranked[:third], ranked[-third:]
    print(f"\n{'tertile':<8} {'files':>6} {'mean drift':>11} {'mean fix rate':>14}")
    for name, group in (("low", low), ("high", high)):
        drift = sum(r.drift for r in group) / len(group)
        fix = sum(r.fix_rate for r in group) / len(group)
        print(f"{name:<8} {len(group):>6} {drift:>11.3f} {fix:>14.3f}")

    print("\n[B3] the same split INSIDE churn strata — the bar that decides")
    print(f"{'churn':<14} {'n':>5} {'low fix':>9} {'high fix':>10} {'gap':>8}")
    bounds = [(MIN_CHURN, 20), (20, 50), (50, 10_000)]
    for lo, hi in bounds:
        band = [r for r in rows if lo <= r.churn < hi]
        if len(band) < 20:
            print(f"{f'{lo}-{hi}':<14} {len(band):>5}   too few to read")
            continue
        by_drift = sorted(band, key=lambda r: r.drift)
        cut = len(by_drift) // 3
        lo_fix = sum(r.fix_rate for r in by_drift[:cut]) / cut
        hi_fix = sum(r.fix_rate for r in by_drift[-cut:]) / cut
        print(
            f"{f'{lo}-{hi}':<14} {len(band):>5} {lo_fix:>9.3f} {hi_fix:>10.3f} "
            f"{(hi_fix - lo_fix) * 100:>7.1f}pp"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
