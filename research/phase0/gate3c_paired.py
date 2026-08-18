"""Gate 3c: does function-level allocation lose more than the file-level analogue?

WHAT: A paired comparison on identical events -- file-top-3, function-top-3, function-top-5 at
      matched coverage, and the hybrid that ranks by function and reads the enclosing file --
      with McNemar on the discordant pairs and the c/c' decomposition.
WHY:  Top-1 says whether the spend is well aimed; only top-3 says whether allocation loses
      defects. The allocator ranks FUNCTIONS and the corpus-wide figure was measured on FILES,
      so the arms had never been compared on the same events. Paired, because only
      disagreements carry information.
IMPORTS: stdlib (bisect, collections, json, os, subprocess, sys), symbol_history_read,
      gate3c_report.
CONSUMED BY: docs/findings/ALLOCATION_EVIDENCE_2026-08.md, gate 3c.

Every rule here -- the discordance criterion, the matched-coverage budget, the hybrid's
expansion -- was pre-specified in the plan before the run. Two assertions guard the read: the
git exit code, and that symbol slots differ from file slots.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import sys

from clone_census import full_object_clones
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
    full = full_object_clones(CL)

    cells = collections.Counter()
    matched = collections.Counter()
    hybrid = {
        1: collections.Counter(),
        2: collections.Counter(),
        3: collections.Counter(),
    }  # (file_hit, sym_hit) -> n
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

            # HYBRID: rank globally by function, then read the ENCLOSING FILE of each.
            def _prior_sym(u, _i=sidx, _t=ts):
                lst = _i.get(u, [])
                return bisect.bisect_left(lst, _t) - bisect.bisect_left(lst, _t - YEAR)

            ordered_syms = sorted(syms, key=lambda u: (-_prior_sym(u), u))
            for nn in (1, 2, 3):
                expanded = {u.split("::", 1)[0] for u in ordered_syms[:nn]}
                hybrid[nn][bool(expanded & ftarget)] += 1
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

    n = sum(cells.values())
    if not render(cells, matched, sizes, per_repo, file_units_total, sym_units_total, BUDGET):
        return 1
    print("\n  HYBRID — rank by function, allocate by enclosing file")
    for nn in (1, 2, 3):
        hm = hybrid[nn][False]
        print(f"    top-{nn} functions -> their files   miss {hm}/{n}")

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
