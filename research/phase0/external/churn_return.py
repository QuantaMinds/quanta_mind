"""Is the ranker aimed at the wrong outcome? Same design, fix-return against churn-return.

WHAT: Replays the V0 policy on the same six out-of-sample repositories with TWO outcome variables
      and nothing else changed: a later FIX-worded commit touching the file (the shipped target),
      and a later commit of any kind touching it (churn). Reports both miss rates against the same
      alphabetical control.
WHY:  **THE SHIPPED TARGET IS A PROXY AND ITS CONTAMINATION IS KNOWN.** Blind labelling put roughly
      86% of symbol-overlap pairs in the not-a-genuine-repair class, and a fix-word match is a
      guess about intent read off a commit message.

      **IF THE TARGET IS SURVIVAL RATHER THAN DEFECTS, THAT CONTAMINATION STOPS MATTERING.** A
      rewrite is a rewrite whatever the author meant by it, so churn needs no intent classifier and
      has no precision penalty to pay. The ranker is a fix-rate-per-file model, and fix rate is a
      subset of rewrite rate; it may have been validated against a harder outcome than it needs.

      **THE ONLY VARIABLE THAT MOVES IS THE OUTCOME.** Window, budget, file cap, event cap, the
      tie-skip and the prior are copied from `defect_return.py` rather than re-picked, because a
      parameter chosen afresh for a second outcome is a parameter tuned on it.

      **A SHORTER WINDOW FOR CHURN, AND THE REASON IS DEGENERACY.** Over ninety days nearly every
      file in an active repository is touched again, so the target swallows the change, both arms
      hit, and the comparison measures nothing. 14 and 30 days are reported, and if the churn
      target still admits nearly everything the miss rates will be near zero for BOTH arms and
      that is the finding -- not a win.
IMPORTS: stdlib only. Local: `commit_stream`.
CONSUMED BY: read by a human; writes `churn_return.json`.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import subprocess
import sys
from math import comb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from commit_stream import ReadFailed, stream

OUT = pathlib.Path(__file__).resolve().parent / "results" / "churn_return.json"
YEAR = 365 * 86400
DAY = 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3
REPOS = (
    "ansible/ansible",
    "celery/celery",
    "django/django",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "scrapy/scrapy",
)
# (label, window in days, whether a fix-word is required)
ARMS = (("fix_90d", 90, True), ("churn_30d", 30, False), ("churn_14d", 14, False))


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def clone(repo: str, root: pathlib.Path) -> pathlib.Path | None:
    where = root / repo.replace("/", "_")
    if (where / ".git").is_dir():
        return where
    done = subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            f"https://github.com/{repo}.git",
            str(where),
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    return where if done.returncode == 0 else None


def score_arm(commits: list, idx: dict, window_days: int, need_fix: bool) -> list[dict]:
    """Events for one outcome definition. Everything but the target is fixed."""
    window = window_days * DAY
    events: list[dict[str, object]] = []
    for i, (ts, _msg, files) in enumerate(commits):
        if not (2 <= len(files) <= MAX_FILES):
            continue
        target: set[str] = set()
        for ts2, msg2, files2 in commits[i + 1 :]:
            if ts2 - ts > window:
                break
            if need_fix and not any(w in msg2 for w in FIXWORDS):
                continue
            target |= files2 & files
        if not target:
            continue
        score = {f: prior(idx, f, ts) for f in files}
        vals = sorted(score.values(), reverse=True)
        if len(set(vals)) == 1:
            continue
        ranked = sorted(files, key=lambda f: (-score[f], f))
        events.append(
            {
                "hit": bool(set(ranked[:BUDGET]) & target),
                "alpha_hit": bool(set(sorted(files)[:BUDGET]) & target),
                "n_files": len(files),
                "n_target": len(target),
            }
        )
        if len(events) >= MAX_EVENTS:
            break
    return events


def main() -> int:
    root = pathlib.Path("/Users/dhanu/.claude/jobs/4cdada9b/tmp/churn-clones")
    root.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict[str, list]] = {}

    for repo in REPOS:
        where = clone(repo, root)
        if where is None:
            print(f"  {repo}: clone failed", flush=True)
            continue
        try:
            commits = stream(str(where))
        except ReadFailed as exc:
            print(f"  {repo}: {str(exc)[:60]}", flush=True)
            continue
        idx: dict[str, list[int]] = collections.defaultdict(list)
        for ts, _, files in commits:
            for f in files:
                idx[f].append(ts)
        out[repo] = {}
        for label, days, need_fix in ARMS:
            ev = score_arm(commits, idx, days, need_fix)
            out[repo][label] = ev
            miss = sum(1 for e in ev if not e["hit"]) / max(1, len(ev))
            am = sum(1 for e in ev if not e["alpha_hit"]) / max(1, len(ev))
            print(
                f"  {repo:<28} {label:<10} n={len(ev):<4} miss {miss:>6.2%}  alpha {am:>6.2%}",
                flush=True,
            )

    OUT.write_text(json.dumps(out, indent=1))
    head = f"{'outcome':<12}{'events':>8}{'ours miss':>11}{'alpha miss':>12}"
    print(f"\n  {head}{'b':>5}{'c':>5}{'p':>10}")
    for label, _d, _f in ARMS:
        ev = [e for r in out.values() for e in r.get(label, [])]
        if not ev:
            continue
        miss = sum(1 for e in ev if not e["hit"]) / len(ev)
        am = sum(1 for e in ev if not e["alpha_hit"]) / len(ev)
        b = sum(1 for e in ev if e["hit"] and not e["alpha_hit"])
        c = sum(1 for e in ev if not e["hit"] and e["alpha_hit"])
        print(
            f"  {label:<12}{len(ev):>8}{miss:>11.2%}{am:>12.2%}{b:>5}{c:>5}{mcnemar(b, c):>10.2e}"
        )
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
