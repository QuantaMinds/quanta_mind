"""The review itself: what we checked, what we did not, what we found, what it cost.

WHAT: `CoverageLine`, `RequestLedger` and `Review` -- the record posted to a pull request and
      written to the store, carrying its own coverage and its own spend.
WHY:  Two things have to be observable rather than asserted. Coverage, because the product's
      whole claim is that silence is readable. And spend, because a request ceiling that is
      never hit and one that was never wired up print the same thing -- so the ledger records
      what actually happened and the gate compares it against the budget.
IMPORTS: stdlib only (dataclasses), and types.change, types.finding, types.ranking,
      types.verdict.
CONSUMED BY: render turns this into a comment; store persists it; telemetry queries it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from quantamind.types.change import PullRequest
from quantamind.types.finding import Finding
from quantamind.types.ranking import Budget
from quantamind.types.verdict import Unresolved


@dataclass(frozen=True, slots=True)
class CoverageLine:
    """What was examined and what was not. The first thing in the comment, deliberately.

    Order is the argument: a reader who sees coverage before findings can weigh a finding
    before reading it. A reader who sees it afterwards has already formed a view.
    """

    units_checked: int
    files_checked: int
    unresolved: tuple[Unresolved, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.units_checked < 0 or self.files_checked < 0:
            raise ValueError("CoverageLine counts cannot be negative")

    @property
    def total_considered(self) -> int:
        return self.units_checked + len(self.unresolved)

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
        return bool(self.units_checked) and not self.unresolved


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
    review rather than a second one. The findings here are the ones that survived
    adjudication; what was dropped lives in the store, not in the comment.
    """

    pull_request: PullRequest
    coverage: CoverageLine
    budget: Budget
    ledger: RequestLedger = field(default_factory=RequestLedger)
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    spoke: bool = False

    def __post_init__(self) -> None:
        unpublishable = [f for f in self.findings if not f.publishable]
        if unpublishable:
            raise ValueError(
                f"Review {self.pull_request.key} carries {len(unpublishable)} finding(s) that "
                "were contradicted or never adjudicated; verify/ must run before a Review exists"
            )
        if self.spoke and not self.findings:
            raise ValueError(
                f"Review {self.pull_request.key} claims to have spoken with no findings; "
                "a coverage-only review has spoke=False"
            )

    @property
    def key(self) -> str:
        return self.pull_request.key

    @property
    def overspent(self) -> bool:
        return not self.ledger.within(self.budget)

    @property
    def ran_model(self) -> bool:
        return self.ledger.requests > 0
