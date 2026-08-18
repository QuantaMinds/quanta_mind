"""A liveness check that reports the process is alive is a check whose output never changes.

WHAT: Asserts health() fails on a missing store, a drifted one, a wrong-version one, and a file
      that is not a database — and succeeds only on a store this build can actually use.
WHY:  The failure mode a probe must catch is a deploy against a database this build cannot safely
      write to. That state opens fine at the file level and is only visible through
      `open_store`'s version and drift checks, which is why health() opens rather than pings.
IMPORTS: quantamind.serve.health, quantamind.store.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.serve.health import health
from quantamind.store import schema


def test_a_store_this_build_created_is_healthy(tmp_path: Path) -> None:
    path = tmp_path / "s.db"
    schema.open_store(path).close()
    got = health(str(path))
    assert got.ok is True, got.detail
    assert str(schema.SCHEMA_VERSION) in got.detail, "the verdict should name what it checked"


def test_a_store_from_another_schema_version_is_not_healthy(tmp_path: Path) -> None:
    """The deploy case: the file opens, and this build must not write to it."""
    path = tmp_path / "s.db"
    schema.open_store(path).close()
    stale = sqlite3.connect(path)
    stale.execute("PRAGMA user_version = 999")
    stale.commit()
    stale.close()
    got = health(str(path))
    assert got.ok is False
    assert "999" in got.detail, f"the verdict must name the version found: {got.detail}"


def test_a_drifted_store_is_not_healthy(tmp_path: Path) -> None:
    path = tmp_path / "d.db"
    stale = sqlite3.connect(path)
    stale.execute("CREATE TABLE touch (repo_id INTEGER, path TEXT)")
    stale.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION}")
    stale.commit()
    stale.close()
    got = health(str(path))
    assert got.ok is False
    assert "schema" in got.detail.lower()


def test_a_file_that_is_not_a_database_is_not_healthy(tmp_path: Path) -> None:
    path = tmp_path / "not.db"
    path.write_bytes(b"this is not sqlite")
    got = health(str(path))
    assert got.ok is False, "a file that merely exists must not read as a working store"


def test_health_never_raises_because_an_orchestrator_needs_a_verdict(tmp_path: Path) -> None:
    """A probe that throws gives a stack trace where a yes/no was needed."""
    unreachable = tmp_path / "no" / "such" / "dir" / "s.db"
    got = health(str(unreachable))
    assert got.ok is False and got.detail, "a failure must carry its reason"
    assert "FAILING" in got.render()
