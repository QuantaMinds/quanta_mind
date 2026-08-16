"""Adjudicate the effort run against the bars fixed before it, and print the verdict.

WHAT: Takes the per-repository event records and the size sample, computes effort saved and catch
      rate for all three policies, and prints PASS/FAIL against each bar in
      `docs/plans/roi-preregistration.md`.
WHY:  Split from `reviewer_effort.py` at the 200-line cap, and it is a real seam rather than a
      convenience one: producing a number and deciding whether it clears a bar are different jobs,
      and keeping the bars in a module that never touches git makes them readable without reading
      the harness.

      THE BARS ARE LITERALS HERE ON PURPOSE. A threshold computed from the data it judges is not a
      threshold. All five are stated in the pre-registration and copied, not derived.
IMPORTS: stdlib only (statistics, math).
CONSUMED BY: `reviewer_effort.py` in this package.
"""

from __future__ import annotations

import statistics
from math import comb

MIN_REDUCTION = 0.50
MIN_CATCH = 0.95
MIN_LIFT = 0.01
MAX_P = 0.05
MIN_WINS = 8
MAX_SIZE_RATIO = 1.25


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def report(
    per: dict[str, list[dict[str, object]]], sizes: list[tuple[float, float]], drop: int
) -> bool:
    """Print the table and the bars. Returns True only if every bar passed."""
    allev = [e for v in per.values() for e in v]
    n = len(allev)
    files_all = sum(int(str(e["n_files"])) for e in allev)
    files_read = sum(int(str(e["read"])) for e in allev)
    reduction = 1 - files_read / files_all
    catch = sum(1 for e in allev if e["hit"]) / n
    acatch = sum(1 for e in allev if e["alpha_hit"]) / n
    b = sum(1 for e in allev if e["hit"] and not e["alpha_hit"])
    c = sum(1 for e in allev if e["alpha_hit"] and not e["hit"])
    wins = sum(
        1
        for v in per.values()
        if v
        and sum(1 for e in v if e["hit"]) / len(v) > sum(1 for e in v if e["alpha_hit"]) / len(v)
    )

    print(f"\n  {n} admissible changes, {len(per)} repositories the method has never seen\n")
    print(f"  {'policy':28s} {'files read':>11} {'of':>7} {'effort saved':>13} {'catch':>9}")
    print(f"  {'read everything':28s} {files_all:11d} {files_all:7d} {'0.0%':>13} {'100.00%':>9}")
    print(
        f"  {'top 3 by fix history':28s} {files_read:11d} {files_all:7d} "
        f"{reduction:12.1%} {catch:8.2%}"
    )
    print(
        f"  {'top 3 alphabetically':28s} {files_read:11d} {files_all:7d} "
        f"{reduction:12.1%} {acatch:8.2%}"
    )
    p = mcnemar(b, c)
    print(
        f"\n  history over alphabetical: {(catch - acatch) * 100:+.2f} points, "
        f"McNemar exact p = {p:.3g} (b={b}, c={c})"
    )
    if drop:
        print(f"  size study dropped {drop} commit(s) whose numstat disagreed with --name-only")

    ratio = (
        statistics.mean(t for t, _ in sizes) / statistics.mean(r for _, r in sizes)
        if sizes
        else float("nan")
    )
    bars = [
        (
            f"B1 effort reduction >= {MIN_REDUCTION:.0%}",
            reduction >= MIN_REDUCTION,
            f"{reduction:.1%}",
        ),
        (f"B2 catch rate >= {MIN_CATCH:.0%}", catch >= MIN_CATCH, f"{catch:.2%}"),
        (
            "B3 beats alphabetical >= 1.0pt, p<0.05",
            (catch - acatch) >= MIN_LIFT and p < MAX_P,
            f"{(catch - acatch) * 100:+.2f}pt p={p:.3g}",
        ),
        (f"B4 positive in >= {MIN_WINS} of 12 repos", wins >= MIN_WINS, f"{wins}/{len(per)}"),
        (
            f"B5 ranked files <= {MAX_SIZE_RATIO}x size of skipped",
            bool(sizes) and ratio <= MAX_SIZE_RATIO,
            f"{ratio:.2f}x on {len(sizes)} sampled changes",
        ),
    ]
    print("\n  PRE-REGISTERED BARS (docs/plans/roi-preregistration.md)")
    for label, ok, detail in bars:
        print(f"    [{'PASS' if ok else 'FAIL'}] {label:40s} {detail}")
    passed = all(o for _, o, _ in bars)
    print(f"\n  {'ALL BARS PASS' if passed else 'FAILED — reported as a fail'}")
    return passed
