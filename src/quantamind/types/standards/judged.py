"""One model-judged rule against one file, and the three answers it can have.

WHAT: `Verdict` and `Judged`. A `Judged` is what a MODEL said about a standard a parser cannot
      check. **It is not a `Checked` and it never becomes one.**
WHY:  **THIS TYPE EXISTS SO THAT A MODEL'S OPINION CANNOT REACH THE COMPLIANCE RATE.**
      `types/checked.py:counts_toward_compliance` is True for `PASSED` and `VIOLATED`, so if a
      model verdict were expressed as an `Outcome` it would land in the number a customer shows an
      auditor. Raw model findings measure **66.7-82.1% wrong** across four blind pools. A separate
      type is the mechanism: there is no `Outcome` to set, no `rule_check` row to write, and no
      renderer shared with the compliance table. D1c asks that the two "never render alike"; they
      cannot, because they are not the same thing.

      **`UNDECIDED` IS A VALUE, NOT AN ABSENCE.** "The model did not answer" and "the model says
      this is fine" must never be the same value on the wire — the invariant `ARCHITECTURE.md`
      states for `Unresolved` and `types/checked.py` states for `UNCHECKABLE`.

      **`BROKEN` WITHOUT A QUOTE IS REFUSED IN `__post_init__`.** Not checked by the caller, not
      validated downstream: refused at construction, the way `Checked` refuses `VIOLATED` without
      evidence. A violation the developer cannot locate in their own file is not a violation they
      can act on.
IMPORTS: types.verdict for `Provenance` and `Site`. Nothing else, from any layer.
CONSUMED BY: `verify/judged_rule.py`, `render/blocks/judged_block.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind.types.verdict import Provenance, Site

MIN_QUOTE_CHARS = 8
"""Shortest quote that may anchor a `BROKEN` verdict.

Matches `verify/anchor.py:MIN_QUOTE_CHARS`. A three-character quote matches somewhere in almost
any file, so anchoring against one proves nothing and would make the check ceremonial."""


class Verdict(Enum):
    """What the model said about one rule and one file.

    **THREE VALUES, AND THE THIRD IS THE POINT.** Two would force every failure to read as `MET`.
    """

    MET = "met"
    BROKEN = "broken"
    UNDECIDED = "undecided"
    """We asked and did not get an answer we could use. **Not a pass.**"""


@dataclass(frozen=True, slots=True)
class Judged:
    """One model-judged rule against one file. Never a `Checked`, never an audit row."""

    rule_id: str
    site: Site
    verdict: Verdict
    quote: str = ""
    """The line the model says breaks the rule. Required by `BROKEN`, empty otherwise."""

    why: str = ""
    """The model's sentence, or ours describing why nothing was decided."""

    def __post_init__(self) -> None:
        if self.verdict is Verdict.BROKEN and len(self.quote.strip()) < MIN_QUOTE_CHARS:
            raise ValueError(
                f"rule {self.rule_id!r}: BROKEN needs a quote of at least "
                f"{MIN_QUOTE_CHARS} characters, so the reader can find what fired"
            )
        if self.verdict is not Verdict.BROKEN and self.quote:
            raise ValueError(f"rule {self.rule_id!r}: only BROKEN carries a quote")

    @property
    def provenance(self) -> Provenance:
        """**ALWAYS `MODEL`.** There is no path by which this object holds a parser's verdict."""
        return Provenance.MODEL

    @property
    def reproducible(self) -> bool:
        """**ALWAYS FALSE.** Re-running this on the same commit may give a different answer."""
        return False
