"""The goal block, and the three absences it must not print alike.

WHAT: Drives `render.context.goal_block.goal()` over every state a `Context` can hold, and pins
      that the block reaches `render.comment.comment()` without a model summary.
WHY:  **THE LAST ASSERTION IS THE REASON D6a EXISTS.** Intent used to reach a pull request only
      through `verdict_block.verdicts(summary)`, so on a delivery where `infer/` was off, refused,
      or hit MAX_TOKENS the comment answered *is anything wrong here* and never *is this what you
      said you were doing*. `test_the_block_survives_a_delivery_with_no_model_summary` is that
      property, and it fails against the version of `comment.py` this branch started from.

      **THREE ABSENCES, THREE DIFFERENT LINES.** No goal stated; the description unreadable;
      nothing at all. The middle one is ours and the other two are the pull request's, and a
      renderer that printed "the author stated no goal" after a failed read would make an
      assertion about somebody's work out of our own outage.

      **TRUNCATION IS ASSERTED TO ANNOUNCE ITSELF.** A body trimmed in silence lets a comment
      appear to quote a goal in full while dropping the sentence that qualified it.
IMPORTS: quantamind.ingest.context.tickets, quantamind.render.{comment,context.goal_block},
      quantamind.types.ranking.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.ingest.context.issue_refs import Ref
from quantamind.ingest.context.tickets import Context, Declined, Skipped, Ticket
from quantamind.ingest.diff import Stated
from quantamind.render.comment import comment
from quantamind.render.context.goal_block import BODY_CAP, goal
from quantamind.types.ranking import Ranking

OURS = Ref(repo="acme/app", number=412, keyword="closes")
THEIRS = Ref(repo="other/lib", number=7, foreign=True)


def test_nothing_at_all_renders_nothing_and_it_is_the_only_case_that_does() -> None:
    """Empty in, empty out — a pull request carrying no stated intent for us to show."""
    assert goal(Context(stated=Stated("", ""))) == ""


def test_an_author_who_stated_no_goal_is_said_so_rather_than_omitted() -> None:
    """A section that disappears reads as a section with nothing to report. This one has
    something to report: the author wrote no description."""
    block = goal(Context(stated=Stated("", ""), skipped=(Skipped(THEIRS, Declined.NOT_READABLE),)))

    assert "stated no goal" in block
    assert "could not read this pull request" not in block


def test_an_unreadable_pull_request_never_reads_as_an_author_who_wrote_nothing() -> None:
    """**OUR FAILURE, PRINTED AS OURS.** These two are one field apart and one libel apart."""
    block = goal(Context(stated=Stated("", ""), unreadable="GET /pulls/9: 502 Bad Gateway"))

    assert "could not read this pull request" in block
    assert "502 Bad Gateway" in block
    assert "stated no goal" not in block, "an outage of ours is not a statement about the author"


def test_the_authors_words_are_quoted_verbatim() -> None:
    """Paraphrasing would move the target the review is measured against."""
    block = goal(Context(stated=Stated("Retire the shim", "It has no callers left.")))

    assert "> Retire the shim" in block
    assert "> It has no callers left." in block


def test_a_body_carrying_its_own_headings_cannot_restructure_the_comment() -> None:
    """Every line is quoted, so an author's `### Summary` stays inside our block."""
    block = goal(Context(stated=Stated("T", "### Summary\n\n- a point")))

    assert "> ### Summary" in block
    assert "\n### Summary" not in block


def test_a_long_body_is_truncated_and_announces_that_it_was() -> None:
    """A silent trim lets a comment appear to quote a goal in full while dropping its caveat."""
    block = goal(Context(stated=Stated("T", "x" * (BODY_CAP * 2))))

    assert f"Quoted to {BODY_CAP} characters" in block
    assert len(block) < BODY_CAP * 2


def test_a_short_body_is_not_announced_as_truncated() -> None:
    """The cheap half of the previous test, and the one that catches an off-by-one cap."""
    assert "Quoted to" not in goal(Context(stated=Stated("T", "x" * (BODY_CAP - 10))))


def test_tickets_and_refusals_appear_together_so_the_reader_knows_what_was_left() -> None:
    """A reader who sees two tickets and no note cannot tell that a third was refused for
    crossing into another repository. Naming it is the point of refusing it."""
    block = goal(
        Context(
            stated=Stated("T", "Closes #412, see other/lib#7"),
            tickets=(Ticket(OURS, "Retire the shim", "open", is_pull=False),),
            skipped=(Skipped(THEIRS, Declined.ANOTHER_REPOSITORY),),
        )
    )

    assert "closes #412 — Retire the shim (issue, open)" in block
    assert "other/lib#7" in block
    assert "we do not quote across one" in block


def test_a_closed_ticket_is_printed_closed_and_nothing_is_concluded_from_it() -> None:
    """Whether closing a ticket before merge is right is a judgement about someone's process."""
    block = goal(
        Context(
            stated=Stated("T", "Closes #412"),
            tickets=(Ticket(OURS, "Retire the shim", "closed", is_pull=False),),
        )
    )

    assert "closed)" in block
    for word in ("already", "stale", "should", "warning"):
        assert word not in block.lower(), f"the block drew a conclusion: {word!r}"


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
    assert "> Retire the shim" in body


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
