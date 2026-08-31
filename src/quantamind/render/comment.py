"""The comment we post: what changed, whether it did what it said, and what nobody checked.

WHAT: `comment(ranking, summary, findings, unresolved, context)` renders the body posted on a
      pull request.
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

      **THE GOAL BLOCK IS FIRST, AND IT DOES NOT DEPEND ON THE MODEL.** Intent used to reach this
      comment only through `verdict_block.verdicts(summary)` — which quoted `Summary.goal`, filled
      from the author's own text, so a DETERMINISTIC fact rode on a model's object and vanished
      whenever `infer/` was off, refused, or out of tokens. Those deliveries answered *is anything
      wrong here* and never *is this what you said you were doing*.
      `render/context/goal_block.py` prints it from the same `ingest/diff.stated_goal` read on
      every delivery, and `verdict_block` no longer prints it at all: for one commit both did, and
      a real posted comment would have carried the author's description twice.

      **A FINDING IS PRINTED WITH ITS LINE AND NOTHING ELSE.** No severity we cannot calibrate, no
      confidence we have not measured. Raw findings ran 66.7-82.1% wrong across four blind pools,
      so what publishes here has passed `verify/publishable.gate()` and is still shown as a claim
      to check rather than a defect to fix.
IMPORTS: types.{checked,finding,ranking,verdict}, render.{context.goal_block,found_block,
      verdict_block}, and `ingest.context.tickets` for the value object D6a retrieves. Nothing to
      its right, and nothing from `infer/`.
CONSUMED BY: serve, which posts it; the live tests, which diff it against a golden file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from quantamind.ingest.context.tickets import Context
from quantamind.parse.change_effort import Effort
from quantamind.parse.duplicate_bodies import Duplicates
from quantamind.render.blocks.duplicate_block import duplicates
from quantamind.render.blocks.found_block import found
from quantamind.render.blocks.scope_block import coverage
from quantamind.render.blocks.verdict_block import Stated, verdicts
from quantamind.render.context.goal_block import goal
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
    "Nothing below is a verdict on your code — it is only what could still be checked."
)
MAX_DEPENDENTS = 3
"""Dependents named before the count takes over. **Five made the single longest line in a
real posted comment** — five `src/quantamind/...` paths wrapped across a screen, and the
remainder is stated either way, so the fourth and fifth bought nothing a reader acts on."""
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
        return HUMAN + " No model read this change; the checks below still ran."
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
    context: Context | None = None,
    repeated: Duplicates | None = None,
    effort: Mapping[str, Effort] | None = None,
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
    violations = [c for c in checks if c.outcome is Outcome.VIOLATED]
    lines = [HEADER, "", _headline(summary, findings, len(violations), blind), ""]

    # **ABOVE THE MODEL'S VERDICT, AND PRINTED EVEN WHEN THERE IS NO VERDICT.** This block is the
    # author's own words plus one API read, so it survives `infer/` being off, refused, or out of
    # tokens — the deliveries where the comment used to carry no statement of intent at all. It is
    # deliberately NOT suppressed by `blind`: a review that could not run still tells the reader
    # what the change claims to be for, which is the half of the question we can always answer.
    if context is not None:
        block = goal(context)
        if block:
            lines += [block, ""]

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

    # **D2c SITS ABOVE THE SCOPE LINE AND BELOW THE MODEL.** It is a parser's claim, so it outranks
    # anything `infer/` said; it is about structure rather than this change's goal, so it comes
    # after the verdict a reader acts on first.
    if repeated is not None:
        repeats = duplicates(repeated)
        if repeats:
            lines += [repeats, ""]

    lines += coverage(ranking, unresolved, effort, checks, findings)
    return "\n".join(lines)
