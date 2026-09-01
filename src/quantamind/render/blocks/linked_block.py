"""The repositories this one declares a link to, and the fact that none of them was read.

WHAT: `linked(links, unreadable)` renders one line naming the declared links, or the fact that the
      declaration could not be read.
WHY:  **D3a SHIPS BEFORE D3b, AND THIS LINE IS WHY IT IS WORTH SHIPPING ALONE.** Reading the linked
      repository — a changed export checked against the repositories that import it — is gated on a
      design partner with more than one repository that matters. What the declaration buys today is
      TYPED SILENCE.

      `render/comment.py` prints one static sentence: *cross-repository impact is not checked at
      all*. A reader has no way to tell whether that means **there is nothing across the boundary**
      or **we did not look**. Naming the repositories makes it the second, which is the true one —
      `AGENTS.md` non-negotiable 3 applied to a boundary rather than a call site.

      **A DECLARATION WE COULD NOT READ IS NOT AN ABSENT ONE**, and the two print differently.
      "This business declares no links" is a claim about somebody's architecture, and making it out
      of our own failed read is the assertion this product refuses everywhere else.

      **NOTHING HERE IS INFERRED.** The repository name and the reason are the customer's own
      words, printed verbatim. An org-wide crawl would produce our guess about their architecture;
      a declaration is provenance an auditor can be shown.
IMPORTS: ingest.standards.links_file. Leftward, value objects only.
CONSUMED BY: `render/blocks/scope_block.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.ingest.standards.links_file import Link

LINKED_UNREADABLE = (
    "_`.quantamind/links.toml` could not be read, so whether this repository declares links to "
    "others is unknown — not established as none._"
)

LINKED = (
    "_This repository declares {count} linked repositor{y}: {names}. **Nothing in {them} was "
    "checked** — nothing this change removed is exported, so there was nothing to ask them._"
)
LINKED_ASKED = (
    "_This repository declares {count} linked repositor{y}: {names}. They were asked about the "
    "removed exports only; nothing else in them was read._"
)


def linked(links: Sequence[Link], unreadable: bool, asked: bool = False) -> list[str]:
    """The repositories this one is declared to touch, and the fact that none was looked at.

    **D3a SHIPS BEFORE D3b AND THIS LINE IS WHY IT IS WORTH SHIPPING.** Reading the linked
    repository is gated on a design partner with more than one that matters. What the declaration
    buys today is TYPED SILENCE: `render/comment.py` prints one static sentence saying
    cross-repository impact is unchecked, and a reader has no way to tell whether that means *there
    is nothing across the boundary* or *we did not look*. Naming the repositories makes it the
    second, which is the true one.

    **A DECLARATION WE COULD NOT READ IS NOT AN ABSENT ONE**, and the two print differently:
    "declares no links" is a claim about the customer's architecture, and we would be making it out
    of our own failed read.
    """
    if unreadable:
        return ["", LINKED_UNREADABLE]
    if not links:
        return []
    # **"NOTHING WAS CHECKED" IS FALSE THE MOMENT D3b ASKS ONE.** The first render of these two
    # blocks together put "Nothing in them was checked" directly beneath a section reporting that
    # `acme/billing` imports a removed export. Two true-when-written sentences contradicting each
    # other in one comment is the failure this product exists to refuse, and it appeared the first
    # time both were printed.
    return [
        "",
        (LINKED_ASKED if asked else LINKED).format(
            count=len(links),
            y="y" if len(links) == 1 else "ies",
            names=", ".join(link.render() for link in links),
            them="it" if len(links) == 1 else "them",
        ),
    ]
