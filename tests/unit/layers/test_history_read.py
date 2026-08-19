"""Read history from REAL git repositories built for each case, and sabotage the checks.

WHAT: Constructs actual git repositories on disk — a normal one, a shallow clone, a
      blob-filtered clone, one with no matching history — and asserts what `read_touches`
      returns or raises for each. Then breaks the exit-code check and requires the test to fail.
WHY:  These are real `git log` invocations against real object stores, not stubs. A mocked
      subprocess would assert that our parser parses our own fixture string, which is the
      failure mode `check_assert_quality.py` exists to catch.

      **The exit-code check is the reason this module exists**, so it gets a known-answer test:
      the sabotage removes the check entirely and the suite must go red. Removing only the
      `raise` while leaving the comparison would be sabotaging the entry point, not the
      mechanism.
IMPORTS: quantamind.ingest.history; stdlib subprocess, pathlib, pytest.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.history import (
    HistoryReadFailed,
    Touch,
    assert_readable,
    read_touches,
)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
    "HOME": "/tmp",
}


def _run(cwd: Path, *args: str) -> None:
    done = subprocess.run(
        ["git", *args], cwd=cwd, env=GIT_ENV, capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0, f"git {' '.join(args)} failed: {done.stderr}"


def _repo(tmp_path: Path, commits: list[tuple[str, str]]) -> Path:
    """A real repository with one commit per (filename, content) pair."""
    d = tmp_path / "repo"
    d.mkdir()
    _run(d, "init", "-q", "-b", "main")
    for name, content in commits:
        (d / name).parent.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(content)
        _run(d, "add", name)
        _run(d, "commit", "-q", "-m", f"add {name}")
    return d


def test_reads_every_file_touch_with_its_commit_time(tmp_path: Path) -> None:
    d = _repo(tmp_path, [("a.py", "1"), ("b.py", "2"), ("a.py", "3")])
    touches = read_touches(d)
    paths = [t.path for t in touches]
    assert paths.count("a.py") == 2, f"a.py was touched twice, got {paths}"
    assert paths.count("b.py") == 1, f"b.py was touched once, got {paths}"
    assert all(t.committed_at > 1_600_000_000 for t in touches), "timestamps are not real"


def test_pathspec_narrows_the_read_the_way_git_does(tmp_path: Path) -> None:
    d = _repo(tmp_path, [("a.py", "1"), ("notes.md", "x"), ("pkg/b.py", "2")])
    py = {t.path for t in read_touches(d, pathspec="*.py")}
    assert py == {"a.py", "pkg/b.py"}, f"pathspec did not narrow to Python, got {py}"


def test_no_matching_history_is_an_empty_list_not_an_error(tmp_path: Path) -> None:
    d = _repo(tmp_path, [("notes.md", "x")])
    assert read_touches(d, pathspec="*.py") == [], "an empty history must be a value, not a raise"


def test_a_shallow_clone_is_refused_rather_than_counted(tmp_path: Path) -> None:
    src = _repo(tmp_path, [("a.py", "1"), ("a.py", "2"), ("a.py", "3")])
    dst = tmp_path / "shallow"
    _run(tmp_path, "clone", "-q", "--depth", "1", f"file://{src}", str(dst))
    with pytest.raises(HistoryReadFailed) as caught:
        read_touches(dst)
    assert "shallow" in str(caught.value), f"wrong reason: {caught.value}"


def test_a_blob_filtered_clone_is_refused(tmp_path: Path) -> None:
    src = _repo(tmp_path, [("a.py", "1"), ("a.py", "2")])
    dst = tmp_path / "filtered"
    _run(tmp_path, "clone", "-q", "--filter=blob:none", "--no-checkout", f"file://{src}", str(dst))
    with pytest.raises(HistoryReadFailed) as caught:
        assert_readable(dst)
    assert "partial clone" in str(caught.value), f"wrong reason: {caught.value}"


def test_a_directory_that_is_not_a_repository_raises_with_its_path(tmp_path: Path) -> None:
    with pytest.raises(HistoryReadFailed) as caught:
        read_touches(tmp_path)
    assert str(tmp_path) in str(caught.value), "the error must carry the call site"


def test_touch_rejects_a_value_that_would_corrupt_a_count() -> None:
    with pytest.raises(ValueError):
        Touch(path="", committed_at=1)
    with pytest.raises(ValueError):
        Touch(path="a.py", committed_at=0)


def test_merge_commits_are_excluded_so_they_cannot_swamp_the_counts(tmp_path: Path) -> None:
    d = _repo(tmp_path, [("a.py", "1")])
    _run(d, "checkout", "-q", "-b", "side")
    (d / "b.py").write_text("2")
    _run(d, "add", "b.py")
    _run(d, "commit", "-q", "-m", "side")
    _run(d, "checkout", "-q", "main")
    (d / "c.py").write_text("3")
    _run(d, "add", "c.py")
    _run(d, "commit", "-q", "-m", "main")
    _run(d, "merge", "-q", "--no-ff", "-m", "merge", "side")
    counts = [t.path for t in read_touches(d)]
    assert counts.count("b.py") == 1, f"the merge re-counted b.py: {counts}"
    assert counts.count("c.py") == 1, f"the merge re-counted c.py: {counts}"


def test_a_repository_with_no_commits_is_no_history_not_a_failure(tmp_path: Path) -> None:
    d = tmp_path / "empty"
    d.mkdir()
    _run(d, "init", "-q", "-b", "main")
    assert read_touches(d) == [], "a repository with no commits is the no-history case"


def test_a_git_failure_mid_read_raises_instead_of_returning_a_short_list(tmp_path: Path) -> None:
    """This is the exit-code check itself. Sabotaging that check must make this test fail."""
    d = _repo(tmp_path, [("a.py", "1")])
    with pytest.raises(HistoryReadFailed) as caught:
        read_touches(d, pathspec=":(bogus)")
    assert "exit" in str(caught.value), f"the exit code must be reported: {caught.value}"


def test_a_commit_on_a_merged_side_branch_is_still_counted(tmp_path: Path) -> None:
    """A pathspec turns on history simplification, which drops commits that DID touch the path.

    When a merge's tree matches one parent, git follows only that parent and discards the other
    side entirely — non-merge commits included. The fixture below makes both sides reach the same
    content, which is the condition that triggers it. Found by gate 2b: on the pinned corpus the
    reader lost 3 to 151 commits per repository, and 23 of 430 for one celery file.
    """
    d = tmp_path / "merged"
    d.mkdir()
    _run(d, "init", "-q", "-b", "main")
    (d / "a.py").write_text("1")
    _run(d, "add", "a.py")
    _run(d, "commit", "-q", "-m", "base")

    _run(d, "checkout", "-q", "-b", "side")
    (d / "a.py").write_text("2")
    _run(d, "commit", "-q", "-am", "side change")

    _run(d, "checkout", "-q", "main")
    (d / "a.py").write_text("2")
    _run(d, "commit", "-q", "-am", "main change")
    _run(d, "merge", "-q", "--no-edit", "side")

    # The fixture is only meaningful if simplification really drops the side commit here, so that
    # is asserted rather than assumed: without it this test would pass against the old reader.
    simplified = subprocess.run(
        ["git", "log", "--no-merges", "--format=%s", "--", "*.py"],
        cwd=d,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.split()
    assert "side" not in simplified, f"fixture does not exercise simplification: {simplified}"

    subjects = len([t for t in read_touches(d, pathspec="*.py") if t.path == "a.py"])
    assert subjects == 3, f"expected base, side and main touches of a.py, counted {subjects}"
