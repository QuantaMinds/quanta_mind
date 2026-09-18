"""Prove a delivery came from Stripe, inside a window, or say exactly why it did not.

WHAT: `verify(secret, body, signature, at)` returns None when a delivery is authentic and a
      `Refusal` when it is not. `sign()` builds the header Stripe would send, for tests.
WHY:  **THIS IS THE SECOND UNTRUSTED INPUT THE PRODUCT ACCEPTS, AND THE FIRST THAT MOVES MONEY.**
      `serve/webhook_github.py` makes the argument for the shape -- verify bytes before parsing,
      constant-time compare, an unset secret RAISES rather than accepting -- and every line of it
      applies here. What is different is worth having:

      **STRIPE SIGNS A TIMESTAMP AND GITHUB DOES NOT.** `serve/webhook_github.py` says so in its own
      docstring: *"a captured delivery stays valid forever... there is no timestamp in it, unlike
      Stripe's."* Stripe signs `f"{t}.{body}"`, so a captured delivery expires. This closes a gap
      the GitHub path cannot close, and it is the reason `TOLERANCE_S` exists at all.

      **THE TOLERANCE IS A CEILING ON CLOCK SKEW, NOT A GUESS, AND A BREACH NAMES THE SKEW.** A
      container whose clock is six minutes out rejects every genuine delivery, and the symptom is
      identical to a wrong secret -- an operator would rotate the secret, change nothing, and still
      be down. So the refusal carries the measured difference in seconds and says which direction.

      **A FUTURE TIMESTAMP IS REFUSED TOO, AND A NAIVE CHECK ADMITS IT.** `now - t < TOLERANCE` is
      true for every timestamp in the future, however far. The comparison is on the absolute value.

      **EVERY `v1` IS COMPARED, NOT THE FIRST.** During a secret rotation Stripe sends two
      signatures in one header. Reading only the first breaks rotation silently, and only for the
      customer who rotates -- which is to say, only in production.

      **VERIFICATION IS STILL NOT REPLAY PROTECTION.** The tolerance bounds the window; inside it a
      delivery can arrive twice, and Stripe legitimately retries the same event for three days.
      `store/deliveries.py` keyed on the event id is what makes a retry a retry, and the caller must
      use it. This module does not, because the store is to its LEFT.

      **READING THE PAYLOAD IS A DIFFERENT CONCERN AND LIVES NEXT DOOR.** `serve/stripe_event.py`
      turns an authenticated body into a subscription. This module never parses JSON at all: the
      HMAC covers exact bytes, and a module that both authenticates and deserialises invites a
      reader to do the second before the first.
IMPORTS: stdlib only (hashlib, hmac, dataclasses, enum). Nothing to its right, nothing to its left.
CONSUMED BY: `serve/web/billing_route.py`, and nothing else -- the decision here needs no socket.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from enum import Enum

SIGNATURE_HEADER = "Stripe-Signature"
TIMESTAMP_KEY = "t"
SIGNATURE_KEY = "v1"
DIGEST_HEX_LEN = 64

TOLERANCE_S = 300
"""How far a delivery's timestamp may be from our clock. **Stripe's own recommended default**, and
a ceiling on skew rather than on latency: five minutes of queueing is not normal, five minutes of
NTP drift on a container is."""


class Reason(Enum):
    """Why a delivery was refused. Distinct values because they need distinct responses."""

    NO_SIGNATURE = "no Stripe-Signature header"
    MALFORMED_SIGNATURE = "Stripe-Signature is not t=<unix>,v1=<64 hex chars>"
    BAD_SIGNATURE = "no v1 signature matches the body"
    TIMESTAMP_OUTSIDE_TOLERANCE = "the signed timestamp is outside the tolerance"


@dataclass(frozen=True, slots=True)
class Refusal:
    """A refused delivery. **Carries the measured detail, because the reason alone misleads.**"""

    reason: Reason
    detail: str = ""

    def sentence(self) -> str:
        return f"{self.reason.value}{f': {self.detail}' if self.detail else ''}"


class SecretMissing(RuntimeError):
    """No Stripe signing secret is configured. **Raised, never treated as 'accept everything'.**

    Same reasoning as `serve/webhook_github.MisconfiguredSecret`: an endpoint that verifies nothing
    when the secret is absent is an open command channel, and every test that supplies a secret
    passes anyway -- which is why this is an exception and not a `False`.
    """


def _parsed_header(signature: str) -> tuple[int | None, list[str]]:
    """The signed timestamp and every `v1` in the header. `None` when it is not the shape."""
    stamp: int | None = None
    offered: list[str] = []
    for part in signature.split(","):
        key, _, value = part.strip().partition("=")
        if key == TIMESTAMP_KEY:
            try:
                stamp = int(value)
            except ValueError:
                return None, []
        elif key == SIGNATURE_KEY:
            offered.append(value)
    return stamp, offered


def verify(secret: str, body: bytes, signature: str | None, *, at: int) -> Refusal | None:
    """None when the delivery is authentic, otherwise why it was refused.

    `at` is the current unix time and is a PARAMETER, not a `time.time()` call. The tolerance is
    the one rule here nothing else can test: with the clock read inside, a test can only ever
    exercise "now", and the two refusals this function exists to make -- too old, and in the
    future -- are unreachable. `serve/web/billing_route.py` passes the real clock.
    """
    if not secret:
        raise SecretMissing(
            "no Stripe signing secret is configured, so no delivery can be authenticated. "
            "Refusing to accept unverified input; set the secret rather than running without one"
        )
    if not signature:
        return Refusal(Reason.NO_SIGNATURE)

    stamp, offered = _parsed_header(signature)
    if stamp is None or not offered:
        return Refusal(Reason.MALFORMED_SIGNATURE, f"header was {signature[:80]!r}")
    if any(
        len(one) != DIGEST_HEX_LEN or any(c not in "0123456789abcdefABCDEF" for c in one)
        for one in offered
    ):
        return Refusal(Reason.MALFORMED_SIGNATURE, "a v1 value is not 64 hex characters")

    # **ABSOLUTE VALUE. `at - stamp < TOLERANCE_S` ADMITS EVERY FUTURE TIMESTAMP.**
    skew = at - stamp
    if abs(skew) > TOLERANCE_S:
        return Refusal(
            Reason.TIMESTAMP_OUTSIDE_TOLERANCE,
            f"signed at {stamp}, our clock says {at} -- {abs(skew)}s "
            f"{'old' if skew > 0 else 'in the future'}, tolerance is {TOLERANCE_S}s. "
            f"A clock this far out refuses every genuine delivery and looks exactly like a "
            f"wrong secret, so check NTP before rotating anything",
        )

    expected = hmac.new(secret.encode(), f"{stamp}.".encode() + body, hashlib.sha256).hexdigest()
    # Constant-time, and EVERY offered signature: two arrive during a secret rotation.
    if any(hmac.compare_digest(expected, one.lower()) for one in offered):
        return None
    return Refusal(Reason.BAD_SIGNATURE, f"{len(offered)} v1 signature(s) offered, none matched")


def sign(secret: str, body: bytes, *, at: int) -> str:
    """The header Stripe would send for this body at this time. Used by tests to build deliveries.

    **A TEST SUITE THAT ONLY EVER VERIFIES WHAT THIS PRODUCED HAS TESTED ITSELF.** The live test
    must put a real Stripe delivery through `verify()`; this exists for the cases a real delivery
    cannot produce on demand -- a forged signature, a stale timestamp, a rotation with two `v1`s.
    """
    if not secret:
        raise SecretMissing("cannot sign with an empty secret")
    digest = hmac.new(secret.encode(), f"{at}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={at},v1={digest}"
