"""Every declared rule against every changed file, kept — the audit trail.

WHAT: `record(conn, repo_id, pr_number, head_sha, rows)` writes one row per `Checked` and returns
      how many it wrote. `for_review(conn, review_id)` reads them back.
WHY:  **A COMPLIANCE READER ASKS "WAS THIS RULE ENFORCED, AND WHAT DID IT SAY" — NOT "DID IT
      FIRE".** A table holding only violations answers the second question and silently invents the
      denominator for the first. All four outcomes are stored, including the ones we could not
      decide, so a rate computed later is over a population that actually existed.

      **`provenance` IS THE COLUMN THAT MAKES THE TRAIL WORTH READING.** A parser's verdict can be
      re-run on the same commit and shown to agree; a model's cannot. Without it every row is worth
      what the least reliable row is worth, which is the difference between evidence and a log.

      **NOTHING IS BACKFILLED AND AN ABSENT ROW MEANS WE DID NOT CHECK.** A review from before the
      rule engine existed has no rows, and inventing "passed" ones would manufacture a compliance
      history — the exact artefact somebody might later show a regulator.

      **THE COUNT IS RETURNED RATHER THAN SUCCESS ASSUMED.** A review with no declared rules writes
      nothing, which is correct and indistinguishable from a write that failed. The caller compares
      it against what it handed in; `sweep()` earned this repository that habit the hard way.
IMPORTS: stdlib sqlite3, `types.checked`. Nothing to its right.
CONSUMED BY: `serve/review_delivery.py`, and the compliance dashboard (D5).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path

from quantamind.store import schema, touches
from quantamind.store.schema import SchemaVersionMismatch
from quantamind.types.checked import Checked
from quantamind.types.rule import Rule


class ReviewNotRecorded(LookupError):
    """No review row for this commit. The checks would have nothing to hang from."""

    def __init__(self, repo_id: int, pr_number: int, head_sha: str) -> None:
        super().__init__(f"no review for repo {repo_id} #{pr_number} at {head_sha[:12]}")


def _review_id(conn: sqlite3.Connection, repo_id: int, pr_number: int, head_sha: str) -> int:
    row = conn.execute(
        "SELECT id FROM review WHERE repo_id = ? AND pr_number = ? AND head_sha = ?",
        (repo_id, pr_number, head_sha),
    ).fetchone()
    if row is None:
        raise ReviewNotRecorded(repo_id, pr_number, head_sha)
    return int(row[0])


def record(
    conn: sqlite3.Connection,
    repo_id: int,
    pr_number: int,
    head_sha: str,
    rows: Sequence[Checked],
    rules: Sequence[Rule] = (),
) -> int:
    """Write the checks for one review. Returns the number written, never a bare success."""
    if not rows:
        return 0
    review_id = _review_id(conn, repo_id, pr_number, head_sha)
    # Provenance is DERIVED from the rule that produced the row, never taken from a caller: a row
    # that could declare itself parser-verified while a model decided it makes the trail worthless.
    by_id = {rule.id: rule.provenance.value for rule in rules}
    conn.executemany(
        "INSERT OR REPLACE INTO rule_check"
        " (review_id, rule_id, path, line, outcome, evidence, reason, provenance)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                review_id,
                row.rule_id,
                row.site.path,
                row.site.line,
                row.outcome.value,
                row.evidence,
                row.why.value if row.why is not None else None,
                by_id.get(row.rule_id, "parser"),
            )
            for row in rows
        ],
    )
    conn.commit()
    return len(rows)


def for_review(conn: sqlite3.Connection, review_id: int) -> list[tuple[str, str, str, str]]:
    """`(rule_id, path, outcome, provenance)` for one review, for an auditor reading it back."""
    return [
        (str(r[0]), str(r[1]), str(r[2]), str(r[3]))
        for r in conn.execute(
            "SELECT rule_id, path, outcome, provenance FROM rule_check"
            " WHERE review_id = ? ORDER BY path, rule_id",
            (review_id,),
        )
    ]


def persist(
    store_path: Path,
    repo: str,
    pr_number: int,
    head_sha: str,
    rows: Sequence[Checked],
    rules: Sequence[Rule] = (),
) -> int:
    """Open the tenant's store, record the checks, close it. Returns how many landed.

    **A FAILURE HERE MUST NOT TAKE THE REVIEW DOWN WITH IT.** The comment is already rendered and
    is worth posting whether or not the trail accepted it; losing the review because a write failed
    would trade the thing the developer needs for the thing the auditor needs. The reason is
    printed and zero is returned, so the caller can see the gap rather than infer it from silence.
    """
    try:
        conn = schema.open_store(store_path)
    except (sqlite3.Error, SchemaVersionMismatch) as exc:
        print(f"[audit] store unavailable, checks not recorded: {exc}", flush=True)
        return 0
    try:
        repo_id = touches.ensure_repo(conn, "github.com", repo)
        return record(conn, repo_id, pr_number, head_sha, rows, rules)
    except (sqlite3.Error, ReviewNotRecorded) as exc:
        print(f"[audit] checks not recorded: {exc}", flush=True)
        return 0
    finally:
        conn.close()
