"""How often does production meet a change the ranking cannot order, and what happens there?

WHAT: Replays the same admissibility as `defect_return.py` over the twelve out-of-sample clones,
      but classifies EVERY admissible event instead of dropping the ones a ranking cannot
      separate. Reports how many changes carry no prior-year history at all, how many carry
      history that is identical across every file touched, and the miss rate inside each class.
WHY:  `defect_return.py` skips an event when every file scores the same -- `if len(set(vals)) == 1:
      continue` -- because there is nothing for a ranking to distinguish. That is right for
      measuring discrimination and wrong for building a product: **production cannot skip a pull
      request.** The headline 1.53% is conditional on a case that was filtered out, and nobody has
      said how often that case arrives or what the ranker should emit inside it.

      A file with no history is NOT a file that is safe. Reporting it as rank-N is the untyped
      silence this product exists to end, so the rate decides whether `Allocation.COLD` is an edge
      case or the common path.
IMPORTS: stdlib only (bisect, collections, json, os, sys). Local: `commit_stream`.
CONSUMED BY: nobody -- it prints and writes degenerate_rate.json. Read by
      `docs/plans/delivered/feat/rank-fix-history.md`.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import sys

from commit_stream import ReadFailed, stream

ROOT = (
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad"
)
SAMPLES = ("fresh", "third")
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, BUDGET = 12, 3
MAX_ADMISSIBLE = 800  # per repo; the original capped at 400 DISCRIMINATING events


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def classify(scores: dict[str, int]) -> str:
    """Which of the three cases a ranking faces. Only the third is what was measured."""
    vals = set(scores.values())
    if vals == {0}:
        return "no_history"
    if len(vals) == 1:
        return "flat_history"
    return "discriminating"


def run_repo(path: str) -> list[dict[str, object]]:
    commits = stream(path)
    idx: dict[str, list[int]] = collections.defaultdict(list)
    for ts, _, files in commits:
        for f in files:
            idx[f].append(ts)

    out: list[dict[str, object]] = []
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
        out.append(
            {
                "case": classify(score),
                "hit": bool(set(ranked[:BUDGET]) & target),
                "alpha_hit": bool(set(sorted(files)[:BUDGET]) & target),
                "n_files": len(files),
                "n_target": len(target),
            }
        )
        if len(out) >= MAX_ADMISSIBLE:
            break
    return out


def main() -> int:
    per: dict[str, list[dict[str, object]]] = {}
    for sample in SAMPLES:
        base = os.path.join(ROOT, sample)
        if not os.path.isdir(base):
            print(f"  REFUSING TO REPORT — {base} is not on disk")
            return 1
        names = [n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n))]
        for name in sorted(names):
            try:
                per[f"{sample}/{name}"] = run_repo(os.path.join(base, name))
            except ReadFailed as exc:
                print(f"  REFUSING TO REPORT — {exc}")
                return 1
            ev = per[f"{sample}/{name}"]
            counts = collections.Counter(str(e["case"]) for e in ev)
            print(
                f"  {name[:26]:26s} n={len(ev):4d}  "
                f"no_history {counts['no_history']:4d}  "
                f"flat {counts['flat_history']:4d}  "
                f"discriminating {counts['discriminating']:4d}"
            )

    allev = [e for v in per.values() for e in v]
    if not allev:
        print("  REFUSING TO REPORT — no admissible events")
        return 1
    with open("results/degenerate_rate.json", "w") as fh:
        json.dump(per, fh)

    n = len(allev)
    print(f"\n  {n} admissible events across {len(per)} out-of-sample repositories\n")
    print(f"  {'case':18s} {'n':>6} {'share':>8} {'history miss':>13} {'alpha miss':>11}")
    for case in ("discriminating", "flat_history", "no_history"):
        g = [e for e in allev if e["case"] == case]
        if not g:
            continue
        hm = sum(1 for e in g if not e["hit"]) / len(g)
        am = sum(1 for e in g if not e["alpha_hit"]) / len(g)
        print(f"  {case:18s} {len(g):6d} {len(g) / n:7.2%} {hm:12.2%} {am:10.2%}")

    nondiscriminating = [e for e in allev if e["case"] != "discriminating"]
    print(
        f"\n  THE MEASURED HEADLINE EXCLUDED {len(nondiscriminating) / n:.2%} OF ADMISSIBLE EVENTS."
    )
    print("  In those the ranking is the alphabetical control, because the tie-break IS the sort.")
    return 0


sys.exit(main())
