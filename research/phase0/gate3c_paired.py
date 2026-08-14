"""Gate 3c: does function-level allocation lose more than the file-level analogue?

WHAT: A paired comparison on identical events -- file-top-3 against function-top-3 -- with
      McNemar on the discordant pairs and the c/c' decomposition.
WHY:  Top-1 says whether the spend is well aimed; only top-3 says whether allocation loses
      defects. The allocator ranks FUNCTIONS and the corpus-wide figure was measured on FILES,
      so the two arms had never been compared on the same events. Paired rather than two
      independent proportions because only disagreements carry information, which is far more
      powerful on the 8 repositories that have complete objects.
IMPORTS: stdlib (bisect, collections, json, os, subprocess, sys) and symbol_history_read.
CONSUMED BY: docs/plans/implementation.md, gate 3c.

PRE-SPECIFIED BEFORE THE RUN (docs/plans/implementation.md):

  Discordance criterion -- a discordant pair is an event where the defect unit is inside
  file-top-3 and outside function-top-3, OR the reverse. BOTH cells are live: a file's touch
  count is roughly a sum over its functions, so a hot function in a lower-ranked file gives
  file-miss/function-hit. Deciding what counts after seeing counts is how a null becomes a
  finding, so it is fixed here.

  Decomposition -- report c and c' (points per uncovered unit) and the ratio m/k, not only
  the gap. Population -- the 8 full-object clones, a convenience sample carrying larger
  changes than the other 17, so a gap measured here plausibly overstates.

TWO ASSERTIONS, because this operation has failed before: the git exit code (asserted in
symbol_history_read), and that symbol slots differ from file slots -- if they match, the
parser did not run and the two arms are the same measurement twice.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import subprocess
import sys

from symbol_history_read import ReadFailed, stream

CL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clones")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate3c_result.json")
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES = 12
MAX_EVENTS = 400
BUDGET = 3


def top3_hit(units, idx, ts, target):
    """Rank units by prior-year touches, return (hit, k). None when the choice is degenerate."""

    def prior(u):
        lst = idx.get(u, [])
        return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)

    scores = {u: prior(u) for u in units}
    if len(set(scores.values())) == 1:
        return None, len(units)
    ordered = sorted(units, key=lambda u: (-scores[u], u))
    return bool(set(ordered[:BUDGET]) & target), len(units)


def main() -> int:
    full = []
    for d in sorted(os.listdir(CL)):
        p = os.path.join(CL, d)
        if not os.path.isdir(os.path.join(p, ".git")):
            continue
        if (
            subprocess.run(
                ["git", "-C", p, "config", "--get", "remote.origin.partialclonefilter"],
                capture_output=True,
            ).returncode
            != 0
        ):
            full.append(d)
    print(f"  full-object clones: {len(full)}\n")

    cells = collections.Counter()  # (file_hit, sym_hit) -> n
    sizes = []  # (k files, m symbols) per event
    per_repo = {}
    sym_units_total = file_units_total = 0

    for name in full:
        repo = os.path.join(CL, name)
        try:
            commits = stream(repo)
        except ReadFailed as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1
        if len(commits) < 200:
            print(f"  {name:34s} skipped: {len(commits)} commits")
            continue

        fidx, sidx = collections.defaultdict(list), collections.defaultdict(list)
        for _, ts, _, files, syms in commits:
            for f in files:
                fidx[f].append(ts)
            for s in syms:
                sidx[s].append(ts)

        local = collections.Counter()
        n_ev = 0
        for i, (_sha, ts, _msg, files, syms) in enumerate(commits):
            if not (2 <= len(files) <= MAX_FILES) or len(syms) < 2:
                continue
            ftarget, starget = set(), set()
            for _s2, ts2, msg2, files2, syms2 in commits[i + 1 :]:
                if ts2 - ts > WINDOW:
                    break
                if any(w in msg2 for w in FIXWORDS):
                    ftarget |= files2 & files
                    starget |= syms2 & syms
            if not ftarget or not starget:
                continue

            fhit, k = top3_hit(files, fidx, ts, ftarget)
            shit, m = top3_hit(syms, sidx, ts, starget)
            if fhit is None or shit is None:
                continue

            n_ev += 1
            cells[(fhit, shit)] += 1
            local[(fhit, shit)] += 1
            sizes.append((k, m))
            file_units_total += k
            sym_units_total += m
            if n_ev >= MAX_EVENTS:
                break

        if n_ev >= 20:
            per_repo[name] = {str(k): v for k, v in local.items()}
            fm = local[(False, True)] + local[(False, False)]
            sm = local[(True, False)] + local[(False, False)]
            print(f"  {name:34s} n={n_ev:4d}  file-miss={fm:3d}  sym-miss={sm:3d}")

    n = sum(cells.values())
    if n == 0:
        print("\n  no events. Nothing to report.")
        return 1

    # THE SECOND ASSERTION: symbol extraction must have produced different units.
    print(f"\n  units seen: {file_units_total} file-slots, {sym_units_total} symbol-slots")
    if sym_units_total == file_units_total:
        print("  REFUSING TO REPORT — symbol count equals file count; the parser did not run.")
        return 1

    b = cells[(True, False)]  # file hit, function miss
    c = cells[(False, True)]  # file miss, function hit
    fmiss = cells[(False, True)] + cells[(False, False)]
    smiss = cells[(True, False)] + cells[(False, False)]

    print(f"\n  PAIRED, n={n} events across {len(per_repo)} repositories\n")
    print(f"    file-level top-3 miss      {fmiss}/{n} = {fmiss / n:.2%}")
    print(f"    function-level top-3 miss  {smiss}/{n} = {smiss / n:.2%}")
    print(f"    gap (function - file)      {100 * (smiss - fmiss) / n:+.2f} points\n")
    print(f"    discordant: file-hit/fn-miss b={b}   file-miss/fn-hit c={c}")

    if b + c == 0:
        print("    no discordant pairs — sign unresolved.")
    else:
        # exact binomial two-sided on b of (b+c) under p=0.5
        from math import comb

        nn = b + c
        tail = sum(comb(nn, i) for i in range(0, min(b, c) + 1)) / (2**nn)
        print(f"    McNemar exact two-sided p = {min(1.0, 2 * tail):.4f}")

    ks = [k for k, _ in sizes]
    ms = [m for _, m in sizes]
    kbar, mbar = sum(ks) / len(ks), sum(ms) / len(ms)
    print("\n  DECOMPOSITION")
    print(f"    mean files per change k    {kbar:.2f}")
    print(f"    mean symbols per change m  {mbar:.2f}   ratio m/k = {mbar / kbar:.2f}")
    if kbar > BUDGET:
        print(f"    c  = {100 * fmiss / n / (kbar - BUDGET):.2f} pts per uncovered file")
    if mbar > BUDGET:
        print(f"    c' = {100 * smiss / n / (mbar - BUDGET):.2f} pts per uncovered symbol")

    with open(OUT, "w") as fh:
        json.dump(
            {
                "cells": {str(k): v for k, v in cells.items()},
                "per_repo": per_repo,
                "kbar": kbar,
                "mbar": mbar,
                "file_units": file_units_total,
                "sym_units": sym_units_total,
            },
            fh,
            indent=1,
        )
    print(f"\n  written to {OUT}")
    return 0


sys.exit(main())
