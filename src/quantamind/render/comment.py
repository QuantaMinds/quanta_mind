"""The comment we post: coverage first, ranking second, and no claims about correctness.

WHAT: `comment()` renders a `Ranking` into the body posted on a pull request.
WHY:  **The coverage line is first and that is not a style choice.** A reader who sees findings
      before coverage weighs the findings against nothing; a reader who sees coverage first knows
      what the list is a list OF. Every competitor puts findings first because findings are what
      they are selling.

      **We publish no model claims, because there are none.** `infer/` is closed on evidence: two
      corpora and four blind rater pools put our own findings 66.7-82.1% wrong, and the correct-rate
      is 0.013-0.037 per pull request. The comment therefore says where to look and what we could
      not see, and asserts nothing about whether the code is right.

      **A single-file change gets no "treat them as equally worth reading" note.** Real output
      carried it on a one-file scrapy change, where it reads as a malfunction rather than a caveat.

      **A comment that says nothing is not posted.** `fired=False` returns None rather than a
      cheerful "nothing to report", which would be a claim we did not earn and would train readers
      to ignore the ones that matter.
IMPORTS: types (Ranking, Unresolved), render.coverage_line. Nothing to its right.
CONSUMED BY: serve, which posts it; the live tests, which diff it against a golden file.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.render.coverage_line import coverage_line
from quantamind.types.ranking import Discrimination, Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind — where to look first"
FOOTER = (
    "_QuantaMind ranks changed files by how often a later fix has returned to them. "
    "It does not review your code and makes no claim that anything here is wrong._"
)


def comment(ranking: Ranking, unresolved: Sequence[Unresolved] = ()) -> str | None:
    """The comment body, or None when this change is not worth speaking on.

    None is a decision, not an error. The caller records that it chose silence; it must not
    substitute a reassuring sentence.
    """
    if not ranking.fired:
        return None

    lines = [HEADER, "", coverage_line(ranking, unresolved), ""]

    if ranking.ranked():
        lines.append("| # | file | prior fixes | read |")
        lines.append("|---|---|---|---|")
        for unit in ranking.units:
            read = "yes" if unit.allocation.value != "cold" else "—"
            lines.append(
                f"| {unit.rank} | `{unit.unit.qualified_name}` | {int(unit.score.value)} | {read} |"
            )
        lines.append("")

    if ranking.discrimination is Discrimination.FLAT_NONZERO and len(ranking.units) > 1:
        lines.append(
            "_Every file here has been fixed the same number of times, so the order above is "
            "alphabetical and carries no signal. Treat them as equally worth reading._"
        )
        lines.append("")

    lines.append(FOOTER)
    return "\n".join(lines)
