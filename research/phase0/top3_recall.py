"""Top-3 recall for the allocator's budget policy, on the corpus that produced 85.3% top-1.

WHAT: Measures whether the file a later fix returns to is inside the top 3 by prior-commit
      count -- the ranks the allocator funds -- and reports the cold-miss rate, which is the
      share of events where the budget policy would produce silence.
WHY:  85.3% top-1 was the headline, but the budget gives model calls to ranks 1-3 and none to
      cold units. Top-1 answers "is the spend well aimed"; only top-3 answers "does allocation
      lose defects". A defect in a cold unit yields no finding and no error, so the failure
      mode this measures is invisible everywhere else.
IMPORTS: stdlib (bisect, collections, json, os) and git_history_read, the sibling that
      reads one repository's history. No research dependencies; runs on either interpreter.
CONSUMED BY: docs/plans/gravity-reviewer-build-plan.md, the foundation measurement table.

The allocator funds ranks 1-3 and gives cold units no model call at all. So the number that
decides whether allocation LOSES defects is not top-1 -- it is top-3. A defect in a cold unit
produces no finding and no error: silence that looks identical to a clean review.

Event definition is copied verbatim from scale_ranker.py so the two numbers are comparable.
The only additions are the top-3 arms and the controls.

THE VACUITY CONTROL, which is the point of this script: for a change touching <= 3 files,
"is the target in the top 3" is True by construction and measures nothing. Reporting a pooled
top-3 recall would therefore report mostly arithmetic. Every arm is stratified by file count,
and the >= 4 stratum is the only one that carries information. A pooled figure is printed only
next to the stratified one, never alone.

Controls, because a number without one is not a measurement:
  - alphabetical null: the first three files by name. Non-informative by construction.
  - random baseline:   expected coverage of drawing 3 of len(files) without replacement.
"""

from __future__ import annotations

import bisect
import collections
import json
import os

from git_history_read import GitReadFailed, load

CL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clones")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "top3_result.json")
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES = 12
MAX_EVENTS = 400
BUDGET = 3  # ranks 1-3 get a model call; everything below is cold


def main():
    # strata: "<=3" is vacuous for top-3, ">=4" is the informative one
    arms = {s: collections.Counter() for s in ("<=3", ">=4")}
    per_repo = []
    skipped = []  # every exclusion, with its reason. Silence here is what broke run one.

    for name in sorted(os.listdir(CL)):
        d = os.path.join(CL, name)
        if not os.path.isdir(os.path.join(d, ".git")):
            continue
        try:
            commits = load(d)
        except GitReadFailed as exc:
            skipped.append((name, f"GIT READ FAILED: exit {exc.returncode}"))
            continue
        if len(commits) < 200:
            skipped.append((name, f"ineligible: {len(commits)} commits < 200"))
            continue

        idx = collections.defaultdict(list)
        for _, ts, _, files in commits:
            for f in files:
                idx[f].append(ts)

        local = collections.Counter()
        n_ev = 0
        for i, (_sha, ts, _msg, files) in enumerate(commits):
            if not (2 <= len(files) <= MAX_FILES):
                continue
            target = set()
            for _sha2, ts2, msg2, files2 in commits[i + 1 :]:
                if ts2 - ts > WINDOW:
                    break
                if any(w in msg2 for w in FIXWORDS):
                    target |= set(files2) & set(files)
            if not target:
                continue

            # Bound as defaults, not captured late. The call sites are all inside this
            # iteration so late binding was correct by accident; correct-by-accident is
            # the class of thing that stops being correct when someone moves a line.
            def prior(f, _idx=idx, _ts=ts):
                lst = _idx[f]
                return bisect.bisect_left(lst, _ts) - bisect.bisect_left(lst, _ts - YEAR)

            scores = {f: prior(f) for f in files}
            if len(set(scores.values())) == 1:
                continue
            n_ev += 1

            stratum = "<=3" if len(files) <= BUDGET else ">=4"
            a = arms[stratum]
            a["n"] += 1

            # ranker: descending prior-commit count, ties broken by name for determinism
            ordered = sorted(files, key=lambda f: (-scores[f], f))
            top1, top3 = ordered[0], set(ordered[:BUDGET])
            a["top1"] += top1 in target
            a["top3"] += bool(top3 & target)

            # controls
            alpha = sorted(files)
            a["null1"] += alpha[0] in target
            a["null3"] += bool(set(alpha[:BUDGET]) & target)
            # expected coverage of a random 3-of-k draw, computed exactly rather than sampled
            k, t = len(files), len(target)
            miss = 1.0
            for j in range(min(BUDGET, k)):  # k<=BUDGET means the draw takes every file
                miss *= max(0.0, (k - t - j)) / (k - j)
            a["rand3"] += 1.0 - miss

            local[stratum + "_n"] += 1
            local[stratum + "_top3"] += bool(top3 & target)
            if n_ev >= MAX_EVENTS:
                break

        if n_ev >= 20:
            per_repo.append([name, dict(local)])
        else:
            skipped.append((name, f"ineligible: {n_ev} events < 20"))

    # The ledger prints BEFORE the table, so a failed read cannot be scrolled past.
    failures = [(n, r) for n, r in skipped if r.startswith("GIT READ")]
    print(f"\n  repositories included : {len(per_repo)}")
    print(f"  repositories skipped  : {len(skipped)}")
    for n, r in skipped:
        print(f"      {n:42s} {r}")
    if failures:
        raise SystemExit(
            f"\n  REFUSING TO REPORT: {len(failures)} repository read(s) failed. A partial "
            f"population produces a plausible table and a wrong number."
        )

    print(
        f"\n{'stratum':>8} {'n':>6} {'top-1':>8} {'top-3':>8} "
        f"{'null-3':>8} {'rand-3':>8} {'COLD MISS':>10}"
    )
    print("-" * 62)
    pooled = collections.Counter()
    for s in ("<=3", ">=4"):
        a = arms[s]
        n = a["n"]
        pooled.update(a)
        if not n:
            continue
        print(
            f"{s:>8} {n:>6} {a['top1'] / n:>7.1%} {a['top3'] / n:>7.1%} "
            f"{a['null3'] / n:>7.1%} {a['rand3'] / n:>7.1%} {1 - a['top3'] / n:>9.1%}"
        )
    n = pooled["n"]
    print("-" * 62)
    print(
        f"{'POOLED':>8} {n:>6} {pooled['top1'] / n:>7.1%} {pooled['top3'] / n:>7.1%} "
        f"{pooled['null3'] / n:>7.1%} {pooled['rand3'] / n:>7.1%} "
        f"{1 - pooled['top3'] / n:>9.1%}"
    )
    print("\n  POOLED top-3 is inflated by the <=3 stratum, where it is 100% by construction.")
    print("  The >=4 row is the one that answers the allocator question.")
    print(
        f"\n  share of events in the vacuous stratum: "
        f"{arms['<=3']['n']}/{n} = {arms['<=3']['n'] / n:.1%}"
    )

    with open(OUT, "w") as fh:
        json.dump(
            {"arms": {s: dict(a) for s, a in arms.items()}, "per_repo": per_repo}, fh, indent=1
        )
    print(f"\n  written to {OUT}")


main()
