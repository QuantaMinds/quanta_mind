"""Fetch pull requests old enough to have both a history and a future.

WHAT: Draws merged pull requests from before a cutoff, refuses any that are too recent to have an
      outcome, and records the full file sources the reviewer needs.
WHY:  Two corpora in this session were drawn from the present and then asked what happened next.
      The review-comment study sampled recent pages and measured project activity phase. The
      pull-request corpus fetched newly merged PRs and left 0.4 days of forward history against a
      90-day outcome rule, which made the relevance check impossible after the adjudication had
      already been paid for.

      `corpus_age.assert_corpus_age` is called here, at fetch time, so the failure lands before the
      expensive part rather than after it. Pre-2022 also predates the AI reviewers that contaminate
      31.5% of recent review comments in this corpus.
IMPORTS: stdlib only (base64, json, subprocess, sys, os). Local: `corpus_age`.
CONSUMED BY: `execution_run.py` in this package.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))

from corpus_age import CorpusTooRecent, assert_corpus_age  # noqa: E402

REPOS = [
    "scrapy/scrapy",
    "celery/celery",
    "pallets/flask",
    "psf/requests",
    "tornadoweb/tornado",
    "encode/django-rest-framework",
]
CUTOFF = "2022-01-01"
PER_REPO = 4
MAX_PY = 10


def gh(path: str) -> object:
    p = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        raise RuntimeError(f"{path}: {p.stderr.strip()[:160]}")
    return json.loads(p.stdout)


def blob(repo: str, sha: str, path: str) -> str:
    try:
        d = gh(f"/repos/{repo}/contents/{path}?ref={sha}")
    except RuntimeError:
        return ""
    if not isinstance(d, dict) or d.get("encoding") != "base64":
        return ""
    try:
        return base64.b64decode(d["content"]).decode("utf-8", "replace")
    except (KeyError, ValueError):
        return ""


def main() -> int:
    out, dates = [], []
    for repo in REPOS:
        taken, page = 0, 1
        while taken < PER_REPO and page <= 12:
            try:
                prs = gh(
                    f"/repos/{repo}/pulls?state=closed&per_page=100&page={page}"
                    f"&sort=created&direction=asc"
                )
            except RuntimeError as exc:
                print(f"  REFUSING TO REPORT — {exc}")
                return 1
            page += 1
            if not prs:
                break
            for pr in prs:
                if taken >= PER_REPO or not pr.get("merged_at"):
                    continue
                if str(pr["merged_at"])[:10] >= CUTOFF:
                    continue
                num, sha = pr["number"], pr["merge_commit_sha"]
                try:
                    files = gh(f"/repos/{repo}/pulls/{num}/files?per_page=100")
                except RuntimeError:
                    continue
                py = [f for f in files if str(f["filename"]).endswith(".py") and f.get("patch")]
                if not (2 <= len(py) <= MAX_PY):
                    continue
                rec = {
                    "repo": repo,
                    "number": num,
                    "title": pr["title"],
                    "sha": sha,
                    "merged_at": pr["merged_at"],
                    "files": [],
                }
                for f in py:
                    rec["files"].append(
                        {
                            "path": f["filename"],
                            "patch": f["patch"],
                            "additions": f["additions"],
                            "deletions": f["deletions"],
                            "source": blob(repo, sha, f["filename"]),
                        }
                    )
                out.append(rec)
                dates.append(str(pr["merged_at"]))
                taken += 1
                print(
                    f"  {repo:30s} #{num:<6} merged {str(pr['merged_at'])[:10]}  {len(py)} py files"
                )

    if not out:
        print("  REFUSING TO REPORT — no admissible pull requests")
        return 1
    try:
        assert_corpus_age(dates)
    except CorpusTooRecent as exc:
        print(f"  REFUSING TO REPORT — {exc}")
        return 1

    with open("corpus_aged.json", "w") as fh:
        json.dump(out, fh)
    print(f"\n  {len(out)} pull requests, all merged before {CUTOFF}")
    print("  every one passes the outcome-window check, so a later-fix relevance test is possible")
    return 0


sys.exit(main())
