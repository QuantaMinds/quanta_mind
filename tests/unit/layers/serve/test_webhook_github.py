"""The only untrusted input the product accepts, tested as the attacker would probe it.

WHAT: Authentic deliveries, forged ones, malformed signatures, a missing secret, and every payload
      shape that must NOT become a review.
WHY:  Everything else the product reads comes from git or a repository we were pointed at. This
      arrives from the network from anyone who finds the URL, so the two dangerous decisions — is
      this really GitHub, is this ours to act on — are pure functions and are tested exhaustively.

      **The missing-secret case is the one that matters most.** "No secret configured, so accept
      everything" reads as working perfectly in every test that supplies a secret, and turns the
      endpoint into an open command channel.
IMPORTS: quantamind.serve.webhook_github.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.serve.webhook_github import (
    PREFIX,
    Ignore,
    MisconfiguredSecret,
    Rejected,
    Review,
    interpret,
    sign,
    verify,
)

SECRET = "s3cr3t-not-a-real-one"
BODY = b'{"action":"opened"}'


def _pull_payload(**over: object) -> bytes:
    payload: dict[str, object] = {
        "action": "opened",
        "repository": {"full_name": "acme/widgets"},
        "pull_request": {"number": 42, "draft": False, "head": {"sha": "deadbeef" * 5}},
    }
    payload.update(over)
    return json.dumps(payload).encode()


def test_an_authentic_delivery_is_accepted_and_a_forged_one_is_not() -> None:
    """Acceptance alone proves nothing: a verify() that always returned None would pass it."""
    authentic = sign(SECRET, BODY)
    assert verify(SECRET, BODY, authentic) is None
    forged = PREFIX + ("0" * 64)
    assert verify(SECRET, BODY, forged) is Rejected.BAD_SIGNATURE, (
        "the same call must reject a wrong digest, or it is not checking anything"
    )


def test_a_body_altered_after_signing_is_rejected() -> None:
    """The whole point: the signature covers the bytes, not the headers."""
    signature = sign(SECRET, BODY)
    assert verify(SECRET, BODY + b" ", signature) is Rejected.BAD_SIGNATURE


def test_a_signature_from_a_different_secret_is_rejected() -> None:
    assert verify(SECRET, BODY, sign("someone-elses-secret", BODY)) is Rejected.BAD_SIGNATURE


def test_a_missing_secret_raises_rather_than_accepting_everything() -> None:
    """An endpoint that verifies nothing when the secret is absent is an open command channel."""
    with pytest.raises(MisconfiguredSecret) as caught:
        verify("", BODY, sign(SECRET, BODY))
    assert "unverified" in str(caught.value) or "no delivery can be authenticated" in str(
        caught.value
    )


def test_the_rejection_reasons_are_distinct_because_they_need_distinct_responses() -> None:
    assert verify(SECRET, BODY, None) is Rejected.NO_SIGNATURE
    assert verify(SECRET, BODY, "deadbeef") is Rejected.MALFORMED_SIGNATURE
    assert verify(SECRET, BODY, "sha256=short") is Rejected.MALFORMED_SIGNATURE
    assert verify(SECRET, BODY, "sha256=" + "z" * 64) is Rejected.MALFORMED_SIGNATURE
    assert verify(SECRET, BODY, sign("other", BODY)) is Rejected.BAD_SIGNATURE


def test_an_uppercase_digest_still_verifies() -> None:
    """GitHub sends lowercase, but a proxy that upcases it must not look like a forgery."""
    signature = sign(SECRET, BODY)
    upper = signature.upper().replace("SHA256=", "sha256=")
    assert upper != signature, "the fixture must actually differ, or this tests nothing"
    assert verify(SECRET, BODY, upper) is None
    assert verify(SECRET, BODY + b"x", upper) is Rejected.BAD_SIGNATURE


def test_a_pull_request_opened_becomes_a_review() -> None:
    got = interpret("pull_request", _pull_payload())
    assert isinstance(got, Review)
    assert (got.repo, got.number) == ("acme/widgets", 42)


def test_an_event_we_do_not_act_on_is_ignored_with_a_reason() -> None:
    """The first version asserted `(A and B) or isinstance(got, Ignore)` — true whenever the last
    clause is, so it would have passed with an empty reason."""
    for event in ("ping", "issues", "push", None):
        got = interpret(event, _pull_payload())
        assert isinstance(got, Ignore), f"{event!r} must not become a review"
        assert repr(event) in got.reason, (
            f"the reason must name the event dropped, got {got.reason!r}"
        )


def test_an_action_that_does_not_change_the_code_is_ignored() -> None:
    for action in ("labeled", "assigned", "closed", "edited"):
        got = interpret("pull_request", _pull_payload(action=action))
        assert isinstance(got, Ignore), f"{action} must not trigger a review"
        assert action in got.reason


def test_a_draft_is_ignored() -> None:
    payload = json.loads(_pull_payload())
    payload["pull_request"]["draft"] = True
    got = interpret("pull_request", json.dumps(payload).encode())
    assert isinstance(got, Ignore) and "draft" in got.reason


def test_a_malformed_payload_is_ignored_rather_than_crashing_the_endpoint() -> None:
    expected = {
        b"not json": "not JSON",
        b"[]": "list, not an object",
        b"{}": "does not change the code",
        b'{"action":"opened"}': "no pull_request or repository",
    }
    for body, fragment in expected.items():
        got = interpret("pull_request", body)
        assert isinstance(got, Ignore), f"{body!r} must not become a review"
        assert fragment in got.reason, (
            f"{body!r} should say {fragment!r}, said {got.reason!r} — an ignore whose reason does "
            "not name the problem is the same as silence"
        )
