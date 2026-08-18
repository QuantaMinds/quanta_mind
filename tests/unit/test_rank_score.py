"""The ranking policy, with the tie-break fed SHUFFLED input so a stable sort cannot fake it.

WHAT: Asserts the ordering, the tie-break, and the three-case discrimination.
WHY:  **The first live equivalence check passed against a deliberately broken tie-break**, because
      it fed paths already in alphabetical order and Python's sort is stable. Every ordering test
      here shuffles first. A test whose input is already in the answer's order is not testing the
      key it thinks it is.
IMPORTS: quantamind.rank.score.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import random

from quantamind.rank.score import Discrimination, discriminate, order, rendered, top


def test_paths_rank_by_descending_count(tmp_path: object) -> None:
    assert order({"a.py": 1, "b.py": 9, "c.py": 5}) == ["b.py", "c.py", "a.py"]


def test_ties_break_by_path_regardless_of_input_order() -> None:
    scores = {f"f{i}.py": 3 for i in range(8)}
    items = list(scores.items())
    random.Random(7).shuffle(items)
    shuffled = dict(items)
    assert order(shuffled) == sorted(scores), "an all-tie set must come back alphabetical"
    assert order(shuffled) != list(shuffled), "and not simply in the order it arrived"


def test_an_all_zero_set_is_no_history_not_a_ranking() -> None:
    assert discriminate({"a.py": 0, "b.py": 0}) is Discrimination.NO_HISTORY


def test_equal_nonzero_scores_are_flat_history_not_ordered() -> None:
    assert discriminate({"a.py": 4, "b.py": 4}) is Discrimination.FLAT_NONZERO


def test_differing_scores_are_ordered() -> None:
    assert discriminate({"a.py": 4, "b.py": 1}) is Discrimination.ORDERED


def test_rendered_carries_cold_units_not_only_the_funded_ones() -> None:
    rows = rendered({"a.py": 9, "b.py": 5, "c.py": 1, "d.py": 0}, budget=3)
    assert len(rows) == 4, "cold rows are the coverage line and shadow evaluation's denominator"
    assert [r[3] for r in rows] == [True, True, True, False]


def test_top_returns_every_file_when_there_are_fewer_than_the_budget() -> None:
    assert top({"a.py": 1}, budget=3) == ["a.py"]
