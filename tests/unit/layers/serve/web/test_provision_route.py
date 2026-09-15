"""The provisioning routes refuse before they read, and say what they did not verify.

WHAT: Drives `serve.web.provision_route.answer()` over a real temporary store — the auth refusals,
      the tier routing, and what a successful Team provision writes.
WHY:  **THIS ENDPOINT GRANTS A PAID TIER.** An unauthenticated POST that sets `tier=enterprise` is
      not a provisioning endpoint, it is a free upgrade for anyone who can reach the port, so the
      refusals are the tests that matter and the 202 is almost incidental.

      **THE UNSET-SECRET CASE IS THE ONE A GREEN SUITE WOULD HIDE.** A test that only supplies a
      secret says nothing about a deployment that has none — that is `AGENTS.md` rule 14's "a check
      that runs only where the thing it checks cannot happen". `test_an_unset_secret_refuses` is
      the assertion that "not configured" and "no authentication required" are different answers.

      **IT WRITES TO A REAL STORE, NOT A MOCK.** `AGENTS.md` non-negotiable 1: a behavioural test
      asserts on data a real run produced. The installation row is read back out of SQLite.
IMPORTS: quantamind.serve.web.provision_route, quantamind.store.{installations,tenancy}.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from quantamind.serve.web.provision_route import answer
from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store

SECRET = "provision-secret-value"
GOOD = "Bearer " + SECRET


@dataclass
class _Settings:
    database_path: str


def _body(**fields: object) -> bytes:
    return json.dumps(fields).encode()


def _team(tmp_path: Path, **overrides: object) -> tuple[int, dict]:
    fields: dict[str, object] = {
        "account": "acme",
        "repos": ["acme/api"],
        "seats": 12,
        "payment_ref": "sub_123",
    }
    fields.update(overrides)
    return answer("/provision/team", _body(**fields), GOOD, SECRET, _Settings(str(tmp_path)))


def test_an_unset_secret_refuses_rather_than_opening(tmp_path: Path) -> None:
    """**THE TEST THE HAPPY PATH WOULD HIDE.** No secret must not mean no authentication."""
    status, payload = answer(
        "/provision/team", _body(account="a", repos=["a/b"]), GOOD, "", _Settings(str(tmp_path))
    )
    assert status == 503
    assert "QUANTAMIND_PROVISION_SECRET is unset" in payload["error"]


def test_a_blank_secret_is_also_unset(tmp_path: Path) -> None:
    """Whitespace is not a secret. A deployment that set it to a space is not configured."""
    status, _ = answer(
        "/provision/team", _body(account="a", repos=["a/b"]), GOOD, "   ", _Settings(str(tmp_path))
    )
    assert status == 503


def test_a_wrong_token_is_refused(tmp_path: Path) -> None:
    status, payload = answer(
        "/provision/team",
        _body(account="a", repos=["a/b"]),
        "Bearer wrong",
        SECRET,
        _Settings(str(tmp_path)),
    )
    assert status == 401 and "bearer" in payload["error"]


def test_a_missing_header_is_refused(tmp_path: Path) -> None:
    status, _ = answer(
        "/provision/team", _body(account="a", repos=["a/b"]), None, SECRET, _Settings(str(tmp_path))
    )
    assert status == 401


def test_an_unknown_tier_is_404_not_a_default(tmp_path: Path) -> None:
    """**A TIER WE DO NOT SELL MUST NOT FALL THROUGH TO ONE WE DO.**"""
    status, payload = answer("/provision/platinum", _body(), GOOD, SECRET, _Settings(str(tmp_path)))
    assert status == 404 and payload["error"] == "no such tier"


def test_a_body_that_is_not_json_is_named(tmp_path: Path) -> None:
    status, payload = answer("/provision/team", b"not json", GOOD, SECRET, _Settings(str(tmp_path)))
    assert status == 400 and "not JSON" in payload["error"]


def test_a_refused_request_carries_every_reason(tmp_path: Path) -> None:
    status, payload = _team(tmp_path, payment_ref="", seats=0)
    assert status == 422
    assert payload["provisioned"] == []
    assert len(payload["refused"]) == 2, "one reason at a time means a caller is refused twice"


def test_a_team_provision_writes_a_real_installation_row(tmp_path: Path) -> None:
    """**ASSERTS ON WHAT THE RUN PRODUCED** — read back from SQLite, not from the reply."""
    status, payload = _team(tmp_path)
    assert status == 202, "202 because warming has not happened yet"
    assert payload["provisioned"] == ["acme/api"]
    assert payload["warming"] == ["acme/api"]

    conn = open_store(tenancy.shared(tmp_path, tenancy.ACCOUNTS))
    try:
        entitlement = installations.entitled(conn, "acme/api")
    finally:
        conn.close()
    assert entitlement.tier == "team"
    assert entitlement.state.value == "active"


def test_a_paid_reply_says_the_payment_was_not_verified(tmp_path: Path) -> None:
    """**B3 IS PARKED.** A caller must not infer that we checked a payment processor."""
    _, payload = _team(tmp_path)
    assert payload["payment_verified"] is False
    assert "recorded, not verified" in payload["note"]


def test_enterprise_without_an_org_is_refused_even_with_a_valid_token(tmp_path: Path) -> None:
    status, payload = answer(
        "/provision/enterprise",
        _body(account="acme", repos=["acme/api"], seats=50, payment_ref="sub_1"),
        GOOD,
        SECRET,
        _Settings(str(tmp_path)),
    )
    assert status == 422
    assert any("organisation" in why for why in payload["refused"])


def test_nothing_is_written_when_the_request_is_refused(tmp_path: Path) -> None:
    """A refusal must leave no store behind — otherwise a rejected caller still took a place."""
    _team(tmp_path, payment_ref="")
    assert not list(tmp_path.rglob("*.db")), "a refused request provisioned a store"
