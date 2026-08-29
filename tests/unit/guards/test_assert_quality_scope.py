"""Verification that the assert-quality guard scans this repository and not its dependencies.

WHAT: Pins that `main` enumerates test modules through `discovery.walk`, so an excluded
      directory holding test files is never judged, and that the coverage floor counts the
      same population the scan does.
WHY:  **THE GUARD USED `root.rglob("test_*.py")`, WHICH DESCENDS INTO `.venv`.** Pointed at
      the repository root it returned 28,009 violations, every one of them inside mypy,
      werkzeug or flask. `just check` passes `tests`, so the gate never showed it, and the
      guard's own docstring said it imported `discovery` -- it did, for `report`, never for
      `walk`.

      **THE FLOOR COUNTED THROUGH THE SAME UNFILTERED GLOB.** A root containing `.venv`
      inflated the module count into the thousands, so `assert_examined` would have passed
      on a population that was almost entirely somebody else's code. Scan and floor now read
      one list, because two enumerations of one population drift.
IMPORTS: pytest, scripts/guard/check_assert_quality.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard"))

import check_assert_quality

VACUOUS = "def test_planted():\n    assert True\n"
REAL = "from mod import double\n\n\ndef test_real_{n}():\n    assert double({n}) == {d}\n"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A root holding real tests, one planted violation, and a violation inside `.venv`."""
    (tmp_path / "tests").mkdir()
    (tmp_path / ".venv" / "tests").mkdir(parents=True)
    for n in range(1, 26):
        (tmp_path / "tests" / f"test_ok_{n}.py").write_text(REAL.format(n=n, d=n * 2))
    (tmp_path / "tests" / "test_planted.py").write_text(VACUOUS)
    (tmp_path / ".venv" / "tests" / "test_foreign.py").write_text(VACUOUS)
    return tmp_path


def test_venv_is_not_scanned(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The planted violation is named; the identical one under `.venv` is not."""
    check_assert_quality.main(["check_assert_quality", str(tree)])
    printed = capsys.readouterr().out

    assert "test_planted.py" in printed, "the guard stopped catching a vacuous assert"
    assert "test_foreign.py" not in printed, "the guard descended into .venv again"


def test_real_assertions_are_not_flagged(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Twenty-five assertions naming a call are left alone. The false-positive direction."""
    check_assert_quality.main(["check_assert_quality", str(tree)])

    assert "test_ok_" not in capsys.readouterr().out


def test_floor_counts_the_scanned_population(tree: Path) -> None:
    """The floor's count excludes `.venv`, so it cannot be met by a dependency's tests."""
    counted: list[int] = []
    original = check_assert_quality.assert_examined
    check_assert_quality.assert_examined = (  # type: ignore[assignment]
        lambda what, n, floor, root: counted.append(n)
    )
    try:
        check_assert_quality.main(["check_assert_quality", str(tree)])
    finally:
        check_assert_quality.assert_examined = original  # type: ignore[assignment]

    assert counted == [26], f"floor counted {counted}, so it is not reading the scanned list"
