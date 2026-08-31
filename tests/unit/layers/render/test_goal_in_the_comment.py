"""Where the goal block sits in the comment, and that it does not depend on the model.

WHAT: Renders through `render.comment.comment()` rather than the block alone, and asserts the
      block is present with no summary, present under a refusal, absent with no context, and that
      the author's description is printed exactly once.
WHY:  **SPLIT FROM `test_goal_block.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That file
      asks what the block SAYS; this one asks where it appears and what else appears beside it.
      The two failed for different reasons on this branch — one on the wording of an absence, the
      other on a paragraph printed twice.

      **THE FIRST TWO ARE THE REASON D6a EXISTS.** Intent used to reach a pull request only through
      `verdict_block.verdicts(summary)`, so on a delivery where `infer/` was off, refused, or hit
      MAX_TOKENS the comment answered *is anything wrong here* and never *is this what you said you
      were doing*. Both fail against the `comment()` this branch started from.

      **AND `test_the_pr_description_is_printed_exactly_once` IS THE ONE A LIVE COMMENT TAUGHT.**
      For one commit both blocks quoted the description, and no test objected because each was
      correct alone.
IMPORTS: quantamind.infer.change_summary, quantamind.ingest.{context.tickets,diff},
      quantamind.rank.order, quantamind.render.comment, quantamind.types.ranking.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.infer.change_summary import Summary
from quantamind.ingest.context.tickets import Context
from quantamind.ingest.diff import Stated
from quantamind.rank.order import rank
from quantamind.render.comment import comment
from quantamind.types.ranking import Ranking

ORDERED = {"a.py": 40, "b.py": 12, "c.py": 3, "d.py": 1}
FULL = Summary(
    what_changed="Adds a table and records every rule against every changed file.",
    achieves_goal=True,
    reasoning="The table, the writer and the migration are present.",
    goal="feat(store): the audit trail",
    impact="Callers are unaffected; the table is additive.",
    breaks=False,
    breaks_why="The migration only adds a table.",
    convention="",
    dependents=("a.py",),
)
STATED = Context(stated=Stated("feat(store): the audit trail", ""))


def test_the_goal_is_quoted_from_the_pr_not_summarised() -> None:
    """A model restating the goal puts a second author between the reviewer and the promise.

    **THE PROPERTY DID NOT CHANGE; ITS SOURCE DID.** This used to read the quote out of
    `Summary.goal`, so a deterministic fact was shown only when a model happened to answer.
    `render/context/goal_block.py` prints it from the same `stated_goal` read on every delivery.
    """
    body = comment(
        rank(ORDERED),
        summary=FULL,
        context=STATED,
    )

    assert "> feat(store): the audit trail" in body


def test_the_pr_description_is_printed_exactly_once() -> None:
    """**THE DEFECT THE FIRST LIVE DELIVERY WOULD HAVE SHIPPED.** Both blocks quoted it.

    `verdict_block` quoted `Summary.goal` and D6a's block quoted `Context.stated`, and they are
    filled from the same `ingest/diff.stated_goal` call — so a delivery with the model ON printed
    the author's description twice. In a product whose measured weakness is saying the same thing
    twice — 17.3% redundancy against Qodo's 1.0% — shipping a second copy of one paragraph is the
    defect we are least entitled to. Caught by reading a real posted comment, not by a test.
    """
    body = comment(
        rank(ORDERED),
        summary=FULL,
        context=STATED,
    )

    assert body.count("> feat(store): the audit trail") == 1, body
    assert body.count("Goal — from the PR description") == 0, (
        "the model-path goal heading is gone; the deterministic block carries it now"
    )


def test_the_block_survives_a_delivery_with_no_model_summary() -> None:
    """**THE WHOLE OF D6a, AS ONE ASSERTION.** `summary=None` is the delivery where `infer/` was
    off, refused, or out of tokens — precisely where the comment used to carry no statement of
    intent at all. This fails against the `comment()` this branch started from.
    """
    body = comment(
        Ranking(units=()),
        summary=None,
        context=Context(stated=Stated("Retire the shim", "Closes #412")),
    )

    assert "What this change says it is for" in body
    assert "> Closes #412" in body, (
        "the body is the goal when there is one; the title is a fallback"
    )


def test_a_review_that_could_not_run_still_says_what_the_change_claims_to_be_for() -> None:
    """`blind` suppresses the model's verdict and must not suppress the author's own words —
    a refusal that also withheld the goal would tell the reader less than the pull request does.
    """
    body = comment(
        Ranking(units=()),
        blind="the model was unreachable",
        context=Context(stated=Stated("Retire the shim", "")),
    )

    assert "could not review this change" in body
    assert "> Retire the shim" in body


def test_no_context_means_no_block_and_no_placeholder() -> None:
    """The CLI has no pull request to read a goal from, and must not print an empty heading."""
    assert "What this change says it is for" not in comment(Ranking(units=()))
