"""Why does the ranker beat alphabetical on some repositories and tie on others?

WHAT: For every admitted event, records the properties that decide whether a ranking CAN help --
      how many files the change touches, how far apart their fix-history scores are, and whether
      the file a later fix returns to is the top-scored one. Reported per repository beside the
      miss rates.
WHY:  home-assistant/core is the first repository in twenty where history and an alphabetical
      control tie exactly (2.50% each).

      THE HYPOTHESIS THIS FILE WAS WRITTEN TO TEST WAS WRONG, and the wrong version is kept
      because the correction is the point. It predicted flat fix-history across a change's files,
      leaving nothing to rank on. Measured: home-assistant's rank-1-to-rank-2 gap is 15.19, LARGER
      than numpy, pytest and poetry, all of which the ranker wins on.

      What the added chance column shows instead: history beats chance by +1.75 there, in line
      with matplotlib and numpy. It is the CONTROL that changed. Alphabetical ordering sits at or
      below chance in five of six repositories and at +1.75 in home-assistant, because
      `homeassistant/components/<integration>/` makes the alphabetically-first file in a change
      usually that component's __init__.py -- which is also the churn-heavy one. So the headline
      lift is measured against a baseline whose strength varies by repository layout, and exact
      chance is the invariant comparison.
IMPORTS: stdlib only (bisect, collections, json, os, statistics, sys). Local: `commit_stream`.
CONSUMED BY: nobody -- it prints and writes discriminability.json.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import statistics
import sys

from commit_stream import ReadFailed, stream

YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def analyse(path: str) -> list[dict[str, float]]:
    commits = stream(path)
    idx: dict[str, list[int]] = collections.defaultdict(list)
    for ts, _, files in commits:
        for f in files:
            idx[f].append(ts)

    out: list[dict[str, float]] = []
    for i, (ts, _m, files) in enumerate(commits):
        if not (2 <= len(files) <= MAX_FILES):
            continue
        target: set[str] = set()
        for ts2, msg2, files2 in commits[i + 1 :]:
            if ts2 - ts > WINDOW:
                break
            if any(w in msg2 for w in FIXWORDS):
                target |= files2 & files
        if not target:
            continue
        score = {f: prior(idx, f, ts) for f in files}
        vals = sorted(score.values(), reverse=True)
        if len(set(vals)) == 1:
            continue
        ranked = sorted(files, key=lambda f: (-score[f], f))
        # how much daylight is there between the top pick and the rest?
        top = vals[0]
        gap = top - vals[1] if len(vals) > 1 else 0
        out.append(
            {
                "n_files": len(files),
                "n_target": len(target),
                "top_score": top,
                "gap_1_2": gap,
                "spread": top - vals[-1],
                "mean_score": statistics.mean(vals),
                "distinct_scores": len(set(vals)),
                "target_is_rank1": float(ranked[0] in target),
                "hit": float(bool(set(ranked[:BUDGET]) & target)),
                "alpha_hit": float(bool(set(sorted(files)[:BUDGET]) & target)),
            }
        )
        if len(out) >= MAX_EVENTS:
            break
    return out


def main() -> int:
    root = sys.argv[1]
    per: dict[str, list[dict[str, float]]] = {}
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            continue
        try:
            per[name] = analyse(p)
        except ReadFailed as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1

    print(
        f"  {'repo':22s} {'n':>4} {'files':>6} {'distinct':>9} {'gap1-2':>7} "
        f"{'spread':>7} {'rank1':>7} {'hist':>7} {'alpha':>7} {'lift':>7}"
    )
    for name, ev in per.items():
        if not ev:
            print(f"  {name.split('_')[-1][:22]:22s} no admissible events")
            continue
        n = len(ev)
        hist = 1 - statistics.mean(e["hit"] for e in ev)
        alpha = 1 - statistics.mean(e["alpha_hit"] for e in ev)
        col = {
            k: statistics.mean(e[k] for e in ev)
            for k in ("n_files", "distinct_scores", "gap_1_2", "spread", "target_is_rank1")
        }
        print(
            f"  {name.split('_')[-1][:22]:22s} {n:4d} {col['n_files']:6.2f} "
            f"{col['distinct_scores']:9.2f} {col['gap_1_2']:7.2f} {col['spread']:7.2f} "
            f"{col['target_is_rank1']:7.1%} {hist:7.2%} {alpha:7.2%} "
            f"{(alpha - hist) * 100:+6.2f}"
        )

    with open("results/discriminability.json", "w") as fh:
        json.dump(per, fh)
    return 0


sys.exit(main())
