"""Verification that the firing threshold is one decision, not three numbers that happen to match.

WHAT: Pins `rank.order.DEFAULT_THRESHOLD`, `types.settings.DEFAULT_THRESHOLD_PERCENTILE` and the
      default on `types.ranking.Ranking.threshold_percentile` to each other and to the decile the
      research measured, and checks the default actually reaches a `Ranking`.
WHY:  **THE SAME NUMBER IS WRITTEN IN THREE LAYERS AND NOTHING REQUIRED THEM TO AGREE.** Changing
      `DEFAULT_THRESHOLD` from 0.9 to 0.0 left every tier green — unit, property, and live against
      real repositories — while `Settings` and `Ranking` went on saying 0.9. A caller reading the
      settings default and a caller taking `rank()`'s would then disagree about when a file fires,
      and the disagreement would be invisible because each is separately consistent.

      **THIS DIRECTORY DID NOT EXIST.** `rank/` decides where inference is spent, which
      `AGENTS.md` calls a correctness bug when it goes wrong, and it had no unit tests at all —
      only live coverage. Found by mutating every numeric constant in `src/quantamind`.

      **0.9 IS WRITTEN AS A LITERAL.** A test phrased as `== DEFAULT_THRESHOLD` reads the value
      under test and passes at any value; that is how the threshold went unnoticed in the first
      place, and the same mistake was made once more while writing these tests.
IMPORTS: pytest, quantamind.rank.order, quantamind.types.settings, quantamind.types.ranking.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import dataclasses

from quantamind.rank.order import DEFAULT_THRESHOLD, rank
from quantamind.types.ranking import Ranking
from quantamind.types.settings import DEFAULT_THRESHOLD_PERCENTILE

DECILE = 0.9
"""The top-decile rule the research settled on: it fires on 10-12% of pull requests across an
eighty-fold range of repository velocity. Written out so this file does not move with the code."""


def _ranking_default() -> float:
    field = next(f for f in dataclasses.fields(Ranking) if f.name == "threshold_percentile")
    assert not isinstance(field.default, dataclasses._MISSING_TYPE), (
        "Ranking.threshold_percentile lost its default, so callers no longer share one"
    )
    return float(field.default)


def test_the_threshold_is_the_decile_the_research_measured() -> None:
    """Each of the three, against the literal. Any one drifting is a different product."""
    assert DEFAULT_THRESHOLD == DECILE
    assert DEFAULT_THRESHOLD_PERCENTILE == DECILE
    assert _ranking_default() == DECILE


def test_the_three_declarations_agree_with_each_other() -> None:
    """Stated separately from the literal: these must match even if the decile is ever revised."""
    assert DEFAULT_THRESHOLD == DEFAULT_THRESHOLD_PERCENTILE == _ranking_default()


def test_ranking_without_a_threshold_carries_the_default() -> None:
    """Behavioural: the default is wired through, not merely declared beside the function."""
    ranked = rank({"a.py": 10, "b.py": 5, "c.py": 1})

    assert ranked.threshold_percentile == DECILE


def test_an_explicit_threshold_overrides_the_default() -> None:
    """The false-positive direction: a hard-coded 0.9 would pass every test above."""
    ranked = rank({"a.py": 10, "b.py": 5, "c.py": 1}, threshold=0.25)

    assert ranked.threshold_percentile == 0.25
