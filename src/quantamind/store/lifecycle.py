"""What became of a change after we spoke: posted, merged, and what production said.

WHAT: `observe(conn, review_id, ...)` records the merge state of a reviewed pull request.
      `signal(conn, review_id, state, source, ...)` appends one production observation.
      `board(conn, repo_id, limit)` joins them into the rows a dashboard shows.
WHY:  **THIS IS THE ONLY MEASUREMENT IN THE PRODUCT THAT DOES NOT NEED THE COMMENT TO BE RIGHT.**
      Whether a finding was insightful is a judgement, and four blind rater pools put our raw
      findings at 66.7-82.1% wrong. Whether the change we pointed at later broke in production is
      an OUTCOME -- it is true or false regardless of how good the sentence was, and nobody has to
      grade anything for it to be recorded.

      **`prod_signal` IS A LOG, NOT A COLUMN.** "Still running" is a claim about an instant. A
      single mutable state field would overwrite the only evidence of what a service looked like
      before it broke, which is exactly the interval an incident review needs.

      **NOTHING IS BACKFILLED AND `unknown` IS NEVER INVENTED.** A review with no lifecycle row
      means we have not looked. A row saying `unknown` means we looked and could not tell. Storing
      the first as the second makes an absence of evidence indistinguishable from an observation,
      which is the defect this codebase names as typed silence.

      **THE LABELS WILL BE THIN AND SAYING SO IS PART OF THE INSTRUMENT.** A client at 200 pull
      requests a month firing at 12% yields about 24 reviewed changes monthly, and production
      incidents that trace to one are a handful a quarter. `Board.thin()` reports when there are
      too few to conclude anything, so the dashboard cannot be read as evidence before it is.
IMPORTS: stdlib only, and the enum below. Nothing to its right.
CONSUMED BY: `render/dashboard.py`; `serve/` when it learns a pull request merged.
"""

from __future__ import annotations

import enum
import sqlite3
from dataclasses import dataclass

MIN_FOR_A_RATE = 20


class MergeState(enum.Enum):
    """What GitHub says happened to the pull request. `UNKNOWN` means we have looked and cannot
    tell -- a review we have never looked at has no lifecycle row at all."""

    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class ProdState(enum.Enum):
    """What production said at one instant. Never overwritten; always appended."""

    HEALTHY = "healthy"
    FAILING = "failing"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Row:
    """One line of the dashboard: what we said, what happened, what production reported."""

    review_id: int
    pr_number: int
    head_sha: str
    fired: bool
    units: int
    read: int
    posted_at: int | None
    merge_state: MergeState
    merged_at: int | None
    prod_state: ProdState
    prod_observed_at: int | None


@dataclass(frozen=True, slots=True)
class Board:
    """The dashboard, and an honest statement of whether it can be read yet."""

    rows: tuple[Row, ...]

    @property
    def merged(self) -> int:
        return sum(1 for r in self.rows if r.merge_state is MergeState.MERGED)

    @property
    def failing(self) -> int:
        return sum(1 for r in self.rows if r.prod_state is ProdState.FAILING)

    def thin(self) -> str | None:
        """Why this board cannot be read as evidence yet, or None when it can.

        Returned rather than printed, and checked rather than assumed: a dashboard that shows a
        rate over four observations invites a conclusion the data cannot carry.
        """
        if len(self.rows) < MIN_FOR_A_RATE:
            return (
                f"{len(self.rows)} reviewed change(s) recorded; a rate needs at least "
                f"{MIN_FOR_A_RATE}. Counts below are real, proportions are not yet meaningful."
            )
        looked = sum(1 for r in self.rows if r.prod_observed_at is not None)
        if looked < MIN_FOR_A_RATE:
            return (
                f"production was observed for {looked} of {len(self.rows)} changes; the merge "
                f"column is readable and the production column is not."
            )
        return None


def observe(
    conn: sqlite3.Connection,
    review_id: int,
    *,
    at: int,
    merge_state: MergeState,
    merged_at: int | None = None,
    posted_at: int | None = None,
) -> None:
    """Record what we now know about a reviewed pull request. Replaces the previous knowledge."""
    conn.execute(
        "INSERT INTO lifecycle (review_id, posted_at, merge_state, merged_at, observed_at) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT(review_id) DO UPDATE SET "
        "  posted_at = COALESCE(excluded.posted_at, lifecycle.posted_at), "
        "  merge_state = excluded.merge_state, merged_at = excluded.merged_at, "
        "  observed_at = excluded.observed_at",
        (review_id, posted_at, merge_state.value, merged_at, at),
    )
    conn.commit()


def signal(
    conn: sqlite3.Connection,
    review_id: int,
    *,
    at: int,
    state: ProdState,
    source: str,
    detail: str = "",
) -> None:
    """Append one production observation. Never replaces an earlier one."""
    if not source.strip():
        raise ValueError(
            "a production signal with no source cannot be audited later; name what reported it"
        )
    conn.execute(
        "INSERT INTO prod_signal (review_id, observed_at, state, source, detail) "
        "VALUES (?, ?, ?, ?, ?)",
        (review_id, at, state.value, source, detail),
    )
    conn.commit()


def board(conn: sqlite3.Connection, repo_id: int, limit: int = 100) -> Board:
    """Reviews for one repository with their outcomes, newest first."""
    rows = conn.execute(
        "SELECT r.id, r.pr_number, r.head_sha, r.fire_decision, "
        "  (SELECT COUNT(*) FROM ranked_unit u WHERE u.review_id = r.id), "
        "  (SELECT COUNT(*) FROM ranked_unit u WHERE u.review_id = r.id "
        "     AND u.allocation != 'cold'), "
        "  l.posted_at, l.merge_state, l.merged_at, "
        "  (SELECT p.state FROM prod_signal p WHERE p.review_id = r.id "
        "     ORDER BY p.observed_at DESC, p.id DESC LIMIT 1), "
        "  (SELECT p.observed_at FROM prod_signal p WHERE p.review_id = r.id "
        "     ORDER BY p.observed_at DESC, p.id DESC LIMIT 1) "
        "FROM review r LEFT JOIN lifecycle l ON l.review_id = r.id "
        "WHERE r.repo_id = ? ORDER BY r.created_at DESC, r.id DESC LIMIT ?",
        (repo_id, limit),
    ).fetchall()
    return Board(
        tuple(
            Row(
                int(a),
                int(b),
                str(c),
                bool(d),
                int(e),
                int(f),
                None if g is None else int(g),
                MergeState(h) if h else MergeState.UNKNOWN,
                None if i is None else int(i),
                ProdState(j) if j else ProdState.UNKNOWN,
                None if k is None else int(k),
            )
            for a, b, c, d, e, f, g, h, i, j, k in rows
        )
    )
