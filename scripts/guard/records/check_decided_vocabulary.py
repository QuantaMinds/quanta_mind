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
IMPORTS: scripts/guard/discovery.py; stdlib re. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coverage import assert_examined
from discovery import Violation, project_root, report

SCANNED = ("docs/product/QUANTAMIND.md",)
# A line carrying any of these is discussing the decision rather than asserting the losing side.
EXEMPT = re.compile(
    # Marked as not shipping, or as the rejected side of a decision.
    r"~~|NOT BUILT|NOT SELLABLE|not built|closed on evidence|used to|no longer|superseded|"
    r"retired|road not taken|were written when|rejected|would\s+\w+|"
    # Describing somebody else's product. A price range attributed to a vendor is about them.
    r"incumbent|competitor|CodeRabbit|Greptile|Qodo|Bugbot|Macroscope|Aikido|CodeScene|"
    r"\$[\d,]+[^ ]{1,3}[\d,]+ per seat|sold \*\*per seat\*\*|reviewer sold|"
    # A comparison row whose OWN column already carries the decided value.
    r"\*\*per repository\*\*",
    re.I,
)


class Rule:
    """One decision, the pattern that contradicts it, and where the decision is recorded."""

    __slots__ = ("decided", "pattern", "recorded")

    def __init__(self, decided: str, pattern: str, recorded: str) -> None:
        self.decided = decided
        self.pattern = re.compile(pattern, re.I)
        self.recorded = recorded


RULES = (
    Rule(
        "allocation ranks FILES, not functions",
        r"rank(?:s|ing|ed)?\s+(?:the\s+)?functions?\b|top-ranked function|"
        r"every changed function|names?\s+(?:the\s+)?(?:one\s+)?function\b|"
        r"for every function|ranked function",
        "rank/order.py — `Site(path, line=0)`; docs/plans/delivered/feat-rank-fix-history.md",
    ),
    Rule(
        "pricing is per REPOSITORY, not per seat",
        r"\bper seat\b|\bper developer per month\b|/dev/mo",
        'docs/product/QUANTAMIND.md — "price on the axis the costs actually sit on"',
    ),
    # **THIS RULE REPLACES ONE THAT ENFORCED THE OPPOSITE, AND THE REVERSAL IS RECORDED RATHER
    # THAN QUIETLY APPLIED.** It used to read "no model reads the code -- `infer/` and `verify/`
    # ship nothing", which was true of the product until 2026-08-20, when the reviewer half was
    # brought back in as a product decision. A guard enforcing a withdrawn decision is worse than
    # no guard: it turns the build red for saying the true thing.
    #
    # What is worth protecting NOW is the mechanism that makes shipping a model defensible, and it
    # is the part a summary drops first: findings are published only after an isolated judge in a
    # DIFFERENT model family clears them. Measured 2026-08-20 -- a same-family judge agreed with a
    # careful rater on 34.9% of findings and certified the reviewer's own invented facts.
    Rule(
        "raw model findings are never published, and the judge is a DIFFERENT family",
        r"publish(?:es|ed)? (?:the )?(?:raw |model )?findings? (?:directly|unverified|as[- ]is)|"
        r"same model (?:family|as the reviewer)|"
        r"no judge|without (?:a|the) judge|judge is the same",
        'docs/product/QUANTAMIND.md — "THE JUDGE IS THE RELIABILITY MECHANISM"',
    ),
)


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

    for relative in SCANNED:
        document = root / relative
        if not document.is_file():
            continue
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
        f"[decided-vocabulary] {scanned} paragraph(s) against {len(RULES)} decision(s)", flush=True
    )
    assert_examined("paragraphs", scanned, 100, root)
    return report(violations, root, "decided-vocabulary")


if __name__ == "__main__":
    sys.exit(main())
