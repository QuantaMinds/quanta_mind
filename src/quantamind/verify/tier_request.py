"""What each tier requires of a provisioning request, decided before anything is written.

WHAT: `Tier`, `Request`, and `admissible(tier, request, *, free_verdicts)` -> `Verdict`. No I/O, no
      network, no store. Given a parsed request it returns eligible-with-no-reasons, or every reason
      it is refused.
WHY:  **THE FREE TIER IS THE ONLY ONE WITH A REAL GATE, AND THAT IS NOT AN OVERSIGHT.**
      `verify/qualification.py` checks stars, contributors, history length, recent activity and a
      cap of forty places, because we give that tier away. A paying customer has already answered
      the only question those rules were asking, so re-asking it would be a validation that exists
      for the shape of the documentation rather than for anything it protects.

      **TEAM AND ENTERPRISE DIFFER IN ALMOST NOTHING A PROGRAM CAN CHECK, AND THIS SAYS SO.** SSO, a
      DPA, residency and an SLA are contract terms. **The one difference that is code is `org`**:
      Enterprise sells "define a standard once; every repository is held to it", and
      `ingest/standards/inherited.py` reads those from an organisation's `.quantamind` repository.
      Without an organisation named, the feature distinguishing the tier has nowhere to read from.

      **`payment_ref` IS RECORDED, NEVER VERIFIED, AND THE TYPE CANNOT HIDE THAT.** Rows B3 and B7
      of `docs/plans/roadmap/product-build.md` are parked, so nothing in this product talks to a
      payment processor. A reference is a string a caller supplied. `Verdict.payment_verified` is
      therefore always False here and is carried into the response rather than left for a reader to
      infer -- a field that silently means "we took your word for it" is the shape this project
      refuses everywhere else.

      **NOTHING IS ADMITTED UNLESS EVERY REPOSITORY IS.** A partial provision leaves a customer
      paying for repositories that were not admitted, and no reply shape makes that legible.
IMPORTS: stdlib only, plus `verify.qualification` for the free tier's `Verdict`. Nothing to its
      right, and nothing that touches a network -- the caller does the reads and passes the facts.
CONSUMED BY: `serve/web/provision_route.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from quantamind.verify.qualification import Verdict as RepoVerdict

REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")

MAX_REPOS = 200
"""A ceiling on one request, not on an account. **Chosen, not measured** -- it bounds the work a
single POST can queue, because `admit()` clones every repository it is given."""


class Tier(Enum):
    """The three tiers `docs/product/pricing.md` sells. The value is the URL segment."""

    FREE = "free"
    TEAM = "team"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class Request:
    """A parsed provisioning request. Every field is what a caller SENT, not what is true."""

    account: str
    repos: tuple[str, ...]
    seats: int = 0
    payment_ref: str = ""
    org: str = ""


@dataclass(frozen=True, slots=True)
class Verdict:
    """Admissible, or every reason it is not — and what was checked rather than believed."""

    admissible: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    payment_verified: bool = False

    def __post_init__(self) -> None:
        if self.admissible and self.reasons:
            raise ValueError(f"admissible with reasons is not a verdict: {self.reasons}")
        if not self.admissible and not self.reasons:
            raise ValueError("refused without a reason; a caller cannot act on that")
        if self.payment_verified:
            raise ValueError(
                "payment_verified cannot be True: B3 is parked and nothing here reads a payment "
                "processor. The field exists to carry that fact, not to be set."
            )


def _shared(request: Request) -> list[str]:
    """Rules every tier has, whatever it pays. Returns reasons, empty when there are none."""
    reasons: list[str] = []
    if not request.account.strip():
        reasons.append("no account was named, and an installation belongs to one")
    if not request.repos:
        reasons.append("no repository was named, so there is nothing to provision")
    if len(request.repos) > MAX_REPOS:
        reasons.append(
            f"{len(request.repos)} repositories in one request; the ceiling is {MAX_REPOS}"
        )
    # **NAMED INDIVIDUALLY, NOT COUNTED.** "3 repositories are malformed" is not something a caller
    # can act on, and the path is derived from these values later.
    reasons.extend(f"{name!r} is not owner/name" for name in request.repos if not REPO.match(name))
    if len(set(request.repos)) != len(request.repos):
        reasons.append("the same repository appears twice in one request")
    return reasons


def _paid(request: Request, tier: Tier) -> list[str]:
    """What Team and Enterprise add. **Deliberately short, because honestly it is short.**"""
    reasons: list[str] = []
    if not request.payment_ref.strip():
        reasons.append(f"the {tier.value} tier needs a payment reference to record against")
    if request.seats <= 0:
        reasons.append(
            f"{request.seats} seats; a paid tier is billed per developer and needs a count"
        )
    return reasons


def admissible(
    tier: Tier, request: Request, *, free_verdicts: dict[str, RepoVerdict] | None = None
) -> Verdict:
    """Every rule for this tier, with every failure named.

    `free_verdicts` carries `verify/qualification.qualifies()` per repository and is **required for
    `Tier.FREE`** -- this module performs no I/O, so the caller reads GitHub and passes the answers.
    Missing verdicts are a refusal, never an assumed pass: "we could not check" and "it qualifies"
    must not be the same value.
    """
    reasons = _shared(request)

    if tier is Tier.FREE:
        verdicts = free_verdicts or {}
        for name in request.repos:
            verdict = verdicts.get(name)
            if verdict is None:
                reasons.append(f"{name}: eligibility was never checked, so it is not admitted")
            elif not verdict.eligible:
                reasons.extend(f"{name}: {why}" for why in verdict.reasons)
    else:
        reasons.extend(_paid(request, tier))
        if tier is Tier.ENTERPRISE and not request.org.strip():
            reasons.append(
                "no organisation was named. Enterprise sells one standard across every repository, "
                "and inherited rules are read from an organisation's .quantamind repository"
            )

    return Verdict(not reasons, tuple(reasons))
