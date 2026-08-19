"""`Pooled` -- several repositories as one measurement, which is the shape the published figure has.

WHAT: `pool(outcomes)` sums the strata and the discordant pairs across repositories and carries a
      per-repository positivity count.
WHY:  **Pooling is not a new unit, it is the VALIDATED one.** The out-of-sample result is
      n = 2,400 across six repositories reported with a positivity count, and
      `defect-return-external-preregistration.md`'s CONFIRMED rule is "control beaten, McNemar
      p < 0.05, and >= 4 of 6 repositories individually positive".

      **A SINGLE REPOSITORY RARELY REACHES THE FLOORS.** Measured: requests 551 events, fastapi
      257, click 414, all three INCONCLUSIVE. The pinned six are unusually large. Without pooling
      the retrospective's default answer to a real prospect is "we cannot tell you anything".

      **`positive` SHIPS WITH `repositories` AND IS NEVER OMITTED.** A pooled win carried by one
      repository is an artifact, and this count is the only thing in the report that can say so.
      Splitting an org into more repositories does not improve the number; it exposes it.
IMPORTS: types.replay_outcome. Nothing to its right.
CONSUMED BY: render/replay_report.py, serve/cli.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quantamind.types.replay_outcome import DEGENERATE_AT, Outcome, Stratum


def _sum(strata: Sequence[Stratum], label: str) -> Stratum:
    """One stratum summed across repositories. EVENTS are the unit, not repositories."""
    return Stratum(
        label=label,
        events=sum(s.events for s in strata),
        hits=sum(s.hits for s in strata),
        alpha_hits=sum(s.alpha_hits for s in strata),
        chance_hits=sum(s.chance_hits for s in strata),
    )


@dataclass(frozen=True, slots=True)
class Pooled:
    """Several repositories as one measurement, which is the shape the published figure has.

    **Pooling is not a new unit -- it is the VALIDATED one.** The out-of-sample result is
    n = 2,400 across six repositories with a per-repository positivity count, and the
    pre-registration's CONFIRMED rule is "control beaten, McNemar p < 0.05, and >= 4 of 6
    repositories individually positive". A single repository rarely reaches the floors --
    requests, fastapi and click measured 551, 257 and 414 events -- so pooling is how a
    customer's question gets answered at all.

    **`positive` ships with `repositories` and is never omitted.** A pooled win carried by one
    repository is an artifact, and the count is the only thing in the report that can say so.
    """

    outcomes: tuple[Outcome, ...]
    whole: Stratum
    degenerate: Stratum
    informative: Stratum
    b: int
    c: int

    @property
    def repositories(self) -> int:
        return len(self.outcomes)

    @property
    def positive(self) -> int:
        """Repositories where the ranker beat chance on the informative stratum."""
        return sum(1 for o in self.outcomes if o.informative.lift > 0)

    def _one(self) -> Outcome:
        """The pooled totals as a single Outcome, so the floors and McNemar are computed once."""
        return Outcome(
            repo="pooled",
            whole=self.whole,
            degenerate=self.degenerate,
            informative=self.informative,
            b=self.b,
            c=self.c,
        )

    def p_value(self) -> float:
        return self._one().p_value()

    def inconclusive(self) -> str | None:
        return self._one().inconclusive()


def pool(outcomes: Sequence[Outcome]) -> Pooled:
    """Sum several repositories into one measurement. Raises on an empty set."""
    if not outcomes:
        raise ValueError("pooling nothing produces a number about nothing")
    return Pooled(
        outcomes=tuple(outcomes),
        whole=_sum([o.whole for o in outcomes], "all events"),
        degenerate=_sum([o.degenerate for o in outcomes], f"<={DEGENERATE_AT} files"),
        informative=_sum([o.informative for o in outcomes], f">{DEGENERATE_AT} files"),
        b=sum(o.b for o in outcomes),
        c=sum(o.c for o in outcomes),
    )
