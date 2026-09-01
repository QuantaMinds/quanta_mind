"""D1c: the section must never let a model's view read like a parser's verdict.

WHAT: `render/blocks/judged_block.py` over `Judged` records, and its place in the whole comment.
WHY:  **WRITTEN AFTER A SABOTAGE PASSED.** Deleting the "not decided" count from the summary line
      changed no test, which meant the block's central honesty claim was unenforced: without that
      count, "the model raised nothing" reads as "everything was judged and held" even when the
      transport failed on every file. Each test below pins one word or number the reader depends on.
IMPORTS: render.blocks.judged_block, types.standards.judged, types.verdict.
"""

from __future__ import annotations

from quantamind.render.blocks.judged_block import MAX_SHOWN, judged
from quantamind.types.standards.judged import Judged, Verdict
from quantamind.types.verdict import Site

BROKEN = Judged(
    "explain-why",
    Site("src/app.py", 8),
    Verdict.BROKEN,
    quote="def deceptive(rows):",
    why="Says what it does, not why it exists.",
)
MET = Judged("explain-why", Site("src/ok.py"), Verdict.MET)
UNDECIDED = Judged("explain-why", Site("src/x.py"), Verdict.UNDECIDED, why="could not be asked")


def test_no_records_renders_nothing() -> None:
    """A repository that declared no prose rule gets no section, not an empty heading."""
    assert judged([]) == ""


def test_the_section_says_a_model_decided_it_before_any_claim() -> None:
    """**THE LABEL IS THE POINT OF THE SECTION.** Without it this reads like the rule table."""
    text = judged([BROKEN])
    label = text.index("A model judged these")
    assert label < text.index("explain-why"), "the caveat must precede the first claim"
    assert "cannot be re-run" in text
    assert "not counted in your compliance rate" in text


def test_a_broken_verdict_shows_the_quote_the_reader_can_find() -> None:
    """A finding the developer cannot locate in their own file is not actionable."""
    text = judged([BROKEN])
    assert "def deceptive(rows):" in text
    assert "src/app.py:8" in text or "src/app.py" in text
    assert "Says what it does, not why it exists." in text


def test_the_undecided_count_is_printed() -> None:
    """**"Nothing raised" must not read as "everything held".**

    This is the assertion a sabotage slipped past when it did not exist: with the count gone, a run
    where every single file failed to be judged renders identically to a clean one.
    """
    text = judged([MET, UNDECIDED, UNDECIDED])
    assert "2 not decided" in text
    assert "not passes" in text


def test_a_clean_run_says_so_without_claiming_more() -> None:
    """No undecided rows means the tail states the counts and stops."""
    text = judged([MET, MET])
    assert "2 met" in text
    assert "not decided" not in text
    assert "The model raised nothing" in text


def test_zero_decided_does_not_render_as_a_pass() -> None:
    """**Every file undecided is the case most likely to be misread as compliance.**"""
    text = judged([UNDECIDED, UNDECIDED])
    assert "0 met" in text
    assert "2 not decided" in text


def test_the_heading_does_not_borrow_the_parsers_certainty() -> None:
    """A parser found a violation; a model formed a view. The words differ on purpose."""
    text = judged([BROKEN])
    assert "violation" not in text.lower()


def test_extra_broken_records_are_counted_not_dropped() -> None:
    """**A fold that does not say it folded is a silent truncation.**"""
    text = judged([BROKEN] * (MAX_SHOWN + 3))
    assert "3 more" in text
