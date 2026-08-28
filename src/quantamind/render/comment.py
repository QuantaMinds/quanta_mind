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
from typing import Protocol

from quantamind.render.found_block import found
from quantamind.types.checked import Checked
from quantamind.types.finding import Finding
from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind"
MAX_DEPENDENTS = 5
GOAL_LINES = 8
LOOK = "**Look here first**"
NOT_CHECKED = (
    "_Callers are found by static Python import only: a dynamic import, a re-export, or another "
    "language is invisible to it, and cross-repository impact is not checked at all._"
)


class Stated(Protocol):
    """What `infer.change_summary.Summary` provides, without importing rightward into `infer/`."""

    @property
    def what_changed(self) -> str: ...
    @property
    def achieves_goal(self) -> bool | None: ...
    @property
    def reasoning(self) -> str: ...
    @property
    def impact(self) -> str: ...
    @property
    def breaks(self) -> bool | None: ...
    @property
    def breaks_why(self) -> str: ...
    @property
    def dependents(self) -> tuple[str, ...]: ...
    @property
    def goal(self) -> str: ...


def _goal(summary: Stated) -> list[str]:
    """Whether it did what the author said, in the author's terms."""
    if summary.achieves_goal is None:
        return ["**Does it do what the PR says?** The PR description states no goal to check."]
    verdict = "Yes" if summary.achieves_goal else "**No**"
    said = [f"**Does it do what the PR says?** {verdict} — {summary.reasoning}"]
    if summary.impact:
        said.append(f"**Effect on callers:** {summary.impact}")
    # **THE VERDICT IS THREE-VALUED AND "CANNOT TELL" IS PRINTED AS PLAINLY AS THE OTHER TWO.**
    # "It will not break anything" is the most expensive sentence here, because a reviewer acts on
    # it by not looking. An unknown rendered as reassurance would be the clean bill of health for
    # a check that never ran, which is the failure this product exists to refuse.
    if summary.breaks is True:
        breaks = "**Yes — this can break existing callers**"
    elif summary.breaks is False:
        breaks = "No"
    else:
        breaks = "**Cannot tell**"
    said.append(f"**Will it break anything?** {breaks} — {summary.breaks_why}")
    # **A COUNT AND NAMES, BECAUSE A PARSER PRODUCED THEM.** The sentences above are a model's
    # reading; this line is `parse/importers` output, re-runnable on the same commit by anyone.
    # It is stated separately so a reader can tell which of the two they are trusting.
    if summary.dependents:
        shown = ", ".join(f"`{name}`" for name in summary.dependents[:MAX_DEPENDENTS])
        more = len(summary.dependents) - MAX_DEPENDENTS
        tail = f" and {more} more" if more > 0 else ""
        said.append(
            f"**{len(summary.dependents)} file(s) import this code** — {shown}{tail}. "
            "Symbol-level use inside them is not checked, so these are where a deeper look pays."
        )
    return said


def comment(
    ranking: Ranking,
    *,
    summary: Stated | None = None,
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
    unresolved: Sequence[Unresolved] = (),
) -> str:
    # **KEYWORD-ONLY, BECAUSE THE SECOND POSITIONAL ARGUMENT ALREADY CHANGED MEANING ONCE.**
    # `unresolved` sat there; `summary` took the slot, and a live caller passing `()` bound an
    # empty tuple to a summary and reached for `.what_changed` on it. A signature whose positions
    # shift under callers is a defect the type checker cannot see across a `Sequence` boundary.
    """The comment body. About the reader's change, and honest about its own gaps."""
    read, total = len(ranking.funded()), len(ranking.units)
    lines = [HEADER, ""]

    if summary is not None:
        # **THE GOAL IS QUOTED, NOT SUMMARISED.** It is the sentence the change is measured
        # against, and a model restating it would put a second author between the reviewer and
        # what was actually promised. Everything under it is a reading; this is the record.
        if summary.goal.strip():
            quoted = "\n".join(f"> {ln}" for ln in summary.goal.strip().splitlines()[:GOAL_LINES])
            lines += ["**Goal — from the PR description**", "", quoted, ""]
        else:
            lines += ["**Goal — the PR description states none.**", ""]
        lines += ["**What changed**", "", summary.what_changed, "", *_goal(summary), ""]

    defects = found(checks, findings)
    if defects:
        lines += [defects, ""]

    funded = ranking.funded()
    if funded and not summary:
        lines.append(LOOK)
        lines += [f"- `{unit.unit.qualified_name}`" for unit in funded]
        lines.append("")

    # **THE FACTS ARE LISTED SEPARATELY FROM THE READING, AND THAT SEPARATION IS THE PRODUCT.**
    # Everything above this line is a model's account of the change and carries its error rate.
    # Everything below came from git and a parser: the files, how often a later fix has returned
    # to each, and who imports them. A reader who cannot tell which half they are trusting is
    # being asked to trust both equally, and only one of them can be re-run on the same commit.
    if ranking.units:
        lines.append("**Facts** — from git and a parser, not from a model")
        lines.append(f"- {len(ranking.units)} file(s) touched")
        busiest = sorted(ranking.units, key=lambda u: -u.score.value)[:MAX_DEPENDENTS]
        for unit in busiest:
            fixes = int(unit.score.value)
            been = f"{fixes} later fix(es) have returned here" if fixes else "no prior fixes here"
            lines.append(f"  - `{unit.unit.qualified_name}` — {been}")
        if summary is not None and summary.dependents:
            lines.append(f"- {len(summary.dependents)} file(s) statically import this code")
        # **THE DENOMINATOR MOVED HERE WHEN THE RULE SECTION WAS FOLDED INTO "FOUND".** Only
        # violations are listed there, and a list of violations with no count behind it invites
        # the reader to assume everything else was checked and passed. Undecided rows are the
        # ones our parser could not read at all, and they are not passes.
        if checks:
            decided = sum(1 for c in checks if c.counts_toward_compliance)
            undecided = len(checks) - decided
            tail = f", {undecided} could not be decided" if undecided else ""
            lines.append(f"- {decided} declared rule check(s) decided{tail}")
        lines.append("")

    lines.append(NOT_CHECKED)
    parts = [f"{read} of {total} changed file(s) reviewed" if total else "Nothing to review"]
    if total - read > 0:
        parts.append(f"{total - read} not reviewed")
    if unresolved:
        parts.append(f"{len(unresolved)} construct(s) could not be parsed")
    lines += ["", f"_{'; '.join(parts)}._"]
    return "\n".join(lines)
