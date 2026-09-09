"""The two rules that judge one sentence of the plan against the filesystem.

WHAT: `contradictions(root, plan, number, text, where)` returns a `Violation` per sentence that
      claims a module is absent while it exists, or marks one DONE while it does not.
WHY:  **Split from `check_stage_table.py` at the 200-line cap**, which it hit when the status-cell
      rule was added for issue #96. This is the seam that was already there: these two rules are
      run over *two different things* -- a summary row's evidence cell and a stage section's steps
      -- so they were never about either caller, and the file read as though they were.

      **THE UNIT IS A SENTENCE, AND THAT IS THE WHOLE RULE.** One evidence cell carries both
      polarities -- "`history.py` built. `diff.py` not begun" -- so a whole-cell scan sees an
      absence marker and condemns the module legitimately reported as built. `plan_claims.sentences`
      owns the splitting; this owns what to do with each piece.
IMPORTS: scripts/guard/{discovery,plan_claims}.py; stdlib re and pathlib.
CONSUMED BY: `scripts/guard/records/check_stage_table.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

from discovery import Violation
from plan_claims import PACKAGE, referenced, sentences

# Explicit only. "Nothing is wired to the work callback" is a true statement about behaviour, not a
# claim that a file is missing, and a looser pattern read it as one.
ABSENT = re.compile(r"not begun|not built|not yet built|not started|still to come", re.I)


def contradictions(root: Path, plan: Path, number: int, text: str, where: str) -> list[Violation]:
    """An absence claim about a present module, or a DONE claim about a missing one."""
    out: list[Violation] = []
    for sentence in sentences(text):
        denied = ABSENT.search(sentence)
        done = "**DONE" in sentence or "**NOT BUILT" in sentence
        for name, present in referenced(root, sentence):
            if denied and present:
                out.append(
                    Violation(
                        plan,
                        number,
                        "stage-table",
                        f"{where} says {name} is {denied.group(0)!r}, and it exists on disk. A "
                        f"resuming reader acts on this table before anything else in the file.",
                    )
                )
            elif done and not denied and not present and "NOT BUILT" not in sentence:
                out.append(
                    Violation(
                        plan,
                        number,
                        "stage-table",
                        f"{where} marks {name} DONE and there is no such file under "
                        f"{PACKAGE}/. Either it was never written, or it was renamed "
                        f"without git mv.",
                    )
                )
    return out
