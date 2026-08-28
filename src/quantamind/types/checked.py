"""One rule, one file, one outcome — the row an audit trail is made of.

WHAT: `Outcome` and `Checked`. Every (rule, file) pair produces exactly one `Checked`, including
      the pairs where nothing was found and the pairs we could not decide.
WHY:  **A COMPLIANCE RATE IS A RATIO, AND BOTH HALVES HAVE TO BE REAL.** If only violations are
      recorded, the denominator is whatever somebody assumed, and "98% compliant" means nothing
      because nobody can say 98% of what. A row for every pair makes the denominator observable.

      **FOUR OUTCOMES, BECAUSE THREE OF THEM LOOK LIKE A PASS FROM OUTSIDE.** A rule that found
      nothing, a file in a language we cannot parse, a file that will not parse, and a rule only a
      model can decide all end with no violation reported. Collapsing them would report a JS
      repository as fully compliant with Python-only checks — the exact shape of failure this
      project keeps finding: a clean zero produced by a check that never ran.

      **`VIOLATED` WITHOUT EVIDENCE IS REFUSED, AND SO IS `UNCHECKABLE` WITHOUT A REASON.** A
      violation a developer cannot locate is an accusation, and an unchecked file with no stated
      cause is silence wearing a result's clothes. The constructor enforces both.
IMPORTS: stdlib plus `types.verdict` for `Reason` and `Site`. Nothing to its right.
CONSUMED BY: `verify/rule_check.py`, and the audit trail and dashboard that read these (D4, D5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind.types.verdict import Reason, Site


class Outcome(Enum):
    """What became of one rule on one file. None of these is an absence."""

    PASSED = "passed"
    VIOLATED = "violated"
    UNCHECKABLE = "uncheckable"
    DEFERRED = "deferred"
    """A model-judged rule. A parser did not decide it, and saying so is not the same as a pass."""


@dataclass(frozen=True, slots=True)
class Checked:
    """The audit row. Constructed only when the fields its outcome requires are present."""

    rule_id: str
    site: Site
    outcome: Outcome
    evidence: str = ""
    """The name and line that violated the rule. Required by `VIOLATED`, empty otherwise."""

    why: Reason | None = None
    """Why nothing could be decided. Required by `UNCHECKABLE`, `None` otherwise."""

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("a check with no rule id cannot be attributed to a standard")
        if self.outcome is Outcome.VIOLATED and not self.evidence.strip():
            raise ValueError(
                f"{self.rule_id} at {self.site.render()}: a violation with no evidence is an "
                f"accusation the developer cannot act on"
            )
        if self.outcome is Outcome.UNCHECKABLE and self.why is None:
            raise ValueError(
                f"{self.rule_id} at {self.site.render()}: an unchecked file with no stated reason "
                f"is indistinguishable from one that passed"
            )
        if self.outcome in {Outcome.PASSED, Outcome.DEFERRED} and (self.evidence or self.why):
            raise ValueError(
                f"{self.rule_id}: {self.outcome.value} carries neither evidence nor a reason"
            )

    @property
    def counts_toward_compliance(self) -> bool:
        """Whether this row belongs in the denominator of a compliance rate.

        **UNCHECKABLE AND DEFERRED DO NOT.** A rate computed over rows we never decided would move
        when our parser coverage changed rather than when the customer's code did.
        """
        return self.outcome in {Outcome.PASSED, Outcome.VIOLATED}
