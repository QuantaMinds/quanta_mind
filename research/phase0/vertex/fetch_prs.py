"""Fetch real merged pull requests, with their diffs and the full text of the changed files.

WHAT: Pulls merged PRs touching Python from the corpus repositories, and for each one records
      the unified patch per changed .py file plus the FULL post-merge text of those files.
WHY:  The cost model in `docs/product/QUANTAMIND.md` was priced from token arithmetic, never
      billed. Measuring it needs the real production input shape: a diff, plus the complete
      source of the units the allocator funds -- the product reads whole functions, not hunks,
      so a patch-only estimate understates the prompt.
IMPORTS: stdlib only (base64, json, subprocess, sys, time). Shells out to `gh api`.
CONSUMED BY: `cost.py` in this package. Nothing in `src/`.
"""

from __future__ import annotations

import json
import subprocess
import sys

REPOS = [
    "huggingface/transformers",
    "langchain-ai/langchain",
    "cartography-cncf/cartography",
    "vllm-project/vllm",
    "apache/airflow",
    "Skyvern-AI/skyvern",
]
PER_REPO = 4
MAX_PY_FILES = 12


def gh(path: str) -> object:
    p = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        raise RuntimeError(f"{path}: {p.stderr.strip()[:160]}")
    return json.loads(p.stdout)


def blob(repo: str, sha: str, path: str) -> str:
    """Full file text at a commit. Returns '' when the file is gone or is not text."""
    import base64

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
    out = []
    for repo in REPOS:
        try:
            prs = gh(f"/repos/{repo}/pulls?state=closed&per_page=40&sort=updated&direction=desc")
        except RuntimeError as exc:
            print(f"  REFUSING TO REPORT — {exc}")
            return 1
        taken = 0
        for pr in prs:
            if taken >= PER_REPO or not pr.get("merged_at"):
                continue
            num, sha = pr["number"], pr["merge_commit_sha"]
            try:
                files = gh(f"/repos/{repo}/pulls/{num}/files?per_page=100")
            except RuntimeError:
                continue
            py = [f for f in files if str(f["filename"]).endswith(".py") and f.get("patch")]
            if not (2 <= len(py) <= MAX_PY_FILES):
                continue
            rec = {"repo": repo, "number": num, "title": pr["title"], "sha": sha, "files": []}
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
            taken += 1
            print(
                f"  {repo:30s} #{num:<7} {len(py):2d} py files  "
                f"{sum(len(x['source']) for x in rec['files']):7d} src chars"
            )
    with open("pr_corpus.json", "w") as fh:
        json.dump(out, fh)
    print(f"\n  {len(out)} pull requests written to pr_corpus.json")
    return 0


sys.exit(main())
