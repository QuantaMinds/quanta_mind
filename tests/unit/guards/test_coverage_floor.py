"""Verification that a guard cannot report success having examined nothing.

WHAT: Pins `assert_examined` at its boundaries, and that a floor is waived only for a root that
      is not this repository — audibly, never in silence.
WHY:  An audit of all 24 guards found five reporting a coverage count and exiting 0 when it was
      zero: 590 paragraphs, 82 documented invocations, 35 subprocess call sites among them. Each
      would have printed success the day a moved directory or a narrowed glob broke discovery.
      That is `AGENTS.md` rule 14 — a filter admitting NOTHING must raise — turned on the filters.

      **THE WAIVER IS TESTED AS HARD AS THE FLOOR.** Scoping the floor to the project root is
      itself a way for a check to stop applying, so the test asserts it announces the waiver
      rather than passing quietly.
IMPORTS: pytest, scripts/guard/coverage.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard"))

from coverage import NothingExamined, assert_examined, is_project

ROOT = Path(__file__).resolve().parents[3]


def test_a_count_above_the_floor_is_returned() -> None:
    assert assert_examined("things", 35, 10, ROOT) == 35


def test_a_count_exactly_at_the_floor_passes() -> None:
    """The floor is a minimum, not a strict inequality; off-by-one here fails a healthy repo."""
    assert assert_examined("things", 10, 10, ROOT) == 10


def test_zero_raises_and_names_what_was_being_looked_for() -> None:
    """**THE DEFECT.** Zero examined is a broken instrument, not a clean run."""
    with pytest.raises(NothingExamined) as caught:
        assert_examined("subprocess call sites", 0, 10, ROOT)
    message = str(caught.value)
    assert "subprocess call sites" in message, message
    assert "examined 0" in message and "at least 10" in message, message


def test_one_short_of_the_floor_raises() -> None:
    with pytest.raises(NothingExamined):
        assert_examined("things", 9, 10, ROOT)


def test_this_repository_is_recognised_as_the_project() -> None:
    """If this were false the floor would apply nowhere and every guard would waive it."""
    present = {marker: (ROOT / marker).exists() for marker in ("AGENTS.md", "justfile")}
    assert present == {"AGENTS.md": True, "justfile": True}, present
    assert is_project(ROOT) is True


def test_a_fixture_root_is_not_the_project(tmp_path) -> None:
    assert is_project(tmp_path) is False


def test_a_waived_floor_says_so_rather_than_passing_quietly(tmp_path, capsys) -> None:
    """A check that stops applying without saying so is the shape being fixed, not a fix."""
    assert assert_examined("things", 0, 10, tmp_path) == 0
    out = capsys.readouterr().out
    assert "floor for things not applied" in out, out
    assert str(tmp_path) in out, out


def test_a_root_missing_one_marker_is_not_the_project(tmp_path) -> None:
    """Both markers are required, so half a repository does not switch the floor back on."""
    (tmp_path / "AGENTS.md").write_text("x")
    assert is_project(tmp_path) is False, "one marker must not be enough"


def test_a_subdirectory_of_the_project_still_counts_as_the_project() -> None:
    """**THE HOLE THE FIRST VERSION HAD.** Several guards are rooted at a subdirectory —
    `check_assert_quality` at `tests/`. Testing the markers IN the root meant those guards never
    saw them and had the floor waived on every run: the check silently not applying, which is
    the defect this module exists to stop, reintroduced by its own guard clause.
    """
    assert is_project(ROOT / "tests") is True
    assert is_project(ROOT / "src" / "quantamind" / "serve") is True


def test_a_temp_tree_outside_the_project_is_still_not_the_project(tmp_path) -> None:
    """Walking up must not walk all the way to `/` and find some unrelated repository."""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert is_project(deep) is False


def test_a_repository_cloned_inside_the_project_is_not_the_project(tmp_path) -> None:
    """**FOUND BY RUNNING THE GUARDS AGAINST FOUR EXTERNAL REPOSITORIES.**

    `.verify-clone` holds pallets/flask and lives inside this working tree. The upward walk
    found the project's own `AGENTS.md` above it and applied the floor, so a guard pointed at a
    foreign repository reported a coverage breach for a tree with nothing to do with us — while
    the same four repositories cloned OUTSIDE correctly waived. The walk now stops at the first
    `.git`, which is the enclosing repository.
    """
    outer = tmp_path / "project"
    (outer / ".git").mkdir(parents=True)
    (outer / "AGENTS.md").write_text("x")
    (outer / "justfile").write_text("x")
    assert is_project(outer) is True

    inner = outer / "vendored-clone"
    (inner / ".git").mkdir(parents=True)
    (inner / "src").mkdir()
    assert is_project(inner) is False, "a nested clone counted as the project"
    assert is_project(inner / "src") is False, "a directory inside a nested clone counted too"


def test_a_subdirectory_with_no_git_of_its_own_still_counts() -> None:
    """The ordinary case must survive the stop-at-git rule: `tests/` has no `.git`."""
    assert is_project(ROOT / "tests") is True
