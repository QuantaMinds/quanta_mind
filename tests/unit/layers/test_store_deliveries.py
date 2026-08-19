"""Replay protection, and the redelivery case that makes the naive version wrong.

WHAT: A completed delivery cannot be replayed; an unfinished one can be retried; an unidentifiable
      one is refused.
WHY:  **GitHub does not sign a timestamp**, so a captured delivery stays valid forever and anyone
      who records one can replay it indefinitely. Verification proves origin, never freshness.

      **And a redelivery REUSES the original GUID.** GitHub retries with the same identifier when
      we failed, so the obvious implementation — record on receipt, reject anything seen — would
      drop exactly the work GitHub is telling us to redo. That case is the reason `begin()` and
      `complete()` are separate calls, and it is tested here first.
IMPORTS: quantamind.store.deliveries, quantamind.store.schema.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.store import deliveries, schema

GUID = "6a1b2c3d-4e5f-6789-abcd-ef0123456789"


def test_a_finished_delivery_cannot_be_replayed(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    assert deliveries.begin(conn, GUID, "pull_request") is True
    deliveries.complete(conn, GUID)
    assert deliveries.begin(conn, GUID, "pull_request") is False, (
        "a captured delivery replayed after we finished must not make us act twice"
    )


def test_an_unfinished_delivery_may_be_retried(tmp_path: Path) -> None:
    """GitHub redelivers with the SAME GUID when we failed; refusing it discards that work."""
    conn = schema.open_store(tmp_path / "s.db")
    assert deliveries.begin(conn, GUID, "pull_request") is True
    assert deliveries.begin(conn, GUID, "pull_request") is True, (
        "we started and never finished, so GitHub's retry is legitimate"
    )
    deliveries.complete(conn, GUID)
    assert deliveries.begin(conn, GUID, "pull_request") is False


def test_a_delivery_with_no_identifier_is_refused(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    with pytest.raises(ValueError) as caught:
        deliveries.begin(conn, "   ", "pull_request")
    assert "deduplicated" in str(caught.value)


def test_completing_a_delivery_nobody_started_is_refused(tmp_path: Path) -> None:
    """Marking work finished that never began would let the next replay straight through."""
    conn = schema.open_store(tmp_path / "s.db")
    with pytest.raises(ValueError) as caught:
        deliveries.complete(conn, GUID)
    assert "never claimed" in str(caught.value)


def test_two_different_deliveries_do_not_interfere(tmp_path: Path) -> None:
    conn = schema.open_store(tmp_path / "s.db")
    other = "11111111-2222-3333-4444-555555555555"
    assert deliveries.begin(conn, GUID, "pull_request") is True
    deliveries.complete(conn, GUID)
    assert deliveries.begin(conn, other, "pull_request") is True, (
        "one finished delivery must not suppress a different one"
    )
