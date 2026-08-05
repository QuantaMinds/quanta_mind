"""Verification of the analysis: the A6 split, the arms, and the `PHASE0_PREREGISTRATION.md`
“Decision thresholds” verdict.

WHAT: Asserts that the primary table holds only measurable pairs, that multi-site
      pairs are bounded instead of guessed, that UNANALYZED_RESOURCE is never
      pooled, and that power is read before the point estimate.
WHY:  Three pre-registered decisions are enforced here rather than remembered.

      `PHASE0_PREREGISTRATION.md` “Decision thresholds”: `a < 20` is no result, not a null.
      Reporting an underpowered null as a
      negative is the most expensive mistake available -- it kills a live thesis on
      noise -- so the verdict function checks power first and unconditionally.

      A6: the primary table is the single-site subset. A symbol with no measurable
      pair must be excluded, not defaulted into an arm.

      `PHASE0_RUNBOOK.md` “The `UNANALYZED` arm decides what company this is”: RR_unanalyzed is
      computed separately. If the effect lives there, this is a scalability product, not an
      unsoundness product, and that is a different company. Pooling the arms would hide the
      distinction the section exists on. IMPORTS: phase0.analysis.{build_table,risk,verdict},
      phase0.classify_exposure, phase0.outcome.conclusion. CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.analysis.build_table import Observation, build, tabulate
from phase0.analysis.risk import Counts, katz
from phase0.analysis.verdict import STRONG_CI_LOW, STRONG_RR, WEAK_RR, read_verdict
from phase0.classify_exposure import Exposure
from phase0.outcome.conclusion import Outcome


def _row(
    index: int,
    primary: Exposure | None,
    broke: bool,
    repo: str = "r0",
    stratum: str = "",
) -> Observation:
    return Observation(
        symbol=f"m.s{index}",
        repo_id=repo,
        outcome=Outcome.BROKE if broke else Outcome.CLEAN,
        primary=primary,
        sensitivity_low=primary or Exposure.UNEXPOSED,
        sensitivity_high=primary or Exposure.EXPOSED,
        strata={"framework": stratum} if stratum else {},
    )


def test_verdict_thresholds_match_the_preregistration() -> None:
    """Strong: RR >= 3.0 with CI lower bound > 1.5. Weak but real: RR >= 1.5."""
    assert (STRONG_RR, STRONG_CI_LOW, WEAK_RR) == (3.0, 1.5, 1.5)


def test_unmeasurable_pairs_are_excluded_from_the_primary_table() -> None:
    """A6. A symbol with no single-site pair has no arm, and must not get one."""
    rows = [_row(0, Exposure.EXPOSED, True), _row(1, None, True), _row(2, None, False)]
    counts, _, _, _ = tabulate(rows)
    assert counts.total == 1


def test_unanalyzed_is_never_pooled_into_exposed() -> None:
    """`PHASE0_RUNBOOK.md` “The `UNANALYZED` arm decides what company this is” reads this arm alone.
    Pooling it would hide what kind of product this is.
    """
    rows = [
        _row(0, Exposure.EXPOSED, True),
        _row(1, Exposure.UNANALYZED_RESOURCE, True),
        _row(2, Exposure.UNEXPOSED, False),
    ]
    counts, _, _, _ = tabulate(rows)
    assert (counts.exposed_broke, counts.total) == (1, 2)


def test_underpowered_result_reads_as_no_result_not_null() -> None:
    """The distinction `PHASE0_PREREGISTRATION.md` “Decision thresholds” turns on, and the one most
    easily reported wrongly.
    """
    rows = [_row(i, Exposure.EXPOSED, i < 5, f"r{i % 4}") for i in range(20)]
    rows += [_row(100 + i, Exposure.UNEXPOSED, False, f"r{i % 4}") for i in range(20)]
    assert read_verdict(build(rows).primary).label == "no result"


def test_powered_null_reads_as_null() -> None:
    """With enough events and no effect, the verdict is null, not 'no result'."""
    rows = [_row(i, Exposure.EXPOSED, i % 4 == 0, f"r{i % 8}") for i in range(160)]
    rows += [_row(500 + i, Exposure.UNEXPOSED, i % 4 == 0, f"r{i % 8}") for i in range(160)]
    assert read_verdict(build(rows).primary).label == "null"


def test_strong_result_is_reported_as_strong() -> None:
    """A planted, powered, clustered effect must clear both `PHASE0_PREREGISTRATION.md` “Decision
    thresholds” conditions.
    """
    rows = [_row(i, Exposure.EXPOSED, i % 10 < 6, f"r{i % 12}") for i in range(200)]
    rows += [_row(500 + i, Exposure.UNEXPOSED, i % 10 < 1, f"r{i % 12}") for i in range(200)]
    assert read_verdict(build(rows).primary).label == "strong"


def test_sensitivity_bounds_are_both_reported() -> None:
    """A6: multi-site pairs coded both ways, so the collapse can be bounded."""
    rows = [_row(i, None, i % 3 == 0, f"r{i % 5}") for i in range(60)]
    rows += [_row(500 + i, Exposure.UNEXPOSED, False, f"r{i % 5}") for i in range(60)]
    analysis = build(rows)
    assert analysis.sensitivity_low.counts.total > 0 and analysis.sensitivity_high.counts.total > 0


def test_excluded_multi_site_count_is_reported() -> None:
    """How much A6's restriction cost has to be visible, not inferred."""
    rows = [_row(0, None, True), _row(1, None, False), _row(2, Exposure.EXPOSED, True)]
    assert build(rows).multi_site_excluded == 2


