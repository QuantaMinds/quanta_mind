"""Every recorded check for one repository, read back whole.

WHAT: `rows(conn, repo_id)` returns one `Recorded` per `rule_check`, joined to the review it
      belongs to, oldest first. `window(conn, repo_id)` is the span those rows actually cover.
WHY:  **D4b WAS TICKED "APPEND-ONLY, EXPORTABLE" AND THERE WAS NO EXPORT.**
      `docs/product/unit-economics.md` said it plainly and was ignored for a fortnight: *"There is
      no file, no download, and no scheduled export anywhere in the build plan. A compliance buyer
      asks for the artefact, not the query."* The rows existed and `quantamind compliance` printed
      a summary of them; nothing could hand an auditor the trail itself.

      **A SUMMARY IS NOT AN ARTEFACT.** `store/compliance.py` answers "how are we doing" — counts
      per rule, hotspots, a rate over decided checks. An auditor asks a different question: *show
      me every check you ran on this repository, and let me pick one and re-run it.* That needs the
      rows, each carrying the commit it was decided at.

      **THE WINDOW IS READ FROM THE DATA, NEVER ASSUMED.** Nothing is backfilled, so the trail
      starts when the rule engine was installed and not when the repository did. An export that
      implied otherwise would be the most dangerous document this product could produce — a
      compliance record appearing to cover a period nobody checked.
IMPORTS: stdlib sqlite3, dataclasses. Nothing to its right.
CONSUMED BY: `render/audit_export.py`, behind `quantamind compliance --export`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Recorded:
    """One check, as it was written, with the commit that lets somebody re-run it."""

    pr_number: int
    head_sha: str
    decided_at: int
    rule_id: str
    path: str
    line: int
    outcome: str
    provenance: str
    evidence: str
    reason: str


@dataclass(frozen=True, slots=True)
class Window:
    """What the trail actually covers. **Read from the rows, never assumed.**"""

    first: int | None
    last: int | None
    reviews: int

    def empty(self) -> bool:
        return self.first is None


def rows(conn: sqlite3.Connection, repo_id: int) -> tuple[Recorded, ...]:
    """Every recorded check for this repository, oldest first.

    **ORDERED BY WHEN IT WAS DECIDED, NOT BY RULE.** An auditor reads a trail forwards; grouping by
    rule would be a second summary and this exists because the summary was not enough.
    """
    found = conn.execute(
        "SELECT r.pr_number, r.head_sha, r.created_at, c.rule_id, c.path, c.line, c.outcome, "
        "c.provenance, c.evidence, COALESCE(c.reason, '') "
        "FROM rule_check c JOIN review r ON r.id = c.review_id "
        "WHERE r.repo_id = ? ORDER BY r.created_at, r.pr_number, c.path, c.rule_id",
        (repo_id,),
    ).fetchall()
    return tuple(
        Recorded(
            pr_number=int(row[0]),
            head_sha=str(row[1]),
            decided_at=int(row[2]),
            rule_id=str(row[3]),
            path=str(row[4]),
            line=int(row[5]),
            outcome=str(row[6]),
            provenance=str(row[7]),
            evidence=str(row[8]),
            reason=str(row[9]),
        )
        for row in found
    )


def window(conn: sqlite3.Connection, repo_id: int) -> Window:
    """The span the trail covers, and how many reviews are in it.

    **A REPOSITORY WITH NO ROWS RETURNS AN EMPTY WINDOW, NOT A ZERO-LENGTH ONE.** "We have checked
    nothing here" and "we checked from now until now" are different claims, and the second would
    read as coverage.
    """
    row = conn.execute(
        "SELECT MIN(r.created_at), MAX(r.created_at), COUNT(DISTINCT r.id) "
        "FROM rule_check c JOIN review r ON r.id = c.review_id WHERE r.repo_id = ?",
        (repo_id,),
    ).fetchone()
    if row is None or row[0] is None:
        return Window(None, None, 0)
    return Window(int(row[0]), int(row[1]), int(row[2]))
