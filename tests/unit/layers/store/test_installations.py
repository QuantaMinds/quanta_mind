"""Verification that an installation we never assessed is not read as one we refused.

WHAT: Drives `store/installations` — recording, withdrawing, and the three states `entitled`
      distinguishes, against a real store.
WHY:  **`UNKNOWN` IS A STATE, NOT A DEFAULT FOR `NO`.** Every repository installed before this
      table existed has `eligible` NULL, because no assessment ran. Reading NULL as refused turns
      existing customers off at their next delivery; reading it as allowed grants an entitlement
      nobody checked. B5 refuses only `REMOVED`, and this file is what stops that widening by
      accident.

      **AN UNINSTALL IS RECORDED, NOT DELETED.** "They were never a customer" and "they left" are
      different answers to an auditor, so `withdraw` sets `removed_at` and returns how many rows
      it touched — a no-op is visible rather than silent.

      **`first_seen` SURVIVES A REDELIVERY.** GitHub replays installation events; rewriting the
      first-seen date on a replay a month later would quietly falsify when a customer arrived.
IMPORTS: pytest, quantamind.store.{installations,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.store.installations import Entitlement, State, entitled, record, withdraw
from quantamind.store.schema import open_store

NOW = 1_700_000_000


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    return open_store(tmp_path / "s.db")


def test_a_repository_never_installed_is_unknown(conn: sqlite3.Connection) -> None:
    """No row at all. Must not read as a refusal."""
    seat = entitled(conn, "acme/payments")

    assert seat.state is State.UNKNOWN
    assert seat.may_review is True
    assert "predates the mapping" in seat.why()


def test_an_installation_assessed_as_eligible_is_active(conn: sqlite3.Connection) -> None:
    record(conn, "acme", "acme/payments", at=NOW, eligible=True)

    seat = entitled(conn, "acme/payments")

    assert (seat.state, seat.eligible, seat.tier) == (State.ACTIVE, True, "free")
    assert seat.may_review is True


def test_an_ineligible_installation_is_refused(conn: sqlite3.Connection) -> None:
    """**THIS TEST ASSERTED THE OPPOSITE UNTIL 2026-09-15, AND BOTH WERE RIGHT IN TURN.**

    It read "an ineligible repository is still reviewed", pinning B5's decision that the free-tier
    verdict was information rather than a gate -- because *"a gate with no paid tier to fall back on
    is a dead end with no override"*. `serve/web/provision_route.py` shipped the paid tier, so the
    dead end has an exit and the verdict becomes a gate.

    **The refusal must still be VISIBLE**: `seat.why()` carries the reasons so the delivery can say
    them, and `serve/review/review_delivery.py` posts rather than going quiet.
    """
    record(conn, "acme", "acme/payments", at=NOW, eligible=False, reasons=("22 stars",))

    seat = entitled(conn, "acme/payments")

    assert seat.eligible is False
    assert seat.may_review is False, "an ineligible repository was reviewed anyway"
    assert "22 stars" in seat.why(), "a refusal a customer cannot act on is worse than silence"


def test_an_installation_recorded_without_an_assessment_keeps_eligible_null(
    conn: sqlite3.Connection,
) -> None:
    """The git-outage path: facts unreadable, so nothing is claimed either way."""
    record(conn, "acme", "acme/payments", at=NOW)

    seat = entitled(conn, "acme/payments")

    assert seat.eligible is None
    assert "never assessed" in seat.why()
    assert seat.may_review is True


def test_a_withdrawn_installation_is_the_only_state_that_refuses(conn: sqlite3.Connection) -> None:
    record(conn, "acme", "acme/payments", at=NOW, eligible=True)

    removed = withdraw(conn, "acme/payments", at=NOW + 10)
    seat = entitled(conn, "acme/payments")

    assert removed == 1
    assert seat.state is State.REMOVED
    assert seat.may_review is False


def test_withdrawing_nothing_returns_zero_rather_than_claiming_success(
    conn: sqlite3.Connection,
) -> None:
    """A no-op must be visible: 'we removed them' and 'there was nobody' are different."""
    assert withdraw(conn, "never/installed", at=NOW) == 0


def test_a_redelivered_installation_does_not_move_first_seen(conn: sqlite3.Connection) -> None:
    """GitHub replays. Rewriting first_seen would falsify when a customer arrived."""
    record(conn, "acme", "acme/payments", at=NOW, eligible=True)
    record(conn, "acme", "acme/payments", at=NOW + 2_592_000, eligible=True)

    first = conn.execute("SELECT first_seen FROM installation WHERE repo = ?", ("acme/payments",))

    assert int(first.fetchone()[0]) == NOW


def test_reinstalling_after_removal_clears_the_removal(conn: sqlite3.Connection) -> None:
    """**INVERTED, NOT DELETED — the `reinstate=True` is new and it is the whole point.**

    This test passed without it, because `record()` cleared `removed_at` on EVERY write. That made
    any bookkeeping write resurrect a repository the customer had removed, and it was unreachable
    until `withdraw()` gained a caller. A live endpoint then showed it: install, remove, and the
    install's own slow warm-up landed afterwards and silently undid the removal.

    The behaviour this test was written to protect — a genuine reinstall works — is still true and
    still asserted. What changed is that the caller now has to SAY it is a reinstall.
    """
    record(conn, "acme", "acme/payments", at=NOW, eligible=True)
    withdraw(conn, "acme/payments", at=NOW + 10)
    record(conn, "acme", "acme/payments", at=NOW + 20, eligible=True, reinstate=True)

    assert entitled(conn, "acme/payments").state is State.ACTIVE


def test_an_ordinary_write_does_not_resurrect_a_removal(conn: sqlite3.Connection) -> None:
    """The other half of the same rule, and the half that was the defect.

    A warm-up refreshing eligibility is not a statement that the repository is covered. Only an
    installation event makes that claim, so only it passes `reinstate`.
    """
    record(conn, "acme", "acme/payments", at=NOW, eligible=True)
    withdraw(conn, "acme/payments", at=NOW + 10)
    record(conn, "acme", "acme/payments", at=NOW + 20, eligible=True)

    assert entitled(conn, "acme/payments").state is State.REMOVED


def test_an_installation_needs_an_account_and_a_full_name(conn: sqlite3.Connection) -> None:
    """A row keyed on nothing is a mapping that maps nothing."""
    with pytest.raises(ValueError, match="account and an owner/name"):
        record(conn, "", "acme/payments", at=NOW)
    with pytest.raises(ValueError, match="account and an owner/name"):
        record(conn, "acme", "payments", at=NOW)


def test_an_entitlement_carries_its_evidence_never_a_bare_boolean() -> None:
    """`why()` is what a log line and a support conversation both need."""
    seat = Entitlement(State.ACTIVE, "free", False, ("22 stars", "3 contributors"))

    assert "22 stars" in seat.why() and "3 contributors" in seat.why()
