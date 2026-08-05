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
from dataclasses import dataclass
from pathlib import Path

from phase0.github_http import TOKEN_VAR, MissingTokenError, fetch, require_token

API_ROOT = "https://api.github.com"

# Re-exported so callers keep one import for "talking to GitHub about a PR". The
# transport lives in github_http.py; this module is the queries.
__all__ = ["MergeInfo", "MissingTokenError", "merge_info", "repo_full_name", "require_token"]


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
    # Subjects of the PR's own commits, from the API -- the authoritative list. Shape
    # detection previously compared FILE sets taken from the corpus, and the corpus
    # attributes 92 files to some three-file PRs, so the comparison failed on exactly
    # the PRs whose file lists were wrong. Empty when the endpoint was unavailable, in
    # which case the file-based rule still applies.
    commit_subjects: tuple[str, ...] = ()
    # The PR's own file list, from /pulls/{n}/files. This is what the parent must be
    # verified against: the corpus attributes 92 files to some three-file PRs, so a gate
    # built on the corpus list checked the wrong thing. Empty when unavailable.
    api_files: tuple[str, ...] = ()

    @property
    def is_usable(self) -> bool:
        """Unmerged PRs have no post-merge window and are excluded, not classified."""
        return self.merged and bool(self.merge_commit_sha)


def _cache_path(cache_dir: Path, pr_id: str) -> Path:
    return cache_dir / f"pr-{pr_id}.json"


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
        payload = fetch(
            f"{API_ROOT}/repos/{repo_full_name}/pulls/{number}", token or require_token()
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

    if not payload:
        return None

    subjects = _commit_subjects(repo_full_name, number, pr_id, cache_dir, token)
    files = _api_files(repo_full_name, number, pr_id, cache_dir, token)

    return MergeInfo(
        pr_id=pr_id,
        number=number,
        merged=bool(payload.get("merged_at")),
        merge_commit_sha=str(payload.get("merge_commit_sha") or ""),
        merged_at=str(payload.get("merged_at") or ""),
        base_ref=str((payload.get("base") or {}).get("ref") or ""),
        commit_count=int(payload.get("commits") or 0),
        commit_subjects=subjects,
        api_files=files,
    )


def _api_files(
    repo_full_name: str, number: int, pr_id: str, cache_dir: Path, token: str | None
) -> tuple[str, ...]:
    """The PR's changed files, straight from GitHub. Capped at the first 300.

    Empty when unavailable, which makes the caller fall back to the corpus list rather
    than treat "we could not ask" as "the PR changed nothing".
    """
    path = _cache_path(cache_dir, f"{pr_id}-files")
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif not (token or os.environ.get(TOKEN_VAR, "").strip()):
        # Enrichment, not the primary payload. Without a token this returns empty and
        # the caller falls back, rather than raising and turning a cached merge lookup
        # into a hard failure.
        return ()
    else:
        payload = fetch(
            f"{API_ROOT}/repos/{repo_full_name}/pulls/{number}/files?per_page=100",
            token or require_token(),
        )
        path.write_text(json.dumps(payload), encoding="utf-8")
    if not isinstance(payload, list):
        return ()
    return tuple(str(entry.get("filename") or "") for entry in payload if entry.get("filename"))


def _commit_subjects(
    repo_full_name: str, number: int, pr_id: str, cache_dir: Path, token: str | None
) -> tuple[str, ...]:
    """First lines of the PR's own commits, cached alongside the merge metadata.

    Returns empty rather than raising when the endpoint is unavailable: a missing list
    means the file-based shape rule applies, which is the behaviour that existed before.
    An empty tuple and a one-commit PR are distinguishable because `commit_count` is
    fetched separately.
    """
    path = _cache_path(cache_dir, f"{pr_id}-commits")
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif not (token or os.environ.get(TOKEN_VAR, "").strip()):
        # Enrichment, not the primary payload. Without a token this returns empty and
        # the caller falls back, rather than raising and turning a cached merge lookup
        # into a hard failure.
        return ()
    else:
        payload = fetch(
            f"{API_ROOT}/repos/{repo_full_name}/pulls/{number}/commits?per_page=100",
            token or require_token(),
        )
        path.write_text(json.dumps(payload), encoding="utf-8")
    if not isinstance(payload, list):
        return ()
    return tuple(
        str((entry.get("commit") or {}).get("message") or "").splitlines()[0]
        for entry in payload
        if (entry.get("commit") or {}).get("message")
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
