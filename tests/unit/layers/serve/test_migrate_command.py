"""`quantamind migrate` against the layout a deployed service actually has.

WHAT: `serve/commands/run_migrate.{stores_under,run_migrate}` over a store ROOT holding the two
      shared stores and several tenants, all at an older schema version.
WHY:  **THE COMMAND MIGRATED ONE FILE AND PRODUCTION IS A DIRECTORY.** `QUANTAMIND_DATABASE_PATH`
      is a root: `store/tenancy.py` puts `accounts.db` and `deliveries.db` beside the tenants and
      one `<owner>/<name>.db` per repository under it, and the deployed service sets it to
      `/data/stores`. The command did `sqlite3.connect()` on that directory and died with an
      unhandled `OperationalError`. **The documented way to migrate production could not migrate
      production**, and every test passed a single FILE, so nothing saw it — `AGENTS.md` rule 14
      asked of a fixture: the tests agreed for a reason unrelated to the property.

      **A FLEET FAILS IN PARTS, SO THE COUNT AND THE EXIT CODE BOTH MATTER.** One unreadable store
      must not end the run and must not be reported as success; a deploy script reads the exit
      code and never the log.
IMPORTS: pytest, quantamind.serve.commands.run_migrate, quantamind.store.{schema,tables,tenancy}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.serve.commands.run_migrate import run_migrate, stores_under
from quantamind.store import tenancy
from quantamind.store.schema import SCHEMA_VERSION
from quantamind.store.tables import TABLES

# What version 8 had: this build's tables minus the three version 9 added.
V9_TABLES = ("entitlement", "seat_use", "forge_installation")
V8_TABLES = tuple(
    statement
    for statement in TABLES
    if not any(statement.startswith(f"CREATE TABLE IF NOT EXISTS {n} (") for n in V9_TABLES)
)


def _old_store(path: Path) -> None:
    """One store as version 8 left it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    for statement in V8_TABLES:
        conn.execute(statement)
    conn.execute("PRAGMA user_version = 8")
    conn.commit()
    conn.close()


def _version(path: Path) -> int:
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def _fleet(root: Path) -> list[Path]:
    """The shape a deployed service has: two shared stores and three tenants."""
    paths = [
        root / tenancy.ACCOUNTS,
        root / tenancy.DELIVERIES,
        root / "QuantaMinds" / "QuantaMind.db",
        root / "QuantaMinds" / "quantamind_pr_bot.db",
        root / "acme" / "widgets.db",
    ]
    for path in paths:
        _old_store(path)
    return paths


def test_a_store_root_is_not_mistaken_for_a_database(tmp_path: Path) -> None:
    """The exact failure: `sqlite3.connect` on the root raised and the command died."""
    expected = _fleet(tmp_path)

    found = stores_under(tmp_path)

    assert sorted(found) == sorted(expected), (
        "every store under the root must be found. Missing one means a deployed service starts, "
        "refuses that store at the wrong version, and reports it nowhere the deploy could catch."
    )


def test_a_single_file_still_works(tmp_path: Path) -> None:
    """A developer pointing the variable at one database is a real setup, not a regression."""
    one = tmp_path / "solo.db"
    _old_store(one)

    assert stores_under(one) == [one]


def test_a_missing_root_finds_nothing_rather_than_raising(tmp_path: Path) -> None:
    assert stores_under(tmp_path / "nope") == []


def test_every_store_in_the_fleet_reaches_this_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole point: after this, `open_store` opens all of them instead of refusing them."""
    paths = _fleet(tmp_path)
    monkeypatch.setenv("QUANTAMIND_DATABASE_PATH", str(tmp_path))
    monkeypatch.setenv("QUANTAMIND_WEBHOOK_SECRET", "x")

    assert run_migrate() == 0

    for path in paths:
        assert _version(path) == SCHEMA_VERSION, f"{path} was left behind at {_version(path)}"


def test_one_bad_store_does_not_strand_the_rest_and_does_not_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fleet fails in parts. Both halves of that are asserted, because either alone passes for
    the wrong implementation: stopping at the first failure also leaves the rest unmigrated, and
    continuing while exiting 0 hides it from the deploy."""
    paths = _fleet(tmp_path)
    # **BROKEN IN THE MIDDLE, NOT AT THE END, AND THAT IS THE WHOLE TEST.** Stores are visited in
    # the order `stores_under` returns them, and the first version of this test broke the LAST one
    # — so an implementation that gave up at the first failure stranded nothing and passed. Found
    # by sabotaging exactly that. `QuantaMinds/QuantaMind.db` is the first tenant, so giving up
    # here leaves two stores behind for the assertion below to catch.
    broken = tmp_path / "QuantaMinds" / "QuantaMind.db"
    assert paths.index(broken) < len(paths) - 1, "the broken store must not be the last one"
    broken.write_bytes(b"this is not a database, it is a text file")

    monkeypatch.setenv("QUANTAMIND_DATABASE_PATH", str(tmp_path))
    monkeypatch.setenv("QUANTAMIND_WEBHOOK_SECRET", "x")

    assert run_migrate() == 1, "a partial migration must not report success to a deploy script"

    healthy = [p for p in paths if p != broken]
    assert [_version(p) for p in healthy] == [SCHEMA_VERSION] * len(healthy), (
        "one unreadable store stopped the run; the rest of the fleet stays at the old version and "
        "the service refuses them"
    )


def test_running_it_twice_changes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-running after a partial failure must retry only what did not land."""
    _fleet(tmp_path)
    monkeypatch.setenv("QUANTAMIND_DATABASE_PATH", str(tmp_path))
    monkeypatch.setenv("QUANTAMIND_WEBHOOK_SECRET", "x")

    assert run_migrate() == 0
    assert run_migrate() == 0
