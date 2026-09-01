"""D1c: the model-judged section reaches the comment, with the words that qualify it.

WHAT: `render/comment.comment(judged=...)` — the wiring, not the block. The block has its own
      tests in `tests/unit/layers/render/blocks/test_judged_block.py`.
WHY:  **A SABOTAGE THAT REPLACED THE BLOCK WITH AN EMPTY STRING LEFT THE SUITE GREEN.** The block
      was tested and the CALL was not, so the section could be built correctly and never rendered.
      That is the same shape as a guard that runs on the wrong population: every component passes
      and the product does nothing.
IMPORTS: rank.order, render.comment, types.standards.judged, types.verdict.
"""

from __future__ import annotations

from quantamind.rank.order import rank
from quantamind.render.comment import comment
from quantamind.types.standards.judged import Judged, Verdict
from quantamind.types.verdict import Site

CASES = {"ordered": {"a.py": 40, "b.py": 12, "c.py": 3, "d.py": 1}}


def test_a_model_judged_verdict_reaches_the_comment_and_says_who_judged_it() -> None:
    """**D1c: the section can be built correctly and never wired in, and nothing would fail.**

    A sabotage that replaced the block with an empty string left the whole suite green — the block
    had its own tests and the CALL had none. This asserts the path from `comment()`'s argument to
    the posted text, including the label that stops a model's view reading as a parser's verdict.
    """
    record = Judged(
        "explain-why",
        Site("a.py", 8),
        Verdict.BROKEN,
        quote="def deceptive(rows):",
        why="Says what, not why.",
    )
    body = comment(rank(CASES["ordered"]), judged=[record])

    assert "def deceptive(rows):" in body
    assert "A model judged these" in body, "the section reached the comment without its caveat"
    assert "not counted in your compliance rate" in body


def test_no_judged_records_adds_no_section() -> None:
    """The common case — no prose rule declared — must cost the reader nothing."""
    body = comment(rank(CASES["ordered"]))
    assert "A model judged these" not in body
