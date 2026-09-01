"""The first line of the comment: the one sentence a developer reads before deciding to read on.

WHAT: `headline(summary, findings, violations, blind)` returns one of four openings, and `HEADER`
      is the product's name above it.
WHY:  **SPLIT OUT OF `render/comment.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** `comment()`
      assembles sections; this decides a verdict from four inputs and returns one sentence. It has
      changed for product reasons three times while the assembly around it did not move.

      **`BLIND` OUTRANKS EVERYTHING.** A review that could not run must not open with a verdict on
      code nobody read — that is the single most damaging sentence this product can print, and it
      is why the refusal is checked first rather than folded into the good case.

      **A PARSER'S VIOLATION OUTRANKS A MODEL'S FINDING.** A broken declared rule is reproducible;
      a model finding is 66.7-82.1% wrong raw. The louder headline belongs to the claim that holds.
IMPORTS: render.blocks.verdict_block for `Stated`, types.finding. Leftward and sideways.
CONSUMED BY: `render/comment.py`, and `render/speaks.py` for the fallback body.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.render.blocks.verdict_block import Stated
from quantamind.types.finding import Finding

HEADER = "### QuantaMind"


GOOD = "✅ **Looks good.**"
HUMAN = "⚠️ **Needs a human.**"
BUGS = "🐛 **Found {count} thing(s) worth fixing.**"
BLIND = (
    "⚠️ **I could not review this change.** {why}\n\n"
    "Nothing below is a verdict on your code — it is only what could still be checked."
)
LOOK = "**Look here first**"
NOT_CHECKED = (
    "_Callers are found by static Python import only: a dynamic import, a re-export, or another "
    "language is invisible to it, and cross-repository impact is not checked at all._"
)


def headline(
    summary: Stated | None, findings: Sequence[Finding], violations: int, blind: str
) -> str:
    """The first line, which is the only line some readers will act on.

    **A REVIEW THAT COULD NOT RUN MUST NOT LOOK LIKE ONE THAT FOUND NOTHING.** A real delivery hit
    MAX_TOKENS, the summary was dropped, and the comment degraded into a list of files with no
    verdict — indistinguishable from a clean review to anybody reading it.

    **IT SUMMARISES THE SECTIONS BELOW; IT DOES NOT REPLACE THEM.** An earlier version of this
    collapsed the goal and both verdicts into one line, and the review became an opinion with no
    stated basis. `verdict_block.SECTIONS` is mandatory and a test enforces it.
    """
    if blind:
        return BLIND.format(why=blind)
    count = len(findings) + violations
    if count:
        return BUGS.format(count=count)
    if summary is None:
        return HUMAN + " No model read this change; the checks below still ran."
    if summary.achieves_goal is not True:
        return f"{HUMAN} It may not do what the PR says."
    if summary.breaks is not False:
        return f"{HUMAN} Whether it breaks callers is not settled."
    if summary.convention:
        return f"{HUMAN} It breaks a rule you wrote down."
    return f"{GOOD} It does what the PR says, and nothing that imports it breaks."
