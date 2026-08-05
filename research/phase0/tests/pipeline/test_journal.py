"""Verification that a killed run resumes instead of starting over.

WHAT: Pins the round trip, the done-marker, and the two failure modes that make a
      journal worse than none — losing a finished repository, and re-doing it forever.
WHY:  The full run is over thirty hours. A journal that silently loses rows costs the
      run twice; one that marks a repository done before its rows are on disk loses them
      permanently and reports a complete result. Both are silent, so both are pinned.
IMPORTS: phase0.pipeline.journal, phase0.pilot.report.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.pilot.attempt import Attempt
from phase0.pipeline.journal import COLUMNS, append_repo, completed_repos, read_attempts


def _attempt(repo: str, pr_id: str, admitted: bool = True, stage: str = "") -> Attempt:
    return Attempt(
        pr_id=pr_id,
        repo=repo,
        admitted=admitted,
        stage=stage,
        category="integrity" if stage else "",
        commit_count=3,
        corpus_py_files=4,
        derived_files=4 if admitted else 0,
        changed_symbols=2 if admitted else 0,
        stars=1200,
    )


def test_rows_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "journal.md"
    rows = [_attempt("a/b", "1"), _attempt("a/b", "2", admitted=False, stage="parent_commit")]
    append_repo(path, "a/b", rows)
    assert read_attempts(path) == rows


def test_a_repository_with_no_rows_is_still_marked_done(tmp_path: Path) -> None:
    """Otherwise a clone failure is retried on every restart, forever."""
    path = tmp_path / "journal.md"
    append_repo(path, "a/empty", [])
    assert completed_repos(path) == {"a/empty"}
    assert read_attempts(path) == []


def test_appending_accumulates_across_repositories(tmp_path: Path) -> None:
    path = tmp_path / "journal.md"
    append_repo(path, "a/b", [_attempt("a/b", "1")])
    append_repo(path, "c/d", [_attempt("c/d", "2")])
    assert completed_repos(path) == {"a/b", "c/d"}
    assert [a.pr_id for a in read_attempts(path)] == ["1", "2"]


def test_a_torn_final_row_is_dropped_and_its_repo_is_not_done(tmp_path: Path) -> None:
    """A kill mid-write must lose the repository, not half of it.

    The marker is written after the rows, so a truncated flush leaves the repository
    unmarked and the restart redoes it. Redoing work is the acceptable failure here;
    reporting a repository as complete on partial rows is not.
    """
    path = tmp_path / "journal.md"
    append_repo(path, "a/b", [_attempt("a/b", "1")])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("| c/d | 2 | yes | - | - | 3 | 4 | 4 |")  # short row, no newline

    assert completed_repos(path) == {"a/b"}
    assert [a.pr_id for a in read_attempts(path)] == ["1"]


def test_the_header_is_written_once(tmp_path: Path) -> None:
    path = tmp_path / "journal.md"
    append_repo(path, "a/b", [_attempt("a/b", "1")])
    append_repo(path, "c/d", [_attempt("c/d", "2")])
    assert path.read_text(encoding="utf-8").count("# Pilot journal") == 1


def test_missing_journal_is_an_empty_resume_not_an_error(tmp_path: Path) -> None:
    absent = tmp_path / "nope.md"
    assert completed_repos(absent) == set()
    assert read_attempts(absent) == []


def test_a_journal_from_an_older_schema_still_reads(tmp_path: Path) -> None:
    """Columns are only ever appended, so a short row is an older run, not a corrupt one.

    Without this the only pre-fix baseline is an aggregate, and an aggregate cannot say
    whether failures were FIXED or merely moved to a different stage — the question any
    large drop in one rejection stage raises, and one this pipeline has already answered
    wrongly once by watching a single gate.
    """
    older = tmp_path / "old.md"
    older.write_text(
        "| repo | pr_id | admitted | stage | category | commits | corpus_py | derived "
        "| symbols | stars | outcome |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| o/r | 7 | no | parent_commit | integrity | 3 | 9 | 0 | 0 | 100 | - |\n",
        encoding="utf-8",
    )

    attempts = read_attempts(older)

    assert len(attempts) == 1
    assert (attempts[0].stage, attempts[0].commit_count) == ("parent_commit", 3)
    # The columns that did not exist read as NOT MEASURED, never as a measurement.
    assert attempts[0].merge_on_base == "unknown"
    assert attempts[0].changed_lines == -1


def test_a_row_from_a_newer_schema_is_refused(tmp_path: Path) -> None:
    """A longer row comes from a schema this code does not know; guessing invents data."""
    newer = tmp_path / "new.md"
    columns = "| " + " | ".join(COLUMNS) + " | extra |\n"
    # Sized against COLUMNS rather than written out. A literal row froze the width at
    # fourteen, so appending a fifteenth column made this row exactly the CURRENT schema
    # and the test started asserting that a valid row parses -- passing while testing
    # nothing. The row must be one wider than whatever the schema is today.
    cells = ["o/r", "8", "yes", "-", "-", "1", "1", "1", "1", "1", "clean", "yes", "yes", "10"]
    cells += ["???"] * (len(COLUMNS) + 1 - len(cells))
    newer.write_text(
        columns
        + "|"
        + "|".join("---" for _ in range(len(COLUMNS) + 1))
        + "|\n"
        + "| "
        + " | ".join(cells)
        + " |\n",
        encoding="utf-8",
    )

    assert len(cells) == len(COLUMNS) + 1
    assert read_attempts(newer) == []
