"""The outcome verdict and the evidence that justifies it.

WHAT: The three verdicts, the rule that produced one, and the record carrying both plus
      the evidence commit.
WHY:  Split from `scan_outcome.py`, which owns walking history. This module owns what a
      verdict IS; that one owns how it is reached. The split happened when UNSCANNABLE
      gained a typed reason and the scan module went over the size cap -- but the
      concerns were already two, and the cap only made it visible.

      UNSCANNABLE is the reason this module is worth reading. It is not a third flavour
      of CLEAN; it means the instrument could not look, and every consumer has to drop it
      from the denominator rather than code it 0. The scan walked from the clone's HEAD
      until 15.5% of the corpus turned out to merge into `dev`, `develop` or a feature
      branch -- for those PRs the merge commit and its whole post-merge history sat
      outside the walk, and each one came back CLEAN. Those are the repositories with a
      release process, so the instrument was systematically scoring the more
      process-mature projects as unbroken, in the direction of the null, leaving no trace
      in any exclusion count.
IMPORTS: phase0.outcome_window for the Exclusion categories. Nothing else.
CONSUMED BY: scan_outcome.py, analysis/build_table.py, controls/gate.py,
      handlabel/draw.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from phase0.outcome.window import Exclusion


class Outcome(Enum):
    BROKE = "broke"
    CLEAN = "clean"
    # We could not look. Distinct from CLEAN on purpose -- see the module docstring and
    # `outcome_window.Exclusion`, which owns the reasons. Every consumer must exclude it
    # rather than code it 0: the scan producing an honest UNSCANNABLE does not help if
    # `tabulate` folds it back into the clean cell, which is where this bug lived one
    # layer down after the scan itself was fixed.
    UNSCANNABLE = "unscannable"


class Criterion(Enum):
    """Which `PHASE0_PREREGISTRATION.md` “Outcome variable” rule fired. Recorded so
    Results can report their relative weight.
    """

    REVERT = "revert"  # explicit `This reverts commit <sha>`
    FIX_TOUCHING_SAME_FILE = "fix_touching_same_file"
    ISSUE_LINK = "issue_link"  # A4, optional and API-dependent
    NONE = "none"


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """A verdict and the commit that justifies it."""

    outcome: Outcome
    criterion: Criterion = Criterion.NONE
    evidence_sha: str = ""
    evidence_message: str = ""
    commits_examined: int = 0
    issue_link_checked: bool = False  # A4: stated in Results, never assumed
    # Which category this exclusion belongs to. NONE for every scanned verdict, so
    # `is_consistent` is checkable rather than assumed.
    exclusion: Exclusion = Exclusion.NONE

    @property
    def is_auditable(self) -> bool:
        """A BROKE verdict without evidence is not a result, it is an assertion."""
        return self.outcome is Outcome.CLEAN or bool(self.evidence_sha)

    @property
    def is_consistent(self) -> bool:
        """UNSCANNABLE carries a reason; a scanned verdict carries none.

        Returned rather than commented because the whole point of the exclusion is that
        somebody downstream counts it by category, and an UNSCANNABLE with reason NONE
        would land in whichever bucket the caller happens to default to.
        """
        return (self.outcome is Outcome.UNSCANNABLE) is (self.exclusion is not Exclusion.NONE)
