"""Verification that an assertion naming nothing is caught.

WHAT: Pins `test-vacuous-assert` against every constant form, and pins that a real assertion
      mixing constants with names is NOT caught.
WHY:  **`assert True` PASSED THE GUARD FOR RULE 1.** `_is_weak_assert` classified `Name`,
      `Attribute`, `Call` and `x is not None`; a bare `Constant` fell through every branch and
      scored as a STRONG assertion. So did `assert 1`, `assert "x"`, `assert [1]`,
      `assert not False` and `assert 1 == 1`. Found by feeding the guard the input it was not
      written for, which is the only way this class of hole surfaces.

      **THE FALSE-POSITIVE DIRECTION IS TESTED AS HARD**, because a rule that fires on
      `assert compute() == 1` would be removed within a day and the hole would come back.
IMPORTS: pytest, ast, scripts/guard/check_assert_quality.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "guard"))

from check_assert_quality import _is_vacuous_assert


def _assert_node(source: str) -> ast.Assert:
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.Assert)
    return node


@pytest.mark.parametrize(
    "source",
    [
        "assert True",
        "assert 1",
        'assert "x"',
        "assert [1]",
        "assert (1, 2)",
        "assert not False",
        "assert 1 == 1",
        'assert True, "reason"',
        "assert [1] == [1]",
    ],
)
def test_a_constant_assertion_is_vacuous(source: str) -> None:
    """It is constant-folded before the test runs, so the system cannot affect it."""
    assert _is_vacuous_assert(_assert_node(source)) is True


@pytest.mark.parametrize(
    "source",
    [
        "assert compute() == 1",
        "assert result is True",
        "assert x",
        "assert [x] == [1]",
        "assert len(items) == 3",
        "assert obj.field == 2",
        "assert d['k'] == 1",
    ],
)
def test_an_assertion_naming_something_is_not_vacuous(source: str) -> None:
    """**THE DIRECTION THAT KEEPS THE RULE ALIVE.** A guard that fires on real assertions
    gets deleted, and the hole returns with it."""
    assert _is_vacuous_assert(_assert_node(source)) is False


def test_the_guard_ITSELF_rejects_a_file_of_vacuous_tests(tmp_path) -> None:
    """**THE WIRING, NOT THE PREDICATE.** Disabling the call site left every unit test above
    passing, because they exercise `_is_vacuous_assert` directly. This runs the guard.
    """
    from check_assert_quality import main as guard_main

    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_probe.py").write_text(
        '"""p."""\n\n\ndef test_probe() -> None:\n    assert True\n'
    )
    assert guard_main(["check_assert_quality", str(suite)]) != 0, (
        "the guard accepted a file whose only test is `assert True`"
    )


def test_the_guard_ITSELF_accepts_a_file_of_real_tests(tmp_path) -> None:
    """The other direction, or the rule above could be `return 1` and still pass."""
    from check_assert_quality import main as guard_main

    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_probe.py").write_text(
        '"""p."""\n\n\ndef test_probe() -> None:\n    got = 2 + 2\n    assert got == 4\n'
    )
    assert guard_main(["check_assert_quality", str(suite)]) == 0, (
        "the guard rejected a file of ordinary assertions"
    )
