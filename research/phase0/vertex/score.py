"""Recompute the adjudication result from the recorded verdicts.

WHAT: Reads the per-finding verdicts and prints the bucket counts with Wilson intervals, the
      split of the WRONG bucket into anchor failures and semantic failures, the pre-registered
      threshold checks, and the by-rank breakdown.
WHY:  The verdicts were assigned by a human reading each finding against its diff, which cannot
      be re-derived. What CAN be re-derived is every number computed from them, so the arithmetic
      is separated from the judgement and a second rater can substitute their own verdict file
      and get the same report. The thresholds are in the adjudication pre-registration under
      `docs/plans/preregistrations/`
      and were committed before any finding was read.
IMPORTS: stdlib only (collections, json, math).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
from math import sqrt

STOP_AT, FIELD_FLOOR = 0.50, 0.49


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> None:
    with open("../results/adjudication_verdicts.json") as fh:
        v = json.load(fh)
    n = len(v)
    c = collections.Counter(x["verdict"] for x in v.values())
    print(f"  {n} findings adjudicated, shuffled and blinded to rank\n")
    for b in ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL"):
        lo, hi = wilson(c[b], n)
        print(f"    {b:14s} {c[b]:3d}  {c[b] / n:6.1%}   Wilson 95% [{lo:.1%}, {hi:.1%}]")

    anchor = sum(1 for x in v.values() if x["verdict"] == "WRONG" and x["basis"] == "anchor")
    sem = c["WRONG"] - anchor
    print(f"\n    WRONG by anchor only  {anchor:3d}  {anchor / n:.1%}")
    print(f"    WRONG semantically    {sem:3d}  {sem / n:.1%}")

    w, corr = c["WRONG"] / n, c["CORRECT"] / n
    lo_w, _ = wilson(c["WRONG"], n)
    print("\n  PRE-REGISTERED THRESHOLDS")
    print(
        f"    W/n {w:.1%} vs STOP at {STOP_AT:.0%} -> "
        f"{'STOP' if w >= STOP_AT else 'not triggered'}"
        f"   (interval lower bound {lo_w:.1%} is "
        f"{'also above' if lo_w >= STOP_AT else 'below'} the threshold)"
    )
    print(
        f"    C/n {corr:.1%} vs field floor {FIELD_FLOOR:.0%} -> "
        f"{'BELOW THE FIELD' if corr < FIELD_FLOOR else 'within the field'}"
    )
    ceiling = (c["CORRECT"] + anchor) / n
    print(
        f"    most generous ceiling if every anchor failure were repaired AND correct: "
        f"{ceiling:.1%}"
    )

    print("\n  BY RANK (unblinded only after every verdict was fixed)")
    for r in (1, 2, 3):
        s = [x for x in v.values() if x["rank"] == r]
        if not s:
            continue
        cc = sum(1 for x in s if x["verdict"] == "CORRECT")
        ww = sum(1 for x in s if x["verdict"] == "WRONG")
        print(
            f"    rank {r}: {len(s):2d} findings   correct {cc / len(s):5.1%}   "
            f"wrong {ww / len(s):5.1%}"
        )


main()
