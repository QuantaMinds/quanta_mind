"""Verify a GitHub webhook, decide whether it is ours to act on, and say what to do with it.

WHAT: `verify()` authenticates a delivery against the shared secret, and `interpret()` turns an
      authenticated payload into a decision — review this pull request, or ignore it and why.
WHY:  **This is the only untrusted input the product accepts.** Everything else comes from git or
      from a repository we were pointed at; this arrives from the network from anyone who finds the
      URL. So the two dangerous decisions — is this really GitHub, and is this ours to act on —
      are pure functions over bytes, testable exhaustively without a socket.

      **An absent secret RAISES. It does not skip verification.** "No secret configured, so accept
      everything" is how a webhook endpoint becomes an open command channel, and it is the default
      that reads as working perfectly in every test that supplies a secret.

      **The comparison is constant-time, and NO TEST CAN SEE THAT.** Replacing `compare_digest`
      with `==` leaves every test in `tests/unit/test_webhook_github.py` passing — verified by doing
      it. A byte-by-byte compare leaks the expected digest through response timing, which is a slow
      but real forgery path, and the only things protecting it are this sentence and code review.
      It is written down because a property nothing checks is a property that erodes.

      **A signature we cannot parse is a rejection, never a pass.** Missing header, wrong prefix,
      odd length, non-hex — each is a distinct reason, returned rather than collapsed into False,
      because "someone is probing us" and "our own secret is misconfigured" need different
      responses from an operator.
IMPORTS: types (Settings). Nothing to its right; this is the rightmost layer.
CONSUMED BY: the HTTP binding, and nothing else — the decisions here are testable without one.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

SIGNATURE_HEADER = "X-Hub-Signature-256"
EVENT_HEADER = "X-GitHub-Event"
PREFIX = "sha256="
DIGEST_HEX_LEN = 64
# The only event that can produce a review. Everything else is acknowledged and dropped.
REVIEWABLE_EVENT = "pull_request"
REVIEWABLE_ACTIONS = frozenset({"opened", "synchronize", "reopened", "ready_for_review"})


class Rejected(Enum):
    """Why a delivery was not accepted. Distinct values because they need distinct responses."""

    NO_SIGNATURE = "no signature header"
    MALFORMED_SIGNATURE = "signature is not sha256=<64 hex chars>"
    BAD_SIGNATURE = "signature does not match the body"


class MisconfiguredSecret(RuntimeError):
    """No webhook secret is configured.

    Raised rather than accepting the delivery. An endpoint that verifies nothing when the secret is
    missing is an open command channel, and every test that supplies a secret passes anyway — which
    is why this is an exception and not a `False`.
    """


@dataclass(frozen=True, slots=True)
class Review:
    """A delivery we should act on."""

    repo: str
    number: int
    head_sha: str


@dataclass(frozen=True, slots=True)
class Ignore:
    """A delivery that authenticated and is not ours to act on. Carries why, for the log."""

    reason: str


def verify(secret: str, body: bytes, signature: str | None) -> Rejected | None:
    """None when the delivery is authentic, otherwise why it was rejected.

    `secret` empty raises: see `MisconfiguredSecret`.
    """
    if not secret:
        raise MisconfiguredSecret(
            "no webhook secret is configured, so no delivery can be authenticated. Refusing to "
            "accept unverified input; set the secret rather than running without one"
        )
    if not signature:
        return Rejected.NO_SIGNATURE
    if not signature.startswith(PREFIX):
        return Rejected.MALFORMED_SIGNATURE
    offered = signature[len(PREFIX) :]
    if len(offered) != DIGEST_HEX_LEN or any(c not in "0123456789abcdefABCDEF" for c in offered):
        return Rejected.MALFORMED_SIGNATURE
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # Constant-time: a byte-by-byte compare leaks the expected digest through response timing.
    return None if hmac.compare_digest(expected, offered.lower()) else Rejected.BAD_SIGNATURE


def sign(secret: str, body: bytes) -> str:
    """The header GitHub would send for this body. Used by tests to build authentic deliveries."""
    if not secret:
        raise MisconfiguredSecret("cannot sign with an empty secret")
    return PREFIX + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def interpret(event: str | None, body: bytes) -> Review | Ignore:
    """What to do with an AUTHENTICATED delivery. Never called before `verify()` returns None.

    Returns `Ignore` with a reason rather than raising: a ping, a label change and a comment are all
    normal traffic, and an endpoint that errors on them fills a log with things nobody should read.
    """
    if event != REVIEWABLE_EVENT:
        return Ignore(f"event {event!r} is not {REVIEWABLE_EVENT!r}")
    try:
        payload: Any = json.loads(body)
    except json.JSONDecodeError as exc:
        return Ignore(f"body is not JSON: {exc}")
    if not isinstance(payload, dict):
        return Ignore(f"body is {type(payload).__name__}, not an object")

    action = str(payload.get("action") or "")
    if action not in REVIEWABLE_ACTIONS:
        return Ignore(f"action {action!r} does not change the code under review")

    pull = payload.get("pull_request")
    repository = payload.get("repository")
    if not isinstance(pull, dict) or not isinstance(repository, dict):
        return Ignore("payload carried no pull_request or repository object")
    if pull.get("draft") is True:
        return Ignore("the pull request is a draft")

    repo = str(repository.get("full_name") or "")
    number = pull.get("number")
    head_sha = str((pull.get("head") or {}).get("sha") or "")
    if not repo or not isinstance(number, int) or not head_sha:
        return Ignore(f"incomplete payload: repo={repo!r} number={number!r} head={head_sha[:8]!r}")
    return Review(repo=repo, number=number, head_sha=head_sha)
