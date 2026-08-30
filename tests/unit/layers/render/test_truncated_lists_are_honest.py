"""Verification that every shortened list in a rendered comment says what it left out.

WHAT: Pins `render/coverage_line._names` and `render/verdict_block`'s goal quote at their caps,
      and pins that the remainder is stated rather than dropped.
WHY:  **A LIST THAT SILENTLY SHOWS FIVE OF TWELVE IS THIS PROJECT'S OWN FAILURE MODE PRINTED ON
      A CUSTOMER'S PULL REQUEST.** `_names` exists to give "an honest remainder rather than a
      bare count", and `MAX_NAMED` is what decides how much it hides — freely mutable, with
      every tier green. The same for the quoted goal: `GOAL_LINES` bounds how much of the stated
      intent is echoed back, and at 17 a long commit message floods the comment.

      **THE REMAINDER IS THE PROPERTY, NOT THE CAP.** Five names and "and 7 more" is honest at
      any cap; five names and nothing else is not. So the tests assert the remainder arithmetic
      as well as the count, which is what fails when the cap moves in either direction.
IMPORTS: pytest, quantamind.render.coverage_line, quantamind.render.verdict_block.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.render.coverage_line import MAX_NAMED, _names
from quantamind.render.verdict_block import GOAL_LINES

NAMED, QUOTED = 5, 8
"""The shipped caps, written out. See the module docstring."""


def test_the_caps_are_the_numbers_that_ship() -> None:
    assert MAX_NAMED == NAMED
    assert GOAL_LINES == QUOTED


def test_a_short_list_is_named_in_full_with_no_remainder() -> None:
    """Three paths: all three named, nothing claimed hidden."""
    rendered = _names(["src/a.py", "src/b.py", "src/c.py"])

    assert rendered.count("`") == 6
    assert "more" not in rendered


def test_a_list_at_the_cap_is_named_in_full() -> None:
    """The boundary. At MAX_NAMED = 0 this names none of them."""
    rendered = _names([f"src/f{n}.py" for n in range(NAMED)])

    assert rendered.count("src/f") == NAMED
    assert "more" not in rendered


def test_a_long_list_names_the_cap_and_states_the_remainder() -> None:
    """Twelve paths: five named, seven declared. The arithmetic must add up to twelve."""
    rendered = _names([f"src/f{n:02d}.py" for n in range(12)])

    assert rendered.count("src/f") == NAMED
    assert rendered.endswith("and 7 more")


@pytest.mark.parametrize("count", [NAMED + 1, 9, 40])
def test_the_named_and_the_remainder_always_sum_to_the_total(count: int) -> None:
    """Whatever the cap, nothing is lost between what is shown and what is counted."""
    rendered = _names([f"src/f{n:02d}.py" for n in range(count)])
    shown = rendered.count("src/f")
    stated = int(rendered.rsplit("and ", 1)[1].split(" ")[0])

    assert shown + stated == count
