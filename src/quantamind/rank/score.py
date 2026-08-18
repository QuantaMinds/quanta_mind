"""The ranking: order changed files by prior-touch count, and say when there was nothing to order.

WHAT: `order()` turns {path: prior count} into a ranked list, and `discriminate()` names which of
      the three cases the change fell into.
WHY:  **This is the policy with the p-value**, and it is a pure function so it can be tested
      against the research implementation without a repository. `rank/` may not import `ingest/` or
      `store/` — it receives the counts. That is what keeps this file comparable to
      `research/phase0/external/defect_return.py`, which is what gate 2a demands.

      **The tie-break is `(-score, path)` and it is not cosmetic.** Ties are common — 4.61% of
      changes have every file at zero — and any other tie-break produces a different top three on
      those changes, which is a different policy with a different miss rate.

      **`discriminate()` exists because a ranking over an all-zero score set is not a ranking.**
      It is alphabetical order wearing a ranking's clothes, and that slice misses most: **4.46%
      against 1.21% overall.** A `Ranking` that cannot distinguish *ordered by history* from *no
      history to order by* claims a capability it did not exercise, so the case is a returned value
      rather than a comment.
IMPORTS: nothing. Pure functions over plain data.
CONSUMED BY: allocate, render, and the live comparison against the research ranker.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum


class Discrimination(Enum):
    """What the scores allowed the ranking to do."""

    ORDERED = "ordered"
    """Scores differ: the ranking is by history."""

    FLAT_NONZERO = "flat_nonzero"
    """Every file has the same non-zero count. History exists and does not separate them."""

    NO_HISTORY = "no_history"
    """Every file scores zero. There is nothing to rank, and the order is alphabetical."""


def order(scores: Mapping[str, int]) -> list[str]:
    """Paths ranked by descending prior-touch count, ties broken by path.

    Matches `defect_return.py`'s `sorted(files, key=lambda f: (-scores[f], f))` exactly. Gate 2a
    compares the two lists element by element, so any change here is a change of policy.
    """
    return sorted(scores, key=lambda path: (-scores[path], path))


def discriminate(scores: Mapping[str, int]) -> Discrimination:
    """Which of the three cases this change fell into. Called before the ranking is believed."""
    values = set(scores.values())
    if not values or values == {0}:
        return Discrimination.NO_HISTORY
    if len(values) == 1:
        return Discrimination.FLAT_NONZERO
    return Discrimination.ORDERED


def top(scores: Mapping[str, int], budget: int) -> list[str]:
    """The `budget` highest-ranked paths.

    **No special case for a short list.** With three or fewer files the top three is every file,
    which is true by construction and measures nothing — the caller is responsible for not
    reporting it as evidence, and `discriminate()` is what lets it tell.
    """
    if budget < 0:
        raise ValueError(f"budget cannot be negative, got {budget}")
    return order(scores)[:budget]


def rendered(scores: Mapping[str, int], budget: int) -> Sequence[tuple[int, str, int, bool]]:
    """(rank, path, score, funded) for every path — funded and cold alike.

    Cold rows are carried because they are the coverage line's content and shadow evaluation's
    denominator; returning only the funded subset silently removes both.
    """
    ranked = order(scores)
    return [(i + 1, p, scores[p], i < budget) for i, p in enumerate(ranked)]
