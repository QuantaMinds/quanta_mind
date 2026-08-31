"""A term with a decided value must not appear carrying the value we rejected.

WHAT: Scans the product documents for terms where a decision has been taken and the losing side
      is still quotable -- the ranking unit, the pricing axis, and capabilities that do not ship.
      Reports the file, the line and which decision the sentence contradicts.
WHY:  **A figure-extraction check would have caught none of the six defects that prompted this.**
      Every published number in `QUANTAMIND.md` was already corroborated by a file outside it; the
      document was still wrong, because the errors were prose contradicting a table:

      - "names the one function worth reading first", two paragraphs above a block explaining that
        allocation is file-level everywhere
      - `| Priced | ... | per seat |` in the differentiation table, under a pricing section that
        had been rewritten to per repository, and directly below a note claiming the two agreed
      - "Bring your own key at Business", two hundred lines after the table row saying it is not
        sellable because `infer/` ships nothing
      - a step banner reading "steps 1 and 2 are built" above steps 3 and 4 marked BUILT

      Numbers drift by being restated. **Decisions drift by surviving in the sentence a reader
      quotes**, and the sentence people quote is rarely the one in the table.

      THE CHECK IS DELIBERATELY NARROW. It asserts nothing about whether a decision is right, only
      that the rejected side is not stated as current. Each rule names the decision it enforces
      and where that decision is recorded, so a rule that outlives its decision can be found and
      removed rather than worked around.
IMPORTS: scripts/guard/discovery.py, scripts/guard/coverage.py,
         scripts/guard/records/decided_decisions.py -- which holds SCANNED, EXEMPT and RULES.
         No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coverage import assert_examined, guarded, refuse_path_argument
from discovery import Violation, project_root, report

from records.decided_decisions import EXEMPT, RULES, SCANNED


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """(first line number, joined text) per paragraph, fenced blocks dropped.

    **SCANNED BY PARAGRAPH, NOT BY LINE, AND THE DIFFERENCE IS THREE FALSE POSITIVES.** Prose here
    wraps at 100 characters, so "Charging per seat" ends one line and "would mean charging for a
    resource we do not consume" begins the next. A line-based scan sees the first half, misses the
    negation, and reports a sentence that says the opposite of what it flags.

    Its sibling `check_documented_recipes.py` failed the other way -- it joined every backtick span
    on a line and read a command across the gap between two. **One guard joined too much and one
    joined too little; both were reading a unit that does not match the unit the author wrote in.**
    """
    out: list[tuple[int, str]] = []
    buffer: list[str] = []
    start = 0
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.lstrip().startswith("|"):
            # A TABLE ROW IS ITS OWN UNIT. Joined into the surrounding paragraph, one exempt cell
            # -- a competitor's name in a neighbouring row -- exempts every row in the table, and
            # a sabotage that set all four columns to `per seat` went unreported.
            if buffer:
                out.append((start, " ".join(buffer)))
                buffer = []
            out.append((number, line))
            continue
        if line.strip():
            if not buffer:
                start = number
            buffer.append(line)
            continue
        if buffer:
            out.append((start, " ".join(buffer)))
            buffer = []
    if buffer:
        out.append((start, " ".join(buffer)))
    return out


def main() -> int:
    root = project_root()
    violations: list[Violation] = []
    scanned = 0
    read = 0

    for relative in SCANNED:
        document = root / relative
        if not document.is_file():
            continue
        read += 1
        for number, block in _paragraphs(document.read_text(encoding="utf-8")):
            scanned += 1
            if EXEMPT.search(block):
                continue
            for rule in RULES:
                found = rule.pattern.search(block)
                if found:
                    violations.append(
                        Violation(
                            document,
                            number,
                            "decided-vocabulary",
                            f"{found.group(0)!r} contradicts a decision: {rule.decided}. "
                            f"Recorded in {rule.recorded}. Say the decided thing, or mark the "
                            f"sentence as describing what was rejected.",
                        )
                    )

    print(
        f"[decided-vocabulary] {scanned} paragraph(s) in {read} document(s) "
        f"against {len(RULES)} decision(s)",
        flush=True,
    )
    assert_examined("paragraphs", scanned, 100, root)
    # **THE RULE COUNT IS A POPULATION TOO, AND IT WAS UNGUARDED.** Sabotaging the whole mechanism
    # -- emptying `RULES` -- printed `ok` and exited 0, identical to a document with no drift in it.
    # Every document was still read, so the paragraph floor above passed while the guard checked
    # nothing. A decision retired without its rule being removed on purpose reads the same way.
    assert_examined("decisions", len(RULES), 3, root)
    # **AND THE DOCUMENT COUNT.** `SCANNED` skips a path that does not exist, so a renamed or moved
    # product document silently drops out of the scan. That is how the pricing documents went
    # unscanned in the first place, in a different costume.
    assert_examined("documents", read, 3, root)
    return report(violations, root, "decided-vocabulary")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "decided-vocabulary") or guarded(lambda: main()))
