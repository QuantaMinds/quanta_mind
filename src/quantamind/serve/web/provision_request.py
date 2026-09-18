"""Turn a provisioning URL, a bearer header and a request body into values, or into a refusal.

WHAT: `tier_named(path)` reads the tier out of the URL; `authorised(header, secret)` is the
      constant-time bearer check; `parse(body)` returns a `verify/tier_request.Request` or one
      sentence saying why the body is not one.
WHY:  **SPLIT OUT WHEN `serve/web/provision_route.py` PASSED THE 200-LINE CAP A SECOND TIME.**
      `AGENTS.md` rule 4: split by concern, do not raise the cap. The concern is *reading the
      request* -- which tier, is the caller allowed, and what did they actually send. What is left
      in the route is the decision and the write.

      **AN UNSET SECRET RETURNS FALSE, AND THAT IS THE WHOLE REASON THIS IS ITS OWN FUNCTION.**
      "Not configured" and "no authentication required" are the same code path in most handlers
      and must not be here. The route also refuses with a 503 before ever calling this, and the
      pair is deliberate: a check that runs only where it cannot fail is indistinguishable from
      one that does nothing, so `authorised` is false on an empty secret in its own right.

      **THE COMPARISON IS CONSTANT-TIME AND NO TEST CAN SEE THAT.** `==` on a secret stops at the
      first differing byte and leaks it to anyone who can time the response, and every assertion
      about this function passes either way. `scripts/guard/runtime/check_constant_time_compare.py`
      is what actually holds it.

      **AN UNKNOWN TIER IS None, NEVER A DEFAULT.** The route turns that into a 404. A default here
      would hand somebody a tier by misspelling one.
IMPORTS: stdlib (hmac, json), and `verify/tier_request.py`. Leftward only.
CONSUMED BY: `serve/web/provision_route.py`.
"""

from __future__ import annotations

import hmac
import json
from typing import Any

from quantamind.verify.tier_request import Request, Tier

PREFIX = "/provision/"
AUTH_HEADER = "Authorization"
BEARER = "Bearer "


def tier_named(path: str) -> Tier | None:
    """The tier from the URL, or None. An unknown segment is a 404, never a default."""
    wanted = path.partition("?")[0][len(PREFIX) :].strip("/")
    return next((tier for tier in Tier if tier.value == wanted), None)


def authorised(header: str | None, secret: str) -> bool:
    """Constant-time bearer check. **False when the secret is unset**, never True by omission."""
    if not secret.strip():
        return False
    given = header or ""
    if not given.startswith(BEARER):
        return False
    return hmac.compare_digest(given[len(BEARER) :], secret)


def parse(body: bytes) -> Request | str:
    """A `Request`, or one sentence saying why the body is not one."""
    try:
        raw: Any = json.loads(body)
    except json.JSONDecodeError as exc:
        return f"body is not JSON: {exc}"
    if not isinstance(raw, dict):
        return f"body is {type(raw).__name__}, not an object"
    repos = raw.get("repos")
    if not isinstance(repos, list) or not all(isinstance(name, str) for name in repos):
        return "repos must be a list of 'owner/name' strings"
    return Request(
        account=str(raw.get("account") or ""),
        repos=tuple(repos),
        seats=int(raw.get("seats") or 0),
        payment_ref=str(raw.get("payment_ref") or ""),
        org=str(raw.get("org") or ""),
    )
