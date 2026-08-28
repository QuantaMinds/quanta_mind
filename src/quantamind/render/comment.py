"""The comment we post: what to look at, and what we did not look at. Nothing about ourselves.

WHAT: `comment(ranking, unresolved)` renders the body posted on a pull request.
WHY:  **THIS USED TO EXPLAIN HOW THE PRODUCT WORKS, AND A DEVELOPER READING A PULL REQUEST DOES
      NOT CARE.** The previous body carried a paragraph of method ("ranked by prior-fix history",
      "the budget cut through a tie", "4.46% against 1.21% overall"), a sentence about whether the
      change was in the repository's top decile, and a footer disclaiming what the product is. All
      of it was true and none of it was actionable. A reviewer wants the two facts that change what
      they do: **where to look, and what nobody looked at.**

      **THE COUNTS AND THE METHOD ARE GONE FROM THE COMMENT, NOT FROM THE PRODUCT.** They still
      exist on `Ranking`, still drive the ordering, and `quantamind dashboard` still reports them.
      What changed is who they are shown to: an operator deciding whether to keep paying for this
      is the audience for a firing rate, and the developer waiting to merge is not.

      **WHAT WAS NOT REVIEWED STAYS, IN ONE CLAUSE.** It is the one piece of self-description that
      is also a fact the reader acts on — "three of thirteen files were reviewed" tells them where
      human attention is still required. Dropping it would let a partial review read as a complete
      one, which is the failure this product exists to refuse. It is stated as a count, not as an
      argument for the count.
IMPORTS: types.ranking, types.verdict. Nothing to its right.
CONSUMED BY: serve, which posts it; the live tests, which diff it against a golden file.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind"
LOOK = "**Look here first**"


def _reviewed(ranking: Ranking) -> tuple[int, int]:
    """How many units were read, and how many the change touched. Both are counts, never a rate."""
    return len(ranking.funded()), len(ranking.units)


def comment(ranking: Ranking, unresolved: Sequence[Unresolved] = ()) -> str:
    """The comment body. Short, and about the reader's change rather than about us."""
    read, total = _reviewed(ranking)
    lines = [HEADER, ""]

    funded = ranking.funded()
    if funded:
        lines.append(LOOK)
        lines.extend(f"- `{unit.unit.qualified_name}`" for unit in funded)
        lines.append("")

    # **THE UNREVIEWED COUNT IS NOT OPTIONAL.** Without it a review of 3 files out of 13 reads as
    # a review of the change. `unresolved` is folded into the same sentence rather than given a
    # paragraph: a reader needs to know something was unreadable, not why our parser said so.
    unread = total - read
    parts = [f"{read} of {total} changed file(s) reviewed" if total else "Nothing to review"]
    if unread > 0:
        parts.append(f"{unread} not reviewed")
    if unresolved:
        parts.append(f"{len(unresolved)} construct(s) could not be parsed")
    lines.append(f"_{'; '.join(parts)}._")
    return "\n".join(lines)
