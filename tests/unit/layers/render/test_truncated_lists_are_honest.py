"""Verification that every shortened list in a rendered comment says what it left out.

WHAT: Pins `render/coverage_line._names` and `render/context/goal_block`'s quote at their caps,
      and pins that the remainder is stated rather than dropped.
WHY:  **A LIST THAT SILENTLY SHOWS FIVE OF TWELVE IS THIS PROJECT'S OWN FAILURE MODE PRINTED ON
      A CUSTOMER'S PULL REQUEST.** `_names` exists to give "an honest remainder rather than a
      bare count", and `MAX_NAMED` is what decides how much it hides — freely mutable, with
      every tier green. The same for the quoted goal: `BODY_CAP` bounds how much of the stated
      intent is echoed back, and uncapped a long commit message floods the comment.

      **THE GOAL CAP MOVED MODULES AND THIS TEST FOLLOWED IT.** It was `verdict_block.GOAL_LINES`,
      eight LINES of `Summary.goal`, printed only when a model answered. D6a made the quote
      deterministic and `verdict_block` stopped rendering it, so the cap is now
      `goal_block.BODY_CAP` in CHARACTERS. A cap that loses its test when its module moves is a
      cap nobody is pinning.

      **THE REMAINDER IS THE PROPERTY, NOT THE CAP.** Five names and "and 7 more" is honest at
      any cap; five names and nothing else is not. So the tests assert the remainder arithmetic
      as well as the count, which is what fails when the cap moves in either direction.
IMPORTS: pytest, quantamind.render.coverage_line, quantamind.render.context.goal_block,
      quantamind.ingest.{context.tickets,diff}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.ingest.context.tickets import Context
from quantamind.ingest.diff import Stated
from quantamind.render.context.goal_block import BODY_CAP, goal
from quantamind.render.coverage_line import MAX_NAMED, _names

NAMED, QUOTED = 5, 600
"""The shipped caps, written out. See the module docstring."""


def test_the_caps_are_the_numbers_that_ship() -> None:
    assert MAX_NAMED == NAMED
    assert BODY_CAP == QUOTED


def test_a_goal_at_the_cap_is_quoted_whole_and_claims_no_remainder() -> None:
    """The boundary. Announcing a trim that did not happen is the same lie the other way."""
    block = goal(Context(stated=Stated("t", "x" * (QUOTED - len("t\n\n")))))

    assert "Quoted to" not in block


def test_a_goal_over_the_cap_states_that_it_was_cut() -> None:
    """The remainder is the property. A silent trim lets a comment appear to quote a goal in
    full while dropping the sentence that qualified it."""
    block = goal(Context(stated=Stated("t", "x" * (QUOTED * 2))))

    assert f"Quoted to {QUOTED} characters" in block
    assert "the rest is on the pull request" in block


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
