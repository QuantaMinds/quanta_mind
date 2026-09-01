"""What a model said about the standards a parser cannot check — labelled as a model's opinion.

WHAT: `judged(records)` renders `Judged` records into their own section. Empty string when the
      repository declared no model-judged rules.
WHY:  **D1c REQUIRES THAT A MODEL VERDICT AND A PARSER VERDICT "NEVER RENDER ALIKE", AND THIS IS
      WHERE THAT IS TRUE OR FALSE.** `render/blocks/rule_block.py` states a violation flatly —
      it may, because a forbidden call is in the syntax tree or it is not, and anyone can re-run it
      on the same commit. Nothing here can be re-run to the same answer, so nothing here is stated
      flatly. The section says a model decided it, in those words, above the items.

      **THE HEADING DOES NOT SAY "VIOLATION".** A parser found a violation; a model formed a view.
      Our raw model findings measure 66.7-82.1% wrong across four blind pools, and a heading that
      borrows the parser's certainty spends credibility this half has not earned.

      **UNDECIDED IS COUNTED, NOT LISTED.** Every undecided record printed in full would bury the
      one that matters, and the count is what the reader needs: it is the difference between "the
      standard held" and "we did not manage to ask about most of your files". A count of zero
      decided prints too — **a section that goes quiet when nothing could be judged is
      indistinguishable from one where everything passed.**

      **THE QUOTE IS THE POINT OF EACH ITEM.** `types/judged.py` refuses to construct `BROKEN`
      without one, so every item here can be located in the file by the developer reading it. That
      is the whole difference between this and a model telling somebody their code feels wrong.
IMPORTS: types.judged only. Nothing to its right.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from quantamind.types.standards.judged import Judged, Verdict

HEADING = "**Standards a parser cannot check**"

MAX_SHOWN = 5
"""Broken verdicts listed in full. The rest are counted — **and the count says so.**"""


def judged(records: Sequence[Judged]) -> str:
    """The model-judged section, or empty when no such rule was declared."""
    if not records:
        return ""

    counted = Counter(record.verdict for record in records)
    broken = [record for record in records if record.verdict is Verdict.BROKEN]
    lines = ["", HEADING, ""]

    # **THE LABEL COMES FIRST, BEFORE ANY CLAIM.** A reader who stops after one line has read the
    # part that tells them how much weight to give the rest.
    lines += [
        "_A model judged these, not a parser. They cannot be re-run to the same answer, "
        "and they are not counted in your compliance rate._",
        "",
    ]

    for record in broken[:MAX_SHOWN]:
        where = record.site.render()
        lines.append(f"- `{record.rule_id}` — {where}")
        lines.append(f"  > {record.quote}")
        if record.why:
            lines.append(f"  {record.why}")
    if len(broken) > MAX_SHOWN:
        lines.append(f"- …and {len(broken) - MAX_SHOWN} more the model considers broken.")
    if not broken:
        lines.append("- The model raised nothing against these standards.")

    # **THE UNDECIDED COUNT IS NOT OPTIONAL.** Without it, "nothing raised" reads as "everything
    # was judged and held", which is false whenever the transport failed or a quote was invented.
    undecided = counted[Verdict.UNDECIDED]
    tail = f"{counted[Verdict.MET]} met, {len(broken)} the model says broken"
    if undecided:
        tail += f", **{undecided} not decided** — those are not passes"
    lines += ["", f"_{tail}._", ""]
    return "\n".join(lines)
