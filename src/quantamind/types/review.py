"""The review itself: what we checked, what we did not, and what it cost.

WHAT: `CoverageLine`, `RequestLedger` and `Review` -- the record posted to a pull request and
      written to the store, carrying its own coverage and its own spend.
WHY:  Two things have to be observable rather than asserted. Coverage, because the product's
      whole claim is that silence is readable. And spend, because a request ceiling that is
      never hit and one that was never wired up print the same thing -- so the ledger records
      what actually happened and the gate compares it against the budget.

      A REVIEW CARRIES NO FINDINGS, AND THAT IS THE PRODUCT DECISION, NOT AN OMISSION. It once
      held `findings` and `spoke`. Nothing populated them: seven review designs were measured
      against pre-registered bars and all seven failed, so no `infer/` ships and no `verify/`
      adjudicates. Fields nothing can fill describe a capability to the next reader that the
      system does not have, and the two guards that policed them could not fire -- an
      unreachable check reads exactly like a passing one. → `docs/product/review-half-record.md`
IMPORTS: stdlib only (dataclasses), and types.change, types.ranking, types.verdict.
CONSUMED BY: render turns this into a comment; store persists it; telemetry queries it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from quantamind.types.change import PullRequest
from quantamind.types.ranking import Budget, RankedUnit, Ranking
from quantamind.types.verdict import Unresolved


@dataclass(frozen=True, slots=True)
class CoverageLine:
    """What was examined and what was not, as a VIEW over the ranking that produced it.

    Order is the argument: a reader who sees coverage before findings can weigh a finding
    before reading it. A reader who sees it afterwards has already formed a view.

    **Three states, not two.** A unit is read, or the parser could not resolve it, or **the
    budget never funded it** -- and the third is the common case, measured at 8.84% of changes
    holding their defect in a cold unit at a three-unit budget. A cold unit is a decision not to
    read, not a failure to analyse, and reporting it as silence is the thing this product exists
    to stop.

    **The cold units are named, not counted.** "Eight functions not read" is untyped silence
    wearing a number -- it says something was skipped without saying what to look at, which is
    the failure this product accuses competitors of. Named, a reviewer can say "read that one",
    which is a judgement on the allocation policy from the position best placed to make it.

    **And the counts are derived, not stored, so this cannot disagree with its ranking.** An
    earlier version held them as fields with a `from_ranking` helper that callers were merely
    *expected* to use -- a rule in a docstring, which is exactly what this project keeps finding
    fails. Holding the `Ranking` and computing over it makes the disagreement unrepresentable
    rather than discouraged: there is no field to set inconsistently.
    """

    ranking: Ranking
    files_checked: int
    unresolved: tuple[Unresolved, ...] = field(default_factory=tuple)
    list_limit: int = 10

    def __post_init__(self) -> None:
        if self.files_checked < 0:
            raise ValueError("CoverageLine.files_checked cannot be negative")
        if self.list_limit < 1:
            raise ValueError(
                f"CoverageLine.list_limit must be at least 1, got {self.list_limit}; a line "
                "that names no cold units at all is the untyped silence this type exists to end"
            )

    @property
    def units_checked(self) -> int:
        return len(self.ranking.funded())

    @property
    def cold(self) -> tuple[RankedUnit, ...]:
        """Cold units, least cold first, truncated. Rank order keeps the ones worth reading."""
        return self.ranking.cold()[: self.list_limit]

    @property
    def cold_not_listed(self) -> int:
        return max(0, len(self.ranking.cold()) - self.list_limit)

    @property
    def total_considered(self) -> int:
        """Everything the parser saw: read, skipped by budget, or unresolvable.

        Cold units are in the denominator because a unit the budget never funded was still part
        of the change. Leaving them out would report a review that read three of eleven
        functions as complete coverage.
        """
        return len(self.ranking.units) + len(self.unresolved)

    def ratio(self) -> float:
        """Resolved share of everything considered. 0.0 when nothing was considered.

        An empty review reports no coverage rather than full coverage, because "we looked at
        nothing" and "we understood everything" must not produce the same number.
        """
        if self.total_considered == 0:
            return 0.0
        return self.units_checked / self.total_considered

    @property
    def is_complete(self) -> bool:
        return bool(self.units_checked) and not self.unresolved and not self.ranking.cold()


@dataclass(frozen=True, slots=True)
class RequestLedger:
    """What this review actually spent. Observed, never inferred from configuration.

    Every field here is read back out in the gate. A ledger that always reports zero is how
    a disconnected ceiling looks, and it is indistinguishable from a quiet week unless the
    number is recorded per review and compared.
    """

    requests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cache_read_tokens: int = 0

    def __post_init__(self) -> None:
        for name in ("requests", "tokens_in", "tokens_out", "cache_read_tokens"):
            if getattr(self, name) < 0:
                raise ValueError(f"RequestLedger.{name} cannot be negative")

    def within(self, budget: Budget) -> bool:
        return self.requests <= budget.max_requests

    @property
    def used_cache(self) -> bool:
        """False after a multi-request review means the prompt prefix is not caching.

        A persistent zero here with more than one request is the signature of an invalidator
        in the cached prefix -- a clock, a request id -- which produces no error and simply
        costs full price on every call.
        """
        return self.cache_read_tokens > 0


@dataclass(frozen=True, slots=True)
class Review:
    """One review of one commit: the unit of work, of record, and of measurement.

    Identified by the pull request's head SHA, so a redelivered webhook resolves to the same
    review rather than a second one.

    **A review is its coverage.** There is no field for a claim about whether code is wrong,
    because the product does not make one -- 207 adjudicated findings came back 5.80% correct,
    and 87.3% of the ones quoting code quoted code absent from the line they cited. Every
    attribute below is derived from git or from a counter, so a review can be recomputed and
    disagreed with. `ran_model` stays because it is the one that would change if inference were
    ever wired up by accident, and a claim of "no model runs here" that nothing can falsify is
    the kind this project stopped accepting.
    """

    pull_request: PullRequest
    coverage: CoverageLine
    budget: Budget
    ledger: RequestLedger = field(default_factory=RequestLedger)

    @property
    def key(self) -> str:
        return self.pull_request.key

    @property
    def overspent(self) -> bool:
        return not self.ledger.within(self.budget)

    @property
    def ran_model(self) -> bool:
        return self.ledger.requests > 0
