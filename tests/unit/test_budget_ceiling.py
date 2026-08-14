"""Unit tier: the request ceiling is observable, and settings fail loudly.

WHAT: Asserts that spend is compared against the budget from a recorded ledger rather than
      assumed from configuration, that a free-tier budget is a distinct state, and that a
      bad environment variable raises with its own name in the message.
WHY:  A ceiling never hit and a ceiling never wired up print the same thing. So the ledger
      records what was actually spent and `overspent` compares the two -- and the test that
      matters sets the ceiling to zero and asserts the review is still constructible, because
      a quota that fails the review turns a billing limit into an outage.
IMPORTS: quantamind.types (change, ranking, review, settings), pytest. Tier 1, no mocks.
CONSUMED BY: justfile (`just check`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import pytest

from quantamind.types.change import PullRequest, Repo
from quantamind.types.ranking import Budget, BudgetExceeded
from quantamind.types.review import CoverageLine, RequestLedger, Review
from quantamind.types.settings import SettingsError, load

REPO = Repo(host="github.com", name="acme/widget")
PR = PullRequest(repo=REPO, number=7, head_sha="0123456789abcdef", base_sha="fedcba9876543210")
COVERAGE = CoverageLine(units_checked=3, files_checked=2)


def test_overspend_is_read_from_the_ledger_not_from_the_budget() -> None:
    """The ledger is the observation; the budget is the intention. Compare, never assume."""
    review = Review(
        pull_request=PR,
        coverage=COVERAGE,
        budget=Budget(max_requests=3),
        ledger=RequestLedger(requests=4),
    )
    assert review.overspent is True
    assert review.ran_model is True


def test_a_review_at_its_ceiling_is_not_overspent() -> None:
    review = Review(
        pull_request=PR,
        coverage=COVERAGE,
        budget=Budget(max_requests=3),
        ledger=RequestLedger(requests=3),
    )
    assert review.overspent is False


def test_a_zero_ceiling_still_produces_a_review() -> None:
    """Above quota the review must DEGRADE to coverage-only, never fail.

    This is the known-answer test for the budget ceiling: set it to zero and the review is
    still constructible, still carries its coverage, and simply ran no model. A version that
    raised here would take a customer's reviews down over a billing threshold.
    """
    review = Review(
        pull_request=PR,
        coverage=COVERAGE,
        budget=Budget(max_requests=0, inference_permitted=False),
        ledger=RequestLedger(),
    )
    assert review.budget.is_free_tier is True
    assert review.ran_model is False
    assert review.overspent is False
    assert review.coverage.units_checked == 3


def test_budget_exceeded_names_both_numbers() -> None:
    """An error that says only "limit reached" cannot be diagnosed from a log line."""
    error = BudgetExceeded(spent=4, ceiling=3)
    assert error.spent == 4 and error.ceiling == 3
    assert "4" in str(error) and "3" in str(error)


def test_cache_reads_are_observable_because_their_absence_is_silent() -> None:
    """A persistent zero across multiple requests means the prefix is not caching.

    It produces no error. It simply costs full price on every call, which is why the counter
    exists rather than being trusted.
    """
    assert RequestLedger(requests=3, cache_read_tokens=0).used_cache is False
    assert RequestLedger(requests=3, cache_read_tokens=20_000).used_cache is True


def test_settings_default_to_not_running_a_model() -> None:
    """A process that starts calling a model because a default said so is expensive."""
    settings = load({})
    assert settings.inference_enabled is False
    assert settings.runs_model is False
    assert settings.max_requests == 3


def test_a_bad_environment_value_raises_with_its_variable_name() -> None:
    """`invalid literal for int()` in a startup log costs an hour. The name costs nothing."""
    with pytest.raises(SettingsError, match="MAX_REQUESTS"):
        load({"QUANTAMIND_MAX_REQUESTS": "three"})
    with pytest.raises(SettingsError, match="THRESHOLD_PERCENTILE"):
        load({"QUANTAMIND_THRESHOLD_PERCENTILE": "1.5"})
    with pytest.raises(SettingsError, match="INFERENCE_ENABLED"):
        load({"QUANTAMIND_INFERENCE_ENABLED": "maybe"})


def test_settings_are_read_from_the_mapping_given_not_the_process() -> None:
    """Tests configure by argument. A test that mutates os.environ leaks into the next one."""
    settings = load({"QUANTAMIND_MAX_REQUESTS": "1", "QUANTAMIND_INFERENCE_ENABLED": "true"})
    assert settings.max_requests == 1
    assert settings.runs_model is True
