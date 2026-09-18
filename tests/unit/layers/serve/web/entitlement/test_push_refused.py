"""Every way the entitlement push must be refused, and the nothing it must write.

WHAT: `serve/web/entitlement_route.answer` against a REAL store, for the auth ladder and every
      body shape that must not become a row.
WHY:  **THIS ROUTE GRANTS A PAID TIER, SO IT AUTHENTICATES BEFORE IT READS.** An unauthenticated
      POST setting `tier=enterprise` is not an entitlement endpoint, it is a free upgrade for
      anyone who finds the port. An unset secret refuses rather than opening, and that has its own
      case because "not configured" and "no authentication required" are one code path in most
      handlers.

      **AN UNKNOWN STATE IS REFUSED AT THE DOOR.** Stored, it would read back as NONE — a paid
      account silently on Free, with a 200 already sent and nothing recording why.

      Every case asserts the store is still empty afterwards, not merely that the status was 4xx.
IMPORTS: quantamind.serve.web.entitlement_route, quantamind.store.{billing,schema,tenancy},
      quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from quantamind.serve.web.entitlement_route import answer
from quantamind.store import tenancy
from quantamind.store.billing import entitlement
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings

SECRET = "a-shared-secret"
NOW = 1_700_000_000


def _settings(root: Path) -> Settings:
    return Settings(database_path=str(root))


def _push(**over: Any) -> bytes:
    body: dict[str, Any] = {
        "forge": "github",
        "account": "acme",
        "tier": "team",
        "state": "active",
        "seats_included": 25,
        "payment_ref": "sub_123",
        "as_of": NOW,
    }
    body.update(over)
    return json.dumps(body).encode()


def _stored(root: Path, forge: str = "github", account: str = "acme") -> entitlement.Coverage:
    conn = open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        return entitlement.covering(conn, forge, account, now=NOW)
    finally:
        conn.close()


# ---------------------------------------------------------------- the auth ladder


def test_an_unset_secret_refuses_rather_than_opening(tmp_path: Path) -> None:
    status, _ = answer(_push(), "Bearer anything", "", _settings(tmp_path))

    assert status == 503
    assert _stored(tmp_path).state is entitlement.State.NONE, "an unconfigured route wrote a row"


@pytest.mark.parametrize(
    "header", [None, "", "Bearer wrong", "Basic a-shared-secret", "a-shared-secret"]
)
def test_a_bad_token_is_refused_and_writes_nothing(tmp_path: Path, header: str | None) -> None:
    status, _ = answer(_push(), header, SECRET, _settings(tmp_path))

    assert status == 401
    assert _stored(tmp_path).state is entitlement.State.NONE


# ---------------------------------------------------------------- shapes that must not be stored


@pytest.mark.parametrize(
    ("body", "expect"),
    [
        (b"not json at all", "not JSON"),
        (b"[1,2,3]", "not an object"),
        (
            json.dumps({"account": "acme", "tier": "t", "state": "active", "as_of": 1}).encode(),
            "no forge",
        ),
        (
            json.dumps({"forge": "github", "tier": "t", "state": "active", "as_of": 1}).encode(),
            "no account",
        ),
        (
            json.dumps({"forge": "g", "account": "a", "state": "active", "as_of": 1}).encode(),
            "no tier",
        ),
        (json.dumps({"forge": "g", "account": "a", "tier": "t", "as_of": 1}).encode(), "no state"),
    ],
)
def test_an_unreadable_push_is_refused(tmp_path: Path, body: bytes, expect: str) -> None:
    status, reply = answer(body, f"Bearer {SECRET}", SECRET, _settings(tmp_path))

    assert status == 400
    assert expect in reply["error"]


def test_an_unknown_state_is_refused_at_the_door(tmp_path: Path) -> None:
    """Storing it would read back as NONE — a paid account silently downgraded, with a 200 sent."""
    status, reply = answer(
        _push(state="gold_plated"), f"Bearer {SECRET}", SECRET, _settings(tmp_path)
    )

    assert status == 400
    assert "gold_plated" in reply["error"]
    assert _stored(tmp_path).state is entitlement.State.NONE


def test_an_account_keyed_on_nothing_is_refused(tmp_path: Path) -> None:
    status, _ = answer(_push(account="  "), f"Bearer {SECRET}", SECRET, _settings(tmp_path))

    assert status == 400
