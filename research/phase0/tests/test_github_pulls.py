"""Verification of the merge-metadata client — amendment A2's prerequisite.

WHAT: Asserts that a missing token fails loudly and namefully, that the cache is
      honoured without any network call, and that AIDev's API URLs parse.
WHY:  A2 makes a GitHub token a prerequisite of the study rather than an
      implementation detail. The failure mode this guards against is subtle:
      unauthenticated requests are capped at 60/hour rather than refused, so a
      client that silently fell back would produce a run that looked like it
      worked while dropping most of the corpus.

      The cache is not an optimisation. RUNBOOK section 5 requires the study
      reproduce from raw data on another machine, and an uncached client would
      cost another full pass of quota and return different data as repositories
      change under it.
IMPORTS: phase0.github_pulls, pytest, monkeypatch.
CONSUMED BY: `just test-phase0`. No network: every test reads a seeded cache.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase0.github_pulls import (
    TOKEN_VAR,
    MissingTokenError,
    merge_info,
    repo_full_name,
    require_token,
)


def _seed(cache_dir: Path, pr_id: str, payload: dict[str, object]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"pr-{pr_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_missing_token_fails_loudly_naming_the_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never fall back to unauthenticated: 60/hour looks like a working run."""
    monkeypatch.delenv(TOKEN_VAR, raising=False)
    with pytest.raises(MissingTokenError, match="public_repo"):
        require_token()


def test_token_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read from the environment, never from a file the repository could commit."""
    monkeypatch.setenv(TOKEN_VAR, "  ghp_example  ")
    assert require_token() == "ghp_example"


def test_api_url_becomes_owner_and_name() -> None:
    """AIDev stores the API URL, not the owner/name pair the API path needs."""
    assert repo_full_name("https://api.github.com/repos/milvus-io/pymilvus") == "milvus-io/pymilvus"


def test_plain_owner_name_is_left_alone() -> None:
    assert repo_full_name("milvus-io/pymilvus") == "milvus-io/pymilvus"


def test_cached_response_needs_no_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A re-run must cost no quota. If the cache is honoured, no token is required."""
    monkeypatch.delenv(TOKEN_VAR, raising=False)
    _seed(
        tmp_path,
        "42",
        {
            "merged_at": "2026-03-01T12:00:00Z",
            "merge_commit_sha": "abc123",
            "base": {"ref": "main"},
            "commits": 3,
        },
    )
    info = merge_info("o/r", 7, "42", tmp_path)
    assert info is not None
    assert (info.merge_commit_sha, info.commit_count) == ("abc123", 3)


def test_unmerged_pr_is_not_usable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No merge means no 7-day window, so the PR cannot be classified at all."""
    monkeypatch.delenv(TOKEN_VAR, raising=False)
    _seed(tmp_path, "43", {"merged_at": None, "merge_commit_sha": None, "commits": 2})
    info = merge_info("o/r", 8, "43", tmp_path)
    assert info is not None
    assert info.is_usable is False


def test_deleted_repository_is_attrition_not_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gone repository yields no metadata, and must not raise.

    The 2025-08 snapshot ages: repositories are deleted, renamed and made private.
    RUNBOOK §3 expects 80-95% clone success, so this is the common path, and a
    raise here would end a 3,300-PR run on the first casualty.
    """
    monkeypatch.delenv(TOKEN_VAR, raising=False)
    _seed(tmp_path, "44", {})
    _seed(tmp_path, "45b", {"merged_at": "2026-01-01T00:00:00Z", "merge_commit_sha": "x"})
    results = {
        "deleted": merge_info("o/r", 9, "44", tmp_path),
        "present": merge_info("o/r", 11, "45b", tmp_path),
    }
    assert [k for k, v in results.items() if v is None] == ["deleted"]


def test_commit_count_comes_from_the_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A2's rebase walk is bounded by this, so it must not be inferred locally."""
    monkeypatch.delenv(TOKEN_VAR, raising=False)
    _seed(
        tmp_path, "45", {"merged_at": "2026-01-01T00:00:00Z", "merge_commit_sha": "d", "commits": 5}
    )
    info = merge_info("o/r", 10, "45", tmp_path)
    assert info is not None and info.commit_count == 5
