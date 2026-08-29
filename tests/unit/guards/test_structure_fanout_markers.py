"""Verification that plumbing files do not consume the directory fan-out budget.

WHAT: Pins the fan-out cap at its boundary — fifteen real modules pass, sixteen fail, and
      neither `__init__.py` nor `py.typed` shifts that boundary in either direction.
WHY:  **`py.typed` WAS CHARGED AGAINST THE CAP.** It is a zero-byte PEP 561 marker whose only
      job is to make type checkers read the package. Three packages here sit at exactly 15,
      so adding the marker to one of them would have failed the build with a fan-out
      violation raised by a file that has no contents — a cap that counts a thing no reader
      has to understand is measuring the wrong population. Found by running the guard against
      `requests`, whose `src/requests` holds the marker, and reconciling its count of 19
      against a hand count of 18.

      **THE BOUNDARY IS TESTED FROM BOTH SIDES**, because an exemption that silently
      widened the cap to 17 would look identical to this fix on every green run.

      **AND THE CAPS ARE PINNED TO THE NUMBERS AGENTS.md STATES.** Every other test here is
      written in terms of `MAX_DIR_FILES`, so all six passed unchanged when the constant was
      sabotaged from 15 to 16 — a test that reads the value it is checking cannot detect a
      change to it. `test_caps_match_the_documented_rules` reads the rules instead, so
      raising a cap in the guard now fails until the rule it enforces is raised too.
IMPORTS: pytest, scripts/guard/check_structure.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard"))

from check_structure import (
    FANOUT_EXEMPT_NAMES,
    MAX_DIR_FILES,
    MAX_FILE_LINES,
    check_dir_fanout,
)


def _package(root: Path, modules: int, *, markers: bool) -> Path:
    """A package holding `modules` real modules, optionally with both plumbing files."""
    pkg = root / "pkg"
    pkg.mkdir()
    for n in range(modules):
        (pkg / f"mod_{n:02d}.py").write_text("x = 1\n")
    if markers:
        (pkg / "__init__.py").write_text("")
        (pkg / "py.typed").write_text("")
    return pkg


@pytest.mark.parametrize("markers", [False, True])
def test_at_the_cap_passes(tmp_path: Path, markers: bool) -> None:
    """Fifteen real modules is legal, and stays legal when the plumbing is added."""
    _package(tmp_path, MAX_DIR_FILES, markers=markers)

    assert check_dir_fanout(tmp_path) == []


@pytest.mark.parametrize("markers", [False, True])
def test_one_over_the_cap_fails(tmp_path: Path, markers: bool) -> None:
    """Sixteen real modules is a violation, and the plumbing does not buy it a reprieve."""
    _package(tmp_path, MAX_DIR_FILES + 1, markers=markers)

    violations = check_dir_fanout(tmp_path)

    assert [v.rule for v in violations] == ["dir-fanout"]
    assert f"{MAX_DIR_FILES + 1} files" in violations[0].detail


def test_markers_alone_are_never_counted(tmp_path: Path) -> None:
    """A package of nothing but plumbing reports zero files, not two."""
    _package(tmp_path, 0, markers=True)

    assert check_dir_fanout(tmp_path) == []


def test_the_marker_does_not_widen_the_cap(tmp_path: Path) -> None:
    """The exemption removes exactly one file from the count, not the cap's meaning.

    Sixteen real modules plus both markers must still name sixteen. An exemption
    implemented as `cap + 1` would pass every other test in this file.
    """
    _package(tmp_path, MAX_DIR_FILES + 1, markers=True)

    detail = check_dir_fanout(tmp_path)[0].detail

    assert f"{MAX_DIR_FILES + 1} files, cap is {MAX_DIR_FILES}" in detail


def test_caps_match_the_documented_rules() -> None:
    """The guard enforces the numbers rule 4 and rule 5 state, not numbers of its own.

    Sabotaging `MAX_DIR_FILES` from 15 to 16 left every other test in this file green,
    because they are all phrased in terms of the constant. This one is phrased in terms of
    AGENTS.md, which is where the cap is promised to a reader.
    """
    rules = (Path(__file__).resolve().parents[3] / "AGENTS.md").read_text()

    file_cap = re.search(r"\*\*≤(\d+) lines per source file\*\*", rules)
    dir_cap = re.search(r"\*\*≤(\d+) files per directory\*\*", rules)

    assert file_cap is not None, "rule 4 no longer states a line cap"
    assert dir_cap is not None, "rule 5 no longer states a file cap"
    assert int(file_cap.group(1)) == MAX_FILE_LINES, "check_structure and rule 4 disagree"
    assert int(dir_cap.group(1)) == MAX_DIR_FILES, "check_structure and rule 5 disagree"


def test_the_exemption_is_documented_in_the_rule() -> None:
    """Rule 5 names every file the guard exempts, so the promise matches the mechanism."""
    rules = (Path(__file__).resolve().parents[3] / "AGENTS.md").read_text()
    stated = rules.split("**≤15 files per directory**", 1)[1].split("\n", 1)[0]

    for exempt in FANOUT_EXEMPT_NAMES:
        assert exempt in stated, f"the guard exempts {exempt} and rule 5 does not say so"
