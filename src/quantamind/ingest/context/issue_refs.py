"""The issue references a pull request's own text makes, and which of them we may follow.

WHAT: `references(title, body)` returns one `Ref` per distinct issue named in the author's text,
      each carrying the closing keyword when there was one and whether it points outside this
      repository.
WHY:  **NOTHING IN THIS CODEBASE HAS EVER READ `Closes #412`.** `ingest/diff.stated_goal` fetches
      the title and body and `infer/change_review` is its only consumer, so the ticket behind a
      change reaches a model and never reaches the human -- which is the whole of D6a, and the
      first half of the question this product exists to answer. A goal shown only when a model
      produced a summary is a goal shown on the path measured at 25.0% correct.

      **WHETHER A REFERENCE LEAVES THIS REPOSITORY IS DECIDED HERE, WHERE THE TEXT IS, AND NOT AT
      THE FETCH.** `otherorg/private#5` is a reference we may hold no installation token for, and
      whose title would move somebody's data into this repository's comment if we quoted it.
      `docs/plans/product/product-build.md` "D6c Sources, cheapest first" states the rule --
      *egress is a decision, not a detail* -- and it binds here first because here it costs
      nothing. `Ref.foreign` is what `tickets.py` refuses on; this module never calls anything.

      **THE CLOSING KEYWORD IS KEPT BECAUSE IT IS A DIFFERENT CLAIM.** "Closes #412" says this
      change finishes that work; a bare "#412" says only that somebody thought it related. Folding
      them together would print a stronger claim than the author made, in a block whose entire job
      is to state the author's claim faithfully.

      **ORDER IS THE AUTHOR'S, NOT SORTED.** The first reference in a body is usually the one the
      change is for. Sorting by number would put a five-year-old ticket above it.
IMPORTS: stdlib re, dataclasses. Nothing from this project.
CONSUMED BY: `ingest/context/tickets.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# `closes #412`, `Fixes: owner/name#7`, `resolved https://github.com/o/n/issues/9`. GitHub's own
# list, which is what an author's habit follows.
CLOSING = "close[sd]?|fix(?:e[sd])?|resolve[sd]?"

# Three spellings of one reference, in one pattern so a body is scanned once and the ORDER the
# author wrote them in survives. `owner/name` is optional; the URL form carries it in the path.
REFERENCE = re.compile(
    rf"(?:(?P<keyword>{CLOSING})\b[:\s]+)?"
    r"(?:"
    r"https?://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/(?:issues|pull)/(?P<url_number>\d+)"
    r"|(?:(?P<repo>[\w.-]+/[\w.-]+))?#(?P<number>\d+)"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Ref:
    """One issue the author named, and what they claimed about it."""

    repo: str
    """`owner/name`, always resolved -- an unqualified `#412` takes the reviewed repository's."""

    number: int
    keyword: str = ""
    """The closing word the author used, lowercased, or empty for a bare mention."""

    foreign: bool = False
    """True when this points at another repository. Named in the comment, never fetched."""

    def render(self) -> str:
        """How the author's claim reads back: `closes #412`, or `owner/name#7`."""
        where = "" if not self.foreign else self.repo
        return f"{self.keyword} {where}#{self.number}".strip()


def references(title: str, body: str, repo: str) -> tuple[Ref, ...]:
    """Every distinct issue named in the author's own text, in the order they wrote them.

    **DE-DUPLICATED ON REPOSITORY AND NUMBER, KEEPING THE FIRST.** A body that says "Closes #412"
    and mentions "#412" again three paragraphs down names one ticket, and fetching it twice would
    print it twice. The FIRST occurrence wins because that is where the keyword usually is; taking
    the last would silently downgrade "closes #412" to a bare mention.
    """
    seen: set[tuple[str, int]] = set()
    found: list[Ref] = []
    for match in REFERENCE.finditer(f"{title}\n{body}"):
        number = int(match["url_number"] or match["number"])
        where = (match["url_repo"] or match["repo"] or repo).strip("/")
        key = (where, number)
        if key in seen:
            continue
        seen.add(key)
        found.append(
            Ref(
                repo=where,
                number=number,
                keyword=(match["keyword"] or "").lower(),
                foreign=where.lower() != repo.lower(),
            )
        )
    return tuple(found)
