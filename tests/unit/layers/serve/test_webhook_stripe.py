"""Verification that a forged, stale, future-dated or rotated delivery each get their own answer.

WHAT: Drives `serve/webhook_stripe.verify` over raw bytes. No socket, no Stripe, no mock.
WHY:  **THE TIMESTAMP IS THE THING GITHUB'S WEBHOOK CANNOT DO, SO IT IS THE THING TESTED HARDEST.**
      `serve/webhook_github.py` records that its signature covers the body and nothing else, so a
      captured delivery stays valid forever. Stripe signs `t.body`, and that only helps if the
      tolerance is real in both directions.

      **A NAIVE `now - t < TOLERANCE` ADMITS EVERY FUTURE TIMESTAMP, HOWEVER FAR.** That is the
      defect this file exists to keep out, and it is invisible to any test that only ages a
      delivery.

      **A ROTATION SENDS TWO `v1` VALUES IN ONE HEADER.** Reading only the first breaks rotation
      silently and only in production, because nobody rotates a secret in a unit test by accident.

      **THE CONSTANT-TIME COMPARE IS NOT TESTED HERE AND CANNOT BE.** Replacing `compare_digest`
      with `==` leaves every assertion below passing — the same admission
      `serve/webhook_github.py` makes about itself. `scripts/guard/runtime/
      check_constant_time_compare.py` is what actually holds it, and this paragraph is the record
      that the gap is known rather than missed.
IMPORTS: pytest, quantamind.serve.webhook_stripe.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.serve.webhook_stripe import (
    TOLERANCE_S,
    Reason,
    SecretMissing,
    sign,
    verify,
)

SECRET = "whsec_a_test_secret"
BODY = b'{"id":"evt_1","type":"customer.subscription.updated"}'
NOW = 1_700_000_000


def test_an_authentic_delivery_passes_and_a_tampered_one_does_not() -> None:
    """**BOTH DIRECTIONS IN ONE ASSERTION.** `verify(...) is None` alone would also pass against a
    function that returns None unconditionally, which is the first sabotage the plan names."""
    header = sign(SECRET, BODY, at=NOW)

    outcomes = [
        verify(SECRET, BODY, header, at=NOW),
        verify(SECRET, BODY.replace(b"evt_1", b"evt_2"), header, at=NOW),
    ]

    assert [None if o is None else o.reason for o in outcomes] == [None, Reason.BAD_SIGNATURE]


def test_one_changed_byte_in_the_body_is_refused() -> None:
    """The MAC covers the bytes. Anything that re-serialises before verifying breaks here."""
    header = sign(SECRET, BODY, at=NOW)

    refused = verify(SECRET, BODY + b" ", header, at=NOW)

    assert refused is not None and refused.reason is Reason.BAD_SIGNATURE
    assert "1 v1 signature(s) offered, none matched" in refused.detail


def test_a_signature_made_with_a_different_secret_is_refused() -> None:
    forged = sign("whsec_someone_elses", BODY, at=NOW)

    refused = verify(SECRET, BODY, forged, at=NOW)

    assert refused is not None and refused.reason is Reason.BAD_SIGNATURE


def test_an_absent_secret_raises_rather_than_accepting_the_delivery() -> None:
    """ "No secret configured, so accept everything" is an open command channel that moves money."""
    with pytest.raises(SecretMissing, match="Refusing to accept unverified input"):
        verify("", BODY, sign(SECRET, BODY, at=NOW), at=NOW)


def test_a_missing_header_and_a_malformed_one_are_different_answers() -> None:
    """ "Someone is probing us" and "our own secret is misconfigured" need different responses."""
    absent = verify(SECRET, BODY, None, at=NOW)
    junk = verify(SECRET, BODY, "v1=nothex", at=NOW)

    assert absent is not None and absent.reason is Reason.NO_SIGNATURE
    assert junk is not None and junk.reason is Reason.MALFORMED_SIGNATURE


def test_a_signature_that_is_not_64_hex_characters_is_malformed_not_merely_wrong() -> None:
    short = f"t={NOW},v1=abcdef"

    refused = verify(SECRET, BODY, short, at=NOW)

    assert refused is not None and refused.reason is Reason.MALFORMED_SIGNATURE
    assert "64 hex characters" in refused.detail


def test_a_delivery_older_than_the_tolerance_is_refused_at_the_second_it_turns() -> None:
    """Replay protection is the whole reason the timestamp is inside the MAC."""
    stale = sign(SECRET, BODY, at=NOW - TOLERANCE_S - 1)
    edge = sign(SECRET, BODY, at=NOW - TOLERANCE_S)

    refused = verify(SECRET, BODY, stale, at=NOW)

    assert refused is not None and refused.reason is Reason.TIMESTAMP_OUTSIDE_TOLERANCE
    assert verify(SECRET, BODY, edge, at=NOW) is None, "exactly at the tolerance is still accepted"


def test_a_future_timestamp_is_refused_and_a_naive_check_would_admit_it() -> None:
    """`at - stamp < TOLERANCE` is true for every timestamp in the future. This is that test."""
    ahead = sign(SECRET, BODY, at=NOW + 10 * TOLERANCE_S)

    refused = verify(SECRET, BODY, ahead, at=NOW)

    assert refused is not None and refused.reason is Reason.TIMESTAMP_OUTSIDE_TOLERANCE
    assert "in the future" in refused.detail


def test_the_refusal_names_the_measured_skew_because_a_bad_clock_looks_like_a_bad_secret() -> None:
    """An operator who rotates the secret on a clock fault changes nothing and is still down."""
    refused = verify(SECRET, BODY, sign(SECRET, BODY, at=NOW - 900), at=NOW)

    assert refused is not None
    assert "900s old" in refused.detail
    assert "check NTP before rotating anything" in refused.detail


def test_every_v1_is_compared_so_a_secret_rotation_does_not_break_silently() -> None:
    """Stripe sends both signatures during a rotation. Reading the first only breaks the new one."""
    old = sign("whsec_the_old_one", BODY, at=NOW)
    new = sign(SECRET, BODY, at=NOW)
    both = f"{old},{new.partition(',')[2]}"

    assert verify(SECRET, BODY, both, at=NOW) is None
    assert both.count("v1=") == 2, "the header under test must really carry two signatures"


def test_an_empty_secret_cannot_be_used_to_sign_either() -> None:
    with pytest.raises(SecretMissing, match="cannot sign with an empty secret"):
        sign("", BODY, at=NOW)
