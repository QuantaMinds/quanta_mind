"""The first-scan report: what a repository's own history says about where rework lands.

WHAT: `report(repo, spots, narration)` renders a `store.touches.Hotspots` as text, with an optional
      model narration printed BELOW the numbers and labelled as a model's.
WHY:  **THE NUMBERS COME FIRST AND THE PROSE COMES SECOND, ALWAYS.** A narration printed above a
      table is read as the finding and the table as its evidence. Here the table IS the finding --
      it is a count of commits, reproducible by anyone with the clone -- and the narration is a
      model's reading of it, which `docs/product/QUANTAMIND.md` measures at 25.0% correct.

      **A SCAN WITH NO HISTORY IS A RESULT, NOT AN EMPTY REPORT.** A fresh repository and a failed
      walk both produce zero rows, and printing the same blank table for each is the defect this
      product exists to refuse. `EMPTY` names the first out loud.

      **THE WINDOW IS PRINTED BECAUSE THE TABLE IS MEANINGLESS WITHOUT IT.** Three weeks of history
      and seven years give the same shape; a reader who cannot see which one they have will read a
      young repository's noise as a hotspot.

      **NO RISK WORD APPEARS HERE.** Not "risky", not "problem", not "hotspot" as a verdict. A file
      that has been fixed often is a file that has been fixed often; whether that is bad is a
      judgement about the codebase that a count cannot support, and `AGENTS.md` rule 14 is the
      reason this file says what it counted rather than what it thinks.
IMPORTS: store.touches for `Hotspots` only -- store is to the left of render. Nothing else.
CONSUMED BY: `serve/commands/run_scan.py` and `serve/web/routes.py`.
"""

from __future__ import annotations

import time

from quantamind.store.touches import Hotspots

DAY = 86400

EMPTY = (
    "No history was read for {repo}.\n\n"
    "Either this repository has no commits we could walk, or the walk failed. Those are "
    "different, and this report cannot tell them apart -- so it claims neither."
)

HEADING = "QuantaMind -- first scan of {repo}"

WINDOW = "{touches:,} file-touches across {tracked:,} file(s), spanning {days:,} day(s) of history."

LEDE = "Where a later commit has come back most often:"

TAIL = (
    "The top {shown} file(s) carry {share:.0f}% of all file-touches in this repository.\n"
    "This is a count of commits, not a judgement about the code. Run it again on the same "
    "clone and it returns the same table."
)

NARRATION = (
    "\n--- a model's reading of the table above ---\n{text}\n"
    "--- end of the model's reading ---\n"
    "Written by a model from the counts above and nothing else -- it was not shown your code. "
    "Published findings from this product's model half are 25.0% correct; treat the paragraph "
    "as a prompt to look, never as a finding."
)


def report(repo: str, spots: Hotspots, narration: str = "") -> str:
    """The scan as text. `narration` is optional and is always printed last, always labelled."""
    if not spots.touches:
        return EMPTY.format(repo=repo)

    days = max(1, (spots.last - spots.first) // DAY)
    lines = [
        HEADING.format(repo=repo),
        "",
        WINDOW.format(touches=spots.touches, tracked=spots.tracked, days=days),
        "",
        LEDE,
        "",
    ]
    width = max((len(path) for path, _ in spots.files), default=0)
    for rank, (path, count) in enumerate(spots.files, start=1):
        lines.append(f"  {rank:>2}. {path:<{width}}  {count:>5} touch(es)")

    shown = sum(count for _, count in spots.files)
    lines += [
        "",
        TAIL.format(shown=len(spots.files), share=100 * shown / spots.touches),
    ]
    if narration.strip():
        lines.append(NARRATION.format(text=narration.strip()))
    return "\n".join(lines)


def as_of(spots: Hotspots) -> str:
    """The last commit time the scan saw, so a reader can tell a stale index from a quiet week."""
    if not spots.last:
        return "never -- no commit was read"
    return time.strftime("%Y-%m-%d", time.gmtime(spots.last))
