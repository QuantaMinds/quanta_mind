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
from quantamind.ingest.standards.inherited import Inheritance
from quantamind.ingest.standards.links_file import Link
from quantamind.parse.change_effort import Effort
from quantamind.parse.duplicate_bodies import Duplicates
from quantamind.parse.public_api import Break
from quantamind.render.blocks.crossing_block import crossing
from quantamind.render.blocks.duplicate_block import duplicates
from quantamind.render.blocks.found_block import found
from quantamind.render.blocks.headline import HEADER, headline
from quantamind.render.blocks.inheritance_block import inheritance
from quantamind.render.blocks.judged_block import judged as judged_block
from quantamind.render.blocks.scope_block import coverage
from quantamind.render.blocks.verdict_block import Stated, verdicts
from quantamind.render.context.goal_block import goal
from quantamind.types.finding import Finding
from quantamind.types.ranking import Ranking
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.judged import Judged
from quantamind.types.verdict import Unresolved
from quantamind.verify.consumers import Crossing

MAX_DEPENDENTS = 3
"""Dependents named before the count takes over. **Five made the single longest line in a
real posted comment** — five `src/quantamind/...` paths wrapped across a screen, and the
remainder is stated either way, so the fourth and fifth bought nothing a reader acts on."""


def comment(
    ranking: Ranking,
    *,
    summary: Stated | None = None,
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
    judged: Sequence[Judged] = (),
    inherited: Inheritance | None = None,
    unresolved: Sequence[Unresolved] = (),
    blind: str = "",
    context: Context | None = None,
    repeated: Duplicates | None = None,
    effort: Mapping[str, Effort] | None = None,
    links: Sequence[Link] = (),
    links_unreadable: bool = False,
    breaks: Sequence[Break] = (),
    crossed: Crossing | None = None,
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
    lines = [HEADER, "", headline(summary, findings, len(violations), blind), ""]

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
    # **ABOVE THE DUPLICATE BLOCK BECAUSE IT REACHES FURTHER.** A repeated body is a fact about
    # this repository; a narrowed export is a fact about everyone who imports it.
    narrowed = crossing(breaks, crossed or Crossing())
    if narrowed:
        lines += [narrowed, ""]

    # **D1e SITS ABOVE THE MODEL'S OPINION.** It says what this change was NOT checked against,
    # which a reader needs before weighing anything below it.
    changed_standards = inheritance(inherited)
    if changed_standards:
        lines += [changed_standards, ""]

    # **UNDER EVERY PARSER CLAIM ABOVE IT.** This is the one section a re-run may contradict, so
    # it sits below the ones that cannot — the reader meets the reproducible half first.
    opinion = judged_block(judged)
    if opinion:
        lines += [opinion, ""]

    if repeated is not None:
        repeats = duplicates(repeated)
        if repeats:
            lines += [repeats, ""]

    lines += coverage(
        ranking,
        unresolved,
        effort,
        checks,
        findings,
        links,
        links_unreadable,
        (crossed or Crossing()).asked(),
    )
    return "\n".join(lines)
