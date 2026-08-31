"""What we read closely, what we did not, and every changed file behind a fold.

WHAT: `coverage(ranking, unresolved)` renders the comment's last block: the scope line and a
      `<details>` list of every changed file.
WHY:  **"3 OF 56 FILE(S) REVIEWED; 53 NOT REVIEWED" READ AS A FAILURE, AND IT IS THE PRODUCT
      WORKING.** A developer waiting to merge saw a large number beside the words "not reviewed"
      and had no way to tell a deliberate budget from a crash. Reported by the person who ships
      this, reading a real comment.

      **THE COUNT IS NOT SOFTENED AND NOTHING IS HIDDEN.** `AGENTS.md` calls the residual the
      product, and a scope line that shrank to spare feelings would be the one dishonest sentence
      in the whole comment. What changed is that a deliberate scope now reads as one, and the
      files it did not read closely are one click away instead of absent.

      **THE LIST CARRIES PATHS AND NOTHING ELSE, AND IT IS ALPHABETICAL. THAT IS A PUBLISHING RULE,
      NOT A LAYOUT CHOICE.** `docs/product/publishing-rules.md` never-publishes *what the ranking
      is built from* and *how the budget is split across a change*. A per-file fix count is the
      first — it was in this comment once and was removed for a different reason — and printing
      the list in RANK order is the second, because a reader could count down to the cut and read
      the budget straight off it. Alphabetical shows a developer every file we saw and hands a
      competitor nothing. *"Your repository's own history"* is the phrasing those rules do allow,
      and it is the phrasing used.

      **`<details>` IS MARKDOWN GITHUB RENDERS AND NEEDS NO SCRIPT.** A link would point at a page
      the reader is not signed in to; a button needs a surface we do not serve on their pull
      request. `dependencies = []` holds either way.
IMPORTS: types.{ranking,verdict}. Nothing to its right.
CONSUMED BY: `render/comment.py`, as the last block.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

SCOPE = (
    "_Read closely: **{read} of {total}** changed file(s) — the ones this repository's own history "
    "points at first. The rest were ranked and not read closely._"
)
NOTHING = "_Nothing to review._"
ALL_FILES = "<details><summary>All {total} changed file(s)</summary>"


def coverage(ranking: Ranking, unresolved: Sequence[Unresolved]) -> list[str]:
    """The scope line, and the full file list behind a fold.

    **"3 OF 56 REVIEWED; 53 NOT REVIEWED" READ AS A FAILURE, AND IT IS THE PRODUCT WORKING.**
    A developer waiting to merge saw a large number next to the words "not reviewed" and had no
    way to tell a deliberate budget from a crash. The count is not softened and nothing is hidden
    — `AGENTS.md` calls the residual the product — but a scope stated as a choice reads as one,
    and the files are one click away rather than absent.

    **THE LIST CARRIES PATHS AND NOTHING ELSE, AND IT IS ALPHABETICAL.**
    `docs/product/publishing-rules.md` never-publishes *what the ranking is built from* and *how
    the budget is split across a change*. Per-file fix counts are the first; printing the list in
    RANK order would be the second, since the reader could read the budget straight off it.
    Alphabetical order shows a developer every file we saw without handing a competitor the
    mechanism — and "this repository's own history" is the phrasing those rules do permit.

    **THE FOLD IS `<details>`, WHICH IS MARKDOWN GITHUB RENDERS AND NEEDS NO SCRIPT.** A link
    would point somewhere a reader is not signed in to; a button needs a page we do not serve.
    """
    total = len(ranking.units)
    if not total:
        return [NOTHING]

    funded = {unit.unit.site.path for unit in ranking.funded()}
    out = [SCOPE.format(read=len(funded), total=total)]
    if unresolved:
        out.append("")
        out.append(f"_{len(unresolved)} construct(s) could not be parsed._")

    paths = sorted({unit.unit.site.path for unit in ranking.units})
    out += ["", ALL_FILES.format(total=total), ""]
    out += [f"- `{path}`" + (" — read closely" if path in funded else "") for path in paths]
    out += ["", "</details>"]
    return out
