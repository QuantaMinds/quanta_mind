"""Verification that a long dependents list is shortened and says how much it hid.

WHAT: Drives `render/comment.comment` across the `MAX_DEPENDENTS` boundary — the count shown,
      the "and N more" tail, and the total, which must always be the real total.
WHY:  **THE TRUNCATION WAS FREELY MUTABLE AND IT IS CUSTOMER-FACING TEXT.** At 0 the comment
      names no dependent while still claiming a number; at 11 it pastes a wall of filenames into
      a pull request. Both left every tier of the suite green.

      **THE FULL COUNT IS STATED SEPARATELY FROM THE SHOWN ONES**, and that is the property worth
      protecting: "Used by 12 other file(s): a, b, c, d, e and 7 more" tells the reader what was
      hidden. A truncation that silently showed five of twelve would be this project's own
      failure mode printed on a customer's pull request.

      The cap is written out rather than imported. `MAX_DEPENDENTS + 1` reads the value under test
      and passes at any value, which is the whole failure this file exists to stop.

      **IT WAS FIVE AND IS NOW THREE, LOWERED 2026-08-31 AFTER READING A REAL POSTED COMMENT** on
      `QuantaMinds/quanta_mind#91`: five `src/quantamind/...` paths made the single longest line in
      the body. The remainder is stated either way, so the fourth and fifth named nothing a reader
      acts on — the cap moved, the property did not.
IMPORTS: pytest, quantamind.render.comment, quantamind.types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.infer.change_summary import Summary
from quantamind.rank.order import rank
from quantamind.render.comment import comment

SHOWN = 3
"""The shipped cap on named dependents. See the module docstring on why it is not imported."""


def _summary(dependents: tuple[str, ...]) -> Summary:
    return Summary(
        what_changed="Adds a table.",
        achieves_goal=True,
        reasoning="The writer and the migration are present.",
        goal="feat(store): the audit trail",
        impact="Additive only.",
        breaks=False,
        breaks_why="The migration only adds a table.",
        convention="",
        dependents=dependents,
    )


def _body(count: int) -> str:
    names = tuple(f"src/dep{n}.py" for n in range(count))
    return comment(rank({"src/a.py": 3}), summary=_summary(names))


def test_a_long_list_names_the_cap_and_says_how_many_it_hid() -> None:
    """Twelve dependents: three named, nine declared hidden, twelve stated as the total."""
    body = _body(12)

    assert body.count("src/dep") == SHOWN, "a different number of dependents was named"
    assert "and 9 more" in body
    assert "Used by 12 other file(s)" in body, "the total must be the real total, not the shown one"


def test_a_short_list_is_shown_whole_with_no_tail() -> None:
    """The false-positive direction: three dependents must not claim anything was hidden."""
    body = _body(3)

    assert body.count("src/dep") == 3
    assert "more" not in body.split("Used by")[1].split(".")[0]


def test_exactly_the_cap_shows_everything_and_hides_nothing() -> None:
    """The boundary. At MAX_DEPENDENTS = 0 this names none; at 11 it is indistinguishable."""
    body = _body(SHOWN)

    assert body.count("src/dep") == SHOWN
    assert "and 0 more" not in body


@pytest.mark.parametrize("count", [1, SHOWN, SHOWN + 1, 20])
def test_the_stated_total_is_always_the_real_total(count: int) -> None:
    """Whatever is shown, the number in the sentence is what the caller actually passed."""
    assert f"Used by {count} other file(s)" in _body(count)
