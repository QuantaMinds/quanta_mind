"""`Stratum` and `Outcome` -- what a retrospective found, with chance beside every number.

WHAT: `Stratum` is one slice of events with its three arms; `Outcome` carries the whole slice,
      the degenerate one, the informative one, and everything the definition rejected.
WHY:  This is the number a prospect quotes back at us, so the record's SHAPE is what stops it
      being quotable dishonestly.

      **CHANCE IS A FIELD, NOT AN OPTION, AND IT IS THE HEADLINE.**
      `defect-return-external-preregistration.md` settled this: alphabetical ordering is not a
      stable reference, because its strength depends on repository layout. In home-assistant it
      beat chance by +1.75, since `components/<name>/__init__.py` sorts first and is also the
      churn-heavy file -- the control accidentally encoded importance. Exact hypergeometric
      chance, computed per event, is the invariant comparison.

      **THE DEGENERATE STRATUM IS SEPARATE BECAUSE IT CANNOT DISCRIMINATE.** With a budget of
      three, a change touching three or fewer files is entirely read: every arm hits, always.
      Measured on the pinned corpus that is 68.6% of events, all three arms at 0.00%, and pooling
      them dilutes the effect about threefold -- 1.05% against chance's 2.76% pooled, versus 3.14%
      against 8.21% where a ranking decides anything.

      **`inconclusive()` IS A VALUE, NOT A WARNING PRINTED SOMEWHERE.** A refusal the caller can
      forget to print is one that will be forgotten.
IMPORTS: stdlib only (dataclasses, math). Nothing from any layer.
CONSUMED BY: serve/retrospective.py, render/replay_report.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import comb

# Copied from research/phase0/external/defect_return.py. Not chosen here.
MIN_EVENTS, MIN_DISCORDANT = 500, 20
# The boundary is the budget: at or below it, the top three IS the whole change.
DEGENERATE_AT = 3


@dataclass(frozen=True, slots=True)
class Stratum:
    """One slice of events and how the three arms did on it.

    `chance_hits` is fractional because chance is a probability per event, not a coin flip: an
    event with 5 files and 2 targets contributes 0.9, not 0 or 1. Summing the probabilities is the
    expectation, which is what a baseline should be.
    """

    label: str
    events: int
    hits: int
    alpha_hits: int
    chance_hits: float

    def _miss(self, got: float) -> float:
        return (1.0 - got / self.events) * 100 if self.events else 0.0

    @property
    def miss(self) -> float:
        return self._miss(self.hits)

    @property
    def alpha_miss(self) -> float:
        return self._miss(self.alpha_hits)

    @property
    def chance_miss(self) -> float:
        return self._miss(self.chance_hits)

    @property
    def lift(self) -> float:
        """Points of miss rate the ranker saves AGAINST CHANCE. Negative means it lost."""
        return self.chance_miss - self.miss

    @property
    def alpha_lift(self) -> float:
        """The control against chance. Near zero means the control is genuinely uninformative."""
        return self.chance_miss - self.alpha_miss

    @property
    def decides_nothing(self) -> bool:
        """True when every arm scored identically -- the signature of a degenerate slice."""
        return self.events > 0 and self.miss == self.alpha_miss == self.chance_miss


@dataclass(frozen=True, slots=True)
class Outcome:
    """One repository's replay. `b` is where the ranker won a discordant pair, `c` the control."""

    repo: str
    whole: Stratum
    degenerate: Stratum
    informative: Stratum
    b: int
    c: int
    rejected: dict[str, int] = field(default_factory=dict)
    skipped_flat: int = 0

    @property
    def degenerate_share(self) -> float:
        """Share of events a budget of three reads entirely, so no ordering could have failed."""
        return self.degenerate.events / self.whole.events * 100 if self.whole.events else 0.0

    def p_value(self) -> float:
        """Two-sided exact McNemar over the discordant pairs.

        Only pairs where the arms disagree carry information. Returns 1.0 when there are none,
        which is the honest answer and not a significant one.
        """
        n = self.b + self.c
        if n == 0:
            return 1.0
        tail = sum(comb(n, k) for k in range(min(self.b, self.c) + 1))
        return min(1.0, 2.0 * tail / (2.0**n))

    def inconclusive(self) -> str | None:
        """Which pre-registered floor this run missed, or None when it cleared both.

        Measured on the pinned corpus, events run 22-57% of commits and every repository cleared
        500 by at least threefold -- so this fires on genuinely small histories, not routinely.
        The shortfall is named so the reader learns how much history the question needs.
        """
        if self.whole.events < MIN_EVENTS:
            short = MIN_EVENTS - self.whole.events
            return f"{self.whole.events} events, {short} short of the {MIN_EVENTS} floor"
        if self.b + self.c < MIN_DISCORDANT:
            return f"{self.b + self.c} discordant pairs, floor is {MIN_DISCORDANT}"
        return None
