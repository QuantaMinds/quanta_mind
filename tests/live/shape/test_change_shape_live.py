"""The change-shape window, checked against a real clone by recomputing it from git.

WHAT: Clones pallets/flask and asserts `ingest.change_shape.shape()` measures a real commit in a
      window bounded by that commit, not by the clock — by naming the answer, by recomputing the
      window from git, and by showing the wall-clock window gives a DIFFERENT answer.
WHY:  **THE BUG THIS PINS SHIPPED AND WAS INVISIBLE.** `shape()` used `--since=30.days.ago`,
      relative to when the process runs. On django `2936a0a9` it reported 6 recent commits to the
      changed files where 3 of the 6 landed AFTER the change under review; on flask `c17f3793` it
      reported 0 against a true 2, because that clone's history ended months before the run and
      the window was EMPTY — indistinguishable from "nobody has touched this file".

      **THE NEGATIVE CONTROL IS THE POINT.** `test_wall_clock_window_gives_a_different_answer`
      recomputes what the old code would have said and requires it to differ. Without it these
      assertions could pass on a repository where both windows happen to agree, and the test would
      read as green while proving nothing — which is the failure mode this file exists to refuse.
IMPORTS: quantamind.ingest.{change_shape,review_window}. Nothing is mocked; every number is git's.
CONSUMED BY: `just test-live`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.change_shape import RECENT_DAYS, shape
from quantamind.ingest.review_window import WindowUnreadable, ending_at, moment_of

# A real flask commit, deliberately NOT the newest: its own past is immutable, so every number
# below is fixed forever regardless of where the clone's HEAD has moved to.
SHA = "c17f3793"
CHURN = 2  # commits to these files in the 30 days before it, excluding the change itself
HANDS = 0  # other people among them -- both prior commits are the change's own author
FILES = 6


def git(clone: Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=300
    )
    assert done.returncode == 0, f"git {args[0]} failed: {done.stderr[:200]}"
    return done.stdout


@pytest.fixture(scope="module")
def flask(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("shape") / "flask"
    done = subprocess.run(
        ["git", "clone", "-q", "https://github.com/pallets/flask.git", str(dest)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert done.returncode == 0, f"clone failed: {done.stderr[:200]}"
    return dest


@pytest.fixture(scope="module")
def changed(flask: Path) -> list[str]:
    paths = [p for p in git(flask, ["show", "--name-only", "--format=", SHA]).splitlines() if p]
    assert len(paths) == FILES, f"{SHA} should touch {FILES} files, git says {len(paths)}"
    return paths


def test_shape_names_the_answer(flask: Path, changed: list[str]) -> None:
    """The known answer, by name. Reintroducing a wall-clock window breaks this line."""
    out = shape(flask, SHA, changed)
    assert (out.churn, out.hands, out.files) == (CHURN, HANDS, FILES)
    assert out.median_files > 0 and out.median_lines > 0, "norms read nothing -- empty git log?"


def test_nothing_counted_had_happened_yet(flask: Path, changed: list[str]) -> None:
    """Recompute the window from git: every commit in it must predate the change."""
    at = git(flask, ["show", "-s", "--format=%cI", SHA]).strip()
    bound = ending_at(at, RECENT_DAYS, site="test")
    counted = [
        line.split(" ", 1)
        for line in git(
            flask,
            ["log", *bound.args, "--no-merges", "--format=%cI %H", SHA, "--", *changed],
        ).splitlines()
    ]
    assert counted, "the window admitted NOTHING -- a filter admitting nothing is a broken filter"
    later = [c for c in counted if c[0] > at]
    assert later == [], f"{len(later)} commit(s) counted that postdate {SHA}: {later}"


def test_the_change_is_not_its_own_churn(flask: Path, changed: list[str]) -> None:
    """`--until` is inclusive, so the change sits in its own window and must be dropped."""
    at = git(flask, ["show", "-s", "--format=%cI", SHA]).strip()
    full = git(flask, ["rev-parse", SHA]).strip()
    bound = ending_at(at, RECENT_DAYS, site="test")
    in_window = git(
        flask, ["log", *bound.args, "--no-merges", "--format=%H", SHA, "--", *changed]
    ).split()
    assert full in in_window, "the change is not inside its own window -- this test proves nothing"
    assert shape(flask, SHA, changed).churn == len(in_window) - 1


def test_wall_clock_window_gives_a_different_answer(flask: Path, changed: list[str]) -> None:
    """**THE NEGATIVE CONTROL.** The old window must not agree, or the tests above are vacuous."""
    at = git(flask, ["show", "-s", "--format=%cI", SHA]).strip()
    old = git(
        flask,
        ["log", f"--since={RECENT_DAYS}.days.ago", "--no-merges", "--format=%cI", "--", *changed],
    ).splitlines()
    anchored = git(
        flask,
        [
            "log",
            *ending_at(at, RECENT_DAYS, site="test").args,
            "--no-merges",
            "--format=%cI",
            SHA,
            "--",
            *changed,
        ],
    ).splitlines()
    assert old != anchored, (
        "the wall-clock window and the change-anchored one returned the same commits, so nothing "
        f"here distinguishes the bug from the fix on this clone (both saw {len(old)})"
    )


def test_walking_from_head_is_what_makes_it_clone_dependent(
    flask: Path, changed: list[str]
) -> None:
    """The third leak, pinned separately: `git log` walks from HEAD unless told otherwise.

    A date bound does NOT exclude commits on branches that were never in the change's history --
    their committer dates sit inside the window. Measured on this commit: 7 walking from main
    against 3 walking from the change, and only the second is the same on every clone.
    """
    at = git(flask, ["show", "-s", "--format=%cI", SHA]).strip()
    bound = ending_at(at, RECENT_DAYS, site="test")
    tail = ["--no-merges", "--format=%H"]
    from_head = git(flask, ["log", *bound.args, *tail, "--", *changed]).split()
    from_change = git(flask, ["log", *bound.args, *tail, SHA, "--", *changed]).split()
    assert set(from_change) < set(from_head), (
        "walking from HEAD did not admit anything extra, so this clone cannot show the defect"
    )
    assert shape(flask, SHA, changed).churn == len(from_change) - 1


def test_an_unreadable_time_raises_rather_than_defaulting_to_now() -> None:
    """The fallback IS the bug, so its absence is asserted, not assumed."""
    assert moment_of("") is None
    assert moment_of("not-a-date") is None
    with pytest.raises(WindowUnreadable) as caught:
        ending_at("not-a-date", RECENT_DAYS, site="repo@deadbeef")
    assert "repo@deadbeef" in str(caught.value), "the error must carry its call site"


def test_a_range_counts_every_commit_in_it(flask: Path, changed: list[str]) -> None:
    """`against` makes a multi-commit change count as one, which is what a pull request is.

    **THE SINGLE-COMMIT READ UNDERSTATES A BRANCH, AND NOT SUBTLY.** Measured on flask PR #5457,
    twenty commits: 694 lines across the range against 26 from the head commit alone. A model told
    "26 lines" about a 694-line change has been given a false fact, not a missing one.
    """
    base = git(flask, ["rev-parse", f"{SHA}~3"]).strip()
    span = [x for x in git(flask, ["diff", "--name-only", f"{base}...{SHA}"]).split() if x.strip()]
    assert len(span) >= len(changed), "the three-commit span touches fewer files than one commit"
    one = shape(flask, SHA, changed)
    many = shape(flask, SHA, span, against=base)
    assert many.lines > one.lines, (
        f"the range counted {many.lines} lines and the single commit {one.lines} -- `against` "
        "changed nothing, so a pull request would be reported as its last commit"
    )
    assert one.lines == shape(flask, SHA, changed, against="").lines, (
        "empty `against` must not move"
    )
