"""`POST /billing/webhook` — authenticate a Stripe delivery, refuse a replay, record the state.

WHAT: `answer(body, signature, ...)` returns `(status, payload)`. `for_request(handler)` reads one
      POST off the wire and calls it.
WHY:  **AUTHENTICATE, CLAIM, THEN WRITE — THE ORDER `serve/listener.py` ALREADY ARGUES FOR.**
      Nothing here treats the body as a document until `serve/webhook_stripe.verify` has passed on
      the exact bytes. Parsing first would run an untrusted document through a parser for anyone
      who can reach the port, and re-serialising to check a signature is how an authentic delivery
      starts failing.

      **A REPLAY IS REFUSED BY THE SAME LEDGER GITHUB'S DELIVERIES USE.** Stripe retries one event
      for three days and reuses its id, so a finished event must not be applied twice and an
      unfinished one must stay retryable. The tolerance in `verify()` bounds the window; it does
      not make a delivery single-use, and conflating the two is how a webhook that looks protected
      is not.

      **AN UNMATCHED SUBSCRIPTION IS ANSWERED 200, AND THAT IS NOT A SHRUG.** A subscription
      created by hand in the Dashboard carries no `metadata.account`. Answering non-2xx makes
      Stripe retry for three days something that will never match; answering 200 silently would
      lose a payment we took. So it is printed with the subscription id in it, and the reply names
      it as unmatched rather than as handled.

      **A STALE, OUT-OF-ORDER DELIVERY IS ALSO 200, AND ALSO NOT SILENT.** `store/subscriptions`
      refuses to let an older event overwrite a newer one and returns why. That refusal is a
      correct outcome, not a failure, so Stripe must not retry it -- but an operator must be able
      to see it happened, so it is printed and carried in the reply.

      **THE DELIVERY IS COMPLETED ONLY AFTER THE ROW IS WRITTEN.** If the write raises, the ledger
      row has no `completed_at` and Stripe's retry is a legitimate second attempt rather than a
      replay. Same shape, same reason, as the GitHub path.
IMPORTS: serve.{webhook_stripe,stripe_event}, store.{deliveries,schema,subscriptions,tenancy}.
      Leftward and same-layer public surface only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from quantamind.serve.stripe_event import Ignore, interpret
from quantamind.serve.web.http_io import read_body
from quantamind.serve.webhook_stripe import SIGNATURE_HEADER, verify
from quantamind.store import deliveries, tenancy
from quantamind.store.billing import subscriptions
from quantamind.store.schema import open_store

PATH = "/billing/webhook"

NOT_CONFIGURED = (
    "billing is not configured on this deployment: QUANTAMIND_STRIPE_WEBHOOK_SECRET is unset. "
    "The route refuses rather than accepting unverified input."
)


def _event_id(body: bytes) -> str:
    """Stripe's event id, for the replay ledger. Empty when the body does not carry one.

    **READ AFTER VERIFICATION, NEVER BEFORE.** It is taken from a body whose signature has already
    matched, so parsing it here is reading a document we have authenticated rather than one an
    attacker sent.
    """
    try:
        parsed: Any = json.loads(body)
    except json.JSONDecodeError:
        return ""
    return str(parsed.get("id") or "") if isinstance(parsed, dict) else ""


def answer(
    body: bytes,
    signature: str | None,
    *,
    secret: str,
    settings: Any,
    at: int | None = None,
) -> tuple[int, dict[str, Any]]:
    """Authenticate one delivery and record what it says. Never raises to the socket."""
    if not secret.strip():
        return 503, {"error": NOT_CONFIGURED}

    moment = int(time.time()) if at is None else at
    refused = verify(secret, body, signature, at=moment)
    if refused is not None:
        print(f"[billing] refused a delivery: {refused.sentence()}", flush=True)
        return 401, {"error": refused.reason.value, "detail": refused.detail}

    event_id = _event_id(body)
    if not event_id:
        return 400, {"error": "the delivery authenticated but carries no event id"}

    root = Path(settings.database_path)
    ledger = open_store(tenancy.shared(root, tenancy.DELIVERIES))
    try:
        try:
            fresh = deliveries.begin(ledger, event_id, "stripe")
        except ValueError as exc:
            return 400, {"error": str(exc)}
        if not fresh:
            # **PRINTED, NOT ONLY RETURNED.** The body goes to Stripe, which discards it, so an
            # operator watching the log saw a bare 200 and could not tell a refused replay from an
            # applied delivery. `serve/listener.py` learned this on the `Ignore` branch; the same
            # gap was reintroduced here and found by resending a real event.
            print(f"[billing] replay of {event_id} refused: already completed", flush=True)
            return 200, {"replay": event_id, "note": "already completed, not applied twice"}

        decision = interpret(body)
        if isinstance(decision, Ignore):
            print(f"[billing] ignored {event_id}: {decision.reason}", flush=True)
            deliveries.complete(ledger, event_id)
            return 200, {"ignored": decision.reason, "event": event_id}

        store = open_store(tenancy.shared(root, tenancy.ACCOUNTS))
        try:
            written = subscriptions.record(store, decision)
        finally:
            store.close()
        deliveries.complete(ledger, event_id)
    finally:
        ledger.close()

    if not written.stored:
        # Correct, and not a failure: see the module docstring on out-of-order deliveries.
        print(f"[billing] {event_id} not applied: {written.reason}", flush=True)
        return 200, {
            "event": event_id,
            "account": decision.account,
            "applied": False,
            "reason": written.reason,
        }

    print(f"[billing] {event_id}: {decision.sentence()}", flush=True)
    return 200, {
        "event": event_id,
        "account": decision.account,
        "applied": True,
        "standing": decision.standing.value,
        "paid": decision.paid,
        "paid_through": decision.current_period_end,
    }


def for_request(handler: Any) -> tuple[int, dict[str, Any]]:
    """Read one POST off the wire and answer it. Mirrors `provision_route.for_request`."""
    given, why = read_body(handler)
    if given is None:
        return 411, {"error": why}
    return answer(
        given,
        handler.headers.get(SIGNATURE_HEADER),
        secret=str(getattr(handler, "stripe_webhook_secret", "")),
        settings=handler.settings,
    )
