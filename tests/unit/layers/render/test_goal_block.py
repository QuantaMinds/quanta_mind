"""The goal block, and the three absences it must not print alike.

WHAT: Drives `render.context.goal_block.goal()` over every state a `Context` can hold. Where the
      block sits in the comment is `test_goal_in_the_comment.py`, split off at the 200-line cap.
WHY:  **THREE ABSENCES, THREE DIFFERENT LINES.** No goal stated; the description unreadable;
      nothing at all. The middle one is ours and the other two are the pull request's, and a
      renderer that printed "the author stated no goal" after a failed read would make an
      assertion about somebody's work out of our own outage.

      **TRUNCATION IS ASSERTED TO ANNOUNCE ITSELF.** A body trimmed in silence lets a comment
      appear to quote a goal in full while dropping the sentence that qualified it.
IMPORTS: quantamind.ingest.{context.issue_refs,context.tickets,diff},
      quantamind.render.context.goal_block.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.ingest.context.issue_refs import Ref
from quantamind.ingest.context.tickets import Context, Declined, Skipped, Ticket
from quantamind.ingest.diff import Stated
from quantamind.render.context.goal_block import BODY_CAP, goal

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

    assert "> It has no callers left." in block


def test_the_title_is_not_repeated_when_there_is_a_body() -> None:
    """GitHub prints the title above the comment. Quoting it here spends a line on something the
    reader is already looking at, which is the cheapest kind of length to cut."""
    block = goal(Context(stated=Stated("Retire the shim", "It has no callers left.")))

    assert "Retire the shim" not in block


def test_a_pull_request_with_only_a_title_quotes_the_title() -> None:
    """**AND THIS IS WHY IT IS A FALLBACK AND NOT A DELETION.** A title with no body IS a stated
    goal, and dropping it would print "the author stated no goal" about somebody who stated one."""
    block = goal(Context(stated=Stated("Retire the shim", "")))

    assert "> Retire the shim" in block
    assert "stated no goal" not in block


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
