"""An extended touch index must equal a rebuilt one, on a real repository, exactly.

WHAT: Builds a repository's index twice — once fresh, once by extending an earlier index across
      new commits — and requires the two to be identical. Then rewrites the history and requires
      the extend path to REFUSE.
WHY:  **A SHORT INDEX IS INVISIBLE.** `touches.counts()` filters by `as_of`, so an index that
      reaches too far is harmless and one that stops short produces a normal-looking ranking
      computed against a history that ended early — no error, no warning, nothing in the output
      that differs. The only defence is requiring the cheap path to equal the expensive one.

      **THE REWRITE CASE IS TESTED BY ACTUALLY REWRITING.** This project once shipped a
      `history_rewritten` check that ran only on admitted records and read zero across 515 — a
      check that could not fire. `git commit --amend` here makes the watermark unreachable for
      real, so the fallback is exercised rather than asserted.
IMPORTS: quantamind.{ingest,store}. Nothing mocked; git and sqlite do the work.
CONSUMED BY: `just test-live`.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest import reachability
from quantamind.ingest.history import read_touches
from quantamind.store import schema
from quantamind.store import touches as touch_store

SPEC = "*.py"
LANGS = "test-langs"


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 0, f"git {args[0]} failed: {done.stderr[:200]}"
    return done.stdout


def commit(repo: Path, name: str, body: str) -> None:
    (repo / name).write_text(body)
    git(repo, "add", name)
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", f"add {name}")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A real git repository with a history worth indexing."""
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main", ".")
    for i in range(6):
        commit(r, f"mod_{i}.py", f"x = {i}\n")
    return r


def rows(conn: sqlite3.Connection, repo_id: int) -> list[tuple[str, int]]:
    """Every indexed touch, ordered, so two indexes can be compared exactly."""
    return sorted(
        (str(p), int(t))
        for p, t in conn.execute(
            "SELECT path, committed_at FROM touch WHERE repo_id = ?", (repo_id,)
        )
    )


def store(tmp_path: Path, name: str) -> tuple[sqlite3.Connection, int]:
    conn = schema.open_store(tmp_path / name)
    return conn, touch_store.ensure_repo(conn, "github.com", "local/repo")


def test_an_extended_index_equals_a_rebuilt_one(repo: Path, tmp_path: Path) -> None:
    """**THE CORRECTNESS BAR.** Cheap path and expensive path, byte for byte."""
    cheap, cheap_id = store(tmp_path, "cheap.db")
    touch_store.index(cheap, cheap_id, read_touches(repo, pathspec=SPEC))
    mark = reachability.head_sha(repo)
    touch_store.extend(cheap, cheap_id, (), head_sha=mark, languages=LANGS, stamped_at=1)

    for i in range(6, 9):  # history moves on
        commit(repo, f"mod_{i}.py", f"y = {i}\n")

    added = read_touches(repo, pathspec=SPEC, since=mark)
    assert added, "the range read returned nothing after three new commits — the bound is wrong"
    touch_store.extend(
        cheap, cheap_id, added, head_sha=reachability.head_sha(repo), languages=LANGS, stamped_at=2
    )

    full, full_id = store(tmp_path, "full.db")
    touch_store.index(full, full_id, read_touches(repo, pathspec=SPEC))

    assert rows(cheap, cheap_id) == rows(full, full_id)


def test_the_range_read_excludes_the_watermark_itself(repo: Path) -> None:
    """Off by one here double-counts a commit, and a doubled count moves a ranking."""
    mark = reachability.head_sha(repo)
    assert read_touches(repo, pathspec=SPEC, since=mark) == [], (
        "a range read at HEAD returned commits — the watermark commit is being re-read, "
        "and re-appending it would double its touches"
    )


def test_a_rewritten_history_is_refused(repo: Path) -> None:
    """**SABOTAGE THE MECHANISM, NOT THE ENTRY POINT.** Amend, so the watermark really is gone."""
    mark = reachability.head_sha(repo)
    assert reachability.is_ancestor(repo, mark), "fixture is wrong: HEAD is not its own ancestor"
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--amend", "-m", "new")
    assert reachability.head_sha(repo) != mark, "the amend did not rewrite anything"
    assert not reachability.is_ancestor(repo, mark), (
        "a rewritten history still reports its old watermark as an ancestor, so the extend path "
        "would run and silently omit whatever the rewrite dropped"
    )


def test_an_absent_watermark_is_not_an_ancestor(repo: Path) -> None:
    """A never-indexed repository and a stale one must reach the same full-read branch."""
    assert not reachability.is_ancestor(repo, "")
    assert not reachability.is_ancestor(repo, "0" * 40)


def test_a_commit_dated_older_than_the_watermark_is_still_read(repo: Path, tmp_path: Path) -> None:
    """**THE TRAP THE WHOLE DESIGN IS BUILT AROUND, given a history that can spring it.**

    Every other test here uses a chronologically ordered fixture, where a `--since=<date>` bound
    and a `<sha>..HEAD` bound return the same commits — so they would pass over the defect. Git
    history is not ordered by time: a rebase or cherry-pick lands commits whose committer date is
    OLDER than ones already indexed. This makes one on purpose and requires the range read to see
    it. A timestamp watermark returns [] here and the touch is lost forever.
    """
    mark = reachability.head_sha(repo)
    newest = int(git(repo, "show", "-s", "--format=%ct", "HEAD").strip())

    stale = str(newest - 86_400)  # a full day BEFORE the commit we are extending from
    (repo / "rebased.py").write_text("z = 1\n")
    git(repo, "add", "rebased.py")
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            "rebased",
            "--date",
            stale,
        ],
        check=True,
        timeout=120,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "GIT_COMMITTER_DATE": stale,
            "HOME": str(tmp_path),
        },
    )
    landed = int(git(repo, "show", "-s", "--format=%ct", "HEAD").strip())
    assert landed < newest, f"fixture failed to backdate: {landed} is not before {newest}"

    added = read_touches(repo, pathspec=SPEC, since=mark)
    assert [t.path for t in added] == ["rebased.py"], (
        f"the range read missed a commit dated before its watermark: {added}. "
        "This is what a timestamp bound does silently, and why the watermark is a SHA."
    )
