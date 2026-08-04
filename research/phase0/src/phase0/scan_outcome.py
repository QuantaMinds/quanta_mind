"""The outcome variable: did a revert or fix land within 7 days?

WHAT: Scans the repository's history after a PR merged and returns BROKE or CLEAN,
      with the commit that triggered the verdict attached as evidence.
WHY:  The outcome is deliberately BEHAVIOURAL, not AST-based. AIDev ships
      breaking-change labels produced by static analysis, and static analysis is
      structurally blind to the breakage this thesis is about -- using those labels
      as ground truth would manufacture a false null. PHASE0_PREREGISTRATION.md
      fixes this choice and RUNBOOK section 6 forbids switching to the AST outcome
      because it gives a nicer number.

      `evidence` is not decoration. It is the commit SHA and message that produced
      the verdict, and it is what makes the result auditable by someone who does not
      trust us (RUNBOOK section 3).

      Expected base rate 5-20%. Below 2% the classifier is too strict; above 40% it
      is counting routine follow-ups (RUNBOOK section 2.3). Gate: >=16/20 agreement
      with hand-labelling, done BEFORE any classifier output is seen.
IMPORTS: git (GitPython), extract_prs (PRRecord).
CONSUMED BY: run_pipeline.py, build_table.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from phase0.extract_prs import PRRecord

WINDOW_DAYS = 7

# A commit is a fix only if it overlaps the PR's files AND says so. "refactor"
# deliberately does not match -- RUNBOOK section 1.3.
FIX_TOKENS: frozenset[str] = frozenset({"fix", "revert", "broke", "broken", "regression"})


class Outcome(Enum):
    BROKE = "broke"
    CLEAN = "clean"


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """A verdict and the commit that justifies it."""

    outcome: Outcome
    evidence_sha: str | None
    evidence_message: str | None


def scan(pr: PRRecord, window_days: int = WINDOW_DAYS) -> OutcomeRecord:
    """Look for a revert or fix touching this PR's files inside the window.

    Raises:
        NotImplementedError: Day 1 of the run. See RUNBOOK section 1.3.
    """
    raise NotImplementedError("Phase 0 Day 1 — see docs/findings/PHASE0_RUNBOOK.md")
