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
from quantamind.store import schema, tenancy


def test_a_store_this_build_created_is_healthy(tmp_path: Path) -> None:
    """`health()` now takes the tenant ROOT, not one file. → `store/tenancy.py`."""
    schema.open_store(tenancy.store_for(tmp_path, "acme", "widgets")).close()
    got = health(str(tmp_path))
    assert got.ok is True, got.detail
    assert str(schema.SCHEMA_VERSION) in got.detail, "the verdict should name what it checked"


def test_a_root_with_no_tenants_is_healthy_and_says_so(tmp_path: Path) -> None:
    """**A fresh install has no stores and is working.** Reporting that as a failure would make
    "nobody has installed us yet" and "our storage is broken" the same alarm."""
    got = health(str(tmp_path))
    assert got.ok is True, got.detail
    assert "no tenants" in got.detail


def test_one_bad_tenant_fails_the_whole_probe_and_is_named(tmp_path: Path) -> None:
    """A version mismatch in ONE tenant is a tenant this build must not write to."""
    schema.open_store(tenancy.store_for(tmp_path, "acme", "good")).close()
    bad = tenancy.store_for(tmp_path, "acme", "bad")
    schema.open_store(bad).close()
    stale = sqlite3.connect(bad)
    stale.execute("PRAGMA user_version = 999")
    stale.commit()
    stale.close()
    got = health(str(tmp_path))
    assert got.ok is False
    assert "bad" in got.detail, f"the verdict must name WHICH tenant: {got.detail}"


def test_a_store_from_another_schema_version_is_not_healthy(tmp_path: Path) -> None:
    """The deploy case: the file opens, and this build must not write to it."""
    path = tenancy.store_for(tmp_path, "acme", "widgets")
    schema.open_store(path).close()
    stale = sqlite3.connect(path)
    stale.execute("PRAGMA user_version = 999")
    stale.commit()
    stale.close()
    got = health(str(tmp_path))
    assert got.ok is False
    assert "999" in got.detail, f"the verdict must name the version found: {got.detail}"


def test_a_drifted_store_is_not_healthy(tmp_path: Path) -> None:
    path = tenancy.store_for(tmp_path, "acme", "drifted")
    stale = sqlite3.connect(path)
    stale.execute("CREATE TABLE touch (repo_id INTEGER, path TEXT)")
    stale.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION}")
    stale.commit()
    stale.close()
    got = health(str(tmp_path))
    assert got.ok is False
    assert "schema" in got.detail.lower()


def test_a_file_that_is_not_a_database_is_not_healthy(tmp_path: Path) -> None:
    """The junk must sit where a TENANT store lives, or the probe never looks at it.

    An earlier version of this test wrote the file directly into the root, where `tenancy.tenants`
    does not look — so the probe reported "no tenants, healthy" and the test passed for the wrong
    reason. It was only visible because the drift test next to it failed the same way.
    """
    tenancy.store_for(tmp_path, "acme", "junk").write_bytes(b"this is not sqlite")
    got = health(str(tmp_path))
    assert got.ok is False, "a file that merely exists must not read as a working store"


def test_health_never_raises_because_an_orchestrator_needs_a_verdict(tmp_path: Path) -> None:
    """A probe that throws gives a stack trace where a yes/no was needed."""
    unreachable = tmp_path / "no" / "such" / "dir" / "s.db"
    got = health(str(unreachable))
    assert got.ok is False and got.detail, "a failure must carry its reason"
    assert "FAILING" in got.render()


def test_a_missing_store_is_not_healthy_and_is_not_created(tmp_path: Path) -> None:
    """open_store() CREATES a missing database, so the first version of this probe answered ok=True
    for a path that did not exist — a deploy pointed at the wrong directory would have made an
    empty store, reported healthy, and served rankings computed over no history at all."""
    absent = tmp_path / "absent.db"
    got = health(str(absent))
    assert got.ok is False, "a store that does not exist cannot be healthy"
    assert not absent.exists(), "the probe must not CREATE the thing it is checking for"
    assert "wrong path" in got.detail or "no store" in got.detail
