"""Verification that the compliance table prints what could not be checked, not just what passed.

WHAT: Renders `store/compliance.Standing` and asserts on the text a buyer would read.
WHY:  **A PASS RATE WITH NO UNCHECKABLE COLUMN IS THE ARTEFACT THIS PRODUCT EXISTS TO REPLACE.**
      The differentiator is not that we check more rules; it is that we say which ones nobody
      could decide. If that column can be dropped without a test failing, the difference is
      decorative.

      **AND AN EMPTY RECORD MUST NOT RENDER AS COMPLIANCE.** A repository with nothing checked
      gets a sentence saying so. A blank table under a green heading is the silence this codebase
      refuses.
IMPORTS: pytest, quantamind.render.compliance_table, quantamind.store.compliance.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.render.compliance_table import table
from quantamind.store.compliance import RuleStanding, Standing

MANY_REVIEWS = 40


def _standing(*rules: RuleStanding, hotspots=(), other=0, reviews=MANY_REVIEWS) -> Standing:
    return Standing(rules=rules, hotspots=hotspots, other_hotspots=other, reviews=reviews)


def test_an_empty_record_says_so_rather_than_rendering_a_clean_table() -> None:
    rendered = table(_standing(), "o/r")

    assert "No rule has been checked" in rendered
    assert "absence of evidence" in rendered


def test_every_outcome_appears_as_its_own_column() -> None:
    """Dropping the uncheckable column would make this product the same as the others."""
    rendered = table(
        _standing(RuleStanding("no-print", passed=8, violated=2, uncheckable=5, deferred=1)),
        "o/r",
    )

    assert "uncheckable" in rendered
    assert "deferred" in rendered
    assert "| `no-print` | 8 | 2 | 5 | 1 | 20% |" in rendered


def test_the_rate_is_over_decided_checks_not_over_everything() -> None:
    """2 violated of 10 decided is 20%, not 2 of 16. The uncheckable are not a denominator."""
    rendered = table(
        _standing(RuleStanding("no-print", passed=8, violated=2, uncheckable=5, deferred=1)),
        "o/r",
    )

    assert "20%" in rendered
    assert "**10 check(s) decided, 6 not.**" in rendered


def test_a_rule_nothing_decided_renders_a_dash_not_a_zero() -> None:
    rendered = table(_standing(RuleStanding("judged", 0, 0, uncheckable=4, deferred=0)), "o/r")

    assert "| `judged` | 0 | 0 | 4 | 0 | - |" in rendered
    assert "0%" not in rendered


def test_the_caveat_is_printed_above_the_numbers() -> None:
    """A limit under a table is read second or not at all."""
    rendered = table(_standing(RuleStanding("no-print", 1, 1, 0, 0), reviews=3), "o/r")
    caveat = rendered.index("a rate needs at least")
    numbers = rendered.index("| `no-print` |")

    assert caveat < numbers


def test_hotspots_name_files_and_count_the_rest() -> None:
    rendered = table(
        _standing(RuleStanding("no-print", 0, 9, 0, 0), hotspots=(("src/a.py", 5),), other=7),
        "o/r",
    )

    assert "- `src/a.py` — 5" in rendered
    assert "and 7 more file(s) with at least one" in rendered


def test_no_developer_is_named_anywhere() -> None:
    """Per repository by decision. The competitor screenshot ranks named engineers."""
    rendered = table(_standing(RuleStanding("no-print", 3, 1, 0, 0)), "o/r")

    for word in ("author", "developer", "engineer", "committer"):
        assert word not in rendered.lower()
