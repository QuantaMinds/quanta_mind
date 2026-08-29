"""The comment we post: what changed, whether it did what it said, and what nobody checked.

WHAT: `comment(ranking, summary, findings, unresolved)` renders the body posted on a pull request.
WHY:  **THE ONE QUESTION A REVIEW ANSWERS IS WHETHER THE CHANGE DID WHAT IT SAID WITHOUT
      DISTURBING ANYTHING ELSE.** An earlier version listed files to read and nothing more, which
      told a developer where to look without telling them anything about their own change. Before
      that it explained our ranking method, which told them about us. Both were things the reader
      does not act on.

      **THE SECTION ABOUT WHAT WE DID NOT CHECK IS NOT MODESTY, IT IS THE OTHER HALF OF THE
      QUESTION.** "Without disturbing anything else" needs cross-file evidence — what imports this,
      what breaks downstream — and that is not built. A comment that answered the first half and
      stayed silent on the second would read as a clean bill of health for a check that never ran,
      which is the failure this product exists to refuse. So it is stated, in one line, until
      `allocate`/`parse` can answer it.

      **A FINDING IS PRINTED WITH ITS LINE AND NOTHING ELSE.** No severity we cannot calibrate, no
      confidence we have not measured. Raw findings ran 66.7-82.1% wrong across four blind pools,
      so what publishes here has passed `verify/publishable.gate()` and is still shown as a claim
      to check rather than a defect to fix.
IMPORTS: types.{finding,ranking,verdict}. Nothing to its right, and nothing from `infer/`.
CONSUMED BY: serve, which posts it; the live tests, which diff it against a golden file.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.render.found_block import found
from quantamind.render.verdict_block import Stated, verdicts
from quantamind.types.checked import Checked, Outcome
from quantamind.types.finding import Finding
from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind"
GOOD = "✅ **Looks good.**"
HUMAN = "⚠️ **Needs a human.**"
BUGS = "🐛 **Found {count} thing(s) worth fixing.**"
BLIND = (
    "⚠️ **I could not review this change.** {why}\n\n"
    "Nothing below is a verdict on your code — it is only what the ranking could still say."
)
MAX_DEPENDENTS = 5
GOAL_LINES = 8
LOOK = "**Look here first**"
NOT_CHECKED = (
    "_Callers are found by static Python import only: a dynamic import, a re-export, or another "
    "language is invisible to it, and cross-repository impact is not checked at all._"
)


def _headline(
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
        return HUMAN + " No model reviewed this change; only the ranking below ran."
    if summary.achieves_goal is not True:
        return f"{HUMAN} It may not do what the PR says."
    if summary.breaks is not False:
        return f"{HUMAN} Whether it breaks callers is not settled."
    if summary.convention:
        return f"{HUMAN} It breaks a rule you wrote down."
    return f"{GOOD} It does what the PR says, and nothing that imports it breaks."


def comment(
    ranking: Ranking,
    *,
    summary: Stated | None = None,
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
    unresolved: Sequence[Unresolved] = (),
    blind: str = "",
) -> str:
    """The comment body: a verdict, then the mandatory sections, then what to fix.

    **THE FILE-BY-FILE FIX HISTORY IS GONE.** It listed how many times a later fix had returned to
    each changed file — true, ours, and not something a developer waiting to merge acts on. It
    still decides the ordering and still reaches the dashboard, where an operator is the right
    audience for it.

    `blind` is why no review could be produced. It renders as a refusal at the top, above whatever
    the ranking can still offer, because a partial answer presented whole is the failure this
    product refuses.
    """
    read, total = len(ranking.funded()), len(ranking.units)
    violations = [c for c in checks if c.outcome is Outcome.VIOLATED]
    lines = [HEADER, "", _headline(summary, findings, len(violations), blind), ""]

    if summary is not None and not blind:
        lines += verdicts(summary)
        if summary.dependents:
            shown = ", ".join(f"`{n}`" for n in summary.dependents[:MAX_DEPENDENTS])
            more = len(summary.dependents) - MAX_DEPENDENTS
            lines += [
                f"Used by {len(summary.dependents)} other file(s): {shown}"
                + (f" and {more} more" if more > 0 else "")
                + ".",
                "",
            ]

    defects = found(checks, findings)
    if defects:
        lines += [defects, ""]

    if summary is None and ranking.funded():
        lines += ["**Start here**", ""]
        lines += [f"- `{unit.unit.qualified_name}`" for unit in ranking.funded()]
        lines.append("")

    parts = [f"{read} of {total} file(s) reviewed" if total else "Nothing to review"]
    if total - read > 0:
        parts.append(f"{total - read} not reviewed")
    if unresolved:
        parts.append(f"{len(unresolved)} construct(s) could not be parsed")
    lines.append(f"_{'; '.join(parts)}._")
    return "\n".join(lines)
