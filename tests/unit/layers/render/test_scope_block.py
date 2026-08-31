"""What the scope block tells a developer, and what the publishing rules forbid it to tell anyone.

WHAT: Drives `render.blocks.scope_block.coverage()` over a ranking, and asserts both halves: the
      developer can see every file we saw, and a competitor reading the same comment learns
      nothing about how the budget or the ranking works.
WHY:  **"3 OF 56 REVIEWED; 53 NOT REVIEWED" MADE DEVELOPERS THINK SOMETHING HAD BROKEN.** It had
      not — three is the budget and the other 53 were ranked. The count is not softened here and
      the residual is still stated, because `AGENTS.md` calls the residual the product; what the
      tests below pin is that the scope reads as a decision and the files are reachable.

      **THE ORDER OF THE LIST IS A PUBLISHING RULE AND IT IS TESTED AS ONE.**
      `docs/product/publishing-rules.md` never-publishes *how the budget is split across a change*.
      A list in RANK order lets a reader count down to the cut and read the budget off it, so the
      list is alphabetical — and `test_the_list_is_alphabetical_and_not_the_ranking` fails if
      anybody "improves" it by sorting on score. That is the kind of change that looks like a
      usability fix and is a disclosure.

      **AND NO NUMBER FROM THE RANKING MAY APPEAR.** *What the ranking is built from* is first on
      the never-publish list. Per-file fix counts were in this comment once.
IMPORTS: quantamind.rank.order, quantamind.render.blocks.scope_block, quantamind.types.verdict.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import re

from quantamind.rank.order import rank
from quantamind.render.blocks.scope_block import coverage
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

# Scores descend, so rank order and alphabetical order are the same here — deliberately NOT the
# fixture used for the ordering test, which needs them to disagree.
SCORES = {f"src/mod{n}.py": 20 - n for n in range(8)}


def _block(scores: dict[str, int], unresolved: tuple[Unresolved, ...] = ()) -> str:
    return "\n".join(coverage(rank(scores), unresolved))


def test_the_scope_states_both_numbers_and_softens_neither() -> None:
    """The residual is the product. A block that reported only what it read would be the one
    dishonest sentence in the comment."""
    block = _block(SCORES)

    assert "**3 of 8**" in block
    assert "All 8 changed file(s)" in block


def test_every_changed_file_is_reachable_even_the_ones_not_read() -> None:
    """The developer's half: nothing was hidden, and they can check any of it."""
    block = _block(SCORES)

    for path in SCORES:
        assert f"`{path}`" in block, f"{path} was ranked and never shown to the author"


def test_the_files_read_closely_are_marked_and_the_others_are_not() -> None:
    """A list where every line looks the same cannot answer "did you look at MY file"."""
    block = _block(SCORES)
    marked = [
        line for line in block.splitlines() if "read closely" in line and line.startswith("-")
    ]

    assert len(marked) == 3, marked
    assert all("mod0" in m or "mod1" in m or "mod2" in m for m in marked)


def test_the_list_is_alphabetical_and_not_the_ranking() -> None:
    """**A PUBLISHING RULE, NOT A LAYOUT PREFERENCE.** Rank order lets a reader count to the cut
    and read the budget off the list, which `publishing-rules.md` never-publishes.

    The scores here make the two orders disagree: `zebra.py` is the busiest file and sorts last.
    """
    block = _block({"src/zebra.py": 99, "src/apple.py": 2, "src/mango.py": 1})
    listed = [line for line in block.splitlines() if line.startswith("- `")]

    assert listed == sorted(listed), (
        f"the list is in rank order, which discloses the budget: {listed}"
    )
    assert "apple" in listed[0], listed


def test_a_listed_file_carries_a_path_and_never_a_number() -> None:
    """*What the ranking is built from* is first on the never-publish list, and a per-file fix
    count was printed in this comment once before being removed for a different reason.

    **THE ASSERTION IS THE SHAPE OF THE LINE, NOT A LIST OF FORBIDDEN WORDS.** A first draft
    searched for `"rank"` and failed on the scope sentence's own "were ranked" — a check that
    fires on correct output is one somebody deletes. A line that is a path, optionally marked as
    read, cannot carry a score whatever the score is called.
    """
    block = _block({"src/zebra.py": 99, "src/apple.py": 2, "src/mango.py": 1})
    listed = [ln for ln in block.splitlines() if ln.startswith("- `")]

    assert len(listed) == 3
    for line in listed:
        assert re.fullmatch(r"- `[^`]+`( — read closely)?", line), (
            f"a listed file carries something besides its path: {line!r}"
        )


def test_a_construct_we_could_not_parse_is_still_reported() -> None:
    """Typed silence survives the rewrite. This line is the other half of the coverage claim."""
    silence = (Unresolved(Site("src/mod0.py", 3), Reason.DYNAMIC_DISPATCH, Construct.CALL_SITE),)
    block = _block(SCORES, silence)

    assert "1 construct(s) could not be parsed" in block


def test_no_construct_means_no_line_about_constructs() -> None:
    """The false-positive direction: a clean parse must not print a zero."""
    assert "could not be parsed" not in _block(SCORES)
