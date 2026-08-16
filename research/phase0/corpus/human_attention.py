"""Does the model-free ranker point where human reviewers actually looked, before AI existed?

WHAT: Takes merged pre-2022 pull requests that carry human inline review comments on `.py`
      files, ranks each PR's changed files by how many commits touched them in the year before
      the PR, and asks whether a file a human chose to comment on is in the top three. Scored
      against an alphabetical control at the same budget.
WHY:  Every ranking result in this project is validated against a LATER FIX -- a proxy whose
      own limit is measured, since only 14% of the pairs it admits are genuine repairs. This is
      a different and more direct question: the product claims to allocate attention the way a
      good reviewer would, and human review comments are ground truth for where an expert
      actually spent attention. Restricting to pre-2022 removes the contamination found in this
      corpus, where a third of inline comments are written by other AI reviewers and would make
      the test a comparison against a competitor rather than against a human.

      IT IS NOT A DEFECT ORACLE. A reviewer's comment marks where attention went, not where a
      bug was. That is the quantity the product sells, which is why it is worth measuring, and
      it is not the quantity a bug-finder would want.
IMPORTS: stdlib only (collections, json, re, subprocess, sys). Shells out to `gh api`.
CONSUMED BY: nobody -- it prints and writes human_attention_v2.json.
"""

from __future__ import annotations

import collections
import json
import re
import subprocess
import sys
import time
from math import comb

# FRESH repositories. The 8 convenience clones have now carried six variants, a holdout, a
# corpus study and a cost run; whatever they say next about themselves is already known.
REPOS = [
    "scikit-learn/scikit-learn",
    "pandas-dev/pandas",
    "django/django",
    "ansible/ansible",
    "scrapy/scrapy",
    "celery/celery",
]
CUTOFF = "2022-01-01"
BUDGET = 3
MIN_FILES, MAX_FILES = 9, 30  # 4 put exact chance at 79.7% -- top-3 of 4 files is not a test
EARLY_PAGES = 10

BOT_MARK = re.compile(
    r"cubic:v=|cubic:review-run=|coderabbit|sourcery-ai|greptile|<!--\s*metadata:\{"
    r"|codecov|sonarcloud|deepsource",
    re.IGNORECASE,
)


def gh(path: str, attempts: int = 4) -> object:
    """GitHub read, retried on the transient 5xx that killed the first run at repo four.

    A 502 is not a result. Retrying it is not papering over a failure -- the failure that must
    stay fatal is a read that keeps failing, because a dropped repository silently shrinks the
    denominator and reads as a smaller sample rather than as an error.
    """
    last = ""
    for i in range(attempts):
        p = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
        if p.returncode == 0:
            return json.loads(p.stdout)
        last = p.stderr.strip()[:150]
        if not any(code in last for code in ("502", "503", "504", "timeout")):
            break
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{path}: {last}")


def is_bot(c: dict[str, object]) -> bool:
    u = c.get("user") or {}
    login = str(u.get("login", ""))
    return bool(
        u.get("type") == "Bot" or login.endswith("[bot]") or BOT_MARK.search(str(c.get("body", "")))
    )


def prior_touches(repo: str, path: str, until: str) -> int:
    """Commits touching this file in the year before the pull request. The ranker's signal."""
    since = f"{int(until[:4]) - 1}{until[4:]}"
    try:
        got = gh(f"/repos/{repo}/commits?path={path}&since={since}&until={until}&per_page=100")
    except RuntimeError:
        return -1  # a read failure is NOT a zero; the caller drops the event
    return len(got) if isinstance(got, list) else -1


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def collect(repo: str) -> dict[int, set[str]]:
    """Pre-2022 pull requests -> the set of .py files a human commented on."""
    by_pr: dict[int, set[str]] = collections.defaultdict(set)
    for pg in range(1, EARLY_PAGES + 1):  # page 1 is oldest: ascending by creation
        for c in gh(f"/repos/{repo}/pulls/comments?per_page=100&page={pg}"):
            if not isinstance(c, dict) or is_bot(c):
                continue
            if str(c.get("created_at", ""))[:10] >= CUTOFF:
                continue
            if not str(c.get("path", "")).endswith(".py"):
                continue
            num = str(c.get("pull_request_url", "")).rsplit("/", 1)[-1]
            if num.isdigit():
                by_pr[int(num)].add(str(c["path"]))
    return by_pr


