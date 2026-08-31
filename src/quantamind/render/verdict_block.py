"""The golden rule, rendered — and it is mandatory, not a choice this renderer makes.

WHAT: `SECTIONS` names every heading a review must carry. `verdicts(summary)` renders them.
WHY:  **THE STRUCTURE IS THE PRODUCT'S ANSWER TO ITS OWN QUESTION, SO IT CANNOT BE OPTIONAL.**
      *Did this change achieve the goal it set out to achieve, without disturbing anything else?*
      Every heading below is one half of that, and a comment missing any of them has stopped
      answering it. This was learned by regression: a redesign collapsed the goal, the
      goal-achieved verdict and the break verdict into a single headline, and the review became an
      opinion with no stated basis.

      **`SECTIONS` EXISTS SO A TEST CAN ENFORCE IT.** A convention nobody checks is a convention
      that lasts until the next redesign — this one lasted about an hour. The list is exported and
      `tests/unit/layers/render/` asserts every heading appears in a rendered comment, so removing
      one fails the build rather than being noticed on a pull request weeks later.

      **THE GOAL IS QUOTED, NEVER SUMMARISED.** It is the sentence the change is measured against,
      and a model restating it puts a second author between the reviewer and what was promised.
IMPORTS: nothing but stdlib typing. Nothing to its right.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from typing import Protocol

# **EVERY ONE OF THESE IS MANDATORY.** A test asserts each appears; see the module docstring.
#
# **"Goal — from the PR description" USED TO BE THE FIRST OF FIVE AND IS NOW RENDERED ELSEWHERE.**
# It quoted `Summary.goal`, which `infer/change_summary` fills from the author's own title and body
# — deterministic content riding on a model's object. `render/context/goal_block.py` (D6a) quotes
# the same text from `ingest/context/tickets.behind()`, and for a while BOTH ran: the first live
# delivery of D6a to `QuantaMinds/quanta_mind#91` would have printed the description twice, in a
# product whose measured weakness is saying the same thing twice (17.3% redundancy against Qodo's
# 1.0%). One fact, one renderer, and the surviving one is the deterministic one — it is there when
# the model is off, refused, or out of tokens, and this one never was.
SECTIONS = (
    "**What changed**",
    "**Does it do what the PR says?**",
    "**Will it break anything?**",
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
    def convention(self) -> str: ...
    @property
    def dependents(self) -> tuple[str, ...]: ...
    @property
    def goal(self) -> str: ...


def _breaks(summary: Stated) -> str:
    """Three-valued, and "cannot tell" is printed as plainly as the other two.

    "It will not break anything" is the most expensive sentence here, because a reviewer acts on it
    by not looking. An unknown rendered as reassurance is a clean bill of health for a check that
    never ran.
    """
    if summary.breaks is True:
        return "**Yes — this can break existing callers**"
    return "No" if summary.breaks is False else "**Cannot tell**"


def verdicts(summary: Stated) -> list[str]:
    """The mandatory sections, in the order the reader needs them.

    **THE GOAL IS NOT QUOTED HERE ANY MORE, AND `achieves_goal` IS STILL JUDGED AGAINST IT.**
    `render/context/goal_block.py` prints it from the same `ingest/diff.stated_goal` read, above
    this block, on every delivery rather than only the ones where a model answered. What the reader
    loses is nothing; what they stop getting is the same paragraph twice.
    """
    achieved = "Yes" if summary.achieves_goal else "**No**"
    if summary.achieves_goal is None:
        achieved = "**Cannot tell**"

    lines = [SECTIONS[0], "", summary.what_changed, ""]
    lines.append(f"{SECTIONS[1]} {achieved} — {summary.reasoning}")
    if summary.impact:
        lines.append(f"**Effect on callers:** {summary.impact}")
    lines.append(f"{SECTIONS[2]} {_breaks(summary)} — {summary.breaks_why}")
    if summary.convention:
        lines.append(f"**Breaks a rule you wrote down:** {summary.convention}")
    lines.append("")
    return lines
