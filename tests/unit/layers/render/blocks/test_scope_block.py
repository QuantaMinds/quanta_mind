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

from quantamind.parse.change_effort import Effort
from quantamind.rank.order import rank
from quantamind.render.blocks.scope_block import coverage
from quantamind.types.checked import Checked
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

# Scores descend, so rank order and alphabetical order are the same here — deliberately NOT the
# fixture used for the ordering test, which needs them to disagree.
SCORES = {f"src/mod{n}.py": 20 - n for n in range(8)}
# **THE TABLE NEEDS SOMETHING TO CARRY OR IT IS NOT RENDERED AT ALL.** With no sizes and no rule
# rows every cell would be an em dash, and `file_table` falls back to a plain list rather than
# print furniture. Tests about the TABLE must therefore supply sizes.
SIZES = {path: Effort(added=4, removed=1) for path in SCORES}


def _block(
    scores: dict[str, int],
    unresolved: tuple[Unresolved, ...] = (),
    sizes: dict[str, Effort] | None = None,
    checks: tuple[Checked, ...] = (),
) -> str:
    return "\n".join(coverage(rank(scores), unresolved, sizes, checks))


def test_the_scope_states_both_numbers_and_softens_neither() -> None:
    """The residual is the product. A block that reported only what it read would be the one
    dishonest sentence in the comment."""
    block = _block(SCORES, sizes=SIZES)

    assert "touches **8** file(s)" in block
    assert "**3** were read line by line" in block
    assert "5 more file(s), nothing found" in block


def test_the_alarming_phrase_is_gone() -> None:
    """**THE WORDS WERE THE DEFECT.** "53 not reviewed" says *untouched*; what happened is that
    every file got the deterministic half and three got the model read as well. Both sentences
    are true and only one of them frightens a developer waiting to merge."""
    block = _block(SCORES)

    assert "not reviewed" not in block
    assert "not read closely" not in block


def test_a_construct_we_could_not_parse_is_still_reported() -> None:
    """Typed silence survives the rewrite. This line is the other half of the coverage claim."""
    silence = (Unresolved(Site("src/mod0.py", 3), Reason.DYNAMIC_DISPATCH, Construct.CALL_SITE),)
    block = _block(SCORES, silence)

    assert "1 construct(s) could not be parsed" in block


def test_no_construct_means_no_line_about_constructs() -> None:
    """The false-positive direction: a clean parse must not print a zero."""
    assert "could not be parsed" not in _block(SCORES)


def test_test_files_are_never_dropped() -> None:
    """**RESEARCHED BEFORE IT WAS DECIDED, AND THE RESEARCH SAID NO.** The ask was to hide test
    files so a developer stops wading through forty paths.

    GitHub's own answer to that problem is COLLAPSE — even `linguist-generated` files stay listed
    and only their diff folds — and the review literature is explicit that noticing inadequate
    testing is one of the few things human review is reliably good at, which needs them visible.

    **THE SPLIT IS FOUND/NOT-FOUND RATHER THAN SOURCE/TEST, AND THAT SUBSUMES IT.** The reason to
    group tests was that developers skip them; the signal they were actually skipping on is "there
    is nothing here", which is what the fold now means. A test file with a real finding stays in
    the open, where a source/test split would have buried it.
    """
    block = _block({"src/a.py": 9, "tests/test_a.py": 8, "src/b.py": 7})

    assert "`tests/test_a.py`" in block, "a test file was dropped from the list"


def test_every_changed_file_is_reachable_even_the_ones_not_read() -> None:
    """The developer's half: nothing was hidden, and they can check any of it."""
    block = _block(SCORES)

    for path in SCORES:
        assert f"`{path}`" in block, f"{path} changed and was never shown to the author"
