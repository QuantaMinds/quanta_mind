"""What `ingest/diff.py` refuses, using real GitHub reads rather than a stubbed client.

WHAT: Reads real merged pull requests and asserts the file list, the base resolution, and that a
      base absent from the clone raises rather than producing a bound.
WHY:  The seam this module owns is WHICH COMMIT bounds the ranking window. Getting it wrong would
      not raise anywhere — it would produce a ranking against the wrong instant, which looks
      identical to a correct one.

      **These read GitHub, so they live in `tests/live/`.** They were written into `tests/unit/`
      first, with a docstring noting that hitting the network there was "unusual" — which was
      noticing the problem and shipping it anyway. CI has no `gh` credentials and failed with
      `exited 4: set the GH_TOKEN environment variable`, four tests down, on a suite that passed
      locally only because this machine is logged in.

      A stubbed client would assert that our parser parses our own fixture, and the failure modes
      here are GitHub's response shapes.
IMPORTS: quantamind.ingest.diff.
CONSUMED BY: `just verify` via `test-live`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.diff import DiffReadFailed, base_commit, changed_files

REPO = "pallets/flask"


def test_a_real_pull_request_yields_only_matching_files_that_still_exist() -> None:
    files = changed_files(REPO, 6096)
    assert files == sorted(set(files)), "the list must be sorted and deduplicated"
    assert all(f.endswith(".py") for f in files), f"a non-Python path survived the filter: {files}"
    assert files, "pull request 6096 changed Python files; an empty list means the read broke"


def test_a_suffix_that_matches_nothing_is_an_empty_list_not_an_error() -> None:
    # **The keyword is `suffixes` and this said `suffix`, so it raised TypeError before reaching
    # its assertion — it had never once tested what it claims to.** It read as coverage for the
    # empty-result-is-not-a-failure property while proving nothing about it.
    assert changed_files(REPO, 6096, suffixes=(".nope",)) == [], (
        "an empty result is a legitimate answer and must not be confused with a failure"
    )


def test_a_pull_request_that_does_not_exist_raises_with_the_call_site() -> None:
    with pytest.raises(DiffReadFailed) as caught:
        changed_files(REPO, 99_999_999)
    assert "99999999" in str(caught.value), "the error must name the pull request"
    assert REPO in str(caught.value), "the error must name the repository"


def test_a_base_commit_absent_from_the_clone_is_refused_rather_than_guessed(
    tmp_path: Path,
) -> None:
    """A fork or force-pushed branch. A guessed bound looks identical to a correct one."""
    empty = tmp_path / "repo"
    empty.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=empty, timeout=60, check=True)
    with pytest.raises(DiffReadFailed) as caught:
        base_commit(REPO, 6096, empty)
    assert "not in" in str(caught.value), f"wrong reason: {caught.value}"
    assert "Refusing to guess" in str(caught.value), (
        "the error must say why guessing is worse than failing"
    )
