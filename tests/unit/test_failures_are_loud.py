"""Every failure path in the pipeline, triggered, with its message asserted.

WHAT: Walks each layer's failure modes and requires two things of every one — that it raises rather
      than returning a plausible value, and that the message names the call site or the reason.
WHY:  A pipeline is only as honest as its quietest layer. Individually each module tests its own
      refusals; nothing tested that the SET of them is complete, and the two that were merely
      returning a value were found by triggering all seventeen and reading the table.

      **Two paths return by design and are asserted to.** `render.comment` returns None below the
      threshold, because silence is a decision the caller records. `parse.units` returns zero hunks
      for an empty diff, because a change with nothing in it is a real answer — but a diff with
      hunk headers and no file header now RAISES, since that read as "a change containing nothing"
      with conservation satisfied vacuously.
IMPORTS: every product layer.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest import commits, github_comments
from quantamind.parse.units import MalformedDiff, units_in
from quantamind.rank.order import NothingToRank, rank
from quantamind.render.comment import comment
from quantamind.render.coverage_line import NothingToReport, coverage_line
from quantamind.store import drift, schema
from quantamind.store import touches as touch_store
from quantamind.types.ranking import Ranking


def test_a_directory_that_is_not_a_repository_names_the_path(tmp_path: Path) -> None:
    with pytest.raises(commits.HistoryReadFailed) as caught:
        commits.read_commits(tmp_path)
    assert str(tmp_path) in str(caught.value), "the error must carry the call site"


def test_a_shallow_clone_says_the_history_is_truncated(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "m"], cwd=src, check=True, timeout=60)
    (src / "a.py").write_text("x = 1")
    subprocess.run(["git", "add", "a.py"], cwd=src, check=True, timeout=60)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"],
        cwd=src,
        check=True,
        timeout=60,
    )
    dest = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{src}", str(dest)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    with pytest.raises(commits.HistoryReadFailed) as caught:
        commits.read_commits(dest)
    assert "truncated" in str(caught.value), f"the reason must be stated: {caught.value}"


def test_a_store_from_another_version_names_both_versions(tmp_path: Path) -> None:
    path = tmp_path / "s.db"
    schema.open_store(path).close()
    stale = sqlite3.connect(path)
    stale.execute("PRAGMA user_version = 999")
    stale.commit()
    stale.close()
    with pytest.raises(schema.SchemaVersionMismatch) as caught:
        schema.open_store(path)
    assert "999" in str(caught.value) and str(schema.SCHEMA_VERSION) in str(caught.value)


def test_a_drifted_store_names_what_differs(tmp_path: Path) -> None:
    path = tmp_path / "d.db"
    stale = sqlite3.connect(path)
    stale.execute("CREATE TABLE touch (repo_id INTEGER, path TEXT)")
    stale.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION}")
    stale.commit()
    stale.close()
    with pytest.raises(drift.SchemaDrift) as caught:
        schema.open_store(path)
    assert "missing" in str(caught.value) or "differs" in str(caught.value)


def test_an_unbounded_count_says_which_argument_was_wrong(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    repo = touch_store.ensure_repo(conn, "github.com", "a/b")
    with pytest.raises(touch_store.UnboundedRankingError) as caught:
        touch_store.counts(conn, repo, ["a.py"], as_of=0)
    assert "as_of" in str(caught.value)
    with pytest.raises(touch_store.UnboundedRankingError) as caught:
        touch_store.counts(conn, repo, ["a.py"], as_of=1_700_000_000, window=0)
    assert "window" in str(caught.value)


def test_ranking_nothing_says_what_the_caller_should_do_instead() -> None:
    with pytest.raises(NothingToRank) as caught:
        rank({})
    assert "record that" in str(caught.value), "the message must name the alternative"


def test_rendering_an_empty_ranking_says_why_a_bland_sentence_is_wrong() -> None:
    with pytest.raises(NothingToReport) as caught:
        coverage_line(Ranking(units=(), fired=True))
    assert "own outcome" in str(caught.value)


def test_a_comment_with_no_key_says_why_the_key_matters() -> None:
    with pytest.raises(ValueError) as caught:
        github_comments.marker("   ")
    assert "deduplicated" in str(caught.value)


def test_a_diff_with_hunks_but_no_file_header_raises_rather_than_reporting_nothing() -> None:
    """Zero hunks would satisfy conservation vacuously and report a change containing nothing."""
    with pytest.raises(MalformedDiff) as caught:
        units_in("@@ -1,2 +1,3 @@ def f():\n+x\n")
    assert "vacuously" in str(caught.value) or "nothing" in str(caught.value)


def test_the_two_paths_that_return_by_design_still_do() -> None:
    """Silence is a decision the caller records, and an empty diff is a real answer."""
    assert comment(rank({"a.py": 0, "b.py": 0})) is None
    assert units_in("").hunks == 0
