"""One authenticated call to Stripe, so the key is used in one place and the version is pinned once.

WHAT: `call(path, api_key, ...)` performs one Stripe API request and returns the parsed object.
      `encode(params)` is Stripe's bracket form encoding. `PaymentsFailed` carries the call and
      what Stripe said about it.
WHY:  **NO STRIPE SDK, AND THE DEPENDENCY COUNT STAYS AT ZERO.** `pyproject.toml` declares
      `dependencies = []`. What this needs is a form-encoded POST and an HMAC compare; the SDK
      would arrive with its own HTTP client, its own retry policy and its own telemetry, in a
      product whose deployment story includes air-gapped. `serve/listener.py` makes the same
      argument for the HTTP server and it is stronger here.

      **THE COST OF THAT IS THE VERSION PIN, SO IT IS PAID EXPLICITLY.** An SDK pins the API
      version for you; nothing else does. Without `Stripe-Version` the account's default applies,
      and Stripe changing that default silently changes the shape of every object this product
      reads -- a breakage with no deploy behind it and nothing in our history to point at.

      **`permit()` IS CALLED BEFORE THE SOCKET OPENS.** An air-gapped deployment refuses Stripe
      rather than timing out against it: an outbound call to a payment processor from inside a
      bank's network is a finding against us whether or not it succeeds.
      `scripts/guard/runtime/check_network_chokepoint.py` fails the build if this line is removed.

      **IT RAISES ON EVERY NON-2XX, AND CARRIES STRIPE'S OWN SENTENCE.** Stripe's error bodies say
      exactly what was wrong -- "No such price", "a subscription requires a recurring price" -- and
      collapsing that into "payment failed" throws away the only text that tells an operator
      whether the fault is our code or their configuration. Returning a value on failure is how a
      broken call becomes a quiet no-op, which this project has already paid for four times.

      **THE KEY IS A PARAMETER AND IS NEVER READ FROM `Settings`.** `types/settings.py` states the
      rule -- *"a credential in a settings object reaches a log or a config dump the first time
      anybody prints one"* -- and `quantamind config` prints that object. It is read in
      `serve/commands/run_endpoint.py` beside the webhook secret and passed down.
IMPORTS: stdlib (json, urllib) and `types.deployment`. Leftward only; nothing from `store`.
CONSUMED BY: `ingest/payments/checkout.py`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from quantamind.types.deployment import Destination, permit

BASE = "https://api.stripe.com"
TIMEOUT_S = 30

API_VERSION = "2026-08-26.dahlia"
"""**PINNED, AND READ OFF THE ACCOUNT RATHER THAN CHOSEN.** This is the version the QuantaMind
account answered with on 2026-09-17, taken from a real `Stripe-Version` response header. Moving it
is a deliberate act with a live test behind it, not something Stripe does to us on a Tuesday."""


class PaymentsFailed(RuntimeError):
    """A Stripe call that did not return 2xx. Carries the call and Stripe's own words."""

    def __init__(self, method: str, path: str, reason: str) -> None:
        super().__init__(f"{method} {path}: {reason}")
        self.method, self.path, self.reason = method, path, reason


def encode(params: dict[str, Any], prefix: str = "") -> list[tuple[str, str]]:
    """Stripe's bracket form encoding, flattened to pairs.

    `{"line_items": [{"price": "p", "quantity": 2}]}` becomes
    `line_items[0][price]=p&line_items[0][quantity]=2`. Stripe takes no JSON request bodies on the
    v1 API, so this is not a style choice.

    **A `None` VALUE IS DROPPED, AND `False` IS NOT.** Stripe reads the string "None" as a value
    and `False` as a meaningful boolean, so the two cannot share a branch -- an omitted optional
    and a deliberate false would otherwise both arrive as text.
    """
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        name = f"{prefix}[{key}]" if prefix else key
        if value is None:
            continue
        if isinstance(value, dict):
            pairs.extend(encode(value, name))
        elif isinstance(value, list | tuple):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    pairs.extend(encode(item, f"{name}[{index}]"))
                else:
                    pairs.append((f"{name}[{index}]", str(item)))
        elif isinstance(value, bool):
            pairs.append((name, "true" if value else "false"))
        else:
            pairs.append((name, str(value)))
    return pairs


def _reason(body: bytes, status: int) -> str:
    """Stripe's own message, or the raw body when it is not the error shape we expect.

    **THE FALLBACK RETURNS THE BODY, NOT A PLACEHOLDER.** A gateway's HTML error page is not JSON
    and is exactly the case where an operator needs to see what actually came back.
    """
    try:
        parsed = json.loads(body)
        error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(error, dict):
            said = str(error.get("message") or "")
            code = str(error.get("code") or error.get("type") or "")
            return f"HTTP {status}: {said}" + (f" [{code}]" if code else "")
    except json.JSONDecodeError:
        pass
    return f"HTTP {status}: {body[:400].decode('utf-8', 'replace')}"


def call(
    path: str,
    *,
    api_key: str,
    method: str = "POST",
    params: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """One Stripe request. The parsed object on 2xx, `PaymentsFailed` on anything else.

    `idempotency_key` is Stripe's own retry protection: the same key replays the first response
    rather than creating a second subscription. **It is a parameter and not generated here** --
    a key this function invented would differ on every retry, which is the same as having none.
    """
    if not api_key.strip():
        raise PaymentsFailed(
            method,
            path,
            "no Stripe API key was given. This is a refusal rather than an unauthenticated "
            "attempt: an unauthenticated call to a payments API is never the right answer",
        )
    permit(Destination.PAYMENTS)
    body = urllib.parse.urlencode(encode(params or {})).encode()
    request = urllib.request.Request(
        f"{BASE}/{path.lstrip('/')}",
        data=body if method != "GET" else None,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Stripe-Version": API_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "quantamind",
            **({"Idempotency-Key": idempotency_key} if idempotency_key else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            answered = response.read()
    except urllib.error.HTTPError as exc:
        raise PaymentsFailed(method, path, _reason(exc.read(), exc.code)) from None
    except urllib.error.URLError as exc:
        raise PaymentsFailed(method, path, f"could not reach Stripe: {exc.reason}") from None
    except TimeoutError:
        raise PaymentsFailed(method, path, f"Stripe did not answer within {TIMEOUT_S}s") from None

    try:
        parsed: Any = json.loads(answered)
    except json.JSONDecodeError as exc:
        raise PaymentsFailed(method, path, f"Stripe answered 2xx with non-JSON: {exc}") from None
    if not isinstance(parsed, dict):
        raise PaymentsFailed(method, path, f"expected an object, got {type(parsed).__name__}")
    # A dict of str to anything: Stripe's objects are heterogeneous and the caller reads the
    # fields it named. Narrowing further here would be inventing a schema we do not own.
    return parsed
