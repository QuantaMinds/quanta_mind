"""The ordering that decides where effort goes, and the budget derived from it.

WHAT: `Score`, `RankedUnit`, `Ranking`, `Allocation` and `Budget` -- the output of rank/ and
      the input to allocate/, expressed so neither needs the other's code to talk about them.
WHY:  The budget is a CEILING, not a target. A ceiling never hit and a ceiling never wired up
      print the same thing, so `Budget` carries the maximum and the review record carries what
      was actually spent, and the two are compared rather than assumed equal.
IMPORTS: stdlib only (dataclasses, enum), and types.change for ChangedUnit.
CONSUMED BY: rank produces Ranking; allocate turns it into Budget; render reports both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from quantamind.types.change import ChangedUnit


class Allocation(Enum):
    """How much attention a unit gets. COLD is a decision, not an oversight.

    A cold unit produces no finding and no error, which is silence that looks exactly like
    a clean read -- so it is a named value that renders into the coverage line rather than
    an absence from a list.
    """

    DEEP = "deep"
    SHALLOW = "shallow"
    COLD = "cold"


@dataclass(frozen=True, slots=True)
class Score:
    """A unit's rank input, with the percentile that decides whether we speak at all.

    Both numbers are kept. The raw value is what ordering uses; the percentile is what the
    firing rule uses, because an absolute threshold fired on 11% of one repository and 53%
    of another -- the same rule an order of magnitude apart in volume.
    """

    value: float
    percentile: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.percentile <= 1.0:
            raise ValueError(f"Score.percentile must be in [0,1], got {self.percentile}")


@dataclass(frozen=True, slots=True)
class RankedUnit:
    """One unit with its position and what that position bought it."""

    unit: ChangedUnit
    rank: int
    score: Score
    allocation: Allocation

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError(f"RankedUnit.rank is 1-indexed, got {self.rank}")


@dataclass(frozen=True, slots=True)
class Ranking:
    """Every changed unit in order, and whether this change is worth speaking on.

    Ranking is global across the diff and never file-then-function: taking the top file and
    then the top unit inside it scored BELOW a non-informative ranker, because the busiest
    file usually does not contain the busiest function.
    """

    units: tuple[RankedUnit, ...] = field(default_factory=tuple)
    fired: bool = False
    threshold_percentile: float = 0.9

    def __post_init__(self) -> None:
        ranks = [ranked.rank for ranked in self.units]
        if ranks != sorted(ranks):
            raise ValueError("Ranking.units must be ordered by rank")
        if len(set(ranks)) != len(ranks):
            raise ValueError("Ranking.units contains a duplicate rank")

    def funded(self) -> tuple[RankedUnit, ...]:
        """The units that will receive a model call. Everything else is cold, by design."""
        return tuple(u for u in self.units if u.allocation is not Allocation.COLD)

    def cold(self) -> tuple[RankedUnit, ...]:
        return tuple(u for u in self.units if u.allocation is Allocation.COLD)


@dataclass(frozen=True, slots=True)
class Budget:
    """What a review is permitted to spend. Exceeding it raises; it never degrades silently.

    `max_requests` is the hard ceiling from the allocator. `inference_permitted` is the
    separate lever the per-repository quota uses: above quota a review still runs and still
    reports coverage, and only inference is withheld. A quota that failed the review
    instead would turn a billing limit into an outage.
    """

    max_requests: int
    inference_permitted: bool = True

    def __post_init__(self) -> None:
        if self.max_requests < 0:
            raise ValueError(f"Budget.max_requests cannot be negative, got {self.max_requests}")

    @property
    def is_free_tier(self) -> bool:
        """True when this review will run the deterministic path and call no model at all."""
        return not self.inference_permitted or self.max_requests == 0


class BudgetExceeded(Exception):
    """Raised when a review tries to spend past its ceiling.

    Deliberately an exception rather than a silent truncation: a run that quietly stops
    calling the model after N requests and a run that was configured for N requests produce
    identical output, and only one of them is correct.
    """

    def __init__(self, spent: int, ceiling: int) -> None:
        super().__init__(f"request {spent} would exceed the ceiling of {ceiling}")
        self.spent = spent
        self.ceiling = ceiling