def main() -> int:
    events: list[dict[str, object]] = []
    skipped: collections.Counter[str] = collections.Counter()
    for repo in REPOS:
        try:
            commented = collect(repo)
        except RuntimeError as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1
        print(f"  {repo:30s} {len(commented):4d} pre-2022 PRs with human .py comments")
        for num, targets in sorted(commented.items()):
            try:
                pr = gh(f"/repos/{repo}/pulls/{num}")
                files = gh(f"/repos/{repo}/pulls/{num}/files?per_page=100")
            except RuntimeError:
                skipped["unreadable"] += 1
                continue
            if not isinstance(pr, dict) or not pr.get("merged_at"):
                skipped["not merged"] += 1
                continue
            py = [str(f["filename"]) for f in files if str(f["filename"]).endswith(".py")]
            if not (MIN_FILES <= len(py) <= MAX_FILES):
                skipped[f"{len(py)} py files, outside {MIN_FILES}-{MAX_FILES}"] += 1
                continue
            hit_targets = targets & set(py)
            if not hit_targets:
                skipped["commented file not in changed set"] += 1
                continue
            until = str(pr["created_at"])
            scores = {p: prior_touches(repo, p, until) for p in py}
            if any(v < 0 for v in scores.values()):
                skipped["history read failed"] += 1
                continue
            if len(set(scores.values())) == 1:
                skipped["flat ranking, no signal to test"] += 1
                continue
            ranked = sorted(py, key=lambda p: (-scores[p], p))
            events.append(
                {
                    "repo": repo,
                    "pr": num,
                    "n_files": len(py),
                    "targets": sorted(hit_targets),
                    "ranked_hit": bool(set(ranked[:BUDGET]) & hit_targets),
                    "alpha_hit": bool(set(sorted(py)[:BUDGET]) & hit_targets),
                    "rank_of_first": min((ranked.index(t) + 1 for t in hit_targets), default=0),
                }
            )
            print(
                f"    #{num:<7} {len(py):2d} files  rank of first commented file: "
                f"{events[-1]['rank_of_first']}"
            )

    if not events:
        print("  REFUSING TO REPORT — no admissible events")
        return 1
    with open("human_attention_v2.json", "w") as fh:
        json.dump(events, fh, indent=1)

    n = len(events)
    r = sum(1 for e in events if e["ranked_hit"])
    a = sum(1 for e in events if e["alpha_hit"])
    b = sum(1 for e in events if e["ranked_hit"] and not e["alpha_hit"])
    c = sum(1 for e in events if e["alpha_hit"] and not e["ranked_hit"])
    print("\n  SKIP LEDGER (printed because a silent drop reads as a null)")
    for k, v in skipped.most_common():
        print(f"    {v:4d}  {k}")
    print(f"\n  n = {n} pre-2022 pull requests, {MIN_FILES}-{MAX_FILES} changed .py files each")
    print(f"    history top-{BUDGET} contains a human-commented file   {r}/{n} = {r / n:.1%}")
    print(f"    alphabetical control at the same budget              {a}/{n} = {a / n:.1%}")
    print(f"    lift                                                 {(r - a) / n:+.1%}")
    print(f"    discordant b={b} c={c}   McNemar exact p = {mcnemar(b, c):.4f}")
    ranks = [int(e["rank_of_first"]) for e in events]
    dist = collections.Counter(ranks)
    print(
        "    rank of the first commented file: " + ", ".join(f"{k}:{dist[k]}" for k in sorted(dist))
    )
    return 0


sys.exit(main())
