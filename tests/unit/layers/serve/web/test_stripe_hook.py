"""Verification that the webhook route authenticates, refuses a replay, and records what arrived.

WHAT: Drives `serve/web/stripe_hook.answer` against a real store on disk, with bodies signed by
      `serve/webhook_stripe.sign` and one body taken verbatim from a real Stripe delivery.
WHY:  **THE ROUTE IS WHERE THE THREE GUARDS MEET, AND EACH ONE PASSES ALONE.** Signature
      verification, the replay ledger and the out-of-order refusal are tested in their own files;
      what is only testable here is that the route actually calls all three, in that order, and
      that the reply distinguishes their outcomes. A route that verified and then forgot to claim
      the delivery would pass every test in `test_webhook_stripe.py`.

      **AN UNSET SECRET IS ASSERTED DIRECTLY.** A configured route answering 200 says nothing about
      an unconfigured one, and "not configured" and "no authentication required" must not be the
      same code path.

      **THE REPLY DISTINGUISHES APPLIED FROM NOT-APPLIED, AND BOTH ARE 200.** Stripe must not retry
      a stale or unmatched delivery — it would retry for three days something that can never
      succeed — so the status code cannot carry that information and the body must.
IMPORTS: pytest, quantamind.serve.web.stripe_hook, quantamind.serve.webhook_stripe,
      quantamind.store.*, quantamind.types.billing.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from pathlib import Path

from quantamind.serve.web.stripe_hook import answer
from quantamind.serve.webhook_stripe import sign
from quantamind.store import tenancy
from quantamind.store.billing.subscriptions import current
from quantamind.store.schema import open_store
from quantamind.types.billing import Standing

SECRET = "whsec_route_test"
FORGED = "t=1789691900,v1=" + "a" * 64
"""Well-formed and wrong: 64 hex characters, a current timestamp, and not our secret."""
NOW = 1_789_691_900

FIXTURE = (
    pathlib.Path(__file__).resolve().parents[5]
    / "tests"
    / "fixtures"
    / "stripe_subscription_created.json"
)


@dataclass
class _Settings:
    database_path: str


def _event(**changes: object) -> bytes:
    """The real captured delivery, with any top-level event field replaced."""
    event = json.loads(FIXTURE.read_text())
    event.update(changes)
    return json.dumps(event).encode()


def _post(tmp_path: Path, body: bytes, *, secret: str = SECRET, at: int = NOW) -> tuple[int, dict]:
    return answer(
        body, sign(SECRET, body, at=at), secret=secret, settings=_Settings(str(tmp_path)), at=at
    )


def _held(tmp_path: Path, account: str = "octocat"):
    conn = open_store(tenancy.shared(tmp_path, tenancy.ACCOUNTS))
    try:
        return current(conn, account)
    finally:
        conn.close()


def test_an_unset_secret_refuses_the_route_rather_than_accepting_unverified_input(
    tmp_path: Path,
) -> None:
    """**THE TEST THE CONFIGURED PATH WOULD HIDE.** No secret must not mean no verification."""
    status, payload = _post(tmp_path, _event(), secret="")

    assert status == 503
    assert "QUANTAMIND_STRIPE_WEBHOOK_SECRET is unset" in payload["error"]


def test_a_blank_secret_is_also_unset(tmp_path: Path) -> None:
    status, _ = _post(tmp_path, _event(), secret="   ")

    assert status == 503


def test_a_real_delivery_is_recorded_and_read_back_from_sqlite(tmp_path: Path) -> None:
    """**ASSERTS ON WHAT THE RUN PRODUCED**, read back from the store rather than from the reply."""
    status, payload = _post(tmp_path, _event())

    assert status == 200
    assert payload["applied"] is True
    assert payload["standing"] == "active"
    held = _held(tmp_path)
    assert held is not None
    assert (held.account, held.seats, held.amount_cents) == ("octocat", 3, 2900)


def test_a_forged_signature_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    body = _event()

    status, payload = answer(
        body,
        FORGED,
        secret=SECRET,
        settings=_Settings(str(tmp_path)),
        at=NOW,
    )

    assert status == 401
    assert payload["error"] == "no v1 signature matches the body"
    assert not list(tmp_path.rglob("*.db")), "a refused delivery created a store"


def test_a_replay_is_refused_and_says_so_rather_than_applying_twice(tmp_path: Path) -> None:
    """Stripe retries one event for three days and reuses its id."""
    body = _event()
    _post(tmp_path, body)

    status, payload = _post(tmp_path, body)

    assert status == 200, "a replay must not be retried by Stripe, so it cannot be non-2xx"
    assert payload["replay"] == "evt_1UGpoaGY5MuBVWoyam3A9ay7"
    assert "not applied twice" in payload["note"]


def test_an_older_event_is_answered_200_and_reported_as_not_applied(tmp_path: Path) -> None:
    """**THE STATUS CANNOT CARRY THIS AND THE BODY MUST.** Correct, and not a failure."""
    newer = _event(id="evt_newer", created=NOW, type="customer.subscription.updated")
    _post(tmp_path, newer)

    older = _event(id="evt_older", created=NOW - 600, type="customer.subscription.updated")
    body = json.loads(older)
    body["data"]["object"]["status"] = "canceled"
    stale = json.dumps(body).encode()
    status, payload = answer(
        stale,
        sign(SECRET, stale, at=NOW),
        secret=SECRET,
        settings=_Settings(str(tmp_path)),
        at=NOW,
    )

    assert status == 200
    assert payload["applied"] is False
    assert "older than the stored" in payload["reason"]
    held = _held(tmp_path)
    assert held is not None and held.standing is Standing.ACTIVE, "a live customer was switched off"


def test_an_unmatched_subscription_is_200_and_named_rather_than_dropped(tmp_path: Path) -> None:
    """Created in the Dashboard. Retrying it for three days would never make it match."""
    event = json.loads(FIXTURE.read_text())
    event["data"]["object"]["metadata"] = {}
    body = json.dumps(event).encode()

    status, payload = _post(tmp_path, body)

    assert status == 200
    assert "carries no metadata.account" in payload["ignored"]
    assert _held(tmp_path) is None, "an unmatched subscription was written to an account"


def test_an_authenticated_body_with_no_event_id_cannot_be_claimed(tmp_path: Path) -> None:
    """Without an id there is no replay key, and applying it would be unrepeatable by design."""
    body = json.dumps({"type": "customer.subscription.updated", "data": {}}).encode()

    status, payload = _post(tmp_path, body)

    assert status == 400
    assert payload["error"] == "the delivery authenticated but carries no event id"
