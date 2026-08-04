"""The exposure variable: could the instrument resolve callers of the changed symbol?

WHAT: Compares the census (denominator) against the graph (numerator) at the
      PARENT commit, and assigns one of three values. UNANALYZED is a third arm and
      is never merged into EXPOSED.
WHY:  Two design decisions carry the study.

      1. Parent commit only. Classifying against the merged state leaks the outcome
         into the exposure and manufactures a correlation. RUNBOOK section 1.2 calls
         this "the single most likely way to fake a positive result by accident" and
         gates on a test for it.
      2. UNANALYZED separate. "We could not process this region" and "this region is
         dynamic" are different claims about different products. RUNBOOK section 4.4
         says which one dominates decides what company this is.

      Expected EXPOSED share is 10-30%. Near 0% or near 100% means the classifier is
      degenerate and the run stops (RUNBOOK section 6, Q4).
IMPORTS: census (denominator), run_graph (numerator), extract_prs (PRRecord).
CONSUMED BY: run_pipeline.py, build_table.py; tests/test_classify_exposure.py.
"""

from __future__ import annotations

from enum import Enum

from phase0.census import CallSite
from phase0.extract_prs import PRRecord
from phase0.run_graph import GraphResult


class Exposure(Enum):
    """Three arms. Never two."""

    EXPOSED = "exposed"  # >=1 call site to the changed symbol went unresolved
    UNEXPOSED = "unexposed"  # every call site resolved
    UNANALYZED = "unanalyzed"  # the tool timed out, OOM'd or crashed on this region


def classify(pr: PRRecord, sites: list[CallSite], graph: GraphResult) -> Exposure:
    """Assign the exposure arm for one PR, using parent-commit state only.

    Raises:
        NotImplementedError: Day 1 of the run. See RUNBOOK section 1.2.
    """
    raise NotImplementedError("Phase 0 Day 1 — see docs/findings/PHASE0_RUNBOOK.md")
