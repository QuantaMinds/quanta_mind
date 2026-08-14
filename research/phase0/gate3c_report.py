"""Reporting for the gate 3c paired comparison: the tables, the tests, the decomposition.

WHAT: `render`, which takes the counted cells and prints both arms, the matched-coverage arm,
      McNemar on each, and the c/c' decomposition.
WHY:  Split from gate3c_paired.py at the 200-line cap, and this is the seam that was already
      there -- counting events is one concern and deciding what to say about them is another.
      Keeping them apart also means the reporting can be re-read without re-running an hour of
      git, which matters when the question is how a number was phrased.
IMPORTS: stdlib only (math.comb). No project imports.
CONSUMED BY: research/phase0/gate3c_paired.py.
"""

from __future__ import annotations

from math import comb


def _mcnemar(b: int, c: int) -> float:
    """Exact two-sided binomial on the discordant pairs. 1.0 when there are none."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n)
    return min(1.0, 2 * tail)


def render(cells, matched, sizes, per_repo, file_units, sym_units, budget):
    """Print every arm. Returns False when an assertion fails and nothing should be reported."""
    n = sum(cells.values())
    if n == 0:
        print("\n  no events. Nothing to report.")
        return False

    print(f"\n  units seen: {file_units} file-slots, {sym_units} symbol-slots")
    if sym_units == file_units:
        print("  REFUSING TO REPORT — symbol count equals file count; the parser did not run.")
        return False

    b, c = cells[(True, False)], cells[(False, True)]
    fmiss = cells[(False, True)] + cells[(False, False)]
    smiss = cells[(True, False)] + cells[(False, False)]

    print(f"\n  PAIRED, n={n} events across {len(per_repo)} repositories\n")
    print(f"    file-level top-{budget} miss      {fmiss}/{n} = {fmiss / n:.2%}")
    print(f"    function-level top-{budget} miss  {smiss}/{n} = {smiss / n:.2%}")
    print(f"    gap (function - file)      {100 * (smiss - fmiss) / n:+.2f} points\n")
    print(f"    discordant: b={b}  c={c}")
    print(f"    McNemar exact two-sided p = {_mcnemar(b, c):.4f}")

    mb, mc = matched[(True, False)], matched[(False, True)]
    mmiss = matched[(True, False)] + matched[(False, False)]
    print("\n  MATCHED COVERAGE — top-3 files vs top-5 functions (3.05 file-equivalents)")
    print(f"    function top-5 miss   {mmiss}/{n} = {mmiss / n:.2%}")
    print(f"    gap vs file top-3     {100 * (mmiss - fmiss) / n:+.2f} points")
    print(f"    discordant b={mb} c={mc}")
    print(f"    McNemar exact two-sided p = {_mcnemar(mb, mc):.4f}")

    ks = [k for k, _ in sizes]
    ms = [m for _, m in sizes]
    kbar, mbar = sum(ks) / len(ks), sum(ms) / len(ms)
    print("\n  DECOMPOSITION")
    print(f"    mean files per change k    {kbar:.2f}")
    print(f"    mean symbols per change m  {mbar:.2f}   ratio m/k = {mbar / kbar:.2f}")
    if kbar > budget:
        print(f"    c  = {100 * fmiss / n / (kbar - budget):.2f} pts per uncovered file")
    if mbar > budget:
        print(f"    c' = {100 * smiss / n / (mbar - budget):.2f} pts per uncovered symbol")
    return True
