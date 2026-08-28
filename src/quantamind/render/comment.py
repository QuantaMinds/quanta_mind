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

from quantamind.types.finding import Finding
from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

HEADER = "### QuantaMind"
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


def _goal(summary: Stated) -> list[str]:
    """Whether it did what the author said, in the author's terms."""
    if summary.achieves_goal is None:
        return ["**Does it do what the PR says?** The PR description states no goal to check."]
    verdict = "Yes" if summary.achieves_goal else "**No**"
    said = [f"**Does it do what the PR says?** {verdict} — {summary.reasoning}"]
    return [*said, f"**Effect on callers:** {summary.impact}"] if summary.impact else said


def comment(
    ranking: Ranking,
    *,
    summary: Stated | None = None,
    findings: Sequence[Finding] = (),
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
        lines += ["**What changed**", "", summary.what_changed, "", *_goal(summary), ""]

    if findings:
        lines.append("**Worth checking**")
        lines += [
            f"- `{f.path}:{f.line}` — {f.claim}" if f.line else f"- `{f.path}` — {f.claim}"
            for f in findings
        ]
        lines.append("")

    funded = ranking.funded()
    if funded and not summary:
        lines.append(LOOK)
        lines += [f"- `{unit.unit.qualified_name}`" for unit in funded]
        lines.append("")

    lines.append(NOT_CHECKED)
    parts = [f"{read} of {total} changed file(s) reviewed" if total else "Nothing to review"]
    if total - read > 0:
        parts.append(f"{total - read} not reviewed")
    if unresolved:
        parts.append(f"{len(unresolved)} construct(s) could not be parsed")
    lines += ["", f"_{'; '.join(parts)}._"]
    return "\n".join(lines)
