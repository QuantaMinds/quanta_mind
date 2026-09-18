"""`POST /entitlement` — the billing service tells us what an account is entitled to.

WHAT: `answer(body, authorization, secret, settings)` validates one push, records it, and replies
      with the row READ BACK from the database rather than with what the caller sent.
WHY:  **IT IS `provision_route.py`'s TWIN, DELIBERATELY.** Same bearer check with
      `hmac.compare_digest`, same refusal when the secret is unset, same `answer`/`for_request`
      split so every rule is testable without a socket. One shape for both, so a reader who has
      understood one has understood the other.

      **THE REPLY IS READ BACK FROM THE STORE, AND THAT IS NOT CEREMONY.** The store is a SQLite
      file on a Cloud Storage FUSE mount with no file locking, and during a revision rollout the
      old and new instances briefly both run — Google's own wording for that filesystem is that
      "the last write wins and all previous writes are lost". A push that lands in that window can
      vanish with a 200 already sent. Echoing what the caller sent would confirm nothing; echoing
      what the database now holds lets the caller compare and re-queue. `store/drift.py` does the
      same thing after a migration for the same reason: verify, do not intend.

      **AN UNSET SECRET REFUSES THE ROUTE, IT DOES NOT OPEN IT.** "Not configured" and "no
      authentication required" are one code path in most handlers and must not be here — the same
      argument `types/deployment.permit()` makes about an unrecognised deployment shape.

      **IT WRITES ENTITLEMENT AND NOTHING ELSE.** No provisioning, no warming, no clone. A push
      arrives on every subscription change, including ones that change nothing we act on, and a
      route that cloned on each would turn a billing webhook into a fleet of git operations.
IMPORTS: serve.web.http_io, store.billing.entitlement, store.{schema,tenancy}. Leftward only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import hmac
import json
from pathlib import Path
from typing import Any

from quantamind.serve.web.http_io import read_body
from quantamind.store import tenancy
from quantamind.store.billing import entitlement
from quantamind.store.schema import open_store

PATH = "/entitlement"
AUTH_HEADER = "Authorization"
BEARER = "Bearer "

NOT_CONFIGURED = (
    "entitlement pushes are not configured on this deployment: QUANTAMIND_PROVISION_SECRET is "
    "unset. The route refuses rather than opening, because 'not configured' and 'no "
    "authentication required' must not be the same answer."
)

# Every state the billing service may assert. An unknown one is refused at the door rather than
# stored: `entitlement.covering` would read it back as NONE, silently downgrading a paid account
# to Free with a 200 already sent and nothing anywhere recording why.
STATES = {one.value: one for one in entitlement.State}


def _authorised(header: str | None, secret: str) -> bool:
    """Constant-time bearer check. **False when the secret is unset**, never True by omission."""
    if not secret.strip():
        return False
    given = header or ""
    if not given.startswith(BEARER):
        return False
    return hmac.compare_digest(given[len(BEARER) :], secret)


def _parse(body: bytes) -> dict[str, Any] | str:
    """The push as a mapping, or a sentence saying why it could not be read."""
    try:
        loaded = json.loads(body or b"null")
    except json.JSONDecodeError as exc:
        return f"body is not JSON: {exc}"
    if not isinstance(loaded, dict):
        return f"body is {type(loaded).__name__}, not an object"
    for required in ("forge", "account", "tier", "state", "as_of"):
        if required not in loaded:
            return f"push names no {required}"
    if str(loaded["state"]) not in STATES:
        return f"unknown state {loaded['state']!r}; known: {', '.join(sorted(STATES))}"
    if not isinstance(loaded["as_of"], int):
        return "as_of must be an integer unix time"
    return loaded


def _int_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, int) else None


def answer(
    body: bytes, authorization: str | None, secret: str, settings: Any
) -> tuple[int, dict[str, Any]]:
    """Record one entitlement push. Returns the status and the row as the store now holds it."""
    if not secret.strip():
        return 503, {"error": NOT_CONFIGURED}
    if not _authorised(authorization, secret):
        return 401, {"error": "bad or missing bearer token"}

    parsed = _parse(body)
    if isinstance(parsed, str):
        return 400, {"error": parsed}

    forge, account = str(parsed["forge"]), str(parsed["account"])
    conn = open_store(tenancy.shared(Path(settings.database_path), tenancy.ACCOUNTS))
    try:
        try:
            entitlement.record(
                conn,
                forge,
                account,
                tier=str(parsed["tier"]),
                state=STATES[str(parsed["state"])],
                as_of=int(parsed["as_of"]),
                seats_included=_int_or_none(parsed.get("seats_included")),
                payment_ref=str(parsed.get("payment_ref") or ""),
                reason=str(parsed.get("reason") or ""),
                valid_through=_int_or_none(parsed.get("valid_through")),
                grace_until=_int_or_none(parsed.get("grace_until")),
            )
        except ValueError as exc:
            return 400, {"error": str(exc)}
        # READ BACK, never echoed. See the module docstring.
        stored = entitlement.covering(conn, forge, account, now=int(parsed["as_of"]))
    finally:
        conn.close()

    print(
        f"[serve] entitlement {forge}/{account}: {stored.tier} ({stored.state.value})", flush=True
    )
    return 200, {
        "forge": forge,
        "account": account,
        "stored": {
            "tier": stored.tier,
            "state": stored.state.value,
            "seats_included": stored.seats_included,
            "as_of": stored.as_of,
            "valid_through": stored.valid_through,
            "grace_until": stored.grace_until,
        },
    }


def for_request(handler: Any) -> tuple[int, dict[str, Any]]:
    """Adapt the socket handler to `answer`, which is the part worth testing."""
    body, why = read_body(handler)
    if body is None:
        return 411, {"error": why}
    return answer(
        body,
        handler.headers.get(AUTH_HEADER),
        getattr(handler, "provision_secret", ""),
        handler.settings,
    )
