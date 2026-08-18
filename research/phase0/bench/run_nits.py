"""Turn the nit suppression off and measure how much of the Greptile gap closes.

WHAT: Re-reviews the same 50 pull requests with `PROMPT_NITS`, judges the result against the same
      golden comments with the same judge, and reports the new four-cell split beside the strict
      arm's.
WHY:  The gap analysis found a 21% deficit rate inside the categories our prompt bans against 2%
      outside, so the prediction is specific: turning nits on should close most of the 9-issue net
      gap and should cost precision, because the same instruction that suppressed the missed
      issues also suppressed noise.

      THE PREDICTION IS WRITTEN DOWN BELOW BEFORE THE RUN, so "the gap closed" cannot be claimed
      afterwards regardless of what happens to precision. This is a diagnosis of the gap's
      mechanism, NOT a proposed product configuration -- Greptile's own quality filter exists to
      delete exactly the comments this arm adds.
IMPORTS: stdlib only (json, pathlib, sys). Local: `corpus`, `judge`, `reviewer`, Vertex `client`.
CONSUMED BY: nobody -- it prints and writes nits_arm.json.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vertex"))

import judge
import reviewer
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "nits_arm.json"
RIVAL = "greptile-v4-1"

# Pre-registered before the run. Strict arm: 79 TP, 102 FP, P=43.6%, R=45.7%, net gap -9.
PREDICT = """  PRE-REGISTERED PREDICTION
    1. the net gap against greptile closes to between -3 and +3 (from -9)
    2. our precision FALLS below the strict arm's 43.6%, because the instruction that
       suppressed the missed nits also suppressed noise
    3. our recall RISES above 45.7%
    4. candidate volume rises above 194 issues
"""


def main() -> int:
    prs = corpus.pulls()
    client = Client(MODEL)
    print(f"  {len(prs)} pull requests, {sum(len(p['golden']) for p in prs)} golden comments")
    print(PREDICT)

    ours: dict[str, list[str]] = {}
    finishes: dict[str, int] = {}
    for i, pr in enumerate(prs, 1):
        try:
            d = corpus.diff(str(pr["original"]))
            issues, finish = reviewer.review(client, str(pr["title"]), d, nits=True)
        except (corpus.FetchFailed, reviewer.ReviewFailed, KeyError, IndexError) as exc:
            print(f"    {i:2d}/50 FAILED: {str(exc)[:80]}")
            finishes["FAILED"] = finishes.get("FAILED", 0) + 1
            continue
        ours[str(pr["key"])] = issues
        finishes[finish] = finishes.get(finish, 0) + 1
        print(f"    {i:2d}/50 {str(pr['original'])[-26:]:26s} {len(issues):2d} issues  {finish}")

    total = sum(len(v) for v in ours.values())
    print(f"\n  finish reasons: {finishes}")
    print(f"  reviewed {len(ours)}/50, {total} candidate issues (strict arm: 194)\n")

    theirs = corpus.rival_candidates(RIVAL)
    tp = fp = fn = errors = 0
    detail: list[dict[str, object]] = []
    for i, pr in enumerate(prs, 1):
        key, golden = str(pr["key"]), list(pr["golden"])
        vo = judge.verdicts(client, golden, ours.get(key, []))
        vt = judge.verdicts(client, golden, theirs.get(key, []))
        tp += len(vo["tp"])
        fp += len(vo["fp"])
        fn += len(vo["fn"])
        errors += int(vo["errors"]) + int(vt["errors"])
        detail.append(
            {
                "key": key,
                "golden": golden,
                "ours_caught": sorted(vo["tp"]),  # type: ignore[arg-type]
                "theirs_caught": sorted(vt["tp"]),  # type: ignore[arg-type]
            }
        )
        if i % 10 == 0:
            p, r, f = judge.score(tp, fp, fn)
            print(f"    judging {i}/50  P={p:.1%} R={r:.1%} F1={f:.1%}")

    OUT.write_text(json.dumps({"candidates": ours, "detail": detail, "errors": errors}, indent=1))

    p, r, f = judge.score(tp, fp, fn)
    both = sum(len(set(d["ours_caught"]) & set(d["theirs_caught"])) for d in detail)  # type: ignore[arg-type]
    only_t = sum(len(set(d["theirs_caught"]) - set(d["ours_caught"])) for d in detail)  # type: ignore[arg-type]
    only_o = sum(len(set(d["ours_caught"]) - set(d["theirs_caught"])) for d in detail)  # type: ignore[arg-type]
    tot = sum(len(d["golden"]) for d in detail)  # type: ignore[arg-type]

    print(f"\n  {'arm':22s} {'cands':>6} {'TP':>4} {'FP':>4} {'prec':>8} {'recall':>8} {'F1':>7}")
    before = f"{194:6d} {79:4d} {102:4d} {0.436:7.1%} {0.457:7.1%} {0.446:6.1%}"
    print(f"  {'strict (ours, before)':22s} {before}")
    print(f"  {'NITS ON (ours, now)':22s} {total:6d} {tp:4d} {fp:4d} {p:7.1%} {r:7.1%} {f:6.1%}")
    print(
        f"  {'greptile-v4-1':22s} {161:6d} {91:4d} {70:4d} {0.565:7.1%} {0.526:7.1%} {0.545:6.1%}"
    )

    print(f"\n  four cells against greptile, {tot} golden comments")
    none = tot - both - only_t - only_o
    print(f"    both {both}, only THEM {only_t}, only US {only_o}, neither {none}")
    print(f"    NET GAP {only_o - only_t:+d}   (strict arm: -9)")
    print(f"    union {(both + only_t + only_o) / tot:.1%}   (strict arm: 68.8%)")
    print(f"\n  judge errors: {errors}")
    return 0


sys.exit(main())
