"""What the author said this change is for, printed above whatever we found.

WHAT: `goal(context)` renders `ingest.context.tickets.Context` as the comment's first block: the
      stated goal, the tickets behind it, and every reference we did not read.
WHY:  **THE GOAL USED TO APPEAR ONLY WHEN A MODEL PRODUCED A SUMMARY.** `render/comment.py` prints
      `verdict_block.verdicts(summary)` and nothing else carries intent, so on a delivery where
      `infer/` was off, refused, or hit MAX_TOKENS the comment answered *is anything wrong here*
      and never *is this what you said you were doing*. This block is built from the pull request's
      own text and one API read, so it is there whatever the model manages -- which is what D6a
      means by *worth something whatever the model does*.

      **THE AUTHOR'S WORDS ARE QUOTED, NEVER SUMMARISED, AND THAT IS WHY THERE IS A LENGTH CAP
      INSTEAD.** A paraphrase moves the target the review is measured against. A body longer than
      the cap is TRUNCATED AND SAID TO BE -- the reader can open the pull request, and a silent
      trim would let a comment appear to quote a goal in full while dropping the sentence that
      qualified it.

      **"THE AUTHOR STATED NO GOAL" IS PRINTED, NOT OMITTED.** An empty body is a real answer and
      a fair one to show a reviewer; a section that disappears reads as a section with nothing to
      report, which is the collapse `AGENTS.md` non-negotiable 3 exists to prevent.

      **DECLINED REFERENCES ARE SHOWN WITH THE ONES WE READ.** A reader who sees three tickets and
      no note cannot tell that a fourth was refused for crossing into another repository. The
      point of naming it is that the context exists and we chose not to move it.

      **NO STATE IS INTERPRETED.** A closed ticket is printed closed. Whether closing it before
      merge is right is a judgement about someone's process, and this block makes none.
IMPORTS: `ingest.context.tickets` — leftward, and only its value objects.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from quantamind.ingest.context.tickets import Context

HEADING = "**What this change says it is for**"
NO_GOAL = "_The author stated no goal — no title text and an empty description._"
UNREADABLE = (
    "_We could not read this pull request's own description, so nothing here is a statement "
    "about what the author wrote: {why}._"
)
BEHIND = "**Behind it**"
NOT_READ = "**Not read**"
BODY_CAP = 600
"""Characters of the author's body quoted. A COST to the reader's attention, not to ours."""

TRUNCATED = "…\n\n_Quoted to {cap} characters; the rest is on the pull request._"


def _stated(context: Context) -> list[str]:
    """Title and body, the fact that there was neither, or the fact that we could not look.

    **THE THIRD CASE IS WHY THIS IS NOT TWO LINES.** "The author stated no goal" is an assertion
    about somebody's work; making it out of our own failed read would be a claim we did not earn,
    and it is the shape `AGENTS.md` non-negotiable 3 names — silence and failure on one wire.
    """
    if context.unreadable:
        return [UNREADABLE.format(why=context.unreadable), ""]
    text = context.stated.text()
    if not text:
        return [NO_GOAL, ""]
    if len(text) > BODY_CAP:
        text = text[:BODY_CAP].rstrip() + TRUNCATED.format(cap=BODY_CAP)
    # Quoted so a body carrying its own headings cannot restructure our comment.
    return [*(f"> {line}" if line else ">" for line in text.splitlines()), ""]


def goal(context: Context) -> str:
    """The block, or an empty string when the author wrote nothing and named nothing.

    **EMPTY IN, EMPTY OUT — AND THAT IS THE ONE CASE WHERE SILENCE IS HONEST.** `Context.empty()`
    is true only when there was no title, no body and no reference at all, which is a pull request
    carrying no stated intent for us to show. Every other absence is printed as an absence.
    """
    if context.empty():
        return ""

    lines = [HEADING, ""]
    lines += _stated(context)

    if context.tickets:
        lines += [BEHIND, ""]
        lines += [f"- {ticket.render()}" for ticket in context.tickets]
        lines.append("")

    if context.skipped:
        lines += [NOT_READ, ""]
        lines += [f"- {item.render()}" for item in context.skipped]
        lines.append("")

    return "\n".join(lines).rstrip()
