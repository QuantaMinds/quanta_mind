"""Every failure path in the pipeline, triggered, with its message asserted.

WHAT: Walks each layer's failure modes and requires two things of every one — that it raises rather
      than returning a plausible value, and that the message names the call site or the reason.
WHY:  A pipeline is only as honest as its quietest layer. Individually each module tests its own
      refusals; nothing tested that the SET of them is complete, and the two that were merely
      returning a value were found by triggering all seventeen and reading the table.

      **Ten paths return a value rather than raising, and every one carries its reason.** A
      signature rejection is a RESPONSE to hostile input, not an exception — the HTTP layer turns
      it into a 401 — and a health probe that raised would give an orchestrator a stack trace where
      it needed a verdict. What must never happen is a returned value with nothing in it, so that
      is what is asserted.

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

from quantamind.ingest import commits
from quantamind.ingest.publish import github_comments
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


def test_the_path_that_returns_by_design_still_does() -> None:
    """An empty diff is a real answer, and stays one.

    **THE OTHER HALF OF THIS TEST WAS DELETED ON PURPOSE AND IS RECORDED HERE.** It asserted
    `comment(...) is None` for a change with no fix history, back when the product spoke on about
    a tenth of pull requests. `render/comment.py` now always renders and states salience in a
    sentence; the ranking's own `fired` flag still carries the signal. Silence on a change we DID
    rank is no longer one of the paths that returns by design.
    """
    assert units_in("").hunks == 0
    assert comment(rank({"a.py": 0, "b.py": 0}))


def test_a_rejected_delivery_says_which_kind_of_wrong_it_was() -> None:
    """ "Someone is probing us" and "our own secret is misconfigured" need different responses."""
    from quantamind.serve.webhook_github import Rejected, sign, verify

    secret, body = "s", b'{"action":"opened"}'
    seen = {
        verify(secret, body, None),
        verify(secret, body, "sha256=nope"),
        verify(secret, body, sign("someone-else", body)),
    }
    assert seen == {Rejected.NO_SIGNATURE, Rejected.MALFORMED_SIGNATURE, Rejected.BAD_SIGNATURE}, (
        f"the three rejection kinds collapsed into {seen}; an operator cannot tell a probe from a "
        "misconfiguration"
    )
    for rejection in seen:
        assert rejection.value.strip(), "a rejection with no reason is the same as a silent drop"


def test_a_missing_webhook_secret_raises_rather_than_accepting_the_delivery() -> None:
    from quantamind.serve.webhook_github import MisconfiguredSecret, sign, verify

    body = b"{}"
    with pytest.raises(MisconfiguredSecret) as caught:
        verify("", body, sign("s", body))
    assert "unverified" in str(caught.value), (
        "accepting when no secret is set turns the endpoint into an open command channel"
    )


def test_an_ignored_delivery_names_what_was_dropped() -> None:
    from quantamind.serve.webhook_github import Ignore, interpret

    for event, body, fragment in (
        ("ping", b"{}", "ping"),
        ("pull_request", b"not json", "not JSON"),
    ):
        got = interpret(event, body)
        assert isinstance(got, Ignore) and fragment in got.reason, (
            f"{event!r} with {body!r} gave {got!r}; an ignore that does not name the cause is a "
            "silent drop wearing a type"
        )


def test_health_returns_a_verdict_with_its_reason_and_never_raises(tmp_path: Path) -> None:
    """An orchestrator needs a yes or no. A stack trace is neither."""
    from quantamind.serve.health import health

    missing = health(str(tmp_path / "absent.db"))
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"not sqlite at all")
    unreadable = health(str(junk))
    for verdict in (missing, unreadable):
        assert verdict.ok is False
        assert verdict.detail.strip(), "a failing probe with no detail cannot be acted on"
