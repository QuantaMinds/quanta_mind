"""Verification that a guard which cannot honour a path argument refuses it.

WHAT: Pins `discovery.refuse_path_argument`, and drives one real guard end to end to prove the
      refusal reaches the exit code rather than living only in the helper.
WHY:  **TEN GUARDS RESOLVED THEIR SUBJECT FROM THE WORKING DIRECTORY AND DISCARDED `argv[1]`.**
      Running `check_schema_shape.py /some/other/repo` reported `[schema-shape] ok` — about THIS
      repository, which it had read instead. A pass with the wrong provenance and nothing in the
      output to reveal it, which is the failure this project treats as most serious.

      **THE REFUSAL IS AT THE ENTRY POINT, NOT INSIDE `main()`.** The first attempt put it in
      `main()`, where `sys.argv` belongs to whoever imported the module: under pytest that is
      pytest's own command line, so every guard refused every programmatic caller and nine tests
      failed at once. `main(...)` stays callable; `__main__` is where an argv is genuinely this
      guard's own.
IMPORTS: pytest, subprocess, scripts/guard/coverage.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from coverage import refuse_path_argument  # noqa: E402

REFUSED = 2


def test_no_argument_is_not_refused(capsys: pytest.CaptureFixture[str]) -> None:
    """The ordinary invocation passes through and says nothing at all."""
    result = refuse_path_argument(["check_schema_shape.py"], "schema-shape")

    assert result is None
    assert capsys.readouterr().err == "", "a guard invoked correctly complained anyway"


def test_a_path_argument_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    """The refusal names the guard and the path it will not read."""
    result = refuse_path_argument(["check_schema_shape.py", "/tmp/pydantic"], "schema-shape")
    printed = capsys.readouterr().err

    assert result == REFUSED
    assert "schema-shape" in printed
    assert "pydantic" in printed, "the refusal does not say which path it declined"


def test_the_refusal_reaches_the_exit_code(tmp_path: Path) -> None:
    """End to end: a real guard given a path exits 2 rather than reporting on this repository.

    Asserting on the guard's own output, not on the helper — the helper returning 2 into a
    value nobody uses would pass the tests above and change nothing.
    """
    guard = ROOT / "scripts" / "guard" / "records" / "check_schema_shape.py"

    given = subprocess.run(
        [sys.executable, str(guard), str(tmp_path)], capture_output=True, text=True, timeout=120
    )

    assert given.returncode == REFUSED, f"guard answered anyway: {given.stdout.strip()[:120]}"
    assert "ok" not in given.stdout, "the guard reported a verdict about a tree it did not read"


def test_the_same_guard_still_works_with_no_argument() -> None:
    """The false-positive direction: refusing everything would be its own defect."""
    guard = ROOT / "scripts" / "guard" / "records" / "check_schema_shape.py"

    plain = subprocess.run(
        [sys.executable, str(guard)], capture_output=True, text=True, timeout=120, cwd=ROOT
    )

    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert "SCHEMA_VERSION" in plain.stdout, "the guard stopped reporting what it read"
