"""What the model said, split into the part a parser can check and the part it cannot.

WHAT: `ClaimKind`, `Verdict`, `Claim` and `Finding` -- a model's output decomposed so that
      verify/ can adjudicate each structural assertion separately from the prose.
WHY:  The verifier is a parser. It can decide that a symbol exists, that a return precedes a
      write, that a caller is reachable. It cannot decide whether logic is WRONG -- and
      semantic defects are the reason a model runs at all. So a finding carries its claims
      individually, each with its own verdict, and a finding whose claims are all
      undecidable is published as a suggestion rather than as a checked result.
IMPORTS: stdlib only (dataclasses, enum), and types.verdict for Site and Provenance.
CONSUMED BY: infer produces these; verify adjudicates them; render publishes what survived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from quantamind.types.verdict import Provenance, Site


class ClaimKind(Enum):
    """What a claim asserts, which determines whether a parser can decide it.

    The first four are decidable against a parse tree. SEMANTIC is not, and is named so
    that "we did not check this" is a value rather than an omission.
    """

    SYMBOL_EXISTS = "symbol_exists"
    SIGNATURE_MATCHES = "signature_matches"
    ORDER_OF_STATEMENTS = "order_of_statements"
    REFERENCE_RESOLVES = "reference_resolves"
    SEMANTIC = "semantic"

    @property
    def is_checkable(self) -> bool:
        """Whether a parser can adjudicate this kind at all."""
        return self is not ClaimKind.SEMANTIC


class Verdict(Enum):
    """What adjudication concluded. UNDECIDABLE is the honest third option.

    Collapsing UNDECIDABLE into CONFIRMED publishes unchecked claims as checked ones;
    collapsing it into CONTRADICTED drops every semantic finding the product exists to
    surface. It is its own value for both reasons.
    """

    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    UNDECIDABLE = "undecidable"


@dataclass(frozen=True, slots=True)
class Claim:
    """One checkable assertion pulled out of a finding, with its adjudication.

    `verdict` is None until verify/ has run. Publishing a claim with a None verdict is the
    bug this type exists to make visible, and `Finding.publishable` refuses it.
    """

    kind: ClaimKind
    site: Site
    assertion: str
    verdict: Verdict | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.assertion:
            raise ValueError(f"Claim at {self.site.render()} has an empty assertion")
        if self.verdict is Verdict.CONFIRMED and not self.kind.is_checkable:
            raise ValueError(
                f"Claim at {self.site.render()} is {self.kind.value} and cannot be CONFIRMED; "
                "a parser cannot decide a semantic claim"
            )

    @property
    def adjudicated(self) -> bool:
        return self.verdict is not None


@dataclass(frozen=True, slots=True)
class Finding:
    """One thing the review has to say, and the evidence for each part of it.

    A finding survives to publication only if no claim was contradicted. One contradicted
    structural claim discredits the whole finding, because a model that described code that
    is not there was not reading the code it claims to describe.
    """

    site: Site
    body: str
    provenance: Provenance = Provenance.MODEL
    claims: tuple[Claim, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.body.strip():
            raise ValueError(f"Finding at {self.site.render()} has an empty body")

    @property
    def contradicted(self) -> tuple[Claim, ...]:
        return tuple(c for c in self.claims if c.verdict is Verdict.CONTRADICTED)

    @property
    def unadjudicated(self) -> tuple[Claim, ...]:
        return tuple(c for c in self.claims if not c.adjudicated)

    @property
    def publishable(self) -> bool:
        """Whether this may be shown to a human.

        Refuses on a contradicted claim, and refuses on an unadjudicated one -- because a
        review that publishes claims verify/ never saw is indistinguishable from one where
        verify/ is not wired up.
        """
        return not self.contradicted and not self.unadjudicated

    @property
    def is_verified(self) -> bool:
        """True only when a parser actually confirmed something, not merely failed to object."""
        return any(c.verdict is Verdict.CONFIRMED for c in self.claims)

    def label(self) -> str:
        """How this finding is presented: what we checked versus what we are suggesting."""
        if self.is_verified:
            return "verified"
        return "suggested"
