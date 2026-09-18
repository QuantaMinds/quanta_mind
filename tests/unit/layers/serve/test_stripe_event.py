"""Verification that a REAL Stripe payload is read correctly, including the field Stripe moved.

WHAT: Drives `serve/stripe_event.interpret` over `tests/fixtures/stripe_subscription_created.json`
      — a `customer.subscription.created` captured from an actual delivery on 2026-09-17, on API
      version `2026-08-26.dahlia`, the version `ingest/payments/stripe_api.py` pins.
WHY:  **A HAND-WRITTEN PAYLOAD TESTS THE AUTHOR'S BELIEF ABOUT STRIPE, NOT STRIPE.** This fixture
      is bytes Stripe sent. That distinction paid for itself immediately: under this API version
      `current_period_end` is **absent from the subscription object entirely** and present only on
      the subscription ITEM. A reader written against the top-level field — which is what every
      older example shows — records 0 for every subscription, and `verify/paid_access` then reports
      every paying customer as having no period. Nothing else in the suite would have caught it.

      **AN UNMATCHED SUBSCRIPTION IS A STATED OUTCOME.** A subscription created in the Dashboard
      carries no `metadata.account`. It must not raise, must not be written to a random account,
      and must not be answered non-2xx — Stripe would retry for three days something that can
      never match.

      **AN UNKNOWN STATUS BECOMES AN IGNORE, NOT A GUESS.** Stripe adds statuses. Reading a new one
      as unpaid cuts off a paying customer on the day it ships.
IMPORTS: pytest, quantamind.serve.stripe_event, quantamind.types.billing.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
import pathlib

from quantamind.serve.stripe_event import Ignore, interpret
from quantamind.types.billing import Standing, Subscription

FIXTURE = (
    pathlib.Path(__file__).resolve().parents[4]
    / "tests"
    / "fixtures"
    / "stripe_subscription_created.json"
)
REAL = json.loads(FIXTURE.read_text())


def delivery(**changes: object) -> bytes:
    """The real event, optionally with one field of the subscription object changed."""
    event = json.loads(FIXTURE.read_text())
    event["data"]["object"].update(changes)
    return json.dumps(event).encode()


def test_a_real_delivery_reads_into_every_field() -> None:
    """**ASSERTS THE WHOLE VALUE.** A per-field check passes while a neighbour silently reads 0."""
    read = interpret(delivery())

    assert read == Subscription(
        account="octocat",
        subscription_id="sub_1UGpoYGY5MuBVWoyoH6gtWwV",
        customer_id="cus_VHObXYYaL5p3z2",
        price_id="price_1UGfiCGY5MuBVWoyiOyqLh6G",
        standing=Standing.ACTIVE,
        seats=3,
        amount_cents=2900,
        currency="usd",
        current_period_end=1792283886,
        event_at=1789691888,
    )


def test_the_period_end_is_absent_from_the_subscription_and_read_off_the_item() -> None:
    """**THE FIXTURE IS THE EVIDENCE.** If Stripe ever puts it back, this says so out loud."""
    subscription = REAL["data"]["object"]

    assert subscription.get("current_period_end") is None, (
        "Stripe now sends current_period_end on the subscription again; the fallback in "
        "serve/stripe_event._period_end is no longer dead and this test should be revisited"
    )
    assert subscription["items"]["data"][0]["current_period_end"] == 1792283886


def test_a_subscription_with_no_account_is_unmatched_and_names_itself() -> None:
    """Created in the Dashboard, not through checkout. It belongs to no GitHub login we know."""
    read = interpret(delivery(metadata={}))

    assert isinstance(read, Ignore)
    assert "carries no metadata.account" in read.reason
    assert "sub_1UGpoYGY5MuBVWoyoH6gtWwV" in read.reason


def test_a_status_this_build_does_not_know_is_refused_rather_than_read_as_unpaid() -> None:
    read = interpret(delivery(status="quantum_superposition"))

    assert isinstance(read, Ignore)
    assert "quantum_superposition" in read.reason
    assert "refused rather than guessed" in read.reason


def test_an_event_type_that_changes_no_entitlement_is_ignored_with_its_name() -> None:
    event = json.loads(FIXTURE.read_text())
    event["type"] = "invoice.payment_succeeded"

    read = interpret(json.dumps(event).encode())

    assert isinstance(read, Ignore)
    assert read.reason == (
        "event 'invoice.payment_succeeded' does not change what an account is entitled to"
    )


def test_checkout_session_completed_is_ignored_because_the_subscription_event_carries_more() -> (
    None
):
    """Acting on both would write one row from two shapes, and the session has no status at all."""
    event = json.loads(FIXTURE.read_text())
    event["type"] = "checkout.session.completed"

    read = interpret(json.dumps(event).encode())

    assert isinstance(read, Ignore)
    assert "does not change what an account is entitled to" in read.reason


def test_a_body_that_is_not_json_is_a_reason_rather_than_an_exception() -> None:
    """A gateway's HTML error page is the realistic case, and it must not reach a stack trace."""
    read = interpret(b"<html>502 Bad Gateway</html>")

    assert isinstance(read, Ignore)
    assert read.reason == "body is not JSON: Expecting value: line 1 column 1 (char 0)"


def test_an_event_with_no_data_object_is_named_rather_than_crashing() -> None:
    read = interpret(json.dumps({"type": "customer.subscription.updated", "data": {}}).encode())

    assert isinstance(read, Ignore)
    assert read.reason == "customer.subscription.updated carried no data.object"


def test_a_cancellation_reads_as_cancelled_and_not_as_absent() -> None:
    read = interpret(delivery(status="canceled"))

    assert isinstance(read, Subscription)
    assert read.standing is Standing.CANCELED
    assert read.paid is False
