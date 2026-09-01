"""Did the Gemini judge over-match OUR candidates more than the rival's?

WHAT: Joins the blind hand verdicts to the arm key and reports the over-match rate per arm --
      the share of issues the Gemini judge scored as a match where the hand rater said no.
WHY:  Our reviewer and our judge are both Gemini; Greptile's candidates were written by another
      system. Self-preference would show up here as a HIGHER over-match rate on our arm than on
      theirs, and it would inflate every table in `docs/findings/reviewer/greptile-gap-analysis.md`.

      EVERY ITEM IN THE SAMPLE WAS SCORED AS A MATCH BY THE GEMINI JUDGE -- they are all issues
      one arm was credited with catching. So a hand verdict of "no" is a false positive of the
      judge, and the two arms' rates are directly comparable.

      THE ASYMMETRY IS THE MEASUREMENT, NOT THE RATE. A judge equally lenient to both arms leaves
      the comparison intact; a judge lenient only to ours does not.
IMPORTS: stdlib only (json, math, pathlib, sys).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import json
import pathlib
import sys
from math import comb

BLIND = pathlib.Path(__file__).resolve().parent / "blind"


def fisher(a: int, b: int, c: int, d: int) -> float:
    def p(a: int, b: int, c: int, dd: int) -> float:
        return comb(a + b, a) * comb(c + dd, c) / comb(a + b + c + dd, a + c)

    obs, tot = p(a, b, c, d), 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k = (a + b) - i, (a + c) - i
        ll = (c + d) - k
        if j < 0 or k < 0 or ll < 0:
            continue
        pr = p(i, j, k, ll)
        if pr <= obs + 1e-12:
            tot += pr
    return tot


def main() -> int:
    key = {
        r["item"]: r for r in json.loads((BLIND / "KEY_DO_NOT_OPEN_UNTIL_RATED.json").read_text())
    }
    verdicts = json.loads((BLIND / "verdicts.json").read_text())
    if len(verdicts) != len(key):
        print(f"  REFUSING TO REPORT — {len(verdicts)} verdicts against {len(key)} items")
        return 1

    stats: dict[str, list[int]] = {"OURS": [0, 0], "THEIRS": [0, 0]}  # [agree, over-match]
    disagreements: list[tuple[int, str, str]] = []
    for n_str, agreed in verdicts.items():
        n = int(n_str)
        arm = str(key[n]["arm"])
        stats[arm][0 if agreed else 1] += 1
        if not agreed:
            disagreements.append((n, arm, str(key[n]["golden"])[:100]))

    print("  THE GEMINI JUDGE SAID 'MATCH' FOR ALL 40. A HAND 'no' IS ITS FALSE POSITIVE.\n")
    print(f"  {'arm':8s} {'n':>4} {'upheld':>7} {'over-matched':>13} {'rate':>7}")
    for arm in ("OURS", "THEIRS"):
        ok, bad = stats[arm]
        n = ok + bad
        print(f"  {arm:8s} {n:4d} {ok:7d} {bad:13d} {bad / n:6.1%}" if n else f"  {arm:8s}    0")

    a, b = stats["OURS"][1], stats["OURS"][0]
    c, d = stats["THEIRS"][1], stats["THEIRS"][0]
    p = fisher(a, b, c, d)
    delta = (a / (a + b) - c / (c + d)) * 100 if (a + b) and (c + d) else float("nan")
    print(f"\n  over-match rate difference (ours minus theirs): {delta:+.1f} points")
    print(f"  Fisher exact p = {p:.4f}")
    print(
        "\n  A POSITIVE DIFFERENCE IS SELF-PREFERENCE. A negative or null one means the judge was\n"
        "  not kinder to the model family that wrote the candidates, and the gap tables stand."
    )
    print("\n  hand rater disagreed on:")
    for n, arm, g in sorted(disagreements):
        print(f"    item {n:2d} [{arm:6s}] {g}")
    return 0


sys.exit(main())
