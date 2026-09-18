"""What a valid push records, and the read-back the reply is built from.

WHAT: The happy path, replacement by a later push, two forges under one account name, and the
      case that tells a read-back from an echo.
WHY:  **TELLING A READ-BACK FROM AN ECHO NEEDS THE WRITE TO FAIL.** An earlier version of this
      file wrote two forges and asserted the rows stayed separate — a STORE property, true whether
      the reply came from the database or from the request. Replacing `covering(...)` with the
      parsed request left every test green, so the file asserted a guarantee it did not hold.

      `test_a_vanished_write_is_not_reported_as_stored` neuters `record` to stand in for a write
      the lock-free gcsfuse mount swallowed during a rollout. Only then do the two behaviours
      differ: an echo answers "team", a read-back answers "free", and the billing service re-queues.
IMPORTS: quantamind.serve.web.entitlement_route, quantamind.store.{billing,schema,tenancy},
      quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


# ---------------------------------------------------------------- the happy path and the read-back


def test_a_valid_push_is_recorded(tmp_path: Path) -> None:
    status, reply = answer(_push(), f"Bearer {SECRET}", SECRET, _settings(tmp_path))

    assert status == 200
    got = _stored(tmp_path)
    assert (got.tier, got.state, got.seats_included) == ("team", entitlement.State.ACTIVE, 25)
    assert reply["stored"]["tier"] == "team"
    assert reply["stored"]["seats_included"] == 25


def test_a_vanished_write_is_not_reported_as_stored(tmp_path: Path, monkeypatch: Any) -> None:
    """The write is lost; the reply must report what the store HOLDS, not what was asked for.

    This is the whole reason the reply is read back. `record` is neutered to stand in for a write
    that the lock-free mount swallowed during a rollout. An echoing handler answers "team" and
    tells the billing service the push landed; a reading handler answers "free" and the billing
    service re-queues it.
    """
    answer(
        _push(tier="free", state="none", seats_included=None),
        f"Bearer {SECRET}",
        SECRET,
        _settings(tmp_path),
    )
    monkeypatch.setattr(entitlement, "record", lambda *a, **k: None)

    _, reply = answer(_push(tier="team"), f"Bearer {SECRET}", SECRET, _settings(tmp_path))

    assert reply["stored"]["tier"] == "free", "the reply echoed the request instead of the store"
    assert _stored(tmp_path).tier == "free"


def test_two_forges_under_one_name_stay_separate(tmp_path: Path) -> None:
    """A store property, kept because it is worth holding — but it does NOT test the read-back."""
    answer(
        _push(forge="bitbucket", tier="free", state="none", seats_included=None),
        f"Bearer {SECRET}",
        SECRET,
        _settings(tmp_path),
    )
    _, reply = answer(_push(), f"Bearer {SECRET}", SECRET, _settings(tmp_path))

    assert reply["stored"]["tier"] == "team"
    assert _stored(tmp_path, "bitbucket").tier == "free", "one forge's push overwrote another's"
    assert _stored(tmp_path, "github").tier == "team"


def test_a_later_push_replaces_an_earlier_one(tmp_path: Path) -> None:
    answer(_push(), f"Bearer {SECRET}", SECRET, _settings(tmp_path))
    _, reply = answer(
        _push(tier="free", state="cancelled", seats_included=None, as_of=NOW + 60),
        f"Bearer {SECRET}",
        SECRET,
        _settings(tmp_path),
    )

    assert reply["stored"]["state"] == "cancelled"
    assert reply["stored"]["seats_included"] is None
    assert _stored(tmp_path).tier == "free"


def test_the_same_account_on_two_forges_stays_two_rows(tmp_path: Path) -> None:
    answer(_push(forge="github", tier="team"), f"Bearer {SECRET}", SECRET, _settings(tmp_path))
    answer(
        _push(forge="bitbucket", tier="enterprise"), f"Bearer {SECRET}", SECRET, _settings(tmp_path)
    )

    assert _stored(tmp_path, "github").tier == "team"
    assert _stored(tmp_path, "bitbucket").tier == "enterprise"
