"""What one reviewer pass produced, with every discard counted and the counts made to conserve.

WHAT: `Deep` — the anchored findings, and how many were dropped by each mechanism.
WHY:  **IT LIVES IN `types/` BECAUSE `render/` MAY NOT IMPORT `serve/`.** The pass is produced in
      `serve/` and printed in `render/`, which sits to its left, so the vocabulary they share has
      to sit left of both. Same reason `Finding` is here and not in `infer/`.

      **THE COUNTS CONSERVE, AND THAT IS CHECKED AT CONSTRUCTION RATHER THAN TESTED.** `unanchored`
      was computed as `len(found) - len(surviving)` — quote-not-in-diff PLUS oracle-refuted — so
      every refuted finding was counted twice, once in each field. A trailing `- refuted + refuted`
      cancelled to nothing and made it read as deliberate. **Nothing in the tree asserted on
      `unanchored`**, so it survived. An arithmetic identity enforced by `__post_init__` cannot be
      got wrong quietly the way an unasserted field can.
IMPORTS: types.finding. Leftmost layer.
CONSUMED BY: `serve/deep_review.py` produces it, `render/deep_report.py` prints it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from quantamind.types.finding import Finding
from quantamind.types.spend import Spend


@dataclass(frozen=True, slots=True)
class Deep:
    """A reviewer pass, with every discard a value rather than an absence."""

    anchored: tuple[Finding, ...]
    raw: int
    """How many the model returned before anything was dropped."""

    unanchored: int
    """Dropped because the quoted code is not in the diff. **A count, never a silence.**"""

    refuted: int
    """Dropped because an oracle contradicted the claim, or could not settle it. The reviewer's
    discrimination on the largest such class is **-8.3%** — a coin flip — so this is not a
    refinement of its judgement, it is a replacement for it."""

    unresolvable: int
    """Dropped because a claim WAS external but no authority could settle it. **Counted apart from
    `refuted` because they are opposite events.** A refutation is an authority contradicting the
    model; an unresolvable is us being unable to ask. Summing them made a gate that had never
    refuted anything read as a gate that refuted once -- see
    `docs/findings/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`."""

    withdrawn: int
    """Dropped because the model itself withdrew the finding once handed a fact it did not have.
    Measured at **18 of 45 wrong findings for 1 of 7 correct**, against a chance null of 2.8."""

    read: tuple[str, ...]
    """The files the model was actually shown."""

    consulted: bool = True

    spend: Spend = field(default_factory=Spend)
    """What this pass cost. `complete=False` means some call in it was not metered."""
    """Whether the model was asked at all.

    **`raw = 0` BECAUSE THERE WAS NO DIFF AND `raw = 0` BECAUSE THE MODEL FOUND NOTHING MUST NOT
    BE THE SAME VALUE ON THE WIRE** — rule 3. The first is an instrument that never ran, the
    second is a result, and a reader shown "0 raw findings" cannot tell them apart.
    """

    def __post_init__(self) -> None:
        """Every finding the model returned ended somewhere, so the five fates must sum to `raw`."""
        placed = (
            len(self.anchored) + self.unanchored + self.refuted + self.unresolvable + self.withdrawn
        )
        if placed != self.raw:
            raise ValueError(
                f"deep review lost count: {self.raw} raw finding(s) but {placed} accounted for "
                f"({len(self.anchored)} anchored, {self.unanchored} unanchored, "
                f"{self.refuted} refuted, {self.unresolvable} unresolvable, "
                f"{self.withdrawn} withdrawn)"
            )
