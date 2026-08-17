"""Does the ranker beat alphabetical at defect-return on repositories it was never developed on?

WHAT: Replays the V0 policy -- rank a change's `.py` files by how many commits touched them in the
      year before, read the top three -- against an alphabetical control, on six repositories that
      are not among the eight the ranker was developed against. Scored by paired McNemar.
WHY:  It is the one claim the company now rests on. On the original eight, file top-3 misses 1.44%
      against the control's 3.31%. That has never been reproduced elsewhere, and both
      out-of-sample tests attempted so far returned nulls in which the ranker scored BELOW
      alphabetical. Every parameter here is copied from `allocation_variants.py` rather than
      chosen, because a parameter re-picked for a fresh corpus is a parameter tuned on it.
IMPORTS: stdlib only (bisect, collections, json, os, sys, math). Local: `commit_stream`.
CONSUMED BY: nobody -- it prints and writes defect_return_external.json.
"""

from __future__ import annotations

import bisect
import collections
import json
import os
import sys
from math import comb

from commit_stream import ReadFailed, stream

CLONES = (
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad/fresh"
)
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3
MIN_EVENTS, MIN_DISCORDANT = 500, 20  # pre-registered floors


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def run_repo(name: str, path: str) -> list[dict[str, object]]:
    """One record per admissible event, carrying everything a later question might need."""
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
        vals = sorted(score.values(), reverse=True)
        if len(set(vals)) == 1:
            continue  # nothing for a ranking to distinguish
        ranked = sorted(files, key=lambda f: (-score[f], f))
        # The full record, not just hit/hit. The first version stored two booleans, so the
        # later question "how does this compare to CHANCE?" could not be answered from the
        # results at all -- it needed every repository re-cloned and every history re-scanned.
        # Storing n_files and n_target costs nothing and makes the baseline a computation.
        events.append(
            {
                "hit": bool(set(ranked[:BUDGET]) & target),
                "alpha_hit": bool(set(sorted(files)[:BUDGET]) & target),
                "n_files": len(files),
                "n_target": len(target),
                "top_score": vals[0],
                "gap_1_2": vals[0] - vals[1] if len(vals) > 1 else 0,
                "target_is_rank1": ranked[0] in target,
            }
        )
        if len(events) >= MAX_EVENTS:
            break
    return events


def main() -> int:
    per: dict[str, list[dict[str, object]]] = {}

    def on_disk(name: str) -> int:
        total = 0
        for root, _, fs in os.walk(os.path.join(CLONES, name)):
            total += sum(
                os.path.getsize(os.path.join(root, f))
                for f in fs
                if os.path.exists(os.path.join(root, f))
            )
        return total

    # SMALLEST FIRST. One repository in the third sample was larger than the other five
    # combined, and running it first meant no output at all until the whole sweep finished.
    # Cheap repositories first gives a readable signal early and makes a doomed run killable.
    names = [n for n in os.listdir(CLONES) if os.path.isdir(os.path.join(CLONES, n))]
    for name in sorted(names, key=on_disk):
        path = os.path.join(CLONES, name)
        try:
            per[name] = run_repo(name, path)
        except ReadFailed as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1
        h = sum(1 for e in per[name] if not e["hit"])
        a_ = sum(1 for e in per[name] if not e["alpha_hit"])
        n = len(per[name])
        if n:
            print(
                f"  {name[:28]:28s} n={n:4d}  history miss {h / n:6.2%}  "
                f"alphabetical miss {a_ / n:6.2%}"
            )
        else:
            print(f"  {name[:28]:28s} n=   0  no admissible events")

    allev = [e for v in per.values() for e in v]
    n = len(allev)
    if not n:
        print("  REFUSING TO REPORT — no admissible events anywhere")
        return 1
    hm = sum(1 for e in allev if not e["hit"])
    am = sum(1 for e in allev if not e["alpha_hit"])
    b = sum(1 for e in allev if e["hit"] and not e["alpha_hit"])
    c = sum(1 for e in allev if e["alpha_hit"] and not e["hit"])
    p = mcnemar(b, c)
    pos = sum(
        1
        for v in per.values()
        if v and sum(1 for e in v if not e["hit"]) < sum(1 for e in v if not e["alpha_hit"])
    )
    nrep = sum(1 for v in per.values() if v)

    print(f"\n  POOLED  n = {n} events over {nrep} fresh repositories")
    print(f"    history top-3 miss        {hm}/{n} = {hm / n:.2%}")
    print(f"    alphabetical control miss {am}/{n} = {am / n:.2%}")
    print(f"    lift                      {(am - hm) / n * 100:+.2f} points")
    print(f"    discordant  b={b} (history wins)  c={c} (control wins)")
    print(f"    McNemar exact p = {p:.5f}")
    print(f"    repositories where history beats control: {pos}/{nrep}")

    print(
        "\n  READING against docs/plans/preregistrations/defect-return-external-preregistration.md"
    )
    if n < MIN_EVENTS or (b + c) < MIN_DISCORDANT:
        print(
            f"    INCONCLUSIVE — needs >={MIN_EVENTS} events (have {n}) and "
            f">={MIN_DISCORDANT} discordant pairs (have {b + c})"
        )
    elif am - hm > 0 and p < 0.05 and pos >= 4:
        print("    CONFIRMED — control beaten, p < 0.05, and >=4 of 6 repositories positive")
    elif am - hm > 0 and p < 0.05:
        print(
            f"    INCONCLUSIVE — pooled win but only {pos} repositories positive; a pooled win "
            "carried by one repository is the artifact, not a refutation of it"
        )
    else:
        print("    NULL — the ranker does not beat alphabetical at defect-return off-corpus")

    with open("defect_return_external.json", "w") as fh:
        json.dump(per, fh)
    return 0


sys.exit(main())
