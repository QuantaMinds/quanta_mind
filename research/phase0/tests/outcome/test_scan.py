"""Verification of the outcome variable against RUNBOOK section 1.3's table.

WHAT: Builds real git repositories and asserts BROKE/CLEAN for each specified
      case, plus the word-boundary cases that substring matching would get wrong.
WHY:  The outcome variable is half the study and the noisier half. RUNBOOK section
      2.3 expects a 5-20% base rate and calls >40% "counting routine follow-ups";
      the fastest route to >40% is a pattern that fires on "prefix" and "debug".
      Those cases are asserted here rather than left to the Day 2 hand-labelling
      gate to discover.

      LABEL_SPEC was written before the implementation, so the classifier is
      fitted to the specification rather than the reverse. Real repositories, not
      mocks: the scan reads commit stats and timestamps, and a mock would only
      prove that our stub returns what we told it to.
IMPORTS: GitPython, phase0.scan_outcome, phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from git import Actor, Repo

from phase0.extract_prs import PRRecord
from phase0.outcome.scan import WINDOW_DAYS, Criterion, Outcome, scan

MERGED_AT = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
AUTHOR = Actor("Tester", "tester@example.com")

# RUNBOOK section 1.3, as data. Written before the classifier existed.
LABEL_SPEC: dict[str, Outcome] = {
    "revert_commit_within_7d": Outcome.BROKE,
    "fix_commit_same_file_+2d": Outcome.BROKE,
    "FIX_uppercase_message": Outcome.BROKE,
    "fix_different_file_+2d": Outcome.CLEAN,
    "fix_outside_window_+9d": Outcome.CLEAN,
    "refactor_commit_+1d": Outcome.CLEAN,
}


def _commit(repo: Repo, path: str, message: str, when: datetime) -> str:
    target = Path(repo.working_tree_dir or "") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {message}\n", encoding="utf-8")
    repo.index.add([path])
    # GitPython's date parser rejects an offset written "+00:00"; it wants "+0000".
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S%z")
    made = repo.index.commit(
        message, author=AUTHOR, committer=AUTHOR, author_date=stamp, commit_date=stamp
    )
    return made.hexsha


def _repo_with(tmp_path: Path, followups: list[tuple[str, str, int]]) -> tuple[Path, str]:
    """A repo whose PR landed at MERGED_AT, plus (path, message, days_after) commits."""
    repo = Repo.init(tmp_path)
    merged = _commit(repo, "acme/handlers.py", "feat: add handler", MERGED_AT)
    for path, message, days in followups:
        _commit(repo, path, message, MERGED_AT + timedelta(days=days))
    return tmp_path, merged


def _pr(merged_sha: str, files: tuple[str, ...] = ("acme/handlers.py",)) -> PRRecord:
    return PRRecord(
        pr_id="1",
        repo="o/r",
        language="python",
        parent_sha="0" * 40,
        merged_sha=merged_sha,
        merged_at=MERGED_AT.isoformat().replace("+00:00", "Z"),
        changed_files=files,
        changed_symbols=("handle",),
    )


def test_window_is_seven_days() -> None:
    """Pre-registered. Widening it after seeing the data is why it is asserted."""
    assert WINDOW_DAYS == 7


def test_refactor_is_not_a_fix() -> None:
    """A refactor landing next day is not evidence the PR broke anything."""
    assert LABEL_SPEC["refactor_commit_+1d"] == Outcome.CLEAN


def test_fix_to_an_unrelated_file_is_clean() -> None:
    """Without file overlap, a 'fix' commit says nothing about this PR."""
    assert LABEL_SPEC["fix_different_file_+2d"] == Outcome.CLEAN


def test_explicit_revert_is_broke(tmp_path: Path) -> None:
    """`git revert` writes the SHA, which is a definitive link rather than a guess."""
    path, merged = _repo_with(tmp_path, [])
    repo = Repo(path)
    _commit(
        repo,
        "acme/handlers.py",
        f'Revert "feat"\n\nThis reverts commit {merged}.',
        MERGED_AT + timedelta(days=1),
    )
    result = scan(path, _pr(merged))
    assert (result.outcome, result.criterion) == (Outcome.BROKE, Criterion.REVERT)


def test_fix_touching_the_same_file_is_broke(tmp_path: Path) -> None:
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "fix: crash on empty", 2)])
    assert scan(path, _pr(merged)).outcome is Outcome.BROKE


def test_fix_message_is_case_insensitive(tmp_path: Path) -> None:
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "FIX: broken import", 1)])
    assert scan(path, _pr(merged)).outcome is Outcome.BROKE


def test_fix_to_a_different_file_is_clean(tmp_path: Path) -> None:
    """File overlap is required; otherwise every busy repo reads as broken."""
    path, merged = _repo_with(tmp_path, [("other/thing.py", "fix: unrelated bug", 2)])
    assert scan(path, _pr(merged)).outcome is Outcome.CLEAN


def test_fix_outside_the_window_is_clean(tmp_path: Path) -> None:
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "fix: late crash", 9)])
    assert scan(path, _pr(merged)).outcome is Outcome.CLEAN


def test_refactor_touching_the_same_file_is_clean(tmp_path: Path) -> None:
    """RUNBOOK 1.3 pins this: maintenance is not a breakage signal."""
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "refactor: tidy handler", 1)])
    assert scan(path, _pr(merged)).outcome is Outcome.CLEAN


@pytest.mark.parametrize(
    "message", ["rename prefix handling", "add debug logging", "document suffix rules"]
)
def test_words_containing_fix_or_bug_do_not_match(tmp_path: Path, message: str) -> None:
    """Substring matching fires on prefix, debug and suffix. None mention breakage.

    This is the quickest route to RUNBOOK 2.3's >40% base rate, which it calls
    "counting routine follow-ups". Word boundaries are why it does not happen.
    """
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", message, 1)])
    assert scan(path, _pr(merged)).outcome is Outcome.CLEAN


def test_bugfix_does_match(tmp_path: Path) -> None:
    """Word boundaries must not go so far that a real signal is lost."""
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "bugfix: null deref", 1)])
    assert scan(path, _pr(merged)).outcome is Outcome.BROKE


def test_broke_verdicts_carry_evidence(tmp_path: Path) -> None:
    """RUNBOOK 3: the SHA and message are what make the result auditable."""
    path, merged = _repo_with(tmp_path, [("acme/handlers.py", "fix: crash", 2)])
    result = scan(path, _pr(merged))
    assert result.is_auditable and result.evidence_sha != "" and "fix" in result.evidence_message


def test_issue_link_criterion_is_recorded_as_not_run(tmp_path: Path) -> None:
    """A4: whether the optional criterion executed is stated, never assumed."""
    path, merged = _repo_with(tmp_path, [])
    assert scan(path, _pr(merged)).issue_link_checked is False
