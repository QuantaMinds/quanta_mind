"""Verification that the degenerate/informative split is stated at the size it actually uses.

WHAT: Pins `DEGENERATE_AT` and the labels `pool` writes from it.
WHY:  **THE SPLIT IS WHAT MAKES THE REPLAY HONEST.** A change touching three files or fewer is
      read entirely by a budget of three, so no ordering could have failed on it and counting it
      as a win inflates the result. `DEGENERATE_AT` is where that line sits, and it was freely
      mutable with every tier green — at 0 every event counts as informative and the headline
      number stops excluding the events it cannot have earned.

      **THE LABEL CARRIES THE NUMBER INTO THE REPORT.** `"<=3 files"` and `">3 files"` are read
      by a person deciding whether to believe the measurement, so a label disagreeing with the
      split would misdescribe the population rather than merely mis-slice it. Both are asserted,
      and they are asserted to partition at the same number.

      Three is written out; `DEGENERATE_AT` in the expectation would pass at any value.
IMPORTS: pytest, quantamind.types.replay_outcome, quantamind.types.pooled_outcome.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.pooled_outcome import pool
from quantamind.types.replay_outcome import DEGENERATE_AT, Outcome, Stratum

SPLIT = 3
"""A budget of three reads a three-file change whole. See the module docstring."""


def _stratum(label: str) -> Stratum:
    return Stratum(label=label, events=10, hits=6, alpha_hits=4, chance_hits=3.0)


def _outcome() -> Outcome:
    return Outcome(
        repo="o/r",
        whole=_stratum("all events"),
        degenerate=_stratum("d"),
        informative=_stratum("i"),
        b=4,
        c=2,
    )


def test_the_split_is_three_files() -> None:
    """The budget the ranker funds, so a change at or below it is read entirely."""
    assert DEGENERATE_AT == SPLIT


def test_the_pooled_labels_state_the_split_and_partition_at_it() -> None:
    """A reader must be able to see which events were excluded and why."""
    pooled = pool([_outcome(), _outcome()])

    assert pooled.degenerate.label == f"<={SPLIT} files"
    assert pooled.informative.label == f">{SPLIT} files"


def test_pooling_nothing_raises_rather_than_reporting_zero() -> None:
    """An empty pool is a number about nothing, which is the failure this project keeps finding."""
    with pytest.raises(ValueError, match="number about nothing"):
        pool([])
