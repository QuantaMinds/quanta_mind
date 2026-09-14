"""`quantamind review --sha` against real flask commits, including a merge. Issue #95.

WHAT: Runs `_timestamp()` and `review_commit()` over two pinned `pallets/flask` commits chosen
      because they are the two shapes the `--sha` path used to collapse into one output: a merge,
      and a commit whose every file is in a language we do not read.
WHY:  **BOTH USED TO PRINT `0 file(s) ranked, 0 skipped as unsupported`.** `git show --name-only`
      emits no filenames for a merge, and the suffix filter ran inside `_timestamp` so nothing
      unreviewable ever reached the `skipped` count. Three different situations -- a merge we did
      not read, a change with nothing in a language we read, and a commit that changed nothing --
      arrived as the same line and the same exit code.

      **EACH TEST NAMES THE ARTEFACT IT MUST FIND**, per AGENTS.md rule 14: not "some files were
      ranked" but `src/flask/app.py`, which a merge-blind reader cannot return. A test asserting
      only a non-zero count passes on any reading of any commit.
IMPORTS: quantamind.serve.commands.run_commit; quantamind.types.{change,review}. Rightmost layer.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.serve.commands.run_commit import _timestamp, review_commit
from quantamind.types.change import REVIEWABLE_SUFFIXES

# **A MERGE, PINNED.** flask's "Merge commit from fork", two parents, six files against its first
# parent. Its own past is immutable, so these names are fixed forever wherever HEAD has moved to.
MERGE_SHA = "089cb86dd22bff589a4eafb7ab8e42dc357623b4"
MERGE_ALL = 6
MERGE_READABLE = (
    "src/flask/app.py",
    "src/flask/ctx.py",
    "src/flask/sessions.py",
    "src/flask/templating.py",
    "tests/test_basic.py",
)
MERGE_SKIPPED = ("CHANGES.rst",)

# **A NON-MERGE WHOSE EVERY FILE IS UNREADABLE.** flask's "release version 3.1.3". One parent, so
# it isolates the suffix-filter half of the defect from the merge half.
RELEASE_SHA = "22d924701a6ae2e4cd01e9a15bbaf3946094af65"
RELEASE_ALL = ("CHANGES.rst", "pyproject.toml", "uv.lock")


@pytest.fixture(scope="module")
def flask(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("review-commit") / "flask"
    done = subprocess.run(
        ["git", "clone", "-q", "https://github.com/pallets/flask.git", str(dest)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert done.returncode == 0, f"clone failed: {done.stderr[:200]}"
    return dest


def test_the_pinned_commits_are_still_the_shapes_this_file_relies_on(flask: Path) -> None:
    """**A KNOWN-ANSWER TEST ON THE CORPUS, NOT THE CODE.** If flask ever rewrote these commits,
    every assertion below would pass or fail for a reason that has nothing to do with the fix."""
    parents = subprocess.run(
        ["git", "-C", str(flask), "log", "-1", "--format=%P", MERGE_SHA],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert len(parents.stdout.split()) == 2, f"{MERGE_SHA[:12]} is no longer a two-parent merge"
    release = subprocess.run(
        ["git", "-C", str(flask), "log", "-1", "--format=%P", RELEASE_SHA],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert len(release.stdout.split()) == 1, f"{RELEASE_SHA[:12]} is no longer a single-parent"


def test_a_merge_commits_files_are_read_and_app_py_is_among_them(flask: Path) -> None:
    """**NAMES THE ARTEFACT.** `src/flask/app.py` is in this merge and a blind reader returns []."""
    found = _timestamp(flask, MERGE_SHA)
    assert found is not None, f"{MERGE_SHA[:12]} should resolve in a full clone"
    changed, _as_of = found

    assert len(changed) == MERGE_ALL, f"merge should report {MERGE_ALL} paths, got {changed}"
    for path in (*MERGE_READABLE, *MERGE_SKIPPED):
        assert path in changed, f"{path} is in this merge and _timestamp did not return it"


def test_timestamp_returns_every_path_and_leaves_the_filtering_to_its_caller(flask: Path) -> None:
    """The suffix filter belongs to the caller, or nothing unreadable can ever reach `skipped`."""
    found = _timestamp(flask, RELEASE_SHA)
    assert found is not None
    changed, _as_of = found

    assert sorted(changed) == sorted(RELEASE_ALL), f"expected {RELEASE_ALL}, got {changed}"
    assert not [p for p in changed if p.endswith(REVIEWABLE_SUFFIXES)], (
        "this commit has no readable file; if that changed, the test below means nothing"
    )


def test_a_change_with_nothing_readable_says_so_rather_than_printing_two_zeros(
    flask: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """**THE OUTPUT MUST DISTINGUISH ITSELF FROM AN EMPTY COMMIT.** It used to print `0 ranked,
    0 skipped`, which is what a commit touching nothing at all prints."""
    code = review_commit(flask, "pallets/flask", RELEASE_SHA)
    out = capsys.readouterr().out

    assert code == 0, "a change with nothing readable is a result, not a failure"
    assert "3 file(s) changed" in out, f"the three changed files must be counted: {out!r}"
    assert "none in a language we read" in out, f"the reason must be named: {out!r}"
    assert "0 file(s) ranked, 0 skipped" not in out, "the two-zero line is the defect in issue #95"


def test_reviewing_the_merge_ranks_its_python_files(
    flask: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """End to end through the command, not just the reader: the merge produces a real ranking."""
    code = review_commit(flask, "pallets/flask", MERGE_SHA)
    out = capsys.readouterr().out

    assert code == 0
    assert f"{len(MERGE_READABLE)} file(s) ranked" in out, f"expected 5 ranked: {out!r}"
    assert f"{len(MERGE_SKIPPED)} skipped as unsupported" in out, f"expected 1 skipped: {out!r}"
