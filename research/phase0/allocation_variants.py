"""Four pre-specified allocation variants, each against its non-informative control.

WHAT: V0 file top-3, V1 function top-3, V2 file ranked by summed touched-function history,
      V3 score-gap stopping, V5 union -- each with an alphabetical control and a train/holdout
      split fixed before the run.
WHY:  A sweep would find a winner by chance: this corpus carries about five comparisons before
      multiplicity eats the result, and this project already recorded ten metadata signals where
      nothing survived Bonferroni. So the variants are pre-specified, corrected at 0.0125, and
      the winner is checked on two clones held out before anything was looked at -- which is
      what caught V2 winning on train and reversing on holdout.
IMPORTS: stdlib (bisect, collections, json, math, os, sys), clone_census, symbol_history_read.
CONSUMED BY: docs/plans/implementation.md, gate 3c.

PRE-SPECIFIED BEFORE THE RUN. Not a sweep -- 1,969 paired events on 8 repositories can carry
about five comparisons before multiplicity eats the result, and this project has already
recorded ten metadata signals where nothing survived Bonferroni.

  HOLDOUT, fixed before any variant ran: clones sorted by name, indices 2 and 5 --
  OpenPipe_ART and browser-use_browser-use. Everything below is fitted on the other six and
  the winner is checked once on those two.

  V0  file top-3                     the incumbent, for reference
  V1  function top-3                 the architecture as specified
  V2  file ranked by SUM of the touch counts of ONLY the functions this change touched.
      Follows directly from the hybrid post-mortem: summing beat taking the maximum, but
      whole-file ranking sums history for functions the change never touched. This keeps the
      aggregation and drops the irrelevant part. Highest-value single test.
  V3  score-gap stopping instead of fixed k: take units while score >= 0.5 x the top score,
      minimum 1, maximum 5. One parameter, stated. Reports mean units so cost is visible.
  V5  union of file top-3 and function top-1. Bounded by the discordance cell at 17/1,969.

  CONTROL for every variant: the alphabetical pick over the same units at the same k. A policy
  that does not beat alphabetical is not a policy -- the rule that killed the 12/12 revert
  result when its control also scored 12/12.

  MULTIPLICITY: four variants against V0, so Bonferroni alpha = 0.05/4 = 0.0125.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import sys
from math import comb

from clone_census import full_object_clones
from symbol_history_read import ReadFailed, stream

CL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clones")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variants_result.json")
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3
GAP_FRACTION, GAP_MAX = 0.5, 5


def prior(idx, unit, ts):
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def ordered(units, scores):
    return sorted(units, key=lambda u: (-scores[u], u))


def hit(picked, target):
    return bool(set(picked) & target)


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def main() -> int:
    full = full_object_clones(CL)
    holdout = {full[2], full[5]}
    print(f"  holdout: {sorted(holdout)}\n")

    arms = ("V0_file3", "V1_func3", "V2_sumfile3", "V3_gap", "V5_union")
    res = {g: {a: collections.Counter() for a in arms} for g in ("train", "hold")}
    ctrl = {g: {a: collections.Counter() for a in arms} for g in ("train", "hold")}
    units_read = {g: collections.defaultdict(list) for g in ("train", "hold")}
    paired = {g: collections.Counter() for g in ("train", "hold")}

    for name in full:
        group = "hold" if name in holdout else "train"
        try:
            commits = stream(os.path.join(CL, name))
        except ReadFailed as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1
        if len(commits) < 200:
            continue

        fidx, sidx = collections.defaultdict(list), collections.defaultdict(list)
        for _, ts, _, files, syms in commits:
            for f in files:
                fidx[f].append(ts)
            for s in syms:
                sidx[s].append(ts)

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

            fscore = {f: prior(fidx, f, ts) for f in files}
            sscore = {s: prior(sidx, s, ts) for s in syms}
            if len(set(fscore.values())) == 1 or len(set(sscore.values())) == 1:
                continue
            n_ev += 1

            # V2: rank files by the summed history of ONLY the functions this change touched
            sumscore: dict[str, int] = collections.defaultdict(int)
            for s in syms:
                sumscore[s.split("::", 1)[0]] += sscore[s]
            for f in files:
                sumscore.setdefault(f, 0)

            fo, so = ordered(files, fscore), ordered(syms, sscore)
            v2o = ordered(list(sumscore), sumscore)

            # V3: score-gap stopping over functions
            top = sscore[so[0]] if so else 0
            gap = [u for u in so[:GAP_MAX] if sscore[u] >= GAP_FRACTION * top] or so[:1]

            picks = {
                "V0_file3": (fo[:BUDGET], ftarget, BUDGET),
                "V1_func3": (so[:BUDGET], starget, BUDGET),
                "V2_sumfile3": (v2o[:BUDGET], ftarget, BUDGET),
                "V3_gap": (gap, starget, len(gap)),
                "V5_union": (fo[:BUDGET], ftarget, BUDGET + 1),
            }
            for arm, (picked, target, k) in picks.items():
                got = hit(picked, target)
                if arm == "V5_union":
                    got = got or hit(so[:1], starget)
                res[group][arm][got] += 1
                units_read[group][arm].append(k)
                # non-informative control: alphabetical over the same units, same k
                pool = sorted(files) if target is ftarget else sorted(syms)
                cgot = hit(pool[: len(picked)], target)
                if arm == "V5_union":
                    cgot = cgot or hit(sorted(syms)[:1], starget)
                ctrl[group][arm][cgot] += 1

            paired[group][(hit(fo[:BUDGET], ftarget), hit(v2o[:BUDGET], ftarget))] += 1
            if n_ev >= MAX_EVENTS:
                break

    for group in ("train", "hold"):
        n = sum(res[group]["V0_file3"].values())
        if not n:
            continue
        print(f"\n  === {group.upper()}  n={n} ===")
        print(f"  {'arm':14s} {'miss':>8}  {'control':>8}  {'lift':>7}  {'units':>6}")
        for arm in arms:
            miss = res[group][arm][False] / n
            cmiss = ctrl[group][arm][False] / n
            mu = sum(units_read[group][arm]) / len(units_read[group][arm])
            print(f"  {arm:14s} {miss:7.2%}  {cmiss:7.2%}  {cmiss - miss:+6.2%}  {mu:6.2f}")
        b = paired[group][(True, False)]
        c = paired[group][(False, True)]
        print(f"  V2 vs V0 paired: b={b} c={c}  McNemar p={mcnemar(b, c):.4f}  (Bonferroni 0.0125)")

    with open(OUT, "w") as fh:
        json.dump(
            {g: {a: dict(res[g][a]) for a in arms} for g in ("train", "hold")},
            fh,
            indent=1,
        )
    return 0


sys.exit(main())
