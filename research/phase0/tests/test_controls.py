"""Verification of the controls, and the capability profile they expose.

WHAT: Pins the pre-registered thresholds, and records which of four
      unresolvable-caller mechanisms the exposure variable can actually detect.
WHY:  RUNBOOK section 2.1 calls the positive control the most important gate in
      the study. Thresholds are asserted here so that lowering one to make a run
      pass shows up as a failing test rather than a quiet edit -- which
      PHASE0_PREREGISTRATION.md calls research misconduct on ourselves.

      CAPABILITY is the more important table. `super()` is PyCG's best-documented
      blind spot and the easiest possible positive; a control firing only there
      means the instrument is narrow, and RUNBOOK section 2.1 wants that known
      BEFORE a null is interpreted. Written down as data so any change to the
      exposure variable's reach shows up as a diff.
IMPORTS: phase0.controls, phase0.build_table, phase0.scan_outcome, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.build_table import Observation
from phase0.classify_exposure import Exposure
from phase0.controls import (
    MECHANISMS,
    NEGATIVE_CONTROL_MAX_RR,
    POSITIVE_CONTROL_MIN_RR,
    POSITIVE_CONTROL_N,
    probe_all_mechanisms,
    probe_mechanism,
    run_negative_controls,
    run_positive_control,
)
from phase0.scan_outcome import Outcome

# The measured reach of the exposure variable as defined in §3.1. Established by
# running the probe with an EMPTY edge set, so a miss is structural rather than
# something PyCG happened to resolve.
#
# Only `super_chain` is detectable. The other three dispatch through a value --
# getattr(m, k)(), REGISTRY[k](), HOOKS[0]() -- so no call site carries the
# symbol's NAME, nothing can be attributed to the symbol, and it produces no pair
# at all. That is a false negative, biased toward the null.
CAPABILITY: dict[str, bool] = {
    "super_chain": True,
    "computed_getattr": False,
    "string_registry": False,
    "registering_decorator": False,
}


def _observation(symbol: str, repo: str, exposed: bool, broke: bool) -> Observation:
    arm = Exposure.EXPOSED if exposed else Exposure.UNEXPOSED
    return Observation(
        symbol=symbol,
        repo_id=repo,
        outcome=Outcome.BROKE if broke else Outcome.CLEAN,
        primary=arm,
        sensitivity_low=arm,
        sensitivity_high=arm,
    )


def test_positive_control_threshold_is_five() -> None:
    """RR >= 5 on synthetic data. Below that the instrument is broken, not the thesis."""
    assert POSITIVE_CONTROL_MIN_RR == 5.0


def test_positive_control_uses_thirty_synthetic_prs() -> None:
    assert POSITIVE_CONTROL_N == 30


def test_negative_control_ceiling_is_one_point_five() -> None:
    """A nonsense variable above this means the pipeline manufactures signal."""
    assert NEGATIVE_CONTROL_MAX_RR == 1.5


def test_all_four_mechanisms_are_probed() -> None:
    """Diversification is the point: one mechanism is not a control."""
    assert set(MECHANISMS) == set(CAPABILITY)


@pytest.mark.parametrize("mechanism", sorted(CAPABILITY))
def test_capability_profile_is_as_recorded(mechanism: str) -> None:
    """The exposure variable's measured reach, pinned so a change is visible.

    This is the capability half of the Judge decomposition, applied to our own
    instrument rather than to someone else's analyser.
    """
    probe = probe_mechanism(mechanism, MECHANISMS[mechanism])
    assert probe.detected is CAPABILITY[mechanism]


def test_only_named_call_sites_are_detectable() -> None:
    """The limitation stated as one number, so it cannot be read past.

    Three of four mechanisms dispatch through a value and carry no callee name.
    Exposure is therefore "named call sites whose edge is missing", not "call
    sites we cannot resolve" -- narrower than §3.1's prose suggests.
    """
    detected = [p.mechanism for p in probe_all_mechanisms() if p.detected]
    assert detected == ["super_chain"]


def test_positive_control_detects_a_planted_effect() -> None:
    """A strong planted effect must clear the RR >= 5 gate.

    Deliberately NOT perfectly separated: 80% of exposed break against 10% of
    unexposed, for a true RR of 8. Perfect separation makes the ratio unbounded
    and the fit unidentified, so a control built that way would pass for a reason
    that tells you nothing about a real corpus.
    """
    rows = [_observation(f"m.s{i}", f"repo{i % 6}", True, i % 10 < 8) for i in range(60)]
    rows += [_observation(f"m.c{i}", f"repo{i % 6}", False, i % 10 < 1) for i in range(60)]
    assert run_positive_control(rows).passed is True


def test_positive_control_fails_when_there_is_no_effect() -> None:
    """A control that passes on noise is not a control."""
    rows = [_observation(f"m.s{i}", f"repo{i % 6}", i % 2 == 0, i % 3 == 0) for i in range(60)]
    assert run_positive_control(rows).passed is False


def test_negative_controls_find_nothing_on_unrelated_outcomes() -> None:
    """Nonsense exposure against outcomes it cannot cause must sit near 1.

    Symbols vary by initial letter and length on purpose. An earlier version named
    every row `m.s{i}`, which made each symbol-derived predicate constant, left the
    2x2 with an empty margin, and produced an uncomputable control that the old
    logic scored as a pass. The fixture was degenerate in exactly the way the
    synthetic corpus was.
    """
    rows = [
        _observation(
            f"{chr(97 + i % 26)}{'x' * (i % 3)}.s{i}",
            f"repo{i % 8}{'x' * (i % 2)}",
            i % 2 == 0,
            i % 7 == 0,
        )
        for i in range(120)
    ]
    assert [r.passed for r in run_negative_controls(rows)] == [True, True, True]


def test_every_negative_control_is_reported() -> None:
    """All three run and all three are reported, pass or fail."""
    rows = [
        _observation(
            f"{chr(97 + i % 26)}.s{i}", f"repo{i % 4}{'x' * (i % 2)}", i % 2 == 0, i % 5 == 0
        )
        for i in range(40)
    ]
    assert len(run_negative_controls(rows)) == 3
