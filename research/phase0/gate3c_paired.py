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

from gate3c_report import render
from symbol_history_read import ReadFailed, stream

CL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clones")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate3c_result.json")
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES = 12
MAX_EVENTS = 400
BUDGET = 3


def top3_hit(units, idx, ts, target, budget=BUDGET):
    """Rank units by prior-year touches, return (hit, k). None when the choice is degenerate."""

    def prior(u):
        lst = idx.get(u, [])
        return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)

    scores = {u: prior(u) for u in units}
    if len(set(scores.values())) == 1:
        return None, len(units)
    ordered = sorted(units, key=lambda u: (-scores[u], u))
    return bool(set(ordered[:budget]) & target), len(units)


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

    cells = collections.Counter()
    matched = collections.Counter()  # (file_hit, sym_hit) -> n
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

            fhit, k = top3_hit(files, fidx, ts, ftarget, 3)
            shit, m = top3_hit(syms, sidx, ts, starget, 3)
            shit5, _ = top3_hit(syms, sidx, ts, starget, 5)
            if fhit is None or shit is None:
                continue

            n_ev += 1
            cells[(fhit, shit)] += 1
            matched[(fhit, shit5)] += 1
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

    if not render(cells, matched, sizes, per_repo, file_units_total, sym_units_total, BUDGET):
        return 1

    with open(OUT, "w") as fh:
        json.dump(
            {
                "cells": {str(k): v for k, v in cells.items()},
                "per_repo": per_repo,
                "kbar": sum(k for k, _ in sizes) / len(sizes),
                "mbar": sum(m for _, m in sizes) / len(sizes),
                "file_units": file_units_total,
                "sym_units": sym_units_total,
            },
            fh,
            indent=1,
        )
    print(f"\n  written to {OUT}")
    return 0


sys.exit(main())
