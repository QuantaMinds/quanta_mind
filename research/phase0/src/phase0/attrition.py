"""Why rows left the corpus during extraction, counted by cause.

WHAT: `Attrition` — one counter per reason a candidate row never became a `PRRecord`,
      plus the total.
WHY:  Split out of `extract_prs.py`, which exported a record type, an attrition type and
      a table-loading function family from one module -- three public concerns, and the
      file had reached its 200-line cap, which is how a module stops being able to carry
      the field it needs next. Separated so `PRRecord` can grow without competing for
      space against counters it has nothing to do with.

      Every field here exists so a row that leaves is REPORTED rather than dropped. A
      corpus that shrinks silently is indistinguishable from one that was always small.
IMPORTS: stdlib dataclasses only. Nothing from phase0 -- extract_prs imports this,
      never the other way.
CONSUMED BY: extract_prs.py; tests/test_extract_prs.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Attrition:
    """Why rows left the corpus. Reported, never silently dropped."""

    not_python: int = 0
    not_structural: int = 0
    not_merged: int = 0
    no_merge_metadata: int = 0
    unresolvable_parent: int = 0

    @property
    def total(self) -> int:
        return (
            self.not_python
            + self.not_structural
            + self.not_merged
            + self.no_merge_metadata
            + self.unresolvable_parent
        )
