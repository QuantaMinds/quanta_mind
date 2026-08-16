"""Draw OSS inline review comments under two sampling schemes, carrying the author.

WHAT: Fetches .py inline review comments from eight public repositories twice -- the most
      recent two pages, and six pages drawn uniformly at random from the repository's full
      page range under a fixed seed -- recording login, user type and a bot-marker match
      alongside each body.
WHY:  Two defects in the first fetch. It took only recent pages, which over-weights whatever
      each project happened to be doing lately, and review content varies sharply by activity
      phase. And it stored no author, so it could not tell that a THIRD of these comments are
      written by other AI review bots -- cubic-dev-ai, ellipsis-dev, cursor, gemini-code-assist
      -- whose templated output matches structural patterns nine times as often as a human's.
      A machine artefact wearing a corpus label is the defect class this project keeps hitting.
IMPORTS: stdlib only (json, random, re, subprocess, sys). Shells out to `gh api`.
CONSUMED BY: `report.py` in this package. Nothing in `src/`.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys

REPOS = [
    "huggingface/transformers",
    "bespokelabsai/curator",
    "langchain-ai/langchain",
    "cartography-cncf/cartography",
    "vllm-project/vllm",
    "browser-use/browser-use",
    "Skyvern-AI/skyvern",
    "apache/airflow",
]
rng = random.Random(20260814)  # SAME seed -> same pages as the uniform draw

# Bots that do not set user.type == "Bot": app comments posted through a user account, and
# machine templates identifiable by their own metadata markers.
BOT_MARK = re.compile(
    r"cubic:v=|cubic:review-run=|coderabbit|sourcery-ai|greptile"
    r"|<!--\s*metadata:\{|codecov|sonarcloud|deepsource",
    re.IGNORECASE,
)


def api(path, hdr=False):
    cmd = ["gh", "api", "-i", path] if hdr else ["gh", "api", path]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError(f"{path}: {p.stderr.strip()[:160]}")
    return p.stdout


def grab(repo, path, scheme, page):
    out = []
    for c in json.loads(api(path)):
        if not str(c.get("path", "")).endswith(".py") or not c.get("body"):
            continue
        u = c.get("user") or {}
        body = c["body"]
        login = str(u.get("login", ""))
        is_bot = (
            u.get("type") == "Bot"
            or login.endswith("[bot]")
            or bool(BOT_MARK.search(body))
            or bool(BOT_MARK.search(login))
        )
        out.append(
            {
                "repo": repo,
                "scheme": scheme,
                "page": page,
                "path": c["path"],
                "body": body,
                "created_at": c.get("created_at", ""),
                "login": login,
                "utype": u.get("type", ""),
                "is_bot": is_bot,
            }
        )
    return out


rows = []
for repo in REPOS:
    try:
        h = api(f"/repos/{repo}/pulls/comments?per_page=100&page=1", hdr=True)
        m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', h)
        lp = int(m.group(1)) if m else 1
        for pg in (1, 2):
            rows += grab(
                repo,
                f"/repos/{repo}/pulls/comments?per_page=100&sort=created&direction=desc&page={pg}",
                "recent",
                pg,
            )
        for pg in sorted(rng.sample(range(1, lp + 1), min(6, lp))):
            rows += grab(
                repo, f"/repos/{repo}/pulls/comments?per_page=100&page={pg}", "uniform", pg
            )
    except RuntimeError as exc:
        print(f"  REFUSING TO REPORT — {exc}")
        sys.exit(1)
    n_r = sum(1 for r in rows if r["repo"] == repo and r["scheme"] == "recent")
    n_u = sum(1 for r in rows if r["repo"] == repo and r["scheme"] == "uniform")
    nb = sum(1 for r in rows if r["repo"] == repo and r["is_bot"])
    print(f"  {repo:32s} recent={n_r:4d} uniform={n_u:4d}  bot={nb:4d}")

with open("review_both.json", "w") as fh:
    json.dump(rows, fh)
print(f"\n  {len(rows)} comments written, with author")
