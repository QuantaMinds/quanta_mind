"""The audit trail: all four outcomes kept, provenance derived, and the count returned.

WHAT: Writes real `Checked` rows into a real store and reads them back.
WHY:  **A TRAIL HOLDING ONLY VIOLATIONS ANSWERS THE WRONG QUESTION.** A compliance reader asks
      "was this rule enforced, and what did it say", not "did it fire". Storing only the failures
      leaves the denominator to whoever reads the percentage later, which is how "98% compliant"
      comes to mean 98% of an unknown population.

      **AND PROVENANCE MUST BE DERIVED, NOT ACCEPTED.** A row that could declare itself
      parser-verified while a model decided it makes every other row worth what the least reliable
      one is worth.
IMPORTS: store.{rule_checks,reviews,schema,touches}, types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3

import pytest

from quantamind.store import rule_checks, touches
from quantamind.store.schema import create
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Reason, Site

PARSED = Rule(
    id="no-print",
    description="print bypasses the log pipeline.",
    severity=Severity.MEDIUM,
    check=CheckKind.FORBID_CALL,
    target="print",
)
JUDGED = Rule(
    id="async-handling",
    description="An awaited call with no handler fails silently.",
    severity=Severity.HIGH,
    check=CheckKind.MODEL_JUDGED,
)
ROWS = (
    Checked("no-print", Site("a.py", 3), Outcome.VIOLATED, evidence="print at line 3"),
    Checked("no-print", Site("b.py"), Outcome.PASSED),
    Checked("no-print", Site("c.ts"), Outcome.UNCHECKABLE, why=Reason.LANGUAGE_UNSUPPORTED),
    Checked("async-handling", Site("a.py"), Outcome.DEFERRED),
)


def _store() -> tuple[sqlite3.Connection, int]:
    conn = sqlite3.connect(":memory:")
    create(conn)
    repo_id = touches.ensure_repo(conn, "github.com", "o/r")
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision)"
        " VALUES (?, 7, 'abc123', 1, 1)",
        (repo_id,),
    )
    conn.commit()
    return conn, repo_id


def test_all_four_outcomes_are_kept_not_only_the_violations() -> None:
    """**THE DENOMINATOR IS THE POINT.** Storing only failures invents the population."""
    conn, repo_id = _store()

    written = rule_checks.record(conn, repo_id, 7, "abc123", ROWS, [PARSED, JUDGED])

    assert written == len(ROWS), f"{written} rows written for {len(ROWS)} checks"
    back = rule_checks.for_review(conn, 1)
    assert {row[2] for row in back} == {"violated", "passed", "uncheckable", "deferred"}, (
        f"an outcome was lost on the way to the trail: {back}"
    )


def test_provenance_comes_from_the_rule_not_from_the_caller() -> None:
    conn, repo_id = _store()
    rule_checks.record(conn, repo_id, 7, "abc123", ROWS, [PARSED, JUDGED])

    by_rule = {row[0]: row[3] for row in rule_checks.for_review(conn, 1)}

    assert by_rule["no-print"] == "parser"
    assert by_rule["async-handling"] == "model", (
        "a model-judged rule was recorded as parser-verified. Every other row in the trail is "
        "then worth what the least reliable row is worth"
    )


def test_nothing_to_write_returns_zero_rather_than_claiming_success() -> None:
    conn, repo_id = _store()

    assert rule_checks.record(conn, repo_id, 7, "abc123", (), []) == 0
    assert rule_checks.for_review(conn, 1) == []


def test_checks_without_a_review_row_refuse_rather_than_dangle() -> None:
    """Rows hanging from no review are unreadable later, and an audit trail is read later."""
    conn, repo_id = _store()

    with pytest.raises(rule_checks.ReviewNotRecorded):
        rule_checks.record(conn, repo_id, 999, "nosuch", ROWS, [PARSED])


def test_a_redelivery_does_not_double_the_rows() -> None:
    """GitHub redelivers; a trail that doubled would report twice the checks that happened."""
    conn, repo_id = _store()
    rule_checks.record(conn, repo_id, 7, "abc123", ROWS, [PARSED, JUDGED])
    rule_checks.record(conn, repo_id, 7, "abc123", ROWS, [PARSED, JUDGED])

    assert len(rule_checks.for_review(conn, 1)) == len(ROWS)
