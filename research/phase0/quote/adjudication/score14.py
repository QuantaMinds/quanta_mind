"""Score design fourteen against the bars fixed before the run, and say pass or fail.

WHAT: Joins the rater's verdicts to the held-back key, prints the sabotage catch-rate FIRST and
      gates everything on it, then W/n and C/n with Wilson intervals against their pre-registered
      thresholds, then the cause breakdown and the file-type cross-tabulation.
WHY:  The bars are in docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md.
      **A near-miss is a fail.**

      **THE SABOTAGE RATE IS PRINTED BEFORE ANY RESULT AND GATES IT.** If the pool graded
      planted-wrong findings CORRECT, its verdicts describe the pool and nothing below them means
      anything. Printed first deliberately: a number read after a result is a number the reader has
      already discounted.

      **THE INTERVAL RULE.** A point estimate on the passing side of a bar passes only if the
      Wilson bound clears it too. This project has passed a bar on a point estimate whose interval
      spanned it twice, and both had to be withdrawn. An interval spanning the threshold is
      INCONCLUSIVE and prints as such -- it is not a pass and it is not a failure.

      **BOTH BARS ARE PRINTED WHATEVER THE FIRST ONE SAYS.** W/n clearing while C/n fails is the
      expected outcome, written into the pre-registration before the run, and reporting only the
      one that moved is how a design gets called promising for years.

      **AND THE HEADLINE SAYS WHAT THIS ARM CANNOT DO.** Arm 1 changes the path filter, not the
      model. It cannot reopen `infer/`, whatever it scores.
IMPORTS: stdlib only (collections, json, math, pathlib).
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
ADJ = HERE / "adj14"
# Fixed in the pre-registration before the run. Never edited to fit a number.
STOP_AT = 0.50
REBUILD_AT = 0.30
FIELD_FLOOR = 0.49
SABOTAGE_FLOOR = 0.80


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def verdict_of(text: str) -> str:
    return str(text).strip().split()[0].upper() if str(text).strip() else "?"


def cause_of(text: str) -> str:
    return str(text).strip().split()[-1].upper() if str(text).strip() else "?"


def bucket(path: str) -> str:
    if path.startswith(".github/"):
        return ".github/"
    if path.endswith((".yml", ".yaml", ".cfg", ".ini", ".toml")):
        return "other config"
    return "source code"


def main() -> int:
    key = {str(e["item"]): e for e in json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())}
    verdicts = json.loads((ADJ / "verdicts.json").read_text())

    missing = [i for i in key if i not in verdicts]
    if missing:
        print(
            f"  {len(missing)} item(s) ungraded: {missing[:10]} — score nothing until every one is"
        )
        return 1

    sab = [(i, verdicts[i]) for i in verdicts if key[i]["kind"] == "SABOTAGE"]
    caught = sum(1 for _, t in sab if verdict_of(t) == "WRONG")
    rate = caught / len(sab) if sab else 0.0
    print("SABOTAGE CATCH-RATE, PRINTED FIRST BECAUSE IT GATES EVERYTHING BELOW")
    print(
        f"  {caught}/{len(sab)} planted-wrong graded WRONG = {rate:.0%}"
        f"   floor {SABOTAGE_FLOOR:.0%}"
    )
    if rate < SABOTAGE_FLOOR:
        print("\n  THE POOL IS RUBBER-STAMPING. These verdicts describe the rater, not the design.")
        print("  Nothing below is reported. Re-grade with a different rater.")
        return 1
    print("  -> the pool discriminates; the numbers below are readable\n")

    real = [(key[i], verdicts[i]) for i in verdicts if key[i]["kind"] == "real"]
    n = len(real)
    counts = collections.Counter(verdict_of(t) for _, t in real)
    W, C, U = counts["WRONG"], counts["CORRECT"], counts["UNFALSIFIABLE"]

    print(f"DESIGN 14 ARM 1 — the config exclusion. NOT the model lever.   n = {n}\n")
    for b in ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL"):
        lo, hi = wilson(counts[b], n)
        share = counts[b] / n
        print(f"  {b:<14}{counts[b]:>4}{share:>8.1%}   Wilson {lo:5.1%} to {hi:5.1%}")

    def call(k: int, bar: float, lower_is_better: bool, name: str) -> str:
        lo, hi = wilson(k, n)
        if lower_is_better:
            if hi < bar:
                return f"CLEARS {name} (upper bound {hi:.1%} < {bar:.0%})"
            if lo >= bar:
                return f"FAILS {name} (lower bound {lo:.1%} >= {bar:.0%})"
            return f"INCONCLUSIVE on {name} — {lo:.1%} to {hi:.1%} spans {bar:.0%}; NOT a pass"
        if lo >= bar:
            return f"CLEARS {name} (lower bound {lo:.1%} >= {bar:.0%})"
        if hi < bar:
            return f"FAILS {name} (upper bound {hi:.1%} < {bar:.0%})"
        return f"INCONCLUSIVE on {name} — {lo:.1%} to {hi:.1%} spans {bar:.0%}; NOT a pass"

    print(f"\n  W/n = {W / n:.1%}   {call(W, STOP_AT, True, 'the STOP bar 50%')}")
    print(f"          {call(W, REBUILD_AT, True, 'the REBUILD bar 30%')}")
    print(f"  U/n = {U / n:.1%}")
    print(f"  C/n = {C / n:.1%}   {call(C, FIELD_FLOOR, False, 'the field floor 49%')}")

    print("\n  WHY the wrong findings were wrong:")
    for c, k in collections.Counter(
        cause_of(t) for _, t in real if verdict_of(t) == "WRONG"
    ).most_common():
        print(f"    {c:<10}{k:>4}")

    print("\n  by file type — the exclusion this arm tests:")
    print(f"    {'bucket':<14}{'n':>4}{'W/n':>9}{'C/n':>9}")
    for b in sorted({bucket(str(e["path"])) for e, _ in real}):
        g = [(e, t) for e, t in real if bucket(str(e["path"])) == b]
        w = sum(1 for _, t in g if verdict_of(t) == "WRONG")
        c = sum(1 for _, t in g if verdict_of(t) == "CORRECT")
        print(f"    {b:<14}{len(g):>4}{w / len(g):>9.1%}{c / len(g):>9.1%}")

    print("\n  READING: both bars must clear for `infer/` to reopen, and this arm cannot reopen it")
    print("  either way — it changed the path filter, not the model. See amendment 1.")
    return 0


raise SystemExit(main())
