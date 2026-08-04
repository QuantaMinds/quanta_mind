"""Controls: earn the right to believe the answer.

WHAT: A positive control (plant breakage caused by an unresolvable edge, prove we
      detect it) and negative controls (replace exposure with a variable that
      cannot possibly matter, prove we find nothing).
WHY:  This is the step everyone skips, and it is the most important gate in the
      study. You cannot interpret a null from an instrument you have not shown can
      produce a positive -- you would probably believe it.

      Positive control: 30 synthetic PRs on the Django fixture where a subclass
      calls `super().method()` and the base signature then changes. PyCG misses
      super() entirely, verified on our own pinned instrument -- see
      ENVIRONMENT.lock, where `super().validate(req)` resolved to `<builtin>.super`
      rather than to the base method. Expected RR >= 5. If RR is about 1 the
      instrument is broken; stop, do not run on real data.

      Negative controls: filename initial in a-m, even line count, odd PR number.
      Expected RR about 1.0 with a CI spanning 1. Any nonsense variable showing
      RR > 1.5 means the pipeline has a bug, most likely an outcome scan
      contaminated by repository identity rather than by the PR.
IMPORTS: classify_exposure (Exposure), scan_outcome (Outcome), build_table.
CONSUMED BY: run_pipeline.py; tests/test_controls.py. Results to results/controls.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

POSITIVE_CONTROL_N = 30
POSITIVE_CONTROL_MIN_RR = 5.0
NEGATIVE_CONTROL_MAX_RR = 1.5


@dataclass(frozen=True, slots=True)
class ControlResult:
    """One control arm and whether it cleared its threshold."""

    name: str
    relative_risk: float
    ci_low: float
    ci_high: float
    passed: bool


def run_positive_control(fixture_repo: Path, n: int = POSITIVE_CONTROL_N) -> ControlResult:
    """Plant super()-mediated breakage and confirm the instrument detects it.

    Raises:
        NotImplementedError: Day 2 of the run. See RUNBOOK section 2.1.
    """
    raise NotImplementedError("Phase 0 Day 2 — see docs/findings/PHASE0_RUNBOOK.md")


def run_negative_controls(exposure_source: Path) -> list[ControlResult]:
    """Re-run the pipeline against variables that cannot matter.

    Raises:
        NotImplementedError: Day 2 of the run. See RUNBOOK section 2.2.
    """
    raise NotImplementedError("Phase 0 Day 2 — see docs/findings/PHASE0_RUNBOOK.md")
