"""The draw's cells: verdict crossed with star band, and what an unrecorded size does.

WHAT: Known-answer tests for `band_of`, `cells_for` and `unfillable`.
WHY:  `draw` clones over the network and cannot run offline, which is how four wrong
      fields once survived inside it. Everything about the draw that CAN be tested
      without a network is factored out here so it is, rather than being verified by
      running the thing that commits a seed.

      The stratum exists because the bands break at different rates — measured over 200
      agent repositories, `<500` 34.25% against `>=500` 24.22%, Fisher p = 0.0594. A rule
      differentially loose on small repositories produces exactly that gap, and a draw
      balanced only on verdict could return every BROKE PR from one band, making the
      question invisible rather than merely underpowered.
IMPORTS: phase0.handlabel.strata, phase0.outcome.conclusion.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from phase0.handlabel.strata import (
    BAND_HIGH,
    BAND_LOW,
    STAR_FLOOR,
    Cell,
    band_of,
    cells_for,
    unfillable,
)
from phase0.outcome.conclusion import Outcome


def test_an_unrecorded_size_gets_no_band_rather_than_the_low_one() -> None:
    """ "We do not know its size" is not "it is small".

    Folding an unmeasured repository into `<500` would put a unit with no size into a
    stratum whose entire purpose is to mean something about size — which is the shape
    A52 records going wrong one layer up, where a human-arm band was read as an
    agent-arm property.
    """
    assert band_of(-1) is None
    assert band_of(0) == BAND_LOW
    assert band_of(STAR_FLOOR - 1) == BAND_LOW
    assert band_of(STAR_FLOOR) == BAND_HIGH


def test_the_floor_is_the_human_arms_own_floor() -> None:
    """A15: the human arm's floor is 503 stars with 0% below it.

    The boundary is not a round number chosen for tidiness — it is the line that decides
    whether an agent-arm PR has any human counterpart at all.
    """
    assert STAR_FLOOR == 500


def test_each_verdict_splits_evenly_across_both_bands() -> None:
    cells = cells_for(10, 10)

    assert cells == {
        Cell(Outcome.BROKE, BAND_LOW): 5,
        Cell(Outcome.BROKE, BAND_HIGH): 5,
        Cell(Outcome.CLEAN, BAND_LOW): 5,
        Cell(Outcome.CLEAN, BAND_HIGH): 5,
    }
    assert sum(cells.values()) == 20


@pytest.mark.parametrize("n_broke,n_clean", [(9, 10), (10, 9), (7, 7)])
def test_an_odd_total_raises_rather_than_rounding(n_broke: int, n_clean: int) -> None:
    """A 5/4 split is an unbalanced draw wearing a stratum label.

    Rounding silently is how a design decision becomes an accident nobody recorded.
    """
    with pytest.raises(ValueError) as raised:
        cells_for(n_broke, n_clean)

    assert "cannot split evenly" in str(raised.value)


def test_the_unfillable_message_names_the_cell_and_both_causes() -> None:
    """One message, two opposite meanings, was the defect. Both must appear."""
    text = unfillable(Cell(Outcome.BROKE, BAND_LOW), got=3, want=5, considered=40, repos=12)

    assert "BROKE <500" in text
    assert "OUTCOME RULE" in text and "DEPLETION" in text
    assert "WALK MORE REPOSITORIES" in text
    assert "7.5%" in text


def test_the_message_survives_zero_examined_without_dividing_by_it() -> None:
    """A cell can fail with nothing examined — every repository failed to clone."""
    text = unfillable(Cell(Outcome.CLEAN, BAND_HIGH), got=0, want=5, considered=0, repos=0)

    assert "no candidates examined" in text
    assert "CLEAN >=500" in text
