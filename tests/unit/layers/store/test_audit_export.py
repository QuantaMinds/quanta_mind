"""The audit trail as a file, and the four things the file must say about itself.

WHAT: Drives `store.audit.export` against a real store and `render.audit_export.document` over what
      it returns, then the whole thing through `quantamind compliance --export`.
WHY:  **D4b WAS TICKED "APPEND-ONLY, EXPORTABLE" FOR A FORTNIGHT WITH NO EXPORT.**
      `docs/product/unit-economics.md` had written the gap down and been ignored: *"There is no
      file, no download, and no scheduled export anywhere in the build plan. A compliance buyer
      asks for the artefact, not the query."* Same shape as D1g's title — a tick right about the
      work and wrong in the word somebody reads.

      **THE LIMITS TRAVEL INSIDE THE FILE, WHICH IS WHY IT IS JSON.** A CSV opens more easily and
      cannot carry them. An export that outlives its covering email is exactly how a partial record
      becomes a claim of full coverage, and this document is one somebody may show a regulator.

      **AN EMPTY EXPORT IS A DOCUMENT, NOT AN ERROR**, and it says it covers nothing. That is a
      true, useful and auditable answer; failing instead would leave the caller with nothing to
      hand over and no statement of why.
IMPORTS: quantamind.render.audit_export, quantamind.store.{audit.export,rule_checks,schema,touches},
      quantamind.types.{checked,rule,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantamind.render.audit_export import document
from quantamind.store import schema, touches
from quantamind.store.audit.export import Window, rows, window
from quantamind.store.rule_checks import record
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Site

RULES = (
    Rule("no-print", "Use the logger.", Severity.LOW, CheckKind.FORBID_CALL, target="print"),
    Rule("judged", "A model decides this.", Severity.LOW, CheckKind.MODEL_JUDGED),
)


def _store(tmp_path: Path) -> tuple[object, int]:
    conn = schema.open_store(tmp_path / "t.db")
    repo_id = touches.ensure_repo(conn, "github.com", "acme/app")
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision) "
        "VALUES (?, 86, ?, 1756600000, 1)",
        (repo_id, "a" * 40),
    )
    conn.commit()
    return conn, repo_id


def test_every_recorded_check_comes_back_with_the_commit_that_decided_it(tmp_path: Path) -> None:
    """**AN AUDITOR PICKS ONE ROW AND RE-RUNS IT.** Without the commit they cannot."""
    conn, repo_id = _store(tmp_path)
    record(
        conn,
        repo_id,
        86,
        "a" * 40,
        [
            Checked("no-print", Site("src/app.py", 12), Outcome.VIOLATED, evidence="print at 12"),
            Checked("judged", Site("src/app.py"), Outcome.DEFERRED),
        ],
        RULES,
    )

    found = rows(conn, repo_id)  # type: ignore[arg-type]

    assert len(found) == 2
    assert {row.head_sha for row in found} == {"a" * 40}
    assert {row.rule_id for row in found} == {"no-print", "judged"}


def test_a_model_judged_row_keeps_its_provenance(tmp_path: Path) -> None:
    """A parser's verdict re-runs and a model's does not. An export that lost the distinction
    would be worth what its least reliable row is worth."""
    conn, repo_id = _store(tmp_path)
    record(conn, repo_id, 86, "a" * 40, [Checked("judged", Site("a.py"), Outcome.DEFERRED)], RULES)

    (row,) = rows(conn, repo_id)  # type: ignore[arg-type]

    assert row.provenance == "model"


def test_a_repository_with_no_checks_has_an_empty_window(tmp_path: Path) -> None:
    """**"WE CHECKED NOTHING" AND "WE CHECKED FROM NOW UNTIL NOW" ARE DIFFERENT CLAIMS**, and the
    second reads as coverage."""
    conn, repo_id = _store(tmp_path)

    covered = window(conn, repo_id)  # type: ignore[arg-type]

    assert covered.empty() is True
    assert (covered.first, covered.reviews) == (None, 0)


def test_the_window_is_read_from_the_rows_not_from_the_repository(tmp_path: Path) -> None:
    """Nothing is backfilled, so the trail starts when rule checking was installed."""
    conn, repo_id = _store(tmp_path)
    record(conn, repo_id, 86, "a" * 40, [Checked("no-print", Site("a.py"), Outcome.PASSED)], RULES)

    covered = window(conn, repo_id)  # type: ignore[arg-type]

    assert covered.first == 1756600000
    assert covered.reviews == 1


def test_the_document_states_its_limits_before_its_rows(tmp_path: Path) -> None:
    """**A READER WHO STOPS AFTER THE FIRST OBJECT HAS READ THE PART THAT STOPS THEM
    OVER-READING THE REST.** The caveat goes above the data, as it does in the comment."""
    conn, repo_id = _store(tmp_path)
    record(conn, repo_id, 86, "a" * 40, [Checked("no-print", Site("a.py"), Outcome.PASSED)], RULES)
    text = document(rows(conn, repo_id), window(conn, repo_id), "acme/app")  # type: ignore[arg-type]

    assert list(json.loads(text)) == ["repository", "limits", "checks"]
    limits = json.loads(text)["limits"]
    assert "backfilled" in limits["not_backfilled"]
    assert "did not run" in limits["absent_means_unchecked"]
    assert "not passes" in limits["undecided_is_not_a_pass"]


def test_an_empty_export_is_a_document_that_says_it_covers_nothing() -> None:
    """Not an error. "We have checked nothing here" is true, useful and auditable."""
    parsed = json.loads(document((), Window(None, None, 0), "acme/new"))

    assert parsed["checks"] == []
    assert parsed["limits"]["covers"]["from"] is None
    assert parsed["limits"]["covers"]["checks"] == 0
