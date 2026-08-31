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
    block = _block(SCORES)

    assert "touches **8** file(s)" in block
    assert "**3** were read line by line" in block
    assert "All 8 changed file(s)" in block


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


def test_tests_are_grouped_and_never_dropped() -> None:
    """**RESEARCHED BEFORE IT WAS DECIDED, AND THE RESEARCH SAID NO.** The ask was to hide test
    files so a developer stops wading through forty paths.

    GitHub's own answer to that problem is COLLAPSE — even `linguist-generated` files stay listed
    and only their diff folds — and the review literature is explicit that noticing inadequate
    testing is one of the few things human review is reliably good at, which needs them visible.
    Omitting forty files would also be the "truncation reads as covered everything" failure this
    product exists to refuse. So: grouped, counted, skippable by eye, absent from nothing.
    """
    block = _block({"src/a.py": 9, "tests/test_a.py": 8, "src/b.py": 7})

    assert "**Source — 2**" in block
    assert "**Tests — 1**" in block
    assert "`tests/test_a.py`" in block, "a test file was dropped from the list"
    assert block.index("**Source") < block.index("**Tests"), "tests came before source"


def test_a_change_with_no_tests_gets_no_empty_headings() -> None:
    """Two headings over one group is furniture. A reader should not have to parse structure that
    carries no information."""
    block = _block({"src/a.py": 9, "src/b.py": 7})

    assert "Source —" not in block
    assert "Tests —" not in block


def test_the_size_and_the_place_to_look_ride_beside_the_path() -> None:
    """The whole point: a reviewer should not have to open a file to learn it changed two lines."""
    sizes = {"src/a.py": Effort(added=160, removed=6, functions=("def handle(request):",))}
    block = _block({"src/a.py": 9, "src/b.py": 7}, sizes=sizes)

    assert "`src/a.py` — 166 lines · `def handle(request):`" in block


def test_a_file_we_have_no_size_for_says_nothing_rather_than_zero() -> None:
    """A pure rename or a binary reaches here with no parsed hunk. "0 lines" beside a file that
    certainly changed is a wrong statement where silence is merely a quiet one."""
    block = _block({"src/a.py": 9, "src/b.py": 7}, sizes={"src/a.py": Effort(added=1)})

    assert "- `src/b.py`" in block
    assert "0 lines" not in block


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


def test_no_score_from_the_ranking_reaches_the_page() -> None:
    """*What the ranking is built from* is first on the never-publish list, and a per-file fix
    count was printed in this comment once before being removed for a different reason.

    **THE ASSERTION IS THE SCORE VALUE, NOT THE SHAPE OF THE LINE.** This used to require a line
    to be a bare path — which was right until the line legitimately gained a size and a rule
    count, both from sources a customer already has. What must never appear is the number the
    RANKING computed, so the fixture uses a distinctive one and looks for it.
    """
    block = _block({"src/zebra.py": 4242, "src/apple.py": 2, "src/mango.py": 1})

    assert "4242" not in block, f"the ranking's own score reached the page: {block}"
    assert "`src/zebra.py`" in block, "the file itself must still be listed"
