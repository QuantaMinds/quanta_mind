"""Whether a change may be held out of a merge, and the rule that only a parser gets to say so.

WHAT: `decide(rows)` folds the `Checked` rows for one change into a `Gate` -- a `Standing`, the
      violations that justify it, and counts of what was deferred or could not be checked.
      It performs no I/O and asks nothing of a model, so the verdict is reproducible from the
      audit rows alone.
WHY:  **A GATE THAT CAN BLOCK ON A MODEL VERDICT MUST NOT EXIST HERE.** Raw model findings measure
      66.7 to 82.1% wrong, and a wrong verdict that merely comments costs a reader thirty seconds
      while a wrong verdict that BLOCKS costs a team its afternoon and this product its welcome.
      The split is not a filter applied on top: `verify/rule_check.check` returns
      `Outcome.DEFERRED` for `CheckKind.MODEL_JUDGED` before reaching any path that can build a
      violation, and `Rule.provenance` is derived from the check kind rather than set by a caller.
      `VIOLATED` is therefore parser-only by construction, and `blocking()` asserts that rather
      than trusting it.

      **A CHANGE WITH NO DECLARED RULES GETS NO VERDICT, NOT A PASS.** `Standing.NOT_DECLARED` is
      distinct from `Standing.CLEAR` because posting success where nothing was checked asserts
      compliance with a standard nobody wrote -- the same lie as a green test that asserts
      nothing. The caller is expected to post no status at all for it.

      **WHAT WE COULD NOT CHECK IS CARRIED, NEVER SWALLOWED.** `UNCHECKABLE` does not block: a
      failure to decide is not a violation. But a gate reporting CLEAR while ten files were
      unparseable is a proxy for compliance rather than compliance, so the count rides along in
      `Gate.unchecked` and belongs in anything a human reads.
IMPORTS: types.checked only. Nothing to its right, and nothing that touches a network.
CONSUMED BY: `serve/review_delivery.py`, which posts the status, and `ingest/publish/
      commit_status.py`, which renders this into GitHub's shape.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from quantamind.types.standards.checked import Checked, Outcome


class Standing(Enum):
    """What a change's declared standards say about it. None of these is an absence."""

    NOT_DECLARED = "not_declared"
    """No rule governed any changed file. Post nothing -- see the docstring above."""

    CLEAR = "clear"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class Gate:
    """The verdict, and the rows that justify it. Built only by `decide`."""

    standing: Standing
    violations: tuple[Checked, ...]
    deferred: int
    """Rows a model was asked to judge. Reported to a human, never counted toward blocking."""

    unchecked: int
    """Rows where a parser could not decide. Never blocks, never silently dropped."""

    passed: int

    def __post_init__(self) -> None:
        if self.standing is Standing.BLOCKED and not self.violations:
            raise ValueError("a blocked gate must name what blocked it")
        if self.standing is not Standing.BLOCKED and self.violations:
            raise ValueError("violations were found and the gate did not block on them")

    @property
    def checked(self) -> int:
        """Every row a rule produced. **The denominator of any rate quoted about this change.**"""
        return len(self.violations) + self.deferred + self.unchecked + self.passed


def blocking(rows: Sequence[Checked]) -> tuple[Checked, ...]:
    """The rows that may hold a merge: `VIOLATED` and nothing else.

    `DEFERRED` is where a model-judged rule lands, so excluding it here is what keeps a model out
    of the gate. That exclusion is checked rather than assumed -- if `rule_check` ever let a
    deferred row carry evidence of a violation, this would be the place it leaked through.
    """
    return tuple(row for row in rows if row.outcome is Outcome.VIOLATED)


def decide(rows: Sequence[Checked]) -> Gate:
    """Fold one change's audit rows into a verdict. No rows means nothing was declared."""
    counts = dict.fromkeys(Outcome, 0)
    for row in rows:
        counts[row.outcome] += 1
    violations = blocking(rows)
    if not rows:
        standing = Standing.NOT_DECLARED
    else:
        standing = Standing.BLOCKED if violations else Standing.CLEAR
    return Gate(
        standing=standing,
        violations=violations,
        deferred=counts[Outcome.DEFERRED],
        unchecked=counts[Outcome.UNCHECKABLE],
        passed=counts[Outcome.PASSED],
    )
