"""What the comment must never tell a customer, whatever block it is rendering.

WHAT: Renders through `render.comment.comment()` and asserts that no string describing OUR METHOD
      reaches the body, on the normal path and the refusal path.
WHY:  **THREE STRINGS LEAKED AT ONCE AND EACH WAS INDIVIDUALLY DEFENSIBLE.** "only the ranking
      below ran", "what the ranking could still say", and "the ones this repository's own history
      points at first". Together they turned a message about somebody's change into a description
      of our pipeline, and it took a person reading a real posted comment to see it.

      **`publishing-rules.md` IS THE FLOOR AND THIS GOES BELOW IT.** Those rules never-publish what
      the ranking is built from and how the budget is split, and permit *"your repository's own
      history"*. The comment says less than it is allowed to: a developer opening a pull request
      wants to know what happened to their change, not how we decide.

      **THE TEST IS AT THE `comment()` LEVEL ON PURPOSE.** A per-block test would have caught one
      of the three. `comment()` assembles them all, so this catches the next one wherever it is
      written.
IMPORTS: quantamind.render.comment, quantamind.rank.order, quantamind.ingest.{context.tickets,diff},
      quantamind.infer.change_summary.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.infer.change_summary import Summary
from quantamind.ingest.context.tickets import Context
from quantamind.ingest.diff import Stated
from quantamind.rank.order import rank
from quantamind.render.comment import comment

CASES = {"ordered": {"a.py": 40, "b.py": 12, "c.py": 3, "d.py": 1}}
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


# Words that describe OUR METHOD rather than the customer's code. `publishing-rules.md`
# never-publishes what the ranking is built from and how the budget is split, and the sentence
# goes further than that: a developer opening a pull request wants to know what happened to their
# change, not how we decide. Reported by reading a real posted comment.
OUR_METHOD = ("rank", "history", "budget", "prior fix", "not reviewed", "decile", "percentile")


def test_the_comment_describes_their_code_and_never_our_method() -> None:
    """**THE COMMENT IS ABOUT THEIR PULL REQUEST, NOT ABOUT US.**

    Three strings leaked at once — "only the ranking below ran", "what the ranking could still
    say", and "the ones this repository's own history points at first". Each was individually
    defensible; together they made a message about somebody's change read as a description of our
    pipeline. This fails on any of them coming back, in any block, because `comment()` assembles
    them all and a per-block test would miss the next one.
    """
    body = comment(
        rank(CASES["ordered"]),
        summary=FULL,
        context=Context(stated=Stated("feat(store): the audit trail", "")),
    ).lower()

    for word in OUR_METHOD:
        assert word not in body, f"the comment told the customer about our method: {word!r}"


def test_a_review_that_could_not_run_also_says_nothing_about_our_method() -> None:
    """The refusal path renders different strings and leaked one of the three."""
    body = comment(rank(CASES["ordered"]), summary=FULL, blind="the model was unreachable").lower()

    for word in OUR_METHOD:
        assert word not in body, f"the refusal told the customer about our method: {word!r}"
