"""The pilot: build records from the corpus and report where rows were lost.

WHAT: `run` walks repositories and admits PRs; `report` turns the attempts into shape
      metrics, cross-tabulated rather than pooled.
WHY:  Grouped because they are one concern with two halves, and because the top-level
      package was at its file cap — which is the cap doing its job, not obstructing it.
IMPORTS: phase0.pilot.{run,report}.
CONSUMED BY: `just pilot`; tests/pipeline/test_journal.py.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt
from phase0.pilot.repo_facts import star_counts
from phase0.pilot.report import report

__all__ = ["Attempt", "report", "star_counts"]
