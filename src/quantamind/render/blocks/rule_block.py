"""What the declared rules said about this change, including what they could not say.

WHAT: `block(rows)` renders `Checked` rows into the section of the comment about standards.
      Empty string when the repository declared no rules.
WHY:  **THE DENOMINATOR IS PRINTED, NOT IMPLIED.** "1 violation" invites the reader to assume
      everything else was checked and passed. It usually was not: only Python is parsed, so a
      repository of TypeScript produces rows we could not decide, and a reader who cannot see that
      count will read our parser coverage as their compliance. The line states checks decided,
      violations found, and how many were left undecided and why.

      **VIOLATIONS ARE SAFE TO PUBLISH IN A WAY MODEL FINDINGS ARE NOT.** A forbidden call either
      appears in the syntax tree or it does not; the verdict is reproducible on the same commit by
      anyone. That is why this block names the rule and the line and asserts the violation
      directly, while `render/comment.py` still refuses to claim anything about correctness.

      **A DEFERRED ROW IS SHOWN, NOT HIDDEN.** A model-judged rule that no parser decided is a
      standard the customer declared and we have not yet enforced. Quietly omitting it would make
      the section describe a narrower standard than the one they wrote down.
IMPORTS: types.checked only. Nothing to its right.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from quantamind.types.standards.checked import Checked, Outcome

HEADING = "**Declared standards**"


def block(rows: Sequence[Checked]) -> str:
    """The standards section, or empty when there is nothing to report."""
    if not rows:
        return ""

    counted = Counter(row.outcome for row in rows)
    decided = counted[Outcome.PASSED] + counted[Outcome.VIOLATED]
    lines = ["", HEADING, ""]

    for row in (r for r in rows if r.outcome is Outcome.VIOLATED):
        lines.append(f"- `{row.rule_id}` — {row.site.render()} — {row.evidence}")
    if counted[Outcome.VIOLATED] == 0:
        lines.append("- No violation of the rules this repository declares.")

    # **THE UNDECIDED COUNT SITS BESIDE THE RESULT, NOT IN A FOOTNOTE.** It is the difference
    # between "your code is compliant" and "the part of your code we can parse is compliant".
    undecided = counted[Outcome.UNCHECKABLE] + counted[Outcome.DEFERRED]
    tail = f"{decided} check(s) decided, {counted[Outcome.VIOLATED]} violated"
    if undecided:
        reasons = sorted({r.why.value for r in rows if r.why is not None})
        deferred = counted[Outcome.DEFERRED]
        detail = ", ".join(reasons) if reasons else ""
        note = f"{undecided} not decided"
        if detail:
            note += f" ({detail})"
        if deferred:
            note += f"; {deferred} await a model and were not enforced here"
        tail += f". **{note}** — those are not passes."
    else:
        tail += ". Every declared rule was decided on every file we could read."
    lines.extend(["", f"_{tail}_", ""])
    return "\n".join(lines)
