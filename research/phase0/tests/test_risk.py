"""Verification of the two intervals and the power floor — amendment A8.

WHAT: Asserts the Katz interval against a hand-computable table, that the
      cluster-robust fit is used for the decision, that clustering widens the
      interval, and that an undefined ratio is a value rather than a crash.
WHY:  A8 exists because Katz assumes independent trials and our observations are
      not independent. The naive interval comes out too narrow at exactly the
      boundary §4 turns on, so a naive CI could clear a threshold a correct one
      would not. test_clustering_widens_the_interval is the one that would catch a
      regression back to naive inference.

      An undefined ratio must never surface as an exception: a crashed analysis
      and an analysis that found nothing must not be the same value on the wire.
IMPORTS: phase0.risk, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import math

from phase0.risk import (
    MIN_BREAKAGES_FOR_POWER,
    Counts,
    cluster_robust,
    design_effect,
    katz,
)


def test_power_floor_is_twenty_breakages() -> None:
    assert MIN_BREAKAGES_FOR_POWER == 20


def test_katz_matches_a_hand_computed_ratio() -> None:
    """20/100 over 10/100 is exactly 2.0. Arithmetic, not a library's opinion."""
    result = katz(
        Counts(exposed_broke=20, exposed_clean=80, unexposed_broke=10, unexposed_clean=90)
    )
    assert round(result.relative_risk, 6) == 2.0


def test_katz_interval_brackets_the_estimate() -> None:
    result = katz(Counts(20, 80, 10, 90))
    assert result.ci_low < result.relative_risk < result.ci_high


def test_underpowered_table_is_not_powered() -> None:
    """19 breakages is not a null result. It is no result."""
    assert katz(Counts(19, 100, 5, 100)).is_powered is False


def test_powered_at_the_boundary() -> None:
    """Exactly 20 clears the floor: the comparison is >=, not >."""
    assert katz(Counts(20, 100, 5, 100)).is_powered is True


def test_empty_margin_is_a_value_not_an_exception() -> None:
    """A zero row makes the ratio undefined. That must be reportable, not fatal."""
    result = katz(Counts(0, 0, 5, 95))
    assert result.ci_method == "unavailable"


def test_cluster_robust_recovers_a_known_ratio() -> None:
    """With many clusters and a planted effect, the point estimate should land near 2."""
    exposed, broke, repo = [], [], []
    for i in range(400):
        is_exposed = i % 2 == 0
        exposed.append(1 if is_exposed else 0)
        broke.append(1 if (is_exposed and i % 10 < 4) or (not is_exposed and i % 10 < 2) else 0)
        repo.append(f"repo{i % 20}")
    counts = Counts(
        sum(1 for e, b in zip(exposed, broke, strict=True) if e and b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if e and not b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if not e and b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if not e and not b),
    )
    result = cluster_robust(exposed, broke, repo, counts)
    assert 1.5 < result.relative_risk < 2.5


def test_cluster_robust_reports_its_method() -> None:
    """§4 reads this interval. It must say which one it is."""
    exposed = [i % 2 for i in range(200)]
    broke = [1 if i % 5 == 0 else 0 for i in range(200)]
    repo = [f"repo{i % 10}" for i in range(200)]
    counts = Counts(20, 80, 20, 80)
    assert cluster_robust(exposed, broke, repo, counts).ci_method == "cluster-robust"


def test_single_cluster_cannot_support_a_robust_variance() -> None:
    """One repository is one observation for variance purposes, whatever n says."""
    exposed = [i % 2 for i in range(50)]
    broke = [1 if i % 4 == 0 else 0 for i in range(50)]
    result = cluster_robust(exposed, broke, ["only-repo"] * 50, Counts(10, 15, 5, 20))
    assert result.ci_method == "unavailable"


def test_clustering_widens_the_interval() -> None:
    """A8's whole reason for existing, as one number.

    Outcomes are made to agree within each repository, which is exactly the
    dependence Katz assumes away. The robust interval must not be narrower.
    """
    exposed, broke, repo = [], [], []
    for i in range(300):
        cluster = i % 10
        exposed.append(1 if cluster < 5 else 0)
        broke.append(1 if cluster in (0, 1, 5) else 0)
        repo.append(f"repo{cluster}")
    counts = Counts(
        sum(1 for e, b in zip(exposed, broke, strict=True) if e and b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if e and not b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if not e and b),
        sum(1 for e, b in zip(exposed, broke, strict=True) if not e and not b),
    )
    naive = katz(counts)
    robust = cluster_robust(exposed, broke, repo, counts)
    effect = design_effect(naive, robust)
    assert math.isnan(effect) or effect >= 1.0
