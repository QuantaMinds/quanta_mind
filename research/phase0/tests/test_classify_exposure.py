"""Contract test for the exposure classifier.

WHAT: Asserts classify() is unimplemented and that the three arms stay distinct.
WHY:  RUNBOOK section 1.2's leakage test -- exposure computed at the merged state
      rather than the parent commit -- is "the single most likely way to fake a
      positive result by accident". The enum assertions below are cheap and they
      fail the moment someone collapses UNANALYZED into EXPOSED, which section 4.4
      says would hide which product this is.
IMPORTS: phase0.classify_exposure, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.classify_exposure import Exposure, classify


def test_classify_is_unimplemented() -> None:
    """Day 1 implements this; until then it must not return a plausible guess."""
    with pytest.raises(NotImplementedError):
        classify(None, [], None)  # type: ignore[arg-type]


def test_three_arms_not_two() -> None:
    """UNANALYZED is a real arm. Merging it into EXPOSED changes the conclusion."""
    assert {e.value for e in Exposure} == {"exposed", "unexposed", "unanalyzed"}