def test_naive_and_robust_intervals_are_both_kept() -> None:
    """A8: the gap between them is the design effect, and it gets reported."""
    rows = [_row(i, Exposure.EXPOSED, i % 3 == 0, f"r{i % 9}") for i in range(120)]
    rows += [_row(500 + i, Exposure.UNEXPOSED, i % 9 == 0, f"r{i % 9}") for i in range(120)]
    analysis = build(rows)
    assert analysis.primary_naive.ci_method == "katz"


def test_strata_are_reported_separately() -> None:
    """`PHASE0_PREREGISTRATION.md` “Pre-specified confounders” pre-specifies stratification so
    adjusting later is not a rescue attempt.
    """
    rows = [_row(i, Exposure.EXPOSED, i % 2 == 0, f"r{i % 6}", "django") for i in range(60)]
    rows += [_row(500 + i, Exposure.UNEXPOSED, False, f"r{i % 6}", "none") for i in range(60)]
    assert sorted(build(rows, strata=["framework"]).strata) == [
        "framework=django",
        "framework=none",
    ]


def test_verdict_refuses_an_unavailable_interval() -> None:
    """A crashed fit is not a null. It reports as no result."""
    assert read_verdict(katz(Counts(0, 0, 5, 95))).label == "no result"


def _unscannable(index: int, primary: Exposure | None, repo: str = "r0") -> Observation:
    """A unit the outcome scan could not look at: the arm is known, the outcome is not."""
    return Observation(
        symbol=f"m.u{index}",
        repo_id=repo,
        outcome=Outcome.UNSCANNABLE,
        primary=primary,
        sensitivity_low=primary or Exposure.UNEXPOSED,
        sensitivity_high=primary or Exposure.EXPOSED,
    )


def test_unscannable_outcomes_are_excluded_not_coded_clean() -> None:
    """The base-branch bug, one layer down.

    `tabulate` coded the outcome as `1 if BROKE else 0`, so a unit the scan reported
    UNSCANNABLE for landed in the clean cell. The scan being fixed to say "I could not
    look" achieves nothing while the analysis translates that back into "nothing broke"
    before the estimate sees it. Asserted on the cell, not on the total, because a count
    that merely stayed the same would pass either way.
    """
    rows = [
        _row(0, Exposure.EXPOSED, True),
        _row(1, Exposure.UNEXPOSED, False),
        _unscannable(2, Exposure.EXPOSED),
        _unscannable(3, Exposure.EXPOSED),
    ]
    counts, exposed, broke, _ = tabulate(rows)

    assert counts.exposed_clean == 0, "an unscannable unit was folded into the clean cell"
    assert counts.total == 2
    assert (exposed, broke) == ([1, 0], [1, 0])


def test_unscannable_units_are_counted_where_someone_reads_them() -> None:
    """Dropping them silently is the same failure wearing a different hat.

    A complete-case table is honest only while the size of the case it is missing is
    reported beside it, so `build` carries the count rather than leaving the caller to
    infer it from a total that does not add up.
    """
    rows = [
        _row(0, Exposure.EXPOSED, True),
        _row(1, Exposure.UNEXPOSED, False),
        _unscannable(2, Exposure.EXPOSED),
        _unscannable(3, None),
    ]
    analysis = build(rows)

    assert analysis.outcome_excluded == 2
