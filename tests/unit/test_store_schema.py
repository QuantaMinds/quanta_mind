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


def test_cost_is_not_stored_as_cents_anywhere(tmp_path: Path) -> None:
    """Prices change and token counts do not, and cents cannot separate a cache read."""
    conn = schema.open_store(tmp_path / "s.db")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    # "cent" as a substring also matches `percentile`; the column being banned is cents.
    offenders = {t: c for t in tables for c in _columns(conn, t) if "cents" in c or "cost" in c}
    assert offenders == {}, f"cost must be derived from tokens, found {offenders}"


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
