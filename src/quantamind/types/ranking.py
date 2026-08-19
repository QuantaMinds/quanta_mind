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


class Discrimination(Enum):
    """What the scores allowed the ranking to do — and it is a FIELD, not a comment.

    A `Ranking` over an all-zero score set is alphabetical order wearing a ranking's clothes: every
    file ties, so `(-score, path)` falls back to `path`, and `__init__.py` outranks the new module
    the change is actually about. Carrying this on the value means a consumer cannot read positions
    off a ranking that never ranked anything.

    **This is the slice that misses most** — 4.46% against 1.21% overall, 3.3x worse — so it is the
    one where a fabricated ordering does the most damage.
    """

    ORDERED = "ordered"
    """Scores differ: the ranking is by history."""

    FLAT_NONZERO = "flat_nonzero"
    """Every file has the same non-zero count. History exists and does not separate them."""

    NO_HISTORY = "no_history"
    """Every file scores zero. Nothing was ranked; any order shown is alphabetical."""


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

    Both numbers are kept. The raw value is what ordering uses.

    **THE PERCENTILE IS NOT USED BY ANY FIRING RULE, AND THIS DOCSTRING USED TO SAY IT WAS.**
    `rank.order.fires()` decides on `max(scores) > 0`; `Settings.threshold_percentile` is read
    from the environment, validated and printed by `quantamind config`, and governs nothing.

    The justification given here was "an absolute threshold fired on 11% of one repository and
    53% of another -- the same rule an order of magnitude apart in volume". **No artefact in this
    repository computes a firing rate**, and no research script mentions one: the allocation
    variants tested WHICH units to read, and V3's score-gap stopping was a budget rule that lost
    to V0. Replayed on the pinned corpus, an absolute threshold on the top file's score fires at
    94.5-99.8% (top>=1) through 48.8-94.5% (top>=10) -- a spread of 1.1x to 1.9x, never an order
    of magnitude, and never near 11%.

    **That is not proof the sentence was invented.** The measurement above is over admissible
    EVENTS, and whatever produced 11%/53% may have been over all pull requests, where changes
    with no history at all would drag both rates down. The claim is left in place, marked, rather
    than deleted: an earlier edit deleted the 4.61% figure for looking unsourced and it was
    sourced -- `degenerate_rate.json` produces it exactly. **Removing a citation on a failed grep
    is the same defect as inventing one.** Someone should find the artefact or run the
    measurement; until then neither the sentence nor its deletion is supported.
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
    discrimination: Discrimination = Discrimination.ORDERED

    def __post_init__(self) -> None:
        ranks = [ranked.rank for ranked in self.units]
        if ranks != sorted(ranks):
            raise ValueError("Ranking.units must be ordered by rank")
        if len(set(ranks)) != len(ranks):
            raise ValueError("Ranking.units contains a duplicate rank")

    def boundary_tie(self) -> tuple[RankedUnit, ...]:
        """Units that scored the same as the last funded one but fell outside the budget.

        A tie at the budget edge is `no_history` in miniature: the ranking has no information
        separating them, so which one got read was decided by `(-score, path)` falling back to
        PATH -- the alphabetical rule used as the non-informative control. Serving control-quality
        output under the product's name without saying so is what typed coverage exists to prevent.

        Not a `Discrimination` member, because it is orthogonal: an ORDERED ranking can still have
        a tie at its edge, and collapsing the two would lose which happened.
        """
        funded = self.funded()
        if not funded or len(funded) >= len(self.units):
            return ()
        edge = funded[-1].score.value
        return tuple(u for u in self.units[len(funded) :] if u.score.value == edge)

    def ranked(self) -> bool:
        """Whether the positions below mean anything at all."""
        return self.discrimination is not Discrimination.NO_HISTORY

    def funded(self) -> tuple[RankedUnit, ...]:
        """The units the review asks a reader to look at first. Everything else is cold, by design.

        Funding buys attention, not inference -- no model runs on these. The distinction matters
        because the ranking is the measured half: 1.53% of changes a later fix returns to are
        missed at a three-unit budget, against 2.97% ordering the same units alphabetically.
        """
        if not self.ranked():
            # Funding is a claim that these units were CHOSEN. With every score at zero nothing was
            # chosen, and returning the alphabetical first three would publish sort(filenames) as a
            # judgement about risk. The units are still carried -- see `units` -- and the coverage
            # line is where their existence is reported.
            return ()
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
