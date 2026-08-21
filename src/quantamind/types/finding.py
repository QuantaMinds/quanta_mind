"""One claim a model made about a diff, and the verdict a judge reached on it.

WHAT: `Finding` — what the reviewer produced. `Verdict` — what `verify/` decided. `Judged` — the
      pair, which is the only shape `render/` may publish.
WHY:  **THIS LIVES IN `types/` BECAUSE `verify/` MAY NOT IMPORT `infer/`.** That is rule 7 and it is
      the point of the layer order: the code adjudicating the model's claims must not be able to
      reach into the code that made them. Both layers need this vocabulary, so it sits to the left
      of both.

      **A FINDING CARRIES ITS QUOTE, NOT A LINE NUMBER THE MODEL CHOSE.** Five designs asked the
      model for a line and repaired it; all five failed. Design thirteen removed the field, and
      real-finding anchor failures went to ZERO of 86 — the model quotes code and the line is
      derived from where that quote sits, so the prose and the anchor cannot disagree because one
      is a function of the other.

      **`Verdict` HAS NO DEFAULT AND `UNJUDGED` IS A VALUE.** An unjudged finding and a cleared one
      must never be the same thing on the wire; that collapse is the bug this project exists to
      avoid. `render/` publishes `CLEARED` and nothing else.
IMPORTS: stdlib only (dataclasses, enum). The leftmost layer.
CONSUMED BY: `infer/`, `verify/`, `render/`, `serve/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind.types.verdict import Provenance


class Verdict(Enum):
    """What the judge decided. There is no default, deliberately."""

    CLEARED = "cleared"
    """A judge confirmed it against the diff. The only value `render/` may publish."""

    DROPPED = "dropped"
    """A judge refused it. Counted and reported, never silently absent."""

    UNJUDGED = "unjudged"
    """No judge ran. NOT the same as cleared, and never published."""


@dataclass(frozen=True, slots=True)
class Finding:
    """A claim about one place in a diff. The quote is the anchor; the line is derived from it."""

    path: str
    quote: str
    claim: str
    fix: str = ""
    provenance: Provenance = Provenance.MODEL
    line: int = 0
    """Derived by the gate from where `quote` sits. Zero means not yet located."""

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("a finding must name the file it is about")
        if not self.quote.strip():
            raise ValueError(
                "a finding must quote the code it describes: the line is derived from the quote, "
                "and a finding with no quote cannot be anchored or checked"
            )
        if not self.claim.strip():
            raise ValueError("a finding must state a claim")


@dataclass(frozen=True, slots=True)
class Judged:
    """A finding and what a judge made of it. The only shape `render/` accepts."""

    finding: Finding
    verdict: Verdict
    why: str = ""
    """The deciding fact, in the judge's words. Empty only when UNJUDGED."""

    judge: str = ""
    """Which judge, and its version. Empty only when UNJUDGED.

    **Recorded per finding because a judge is an instrument that moves.** A model bumps a minor
    version, its mean shifts, the gate keeps passing and the signal stops meaning what it did --
    the failure this project has hit under four other names. A verdict that cannot say which judge
    reached it cannot be audited later.
    """

    def __post_init__(self) -> None:
        if self.verdict is Verdict.UNJUDGED:
            return
        if not self.judge.strip():
            raise ValueError(
                f"a {self.verdict.value} verdict must name the judge that reached it; an "
                f"unattributable verdict cannot be audited when the judge changes"
            )
        if not self.why.strip():
            raise ValueError(f"a {self.verdict.value} verdict must state the fact that decided it")
