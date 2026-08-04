"""Merge metadata from the GitHub API, cached, because AIDev does not carry it.

WHAT: Fetches `merge_commit_sha`, `merged_at` and the merge shape for one PR, and
      caches every response to disk.
WHY:  Amendment A2. AIDev's `pull_request` table has no base, head or merge SHA,
      and `pr_commits` has no parent and no ordering field, so the PR's first
      commit cannot even be identified from it. The parent commit is the entire
      basis of the exposure variable, so a GitHub token is a prerequisite of this
      study rather than an implementation detail.

      Responses are cached keyed by PR id. RUNBOOK section 5 requires the whole
      study be reproducible from raw data on another machine, and an uncached
      client would make a re-run cost another full pass of quota and return
      different data as repositories change under it.

      The token is read from the environment and never written anywhere. A missing
      token fails loudly, naming the scope, rather than proceeding with
      unauthenticated requests -- 60/hour would look like a working run that
      silently drops most of the corpus.
IMPORTS: stdlib json, os, time, urllib. No third-party HTTP client: one endpoint,
      one header, and a dependency here would be a dependency in the reproduction.
CONSUMED BY: extract_prs.py; tests/test_github_pulls.py.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
TOKEN_VAR = "GITHUB_TOKEN"
TIMEOUT_S = 30

# 5,000/hour authenticated. Pause and retry rather than losing the run.
RATE_LIMIT_PAUSE_S = 60
MAX_RETRIES = 3


class MissingTokenError(RuntimeError):
    """Raised when no token is present. Never fall back to unauthenticated."""


@dataclass(frozen=True, slots=True)
class MergeInfo:
    """What A2 needs to resolve the parent commit."""

    pr_id: str
    number: int
    merged: bool
    merge_commit_sha: str
    merged_at: str
    base_ref: str
    commit_count: int  # from the API, so squash and rebase can be told apart

    @property
    def is_usable(self) -> bool:
        """Unmerged PRs have no post-merge window and are excluded, not classified."""
        return self.merged and bool(self.merge_commit_sha)


def require_token() -> str:
    """The token, or a loud failure naming the scope it needs."""
    token = os.environ.get(TOKEN_VAR, "").strip()
    if not token:
        raise MissingTokenError(
            f"{TOKEN_VAR} is not set. The correlation test needs a GitHub token with the "
            f"`public_repo` scope to resolve each PR's parent commit -- AIDev does not "
            f"carry it (PHASE0_PREREGISTRATION.md amendment A2). Unauthenticated "
            f"requests are capped at 60/hour, which would look like a working run while "
            f"silently dropping most of the corpus."
        )
    return token


def _cache_path(cache_dir: Path, pr_id: str) -> Path:
    return cache_dir / f"pr-{pr_id}.json"


def _fetch(url: str, token: str) -> dict[str, Any]:
    """One GET, with a bounded retry on rate limiting."""
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "qmctx-phase0",
        },
    )
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return dict(payload) if isinstance(payload, dict) else {}
        except urllib.error.HTTPError as error:
            if error.code in (403, 429) and attempt < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_PAUSE_S)
                continue
            if error.code == 404:
                return {}  # repository deleted or made private: corpus attrition
            raise
    return {}


def merge_info(
    repo_full_name: str,
    number: int,
    pr_id: str,
    cache_dir: Path,
    token: str | None = None,
) -> MergeInfo | None:
    """Merge metadata for one PR, from cache when present.

    Returns None when the PR or repository is gone. That is corpus attrition and
    extract_prs.py counts it; it is not an error and must not stop the run.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, pr_id)

    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = _fetch(
            f"{API_ROOT}/repos/{repo_full_name}/pulls/{number}", token or require_token()
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

    if not payload:
        return None

    return MergeInfo(
        pr_id=pr_id,
        number=number,
        merged=bool(payload.get("merged_at")),
        merge_commit_sha=str(payload.get("merge_commit_sha") or ""),
        merged_at=str(payload.get("merged_at") or ""),
        base_ref=str((payload.get("base") or {}).get("ref") or ""),
        commit_count=int(payload.get("commits") or 0),
    )


def repo_full_name(repo_url: str) -> str:
    """`https://api.github.com/repos/milvus-io/pymilvus` -> `milvus-io/pymilvus`.

    AIDev stores the API URL rather than the owner/name pair, so this is the only
    place the two representations meet.
    """
    marker = "/repos/"
    if marker in repo_url:
        return repo_url.split(marker, 1)[1].strip("/")
    return repo_url.strip("/")
