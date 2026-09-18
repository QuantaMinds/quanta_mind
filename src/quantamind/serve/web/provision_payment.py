"""What the provisioning route knows about the money, and how little of it a caller can assert.

WHAT: `access_for(root, account, at)` returns `verify/paid_access.Access` for an account, or None
      when nothing in this product has ever heard of a payment for it. `note(...)` is the sentence
      the reply carries about what was verified.
WHY:  **SPLIT OUT WHEN `serve/web/provision_route.py` PASSED THE 200-LINE CAP.** `AGENTS.md` rule 4.
      The concern is *what we know about whether this account pays*, which is a different question
      from *is this request well-formed and may these repositories be admitted*.

      **None AND "BLOCKED" ARE DIFFERENT ANSWERS AND THIS IS WHERE THEY SEPARATE.** No subscription
      row means nobody has ever paid us through Stripe for this account -- which is the normal state
      of an Enterprise customer invoiced against a signed order. Returning
      `Access(NO_SUBSCRIPTION)` there would refuse them, so None is returned and
      `verify/tier_request.py` falls back to the payment reference and reports it UNVERIFIED. A
      subscription that exists and has lapsed is a different fact and does refuse.

      **THE STORE IS NOT CREATED BY THIS READ.** `open_store` makes the file, and a route that
      provisioned a database in order to find out whether to provision anything would leave one
      behind on every refused request -- which a test caught the first time this was written the
      other way. `serve/web/routes.py` makes the same argument for the same file: *"a read would
      provision the thing it is reading, and every visitor would leave a database behind."*
IMPORTS: store.{billing.subscriptions,schema,tenancy}, verify.paid_access, verify.tier_request.
      Leftward and same-layer public surface only.
CONSUMED BY: `serve/web/provision_route.py`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store import tenancy
from quantamind.store.billing import subscriptions
from quantamind.store.schema import open_store
from quantamind.verify import paid_access
from quantamind.verify.tier_request import Tier

UNVERIFIED = (
    "payment_ref was recorded, not verified: no subscription is on record for this account. A "
    "reference in a request body is a string the caller typed. Only a subscription written from a "
    "signed Stripe delivery sets payment_verified."
)
VERIFIED = "verified against the subscription Stripe last told us about: {reason}"


def access_for(root: Path, account: str, tier: Tier, *, at: int) -> paid_access.Access | None:
    """This account's standing with Stripe, or None when we have never heard of one.

    **None FOR `Tier.FREE`, ALWAYS.** Nobody paid for the free tier. Asking the question there
    would invite somebody to later make the answer matter, and `verify/tier_request.py` refuses to
    report a verified payment for it in any case.
    """
    if tier is Tier.FREE:
        return None
    path = tenancy.shared(root, tenancy.ACCOUNTS)
    if not path.exists():
        return None
    try:
        conn = open_store(path)
    except sqlite3.Error:
        # **UNREADABLE IS NOT LAPSED.** A store we cannot open says nothing about whether they
        # paid, and reading it as a refusal would turn our own broken disk into their invoice
        # problem. It falls back to the payment reference, reported unverified.
        return None
    try:
        held = subscriptions.current(conn, account)
    finally:
        conn.close()
    return None if held is None else paid_access.decide(held, at=at)


def note(tier: Tier, verified: bool, access: paid_access.Access | None) -> str:
    """What the reply says about the money. **Empty only for the tier where none changed hands.**"""
    if tier is Tier.FREE:
        return ""
    if verified and access is not None:
        return VERIFIED.format(reason=access.reason)
    return UNVERIFIED
