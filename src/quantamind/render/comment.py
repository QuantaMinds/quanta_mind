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

      **EVERY REVIEWABLE CHANGE GETS A COMMENT, AND SALIENCE IS SAID RATHER THAN IMPLIED BY
      SILENCE.** This returned `None` on `fired=False`, so the product spoke on roughly a tenth of
      pull requests -- correct for a ranking that had to justify interrupting somebody, and wrong
      for a reviewer a business connects to a repository and expects to hear from.

      The objection recorded here when it muted was real and is answered rather than dropped: a
      cheerful "nothing to report" on every change WOULD train readers to ignore the ones that
      matter. So the comment states which it is. A change in the repository's own top decile says
      so in bold; one below it says the ordering is ordering and not an alarm. The signal that was
      carried by whether a comment appeared is now carried by a sentence inside it, where it can
      be read instead of inferred from an absence.
IMPORTS: types (Ranking, Unresolved), render.coverage_line. Nothing to its right.
CONSUMED BY: serve, which posts it; the live tests, which diff it against a golden file.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.render.coverage_line import coverage_line
from quantamind.types.ranking import Discrimination, Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind — where to look first"
LOUD = (
    "**This change is in the top decile of this repository's own changes**, by how often a later "
    "fix has returned to the files it touches."
)
QUIET = (
    "This change is _not_ in this repository's top decile. The order below is an ordering, not an "
    "alarm."
)


def _salience(ranking: Ranking) -> str:
    """Which kind of change this is, said out loud.

    **THIS SENTENCE IS WHAT REPLACED THE SILENCE.** When the product spoke on a tenth of changes,
    the fact that a comment existed at all WAS the signal. Commenting on everything without saying
    which is which would delete that signal rather than move it.
    """
    return LOUD if ranking.fired else QUIET


FOOTER = (
    "_QuantaMind ranks changed files by how often a later fix has returned to them. "
    "It does not review your code and makes no claim that anything here is wrong._"
)


def comment(ranking: Ranking, unresolved: Sequence[Unresolved] = ()) -> str:
    """The comment body. Always a body -- what varies is what it claims.

    **THE CALLER STILL DECIDES WHETHER THERE IS ANYTHING TO RENDER AT ALL.** `run_review` returns
    before reaching this when no changed file is in a language we read, or when there is nothing
    to rank. Those are absences of input, not judgements about salience, and they stay distinct.
    """
    lines = [HEADER, "", coverage_line(ranking, unresolved), "", _salience(ranking), ""]

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
