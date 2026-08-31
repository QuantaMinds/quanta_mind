"""Write down that we reviewed, what we ranked, and what we said. Nothing did.

WHAT: `record(conn, repo_id, pr_number, head_sha, ranking, *, at, coverage_pct)` inserts one
      `review` row and one `ranked_unit` row per unit, returning the review id. `recent(conn,
      repo_id, limit)` reads them back newest first.
WHY:  **THE `review` AND `ranked_unit` TABLES HAVE EXISTED SINCE THE SCHEMA WAS WRITTEN AND HAD
      ZERO WRITERS.** So did `outcome`, `reaction`, `finding` and `shadow_pick`. The product
      ranked, rendered, posted, and kept no record that any of it happened.

      **THAT IS THE REASON A DASHBOARD CANNOT BE BUILT, AND IT IS NOT THE MISSING INTEGRATION.**
      "What we commented on, whether it merged, whether it is still running in production" needs a
      row per comment before it needs anything from Datadog. Without this table there is nothing
      for an incident to be joined TO, and the first question a customer asks after thirty days —
      *what did it actually say, and did any of it matter* — has no answer that is not a guess.

      **EVERY UNIT IS RECORDED, COLD ONES INCLUDED.** `allocation` distinguishes what we read from
      what we ranked and did not, so the cold list is a stored decision rather than an absence. A
      table holding only the units we spoke about could never answer whether the ranking was right,
      because being wrong looks like a unit that is not there.

      **THE INSERT IS IDEMPOTENT ON (repo, pr, head_sha)**, which is the key `github_comments`
      already uses to decide whether it has spoken. A redelivered webhook is a normal event, and a
      second row for one commit would silently double every count computed from this table.
IMPORTS: types.ranking. Left of ingest, so it imports no layer to its right.
CONSUMED BY: `serve/review_delivery.py`; whatever renders the retrospective.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from quantamind.store import schema, touches
from quantamind.store.schema import SchemaVersionMismatch
from quantamind.types.ranking import Ranking
from quantamind.types.spend import Spend


@dataclass(frozen=True, slots=True)
class Recorded:
    """One stored review. `units` counts every ranked unit, not only the read ones."""

    review_id: int
    pr_number: int
    head_sha: str
    created_at: int
    fired: bool
    units: int
    read: int


def record(
    conn: sqlite3.Connection,
    repo_id: int,
    pr_number: int,
    head_sha: str,
    ranking: Ranking,
    *,
    at: int,
    coverage_pct: float | None = None,
) -> int:
    """Store the review and its ranked units. Returns the review id, new or existing.

    Returns the EXISTING id on a redelivery rather than raising: a webhook firing twice for one
    commit is ordinary, and the caller cannot tell it from a first delivery without asking here.
    """
    conn.execute(
        "INSERT OR IGNORE INTO review "
        "(repo_id, pr_number, head_sha, created_at, fire_decision, coverage_pct) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (repo_id, pr_number, head_sha, at, int(ranking.fired), coverage_pct),
    )
    found = conn.execute(
        "SELECT id FROM review WHERE repo_id = ? AND pr_number = ? AND head_sha = ?",
        (repo_id, pr_number, head_sha),
    ).fetchone()
    review_id = int(found[0])

    conn.executemany(
        "INSERT OR IGNORE INTO ranked_unit "
        "(review_id, unit_path, unit_name, rank, score, percentile, allocation) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                review_id,
                ranked.unit.site.path,
                ranked.unit.qualified_name,
                ranked.rank,
                ranked.score.value,
                ranked.score.percentile,
                ranked.allocation.value,
            )
            for ranked in ranking.units
        ],
    )
    conn.commit()
    return review_id


def recent(conn: sqlite3.Connection, repo_id: int, limit: int = 50) -> list[Recorded]:
    """Reviews for one repository, newest first. Empty is a real answer, not a failure."""
    rows = conn.execute(
        "SELECT r.id, r.pr_number, r.head_sha, r.created_at, r.fire_decision, "
        "  (SELECT COUNT(*) FROM ranked_unit u WHERE u.review_id = r.id), "
        "  (SELECT COUNT(*) FROM ranked_unit u WHERE u.review_id = r.id "
        "     AND u.allocation != 'cold') "
        "FROM review r WHERE r.repo_id = ? ORDER BY r.created_at DESC, r.id DESC LIMIT ?",
        (repo_id, limit),
    ).fetchall()
    return [
        Recorded(int(a), int(b), str(c), int(d), bool(e), int(f), int(g))
        for a, b, c, d, e, f, g in rows
    ]


def record_spend(conn: sqlite3.Connection, review_id: int, spend: Spend) -> bool:
    """Write what a review cost onto its row. True when a row was updated.

    **THESE COLUMNS HAVE EXISTED SINCE THE SCHEMA WAS WRITTEN AND NOTHING EVER WROTE THEM.**
    `request_count`, `tokens_in`, `tokens_out` and `latency_ms` sat at their defaults through every
    delivery — the same "tables with zero writers" defect this file already carries a comment
    about, one column deeper. Until they are written, every pricing decision is arithmetic over a
    number nobody has measured.

    **AN UNMEASURED CALL IS NOT WRITTEN AS ZERO.** `Spend.complete` is False when part of the
    review went unmetered, and a floor recorded as a total would put a quietly low number on a
    dashboard and price from it. An incomplete spend is refused here rather than rounded down; the
    caller logs it. **Returning a boolean rather than nothing** is what lets a caller notice.
    """
    if spend.requests == 0:
        return False
    if not spend.complete:
        print(
            f"[store] review {review_id}: cost not recorded — part of it was never metered, and a "
            f"floor written as a total would be priced from",
            flush=True,
        )
        return False
    conn.execute(
        "UPDATE review SET request_count = ?, tokens_in = ?, tokens_out = ?, latency_ms = ? "
        "WHERE id = ?",
        (spend.requests, spend.tokens_in, spend.tokens_out, spend.ms, review_id),
    )
    conn.commit()
    return True


def bank(store_path: Path, repo: str, pr_number: int, head_sha: str, spend: Spend) -> bool:
    """Open the tenant's store and record what this review cost. True when a row was updated.

    **A FAILURE HERE MUST NOT COST THE REVIEW.** The comment is already rendered and worth posting
    whether or not the cost was banked; trading the developer's answer for the operator's metric
    would be the wrong way round. The reason is printed and False returned, so a caller can see the
    gap rather than infer it from silence.
    """
    if spend.requests == 0:
        return False
    try:
        conn = schema.open_store(store_path)
    except (sqlite3.Error, SchemaVersionMismatch) as exc:
        print(f"[store] cost not recorded: {exc}", flush=True)
        return False
    try:
        repo_id = touches.ensure_repo(conn, "github.com", repo)
        row = conn.execute(
            "SELECT id FROM review WHERE repo_id = ? AND pr_number = ? AND head_sha = ?",
            (repo_id, pr_number, head_sha),
        ).fetchone()
        if row is None:
            print(f"[store] no review row for {repo}#{pr_number}; cost not recorded", flush=True)
            return False
        # **THE SUCCESS IS PRINTED HERE, BESIDE THE TWO REFUSALS ABOVE IT.** The caller used to say
        # it, which meant a write that failed for either reason above was silent at the call site
        # and a write that succeeded was announced by somebody who had not checked.
        banked = record_spend(conn, int(row[0]), spend)
        if banked:
            print(
                f"[store] cost: {spend.requests} call(s), {spend.tokens_out} tokens out",
                flush=True,
            )
        return banked
    except sqlite3.Error as exc:
        print(f"[store] cost not recorded: {exc}", flush=True)
        return False
    finally:
        conn.close()
