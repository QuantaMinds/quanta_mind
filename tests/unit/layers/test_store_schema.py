"""Apply the schema to real SQLite files and assert what it stores, refuses and enforces.

WHAT: Creates actual databases on disk, writes rows, and asserts the columns that cannot be
      backfilled exist and hold what the design requires. Then breaks the version gate and requires
      the suite to go red.
WHY:  The schema is append-only and there is no delete-and-reindex path in production, so a column
      missing on the first row is a column missing forever. These are real `sqlite3` connections
      against real files — a mocked cursor would assert that our DDL string equals our DDL string.
IMPORTS: quantamind.store.schema; stdlib sqlite3, pathlib, pytest.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store import schema


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def test_a_fresh_store_is_created_and_stamped(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    assert schema.version(conn) == schema.SCHEMA_VERSION, "a fresh store must carry its version"


def test_shadow_pick_stores_a_ranked_list_not_a_top_pick(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    cols = _columns(conn, "shadow_pick")
    assert {"rank", "score", "percentile"} <= cols, f"top-3 cannot be recomputed from {cols}"
    conn.execute("INSERT INTO repo (host,name,first_seen) VALUES ('gh','a/b',1)")
    conn.execute(
        "INSERT INTO review (repo_id,pr_number,head_sha,created_at,fire_decision) "
        "VALUES (1,1,'sha',1,1)"
    )
    for rank in (1, 2, 3):
        conn.execute(
            "INSERT INTO shadow_pick (review_id,ranker_name,unit_path,rank,score,percentile) "
            "VALUES (1,'null',?,?,?,?)",
            (f"f{rank}.py", rank, 1.0 / rank, 0.5),
        )
    got = conn.execute("SELECT COUNT(*) FROM shadow_pick WHERE review_id=1").fetchone()[0]
    assert got == 3, f"a ranked list of three must persist as three rows, got {got}"


RECORDED_NOT_DERIVED = {("subscription", "amount_cents")}
"""The one cents column, and it is not a cost.

**WHAT WE SPEND AND WHAT A CUSTOMER WAS CHARGED ARE DIFFERENT FACTS WITH DIFFERENT FAILURE
MODES.** `store/schema.py` bans stored cents for OUR spend and gives the reason: prices change,
token counts do not, and cents cannot separate a cache read from fresh input. Every word of that is
about a number we DERIVE.

`subscription.amount_cents` is a number Stripe SENT us about a charge that already happened. It
cannot be re-derived from anything in this database, it does not change when a price changes --
that is the whole point of recording it -- and it is the only way a price id pointing at the wrong
product becomes visible in a row rather than only on somebody's invoice.

**IT IS A PAIR AND NOT A TABLE NAME**, so the exemption cannot widen to a `cost_cents` column on
the same table next month without somebody adding it here on purpose."""


def test_cost_is_not_stored_as_cents_anywhere(tmp_path: Path) -> None:
    """Prices change and token counts do not, and cents cannot separate a cache read."""
    conn = schema.open_store(tmp_path / "s.db")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    # "cent" as a substring also matches `percentile`; the column being banned is cents.
    offenders = {
        (t, c)
        for t in tables
        for c in _columns(conn, t)
        if ("cents" in c or "cost" in c) and (t, c) not in RECORDED_NOT_DERIVED
    }
    assert offenders == set(), f"cost must be derived from tokens, found {sorted(offenders)}"


def test_the_cents_exemption_names_a_column_that_exists(tmp_path: Path) -> None:
    """**AN EXEMPTION FOR A COLUMN NOBODY HAS IS A HOLE WITH NOTHING IN IT.**

    If `amount_cents` is ever renamed, this fails and the exemption is removed with it rather than
    sitting in the file granting a pass to a name that no longer means anything.
    """
    conn = schema.open_store(tmp_path / "s.db")

    for table, column in RECORDED_NOT_DERIVED:
        assert column in _columns(conn, table), f"{table}.{column} is exempted and does not exist"


def test_the_subscription_table_stores_no_derived_cost(tmp_path: Path) -> None:
    """The exemption is for what Stripe charged. It is not a door for our own spend."""
    columns = _columns(schema.open_store(tmp_path / "s.db"), "subscription")

    assert {c for c in columns if "cost" in c} == set(), "our spend does not belong on a customer"
    assert "amount_cents" in columns, "what Stripe charged must be on the record"


def test_request_records_cache_reads_so_a_persistent_zero_is_visible(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    assert "cache_read_tokens" in _columns(conn, "request"), "a total cache miss must be data"


def test_outcome_can_be_re_derived_after_the_attribution_rule_changes(tmp_path: Path) -> None:
    cols = _columns(schema.open_store(tmp_path / "s.db"), "outcome")
    assert "rule_version" in cols, "nobody could tell which rule labelled which row"
    assert "fix_subject" in cols, "the rule reads the subject, so the subject must be stored"


def test_ranked_unit_can_hold_cold_units_not_only_the_funded_ones(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    conn.execute("INSERT INTO repo (host,name,first_seen) VALUES ('gh','a/b',1)")
    conn.execute(
        "INSERT INTO review (repo_id,pr_number,head_sha,created_at,fire_decision) "
        "VALUES (1,1,'sha',1,1)"
    )
    for rank, alloc in ((1, "deep"), (2, "shallow"), (9, "cold")):
        conn.execute(
            "INSERT INTO ranked_unit (review_id,unit_path,rank,score,allocation) "
            "VALUES (1,?,?,?,?)",
            (f"f{rank}.py", rank, 0.0, alloc),
        )
    cold = conn.execute("SELECT COUNT(*) FROM ranked_unit WHERE allocation='cold'").fetchone()[0]
    assert cold == 1, (
        "cold rows are the coverage line's content and shadow evaluation's denominator"
    )


def test_a_store_from_another_schema_version_is_refused_not_migrated(tmp_path: Path) -> None:
    path = tmp_path / "s.db"
    schema.open_store(path).close()
    stale = sqlite3.connect(path)
    stale.execute("PRAGMA user_version = 999")
    stale.commit()
    stale.close()
    with pytest.raises(schema.SchemaVersionMismatch) as caught:
        schema.open_store(path)
    assert caught.value.found == 999, "the error must name the version it found"
    assert str(path) in str(caught.value), "the error must carry the call site"


def test_reopening_an_applied_store_is_not_an_error(tmp_path: Path) -> None:
    path = tmp_path / "s.db"
    schema.open_store(path).close()
    conn = schema.open_store(path)
    assert schema.version(conn) == schema.SCHEMA_VERSION, "reopening must be idempotent"


def test_a_store_whose_tables_drifted_is_refused_even_when_the_version_matches(
    tmp_path: Path,
) -> None:
    """IF NOT EXISTS is silent about a wrong table, and the version is bumped by hand."""
    from quantamind.store import drift

    path = tmp_path / "drifted.db"
    stale = sqlite3.connect(path)
    stale.execute("CREATE TABLE touch (repo_id INTEGER, path TEXT)")  # committed_at missing
    stale.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION}")
    stale.commit()
    stale.close()
    with pytest.raises(drift.SchemaDrift) as caught:
        schema.open_store(path)
    assert "touch differs" in str(caught.value) or "missing" in str(caught.value)


def test_a_healthy_store_reports_no_drift(tmp_path: Path) -> None:
    from quantamind.store import drift

    conn = schema.open_store(tmp_path / "s.db")
    assert drift.differences(conn) == [], "a store this build just created cannot have drifted"
    assert len(drift.fingerprint()) == 16
