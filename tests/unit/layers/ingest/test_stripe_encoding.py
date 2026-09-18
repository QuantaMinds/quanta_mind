"""Verification of the bytes Stripe actually receives, since there is no SDK doing this for us.

WHAT: Drives `ingest/payments/stripe_api.encode` — the bracket form encoding — and the refusals
      `ingest/payments/checkout.open_session` makes before it ever opens a socket.
WHY:  **NOT TAKING THE SDK MEANS OWNING THIS, AND THIS IS THE PART THAT SILENTLY MISENCODES.**
      Stripe's v1 API accepts no JSON body. `line_items[0][price]` is not a style choice, and a
      nested structure flattened wrongly does not error — Stripe ignores parameters it does not
      recognise, so a subscription would be created against no price, or at the wrong quantity,
      and the first symptom is an invoice.

      **`None` IS DROPPED AND `False` IS NOT.** `str(None)` is the four characters "None", which
      Stripe would read as a value. An omitted optional and a deliberate false cannot share a
      branch, and nothing about the happy path exercises the difference.

      **THE REFUSALS RUN BEFORE THE NETWORK, WHICH IS WHY THEY ARE TESTABLE AT ALL.** Each one is a
      number or a name we would otherwise have put on somebody's card statement.
IMPORTS: pytest, quantamind.ingest.payments.{checkout,stripe_api}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import urllib.parse

import pytest

from quantamind.ingest.payments.checkout import SESSIONS, open_session
from quantamind.ingest.payments.stripe_api import PaymentsFailed, encode

PRICE = "price_1UGfiCGY5MuBVWoyiOyqLh6G"


def _form(params: dict[str, object]) -> str:
    return urllib.parse.urlencode(encode(params))


def test_a_checkout_session_encodes_exactly_as_stripe_reads_it() -> None:
    """The real body. **Compared whole**, because a per-key check passes with a key missing."""
    body = _form(
        {
            "mode": "subscription",
            "line_items": [{"price": PRICE, "quantity": 3}],
            "client_reference_id": "octocat",
            "subscription_data": {"metadata": {"account": "octocat"}},
        }
    )

    assert urllib.parse.unquote(body) == (
        "mode=subscription"
        f"&line_items[0][price]={PRICE}"
        "&line_items[0][quantity]=3"
        "&client_reference_id=octocat"
        "&subscription_data[metadata][account]=octocat"
    )


def test_the_account_is_carried_twice_because_two_different_events_need_it() -> None:
    """`client_reference_id` is on the session only; every later event is about the subscription."""
    body = urllib.parse.unquote(
        _form(
            {
                "client_reference_id": "octocat",
                "subscription_data": {"metadata": {"account": "octocat"}},
            }
        )
    )

    assert body.count("octocat") == 2
    assert "subscription_data[metadata][account]=octocat" in body


def test_none_is_dropped_and_false_is_sent() -> None:
    """`str(None)` is the four characters "None", which Stripe would store as a value."""
    body = urllib.parse.unquote(_form({"kept": False, "dropped": None, "also_kept": True}))

    assert body == "kept=false&also_kept=true"


def test_a_list_of_scalars_is_indexed_too() -> None:
    assert urllib.parse.unquote(_form({"expand": ["a", "b"]})) == "expand[0]=a&expand[1]=b"


def test_an_empty_parameter_set_encodes_to_nothing_rather_than_to_braces() -> None:
    assert _form({}) == ""


def test_a_session_with_no_account_is_refused_before_the_socket_opens() -> None:
    """A payment attached to nobody. The repair is a human reading two dashboards side by side."""
    with pytest.raises(PaymentsFailed, match="no account was named") as refused:
        open_session(
            api_key="sk_test_x",
            account="  ",
            price_id=PRICE,
            seats=1,
            success_url="https://x/ok",
            cancel_url="https://x/no",
        )

    assert refused.value.path == SESSIONS


def test_zero_seats_is_refused_before_the_socket_opens() -> None:
    with pytest.raises(PaymentsFailed, match="bills at least one"):
        open_session(
            api_key="sk_test_x",
            account="octocat",
            price_id=PRICE,
            seats=0,
            success_url="https://x/ok",
            cancel_url="https://x/no",
        )


def test_a_missing_price_id_is_refused_before_the_socket_opens() -> None:
    with pytest.raises(PaymentsFailed, match="no price id"):
        open_session(
            api_key="sk_test_x",
            account="octocat",
            price_id="",
            seats=1,
            success_url="https://x/ok",
            cancel_url="https://x/no",
        )


def test_an_empty_api_key_refuses_rather_than_calling_stripe_unauthenticated() -> None:
    """**A REFUSAL, NOT AN ATTEMPT.** An unauthenticated call to a payments API is never right."""
    from quantamind.ingest.payments.stripe_api import call

    with pytest.raises(PaymentsFailed, match="no Stripe API key was given"):
        call("v1/checkout/sessions", api_key="   ")
