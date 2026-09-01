"""Whether anything but the ranking has something to say.

WHAT: `beyond_the_ranking(...)` — True when the full comment body is worth rendering, False when
      the ranking-only one says everything there is.
WHY:  **SPLIT OUT OF `render/comment.py` WHEN IT HIT THE 200-LINE CAP, AND IT IS A REAL SEAM.**
      That module decides what a comment SAYS; this one decides whether there is a comment to say
      it in. They failed for different reasons within a day of each other.

      **`effort` IS DELIBERATELY NOT A TERM HERE, AND THAT IS THE ONE ASYMMETRY.** Every other
      argument corresponds to a SECTION that would be rendered and then thrown away if it were
      missing. Per-file sizes decorate the scope line, which renders regardless — so including it
      would make a change with nothing to say produce a full comment on the strength of some line
      counts. The invariant is "every section has a term", not "every argument".
IMPORTS: ingest.context.tickets, parse.duplicate_bodies, render.blocks.verdict_block,
      types.{checked,finding}.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.ingest.context.tickets import Context
from quantamind.parse.duplicate_bodies import Duplicates
from quantamind.parse.public_api import Break
from quantamind.render.blocks.verdict_block import Stated
from quantamind.types.finding import Finding
from quantamind.types.standards.checked import Checked


def beyond_the_ranking(
    *,
    summary: Stated | None = None,
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
    blind: str = "",
    context: Context | None = None,
    repeated: Duplicates | None = None,
    breaks: Sequence[Break] = (),
) -> bool:
    """Whether anything but the ranking has something to say, so the fuller body is worth rendering.

    **THIS WAS AN EXPRESSION AT THE CALL SITE AND IT WAS MISSING A TERM.** `serve/review_delivery`
    chose between this body and the ranking-only one with
    `told is not None or kept or checks`, which omits `blind` — so when the model was UNREACHABLE
    and the change had no findings and no declared rules, the comment fell back to the ranking and
    **the "I could not review this change" banner was discarded**. A refusal degrading into a
    comment that looks ordinary is the exact failure `_headline` exists to prevent, defeated one
    layer above it. Found by this product reviewing its own pull request,
    `QuantaMinds/quanta_mind#91`.

    **IT TAKES THE SAME ARGUMENTS `comment()` DOES, ON PURPOSE.** One signature decides both what
    is rendered and whether it is worth rendering, so a new section cannot be added to one without
    the other refusing it — which is how the missing term survived in the first place.
    """
    return bool(
        summary is not None
        or findings
        or checks
        or blind
        or (context is not None and not context.empty())
        or (repeated is not None and bool(repeated.repeats))
        or bool(breaks)
    )
