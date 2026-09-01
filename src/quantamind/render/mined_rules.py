"""The standards a team keeps repeating, written up for a human to accept or refuse.

WHAT: `report(proposals, repo, read)` renders mined `Proposal`s as markdown. `read` is how many
      comments were examined, and it is printed whether or not anything was found.
WHY:  **D1d, AND THE HONEST NUMBER IS THE POINT OF THE PAGE.** Measured over 1,213 real comments
      from eight repositories, the yield is **~1.6 candidate clusters per repository and under one
      generalizable standard**. A page that shows three proposals without saying it read 180
      comments to find them invites the reader to believe the miner is thorough.
      → `docs/findings/standards/D1D_REVIEWER_REPETITION_YIELD_2026-08.md`

      **NOTHING HERE IS A RULE AND THE PAGE SAYS SO TWICE.** Once at the top, and once beside the
      copyable declaration. `.quantamind/rules.toml` is edited by a person; this product does not
      write to it. A miner that could install its own standards would be deciding what a team's
      standards are, which is the customer's job and not ours.

      **A PROPOSAL WE COULD NOT CHECK ACROSS CHANGES SAYS SO.** `Proposal.distinct_pulls` is `None`
      when the source carried no pull numbers, and that renders as its own sentence rather than as
      a missing one — four of thirteen real clusters were one reviewer restating themselves inside
      a single thread, and the reader cannot tell those apart without being told.

      **AN EMPTY REPORT IS A DOCUMENT, NOT A BLANK.** "We read 180 comments and found nothing
      repeated" is a finding a team can act on; an empty page reads as a broken tool.
IMPORTS: types.standards.proposal for `Proposal`. Leftward only.
CONSUMED BY: `serve/commands/run_standards.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.standards.proposal import Proposal

QUOTE_CAP = 200
"""Characters of a proposal shown. The full comment is on the pull request, which is linked."""

CAVEAT = (
    "**These are proposals, not rules.** Nothing was added to `.quantamind/rules.toml` and nothing "
    "will be — a standard is yours to declare. Each was said more than once in review; that is the "
    "only claim made about it."
)


def _trim(text: str) -> str:
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= QUOTE_CAP else collapsed[: QUOTE_CAP - 1] + "…"


def _recurrence(proposal: Proposal) -> str:
    """One sentence on how strong the repetition is. **Never silent about not knowing.**"""
    if proposal.across_changes:
        return f"Said on {proposal.distinct_pulls} different changes."
    if proposal.distinct_pulls is None:
        return (
            "The comments read carried no pull request number, so whether this recurs across "
            "changes or is one reviewer restating themselves **could not be checked**."
        )
    return "Said more than once, but all on the same change — possibly one reviewer restating."


def report(proposals: Sequence[Proposal], repo: str, read: int) -> str:
    """The mined-standards page for one repository."""
    lines = [f"# Repeated review comments in `{repo}`", ""]

    if not proposals:
        # **AN EMPTY RESULT IS STATED, NOT IMPLIED.** See the module docstring.
        lines += [
            f"Read **{read}** review comment(s). **Nothing was said more than once** in a way that "
            "looks like a standard.",
            "",
            "That is a normal result. Across eight public repositories this finds roughly one "
            "candidate per repository, and often none.",
            "",
        ]
        return "\n".join(lines)

    lines += [
        f"Read **{read}** review comment(s) and found **{len(proposals)}** point(s) made more "
        "than once.",
        "",
        CAVEAT,
        "",
    ]

    for index, proposal in enumerate(proposals, 1):
        lines += [
            f"## {index}. Said {proposal.occurrences} times",
            "",
            f"> {_trim(proposal.text)}",
            "",
        ]
        lines += [_recurrence(proposal), ""]
        touched = proposal.paths()
        if touched:
            shown = ", ".join(f"`{p}`" for p in touched[:3])
            more = len(touched) - 3
            lines += [
                f"About {shown}" + (f" and {more} more file(s)" if more > 0 else "") + ".",
                "",
            ]

    lines += [
        "---",
        "",
        "To adopt one, write it in `.quantamind/rules.toml` yourself. A rule needs a description a "
        "developer can act on, and the sentence above is a review comment, not that description.",
        "",
    ]
    return "\n".join(lines)
