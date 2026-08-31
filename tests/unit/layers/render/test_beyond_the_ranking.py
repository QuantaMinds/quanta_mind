"""Whether the fuller body is worth rendering, and the term that was missing from that decision.

WHAT: Drives `render.comment.beyond_the_ranking()` over each input that should make a comment more
      than a file list, and over the one case where nothing should.
WHY:  **THIS PRODUCT FOUND THIS BUG ON ITS OWN PULL REQUEST.** The decision lived at the call site
      in `serve/review_delivery.py` as `told is not None or kept or checks`, and `quanminds[bot]`
      reported against `QuantaMinds/quanta_mind#91` that it *"incorrectly omits the unreadable
      status, causing failure information from the explain step to be dropped from the review
      comment if no other findings are present."* It was right.

      **WHAT THAT COST IS THE THING `_headline` EXISTS TO PREVENT, DEFEATED ONE LAYER ABOVE IT.**
      When the model is unreachable, `comment()` renders "I could not review this change" at the
      top — and the caller then threw that body away for the ranking-only one, so a refusal
      degraded into a comment that looks like an ordinary quiet review. Every unit test passed:
      each half was correct alone, which is the shape this repository keeps finding.

      **THE PREDICATE TAKES `comment()`'s OWN ARGUMENTS SO THE TWO CANNOT DRIFT.** A section added
      to the body without a term here would be rendered and then discarded, which is exactly how
      `blind` came to be missing.
IMPORTS: quantamind.render.comment, quantamind.ingest.{context.tickets,diff}, quantamind.types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.infer.change_summary import Summary
from quantamind.ingest.context.tickets import Context
from quantamind.ingest.diff import Stated
from quantamind.render.comment import beyond_the_ranking
from quantamind.types.checked import Checked, Outcome
from quantamind.types.finding import Finding
from quantamind.types.verdict import Site

SUMMARY = Summary(
    what_changed="Adds a table.",
    achieves_goal=True,
    reasoning="Present.",
    goal="feat(store): the audit trail",
    impact="Additive only.",
    breaks=False,
    breaks_why="Additive.",
    convention="",
    dependents=(),
)
FINDING = Finding(path="src/a.py", quote="value = None", claim="This can be None.")
CHECK = Checked("no-print", Site("src/a.py", 1), Outcome.VIOLATED, evidence="print at line 1")
EMPTY = Context(stated=Stated("", ""))


def test_nothing_to_add_means_the_ranking_only_body() -> None:
    """The honest negative. Without it every case below passes against `return True`."""
    assert beyond_the_ranking() is False
    assert (
        beyond_the_ranking(summary=None, findings=(), checks=(), blind="", context=EMPTY) is False
    )


def test_an_unreachable_model_keeps_the_fuller_body() -> None:
    """**THE BUG, AS AN ASSERTION.** `blind` was the term the call site omitted, so the refusal
    banner was rendered and then discarded on exactly the deliveries that could not review."""
    assert beyond_the_ranking(blind="the model was unreachable") is True


@pytest.mark.parametrize(
    ("name", "kwargs"),
    [
        ("a model summary", {"summary": SUMMARY}),
        ("a published finding", {"findings": (FINDING,)}),
        ("a rule verdict", {"checks": (CHECK,)}),
        ("a stated goal", {"context": Context(stated=Stated("Retire the shim", ""))}),
        ("a ticket behind it", {"context": Context(stated=Stated("", "Closes #90"))}),
    ],
)
def test_each_thing_that_makes_a_comment_more_than_a_file_list(
    name: str, kwargs: dict[str, object]
) -> None:
    """One term each, alone. A missing term is invisible when another is always present too."""
    assert beyond_the_ranking(**kwargs) is True, f"{name} was rendered and would be discarded"


def test_no_context_at_all_is_not_the_same_as_an_empty_one() -> None:
    """`None` is the CLI, which has no pull request to read a goal from. Neither speaks, and
    neither may raise — `Context | None` is a real state, not a caller's oversight."""
    assert beyond_the_ranking(context=None) is False
