"""External lookups fail in two different ways, and the difference is the point.

WHAT: That a missing `repository.parquet` degrades to an empty mapping, and that a
      missing `gh` binary raises instead of returning "".
WHY:  `default_branch`'s docstring promised "empty when the lookup fails" while
      `subprocess.run` raised `FileNotFoundError` straight through it. The agent pilot
      died at its first repository with a traceback pointing at the comparison line --
      found by running the pilot on linux, where `gh` is not installed.

      The fix is not simply "catch it". An empty answer is compared to `base_ref` and
      stored as a BOOLEAN, so a missing binary would have made every row in the run read
      `base_is_default=False` -- and the off-default share is a population finding the
      analysis reads, not a cosmetic label. Degrading would have manufactured 100%
      off-default and nothing would have raised. The tool being absent is OUR failure
      and stops the run; one repository's API call failing is the corpus's and returns
      empty.

      PATH is emptied for real rather than patching `subprocess.run`, so the OSError
      comes from a genuine failed exec.
IMPORTS: phase0.pilot.repo_facts, pytest, stdlib pathlib.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.pilot.repo_facts import GhUnavailable, default_branch, star_counts


def test_absent_star_table_yields_unknown_rather_than_failing(tmp_path: Path) -> None:
    """A band reported `unknown` is visibly different from one never measured."""
    assert star_counts(tmp_path / "nope.parquet") == {}


def test_a_missing_gh_raises_instead_of_labelling_every_row_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The regression test for the crash, asserting the CHOICE rather than the catch.

    If this returned "" the run would continue and every PR would read
    `base_is_default=False`, which is a measurement rather than an absence.
    """
    monkeypatch.setenv("PATH", "")
    with pytest.raises(GhUnavailable) as raised:
        default_branch("owner/definitely-not-cached-repo")
    assert "gh" in str(raised.value)
    assert "ENVIRONMENT.lock" in str(raised.value)
