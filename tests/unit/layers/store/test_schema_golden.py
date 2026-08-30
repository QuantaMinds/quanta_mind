"""The serialised FORM, which every other check in this project looks straight past.

WHAT: Compares a freshly created store's `sqlite_master` SQL and per-table column order against a
      checked-in golden, and requires a store migrated from version 2 to be byte-identical to it.
WHY:  **`just verify` SAYS IN ITS OWN BANNER THAT IT CANNOT SEE THIS.** It recomputes every pack
      row from git per path, which is strong on VALUES and blind to column order, row ordering and
      path encoding. `check_schema_shape.py` fires when the DDL moves; **this is the artefact it
      told us to build**, and it was deliberately not built until the DDL actually moved, because
      an unexercised snapshot reads as coverage and gets regenerated unread.

      **THE MIGRATED-EQUALS-FRESH TEST IS THE ONE THAT EARNS ITS PLACE.** A migration that runs
      without raising has still failed if the result differs from what this build creates, and the
      difference is invisible to every value-level check: `ALTER TABLE ADD COLUMN` splices a column
      in before the `UNIQUE` clause on whatever line it lands on, producing DDL text no one would
      predict. That is why version 3 adds tables instead of altering one -- and this test is what
      would catch it if someone later reached for `ALTER`.
IMPORTS: stdlib, quantamind.store.{migrations,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3

from quantamind.store.migrations import migrate
from quantamind.store.schema import SCHEMA_VERSION, create
from quantamind.store.tables import TABLES

GOLDEN = pathlib.Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "schema_golden.json"

# The DDL of version 2, derived from this build's by removing what version 3 added, so a migration
# is exercised from a real older store rather than one this build made and then damaged.
V2_TABLES = tuple(t for t in TABLES if "lifecycle" not in t and "prod_signal" not in t)


def shape_of(conn: sqlite3.Connection) -> dict[str, object]:
    rows = sorted(
        (str(n), str(s or ""))
        for n, s in conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    )
    out: dict[str, object] = {}
    for name, sql in rows:
        cols = [
            (int(c[0]), str(c[1]), str(c[2]), int(c[3]), c[4], int(c[5]))
            for c in conn.execute(f"PRAGMA table_info({name})")
        ]
        out[name] = {"sql": sql, "columns": cols}
    out["__version__"] = conn.execute("PRAGMA user_version").fetchone()[0]
    return out


def golden() -> dict[str, object]:
    loaded: dict[str, object] = json.loads(GOLDEN.read_text())
    return loaded


def normalise(shape: dict[str, object]) -> str:
    return json.dumps(shape, indent=1, sort_keys=True)


def test_a_fresh_store_matches_the_golden_byte_for_byte() -> None:
    conn = sqlite3.connect(":memory:")
    create(conn)
    assert normalise(shape_of(conn)) == normalise(golden()), (
        "the schema's serialised form changed. If that was intended, regenerate "
        "tests/fixtures/schema_golden.json AND read the diff — column order and DDL text are "
        "exactly what no other check in this project can see."
    )


def test_a_store_migrated_from_version_2_is_identical_to_a_fresh_one() -> None:
    """The check the migration exists to pass, and the one a value-level test cannot make."""
    old = sqlite3.connect(":memory:")
    for statement in V2_TABLES:
        old.execute(statement)
    old.execute("PRAGMA user_version = 2")
    old.commit()

    done = migrate(old)
    assert done.version == SCHEMA_VERSION
    # Hardcoded, not derived from the ledger: deriving it would make the test agree with whatever
    # `STEPS` says, including a step that was forgotten. The next schema bump breaks this line on
    # purpose, so somebody has to look at the migration path from a real old store.
    assert done.steps == (3, 4, 5, 6), (
        f"expected the 2->3, 3->4, 4->5 and 5->6 steps, got {done.steps}. Hardcoded on purpose: a "
        "schema bump breaks this line so somebody looks at the path from a REAL old store."
    )
    assert normalise(shape_of(old)) == normalise(golden()), (
        "a migrated store differs from a freshly created one. This is the failure that produces "
        "a database whose version says one thing and whose tables say another."
    )


def test_migrating_an_up_to_date_store_does_nothing() -> None:
    conn = sqlite3.connect(":memory:")
    create(conn)
    before = normalise(shape_of(conn))
    done = migrate(conn)
    assert done.steps == ()
    assert normalise(shape_of(conn)) == before, "a no-op migration changed the schema"


def test_rows_written_before_the_migration_survive_it() -> None:
    """A migration that loses data passes every shape check ever written."""
    old = sqlite3.connect(":memory:")
    for statement in V2_TABLES:
        old.execute(statement)
    old.execute("PRAGMA user_version = 2")
    old.execute("INSERT INTO repo (host, name, first_seen) VALUES ('github.com', 'a/b', 1)")
    old.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision) "
        "VALUES (1, 7, 'deadbeef', 100, 1)"
    )
    old.commit()

    migrate(old)
    kept = old.execute("SELECT pr_number, head_sha FROM review").fetchall()
    assert kept == [(7, "deadbeef")], f"the migration lost or altered existing rows: {kept}"
