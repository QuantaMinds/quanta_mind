"""Verification that a rule nobody could evaluate is never counted as a rule that passed.

WHAT: Builds a store, records rule checks in all four outcomes, and drives
      `store/compliance.standing` — the per-rule counts, the honest denominator, the hotspots.
WHY:  **THE DENOMINATOR IS THE PRODUCT.** Every competitor's compliance screen shows a pass rate.
      `UNCHECKABLE` and `DEFERRED` mean nobody could decide, and folding them into a rate reports
      a standard as met when nothing looked — the collapse `AGENTS.md` rule 3 exists to prevent.
      `violation_rate` is therefore over DECIDED checks only, and is `None` rather than 0.0 when
      nothing was decided, because zero per cent violated reads as compliance.

      **A REPOSITORY WITH NO CHECKS IS AN EMPTY STANDING, NOT AN ERROR**, and must stay
      distinguishable from a failed read: a new installation has checked nothing yet, which is a
      real state and not a clean bill of health.
IMPORTS: pytest, quantamind.store.{compliance,schema,touches,rule_checks}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store.compliance import HOTSPOTS, standing
from quantamind.store.lifecycle import MIN_FOR_A_RATE
from quantamind.store.schema import open_store
from quantamind.store.touches import ensure_repo
from quantamind.types.checked import Outcome


def _store(tmp_path: Path) -> tuple[sqlite3.Connection, int]:
    conn = open_store(tmp_path / "s.db")
    return conn, ensure_repo(conn, "github.com", "o/r")


def _review(conn: sqlite3.Connection, repo_id: int, number: int) -> int:
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision, "
        "request_count) VALUES (?, ?, ?, 1700000000, 1, 0)",
        (repo_id, number, f"sha{number:040d}"),
    )
    conn.commit()
    return int(conn.execute("SELECT id FROM review ORDER BY id DESC LIMIT 1").fetchone()[0])


def _check(
    conn: sqlite3.Connection, review_id: int, rule: str, path: str, outcome: Outcome
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO rule_check (review_id, rule_id, path, line, outcome, provenance) "
        "VALUES (?, ?, ?, 0, ?, 'declared')",
        (review_id, rule, path, outcome.value),
    )
    conn.commit()


def test_a_repository_with_no_checks_is_empty_not_an_error(tmp_path: Path) -> None:
    conn, repo = _store(tmp_path)

    found = standing(conn, repo)

    assert found.rules == ()
    assert found.hotspots == ()
    assert found.reviews == 0


def test_all_four_outcomes_are_counted_separately(tmp_path: Path) -> None:
    """The uncheckable column is the reason this table is worth more than a pass rate."""
    conn, repo = _store(tmp_path)
    review = _review(conn, repo, 1)
    for path, outcome in (
        ("a.py", Outcome.PASSED),
        ("b.py", Outcome.VIOLATED),
        ("c.py", Outcome.UNCHECKABLE),
        ("d.py", Outcome.DEFERRED),
    ):
        _check(conn, review, "no-print", path, outcome)

    (rule,) = standing(conn, repo).rules

    assert (rule.passed, rule.violated, rule.uncheckable, rule.deferred) == (1, 1, 1, 1)
    assert rule.seen == 4
    assert rule.decided == 2, "uncheckable and deferred must not inflate the denominator"
    assert rule.violation_rate == 0.5


def test_a_rule_nothing_could_decide_has_no_rate_rather_than_zero(tmp_path: Path) -> None:
    """0% violated reads as compliance. Nothing decided is silence, and must print differently."""
    conn, repo = _store(tmp_path)
    review = _review(conn, repo, 1)
    _check(conn, review, "model-judged", "a.py", Outcome.UNCHECKABLE)

    (rule,) = standing(conn, repo).rules

    assert rule.violation_rate is None
    assert rule.seen == 1


def test_violations_concentrate_into_hotspots_and_the_rest_is_counted(tmp_path: Path) -> None:
    """More offending files than the list holds: the remainder is stated, never dropped."""
    conn, repo = _store(tmp_path)
    review = _review(conn, repo, 1)
    for n in range(HOTSPOTS + 3):
        _check(conn, review, f"rule-{n}", f"src/f{n}.py", Outcome.VIOLATED)

    found = standing(conn, repo)

    assert len(found.hotspots) == HOTSPOTS
    assert found.other_hotspots == 3


def test_another_repository_s_checks_are_not_counted(tmp_path: Path) -> None:
    """Per repository is the whole point; a shared store must not blend two tenants."""
    conn, mine = _store(tmp_path)
    theirs = ensure_repo(conn, "github.com", "other/repo")
    _check(conn, _review(conn, theirs, 9), "no-print", "a.py", Outcome.VIOLATED)

    assert standing(conn, mine).rules == ()


def test_a_thin_record_says_so_rather_than_showing_a_rate(tmp_path: Path) -> None:
    """The instrument's own limit, returned rather than printed, as the outcome board does."""
    conn, repo = _store(tmp_path)
    _check(conn, _review(conn, repo, 1), "no-print", "a.py", Outcome.VIOLATED)

    caveat = standing(conn, repo).thin()

    assert caveat is not None
    assert str(MIN_FOR_A_RATE) in caveat


def test_enough_reviews_removes_the_caveat(tmp_path: Path) -> None:
    """The control: without this, thin() could return a string always and pass above."""
    conn, repo = _store(tmp_path)
    for n in range(MIN_FOR_A_RATE):
        _review(conn, repo, n)

    found = standing(conn, repo)

    assert found.reviews == MIN_FOR_A_RATE
    assert found.thin() is None
