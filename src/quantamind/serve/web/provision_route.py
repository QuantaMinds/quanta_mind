"""`POST /provision/{free,team,enterprise}` — validate a tier, then admit its repositories.

WHAT: `answer(path, body, authorization, secret, settings)` returns `(status, payload)` for the
      three provisioning routes. The reply names what the caller should warm after answering.
WHY:  **THIS ROUTE GRANTS A PAID TIER, SO IT AUTHENTICATES BEFORE IT READS.** An unauthenticated
      POST that sets `tier=enterprise` is not a provisioning endpoint, it is a free upgrade for
      anyone who can reach the port. The bearer token is compared with `hmac.compare_digest` for the
      same reason `serve/webhook_github.verify` does: `==` on a secret stops at the first differing
      byte and leaks it to anyone who can time the response.

      **AN UNSET SECRET REFUSES THE ROUTE, IT DOES NOT OPEN IT.** "Not configured" and "no
      authentication required" are the same code path in most handlers and must not be here. Same
      shape as `types/deployment.permit()`, which refuses an unrecognised deployment rather than
      reading it as the permissive one.

      **`payment_verified` IS NOW SOMETIMES TRUE, AND ONLY EVER FROM A SIGNED DELIVERY.** Row B3 of
      `docs/plans/roadmap/product-build.md` shipped 2026-09-17. For a paid tier this route reads the
      subscription we hold for the account -- written by `serve/web/stripe_hook.py` from a delivery
      whose HMAC matched -- and asks `verify/paid_access.decide()`. A `payment_ref` in the body is
      still only a string the caller typed and still verifies nothing; the two facts are different
      and the reply distinguishes them.

      **NO SUBSCRIPTION ON RECORD STILL ADMITS ON A REFERENCE, REPORTED UNVERIFIED.** A customer
      invoiced outside Stripe is a real case, and refusing them would make this route unusable for
      exactly the Enterprise tier it serves. What it must never do is call that verified.

      **IT ANSWERS 202, NOT 200.** Warming a repository is a clone plus an index -- about 31 seconds
      on a large one -- and no caller waits. The route validates and records synchronously, replies
      with what it accepted, and the caller warms afterwards. Same acknowledge-then-work shape
      `serve/listener.py` documents for deliveries, for the same reason.

      **NOTHING IS PROVISIONED UNLESS EVERY REPOSITORY PASSES.** A partial provision leaves a
      customer paying for repositories that were not admitted, and no reply shape makes that
      legible.
IMPORTS: verify.{qualification,tier_request}, store.{installations,schema,tenancy}, types.settings.
      Leftward only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from quantamind.serve.web.http_io import read_body
from quantamind.serve.web.provision_payment import access_for, note
from quantamind.serve.web.provision_request import (
    AUTH_HEADER,
    PREFIX,
    authorised,
    parse,
    tier_named,
)
from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store
from quantamind.verify import qualification
from quantamind.verify.tier_request import Tier, admissible

# **DEFINED ONCE, IN THE MODULE THAT READS THEM.** `PREFIX` is re-exported because
# `serve/web/post_routes.py` dispatches on it and has always imported it from here; a second
# literal in two files is how the URL and the parser that strips it drift apart.
__all__ = ["PREFIX", "answer", "for_request"]

NOT_CONFIGURED = (
    "provisioning is not configured on this deployment: QUANTAMIND_PROVISION_SECRET is unset. "
    "The route refuses rather than opening, because 'not configured' and 'no authentication "
    "required' must not be the same answer."
)

NOT_ELIGIBLE = (
    "You are not eligible for the {tier} tier. Every reason is listed in `refused` -- all of them, "
    "not the first, so fixing one does not earn a second refusal."
)


def _free_verdicts(repos: tuple[str, ...], root: Path) -> dict[str, qualification.Verdict]:
    """Eligibility per repository. **A failed read is a refusal, never an assumed pass.**"""
    taken = len(tenancy.tenants(root))
    out: dict[str, qualification.Verdict] = {}
    for name in repos:
        try:
            facts = qualification.facts_for(name)
        except Exception as exc:
            out[name] = qualification.Verdict(False, (f"could not be read: {exc}",))
            continue
        out[name] = qualification.qualifies(facts, owner_already_free=False, repos_taken=taken)
    return out


def answer(
    path: str, body: bytes, authorization: str | None, secret: str, settings: Any
) -> tuple[int, dict[str, Any]]:
    """Validate and record one provisioning request. Returns the status and a JSON body.

    **BOTH `authorization` AND `secret` ARE PARAMETERS, AND NEITHER COMES OFF `settings`.**
    `types/settings.py` refuses to hold the webhook secret for a stated reason -- *"a credential in
    a settings object reaches a log or a config dump the first time anybody prints one"* -- and this
    credential is no different. The request header is a parameter for the mirror-image reason: a
    request value hidden inside a configuration object is how a handler comes to look authenticated
    while reading nothing the caller sent.
    """
    tier = tier_named(path)
    if tier is None:
        return 404, {"error": "no such tier"}

    if not secret.strip():
        return 503, {"error": NOT_CONFIGURED}
    if not authorised(authorization, secret):
        return 401, {"error": "bad or missing bearer token"}

    parsed = parse(body)
    if isinstance(parsed, str):
        return 400, {"error": parsed}

    root = Path(settings.database_path)
    verdicts = _free_verdicts(parsed.repos, root) if tier is Tier.FREE else None
    now = int(time.time())
    # **READ BEFORE ANYTHING IS CREATED.** `access_for` will not open a store that does not exist,
    # so a refused request still leaves no database behind. The first version of this branch opened
    # it here and a test that had been passing for weeks caught it immediately.
    access = access_for(root, parsed.account, tier, at=now)
    verdict = admissible(tier, parsed, free_verdicts=verdicts, access=access)
    if not verdict.admissible:
        return _refused(tier, verdict.reasons)

    made, refused = tenancy.provision(root, list(parsed.repos))
    conn = open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        for name in made:
            installations.record(conn, parsed.account, name, at=now, tier=tier.value, eligible=True)
    finally:
        conn.close()

    return 202, {
        "tier": tier.value,
        "eligible": True,
        "account": parsed.account,
        "provisioned": made,
        "refused": refused,
        "warming": made,
        "payment_verified": verdict.payment_verified,
        "note": note(tier, verdict.payment_verified, access),
    }


def _refused(tier: Tier, reasons: tuple[str, ...]) -> tuple[int, dict[str, Any]]:
    """The 422. Split out so `answer()` can return it from inside the store's `try`/`finally`.

    **EVERY REASON, NOT THE FIRST.** A caller told one reason fixes it and is refused again.
    **THE ANSWER IS A SENTENCE, NOT ONLY A LIST.** A caller that reads `refused[0]` and shows it to
    a user shows them a rule, not a decision. `eligible` is the machine-readable half.
    """
    return 422, {
        "tier": tier.value,
        "eligible": False,
        "message": NOT_ELIGIBLE.format(tier=tier.value),
        "provisioned": [],
        "refused": list(reasons),
    }


def for_request(handler: Any) -> tuple[int, dict[str, Any]]:
    """Read one POST off the wire and answer it.

    **IT TAKES THE HANDLER, THE WAY `http_io.read_body` DOES**, so the socket layer spends three
    lines on this route rather than twelve. `serve/listener.py` sits at the 200-line cap and the
    alternative was unpacking five arguments there, which puts this route's shape inside the module
    that should only be deciding which route it is.

    `answer()` stays separate and takes plain values, so the rules can be tested without a socket.
    """
    given, _ = read_body(handler)
    return answer(
        handler.path,
        given or b"",
        handler.headers.get(AUTH_HEADER),
        str(getattr(handler, "provision_secret", "")),
        handler.settings,
    )
