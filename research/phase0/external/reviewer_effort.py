"""What does a buyer get: how much less is read, and is the returning file still in it?

WHAT: Over the twelve out-of-sample clones, scores every admissible change three ways -- read the
      top three by fix history, read the top three alphabetically, read everything -- and reports
      effort asked against catch rate for each, against the bars fixed in
      `docs/plans/roi-preregistration.md` before this ran.
WHY:  Every measurement before this one scores the METHOD. None scores the PURCHASE. A business
      does not buy a miss rate, it buys reviewer hours, and nobody has measured what the policy
      costs a reader.

      THIS TESTS ONE LINK OF FIVE. Whether a reviewer reads what we rank first, finds the defect
      there, and keeps it out of production is unmeasured and needs a live pilot. The output here
      may not support a sentence containing "prevents" or "reduces incidents".
IMPORTS: stdlib only (bisect, collections, json, os, random, statistics, sys, math).
      Local: `commit_stream`, `patch_size`, `effort_bars`.
CONSUMED BY: nobody -- it prints and writes reviewer_effort.json.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import random
import statistics
import sys

import effort_bars
import patch_size
from commit_stream import ReadFailed, stream

ROOT = (
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad"
)
SAMPLES = ("fresh", "third")
YEAR, WINDOW = 365 * 86400, 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, BUDGET, MAX_EVENTS = 12, 3, 800
SIZE_SAMPLE = 25  # commits per repo re-read with --numstat; ~1s each on a blob:none clone
SEED = 20260816  # fixed: a sample that changes between runs cannot be checked against


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def score_repo(path: str) -> list[dict[str, object]]:
    """One record per admissible change, carrying the split the size study needs."""
    commits = stream(path)
    idx: dict[str, list[int]] = collections.defaultdict(list)
    for ts, _, files in commits:
        for f in files:
            idx[f].append(ts)

    events: list[dict[str, object]] = []
    for i, (ts, _msg, files) in enumerate(commits):
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
        ranked = sorted(files, key=lambda f: (-score[f], f))
        events.append(
            {
                "n_files": len(files),
                "read": min(BUDGET, len(files)),
                "hit": bool(set(ranked[:BUDGET]) & target),
                "alpha_hit": bool(set(sorted(files)[:BUDGET]) & target),
                "ts": ts,
                "top": ranked[:BUDGET],
                "rest": ranked[BUDGET:],
                "all": sorted(files),
            }
        )
        if len(events) >= MAX_EVENTS:
            break
    return events


def size_study(path: str, events: list[dict[str, object]]) -> tuple[list[tuple[float, float]], int]:
    """Mean changed lines of the ranked files against the skipped. Returns (pairs, dropped)."""
    by_ts = patch_size.shas(path)
    rng = random.Random(SEED)
    eligible = [e for e in events if e["rest"] and int(str(e["ts"])) in by_ts]
    pairs: list[tuple[float, float]] = []
    dropped = 0
    for ev in rng.sample(eligible, min(SIZE_SAMPLE, len(eligible))):
        ns = patch_size.numstat(
            path,
            by_ts[int(str(ev["ts"]))],
            frozenset(ev["all"]),  # type: ignore[arg-type]
        )
        if ns is None:
            dropped += 1  # counted, never absorbed -- see patch_size.numstat
            continue
        top = [ns[f] for f in ev["top"] if f in ns]  # type: ignore[union-attr]
        rest = [ns[f] for f in ev["rest"] if f in ns]  # type: ignore[union-attr]
        if top and rest:
            pairs.append((statistics.mean(top), statistics.mean(rest)))
    return pairs, dropped


def main() -> int:
    per: dict[str, list[dict[str, object]]] = {}
    sizes: list[tuple[float, float]] = []
    dropped = 0
    for sample in SAMPLES:
        base = os.path.join(ROOT, sample)
        if not os.path.isdir(base):
            print(f"  REFUSING TO REPORT — {base} is not on disk")
            return 1
        for name in sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n))):
            path = os.path.join(base, name)
            try:
                ev = score_repo(path)
                pairs, drop = size_study(path, ev)
            except (ReadFailed, patch_size.ReadFailed) as exc:
                print(f"  REFUSING TO REPORT — {exc}")
                return 1
            per[f"{sample}/{name}"] = ev
            sizes += pairs
            dropped += drop
            if not ev:
                print(f"  {name[:26]:26s} n=   0  no admissible events")
                continue
            red = 1 - sum(int(str(e["read"])) for e in ev) / sum(int(str(e["n_files"])) for e in ev)
            catch = sum(1 for e in ev if e["hit"]) / len(ev)
            acatch = sum(1 for e in ev if e["alpha_hit"]) / len(ev)
            verdict = "WIN" if catch > acatch else "tie" if catch == acatch else "LOSS"
            print(
                f"  {name[:26]:26s} n={len(ev):4d}  saves {red:5.1%}  "
                f"catch {catch:6.2%}  alpha {acatch:6.2%}  {verdict}"
            )

    if not any(per.values()):
        print("  REFUSING TO REPORT — no admissible events")
        return 1
    with open("reviewer_effort.json", "w") as fh:
        json.dump({"events": per, "sizes": sizes, "dropped": dropped}, fh)
    effort_bars.report(per, sizes, dropped)
    return 0


sys.exit(main())
