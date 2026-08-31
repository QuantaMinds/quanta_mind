"""What the reviews of one repository actually cost, read back from the rows that recorded it.

WHAT: `spent(conn, repo_id)` returns a `Costs` — how many reviews ran, how many consulted a model,
      and the requests and tokens they spent. Read-only; it opens nothing and writes nothing.
WHY:  **THE COLUMNS HAVE BEEN WRITTEN SINCE A5 AND NOTHING HAS EVER READ THEM.** `store/reviews.
      bank()` fills `request_count`, `tokens_in` and `tokens_out` on every delivery, and no `SELECT`
      anywhere in `src/` touched any of them. So the cost figures quoted about this product all come
      from the research bench rather than from a delivery, and the plan says plainly what that
      costs: without this, "BYOK pricing and the free-tier cap are both guesses".

      **"NO REVIEWS" AND "REVIEWS THAT SPENT NOTHING" ARE DIFFERENT ANSWERS AND MUST NOT COLLAPSE.**
      Both would report a total of zero, and they mean opposite things: nothing has run here yet,
      versus the ranker ran and deliberately consulted no model. `Costs.reviews` and `Costs.billed`
      are separate counts, and `per_review` refuses to divide when there is nothing to divide by
      rather than returning a comfortable 0.0.

      **THE MEAN IS REPORTED OVER BILLED REVIEWS, NOT ALL REVIEWS.** Averaging spend across reviews
      that never called a model answers a question nobody asked and quietly understates the cost of
      the reviews that do cost something — which is the number a price has to cover.
IMPORTS: stdlib sqlite3 only. Nothing to its right, and no settings.
CONSUMED BY: `render/dashboard.py` for the table, `serve/commands/run_report.py` behind
      `quantamind cost`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


class NothingRecorded(ValueError):
    """Asked for a per-review figure when no review has spent anything. Carries the counts."""

    def __init__(self, reviews: int) -> None:
        super().__init__(
            f"no review consulted a model: {reviews} review(s) recorded, 0 billed. "
            "There is no cost per review yet, which is not the same as a cost of zero."
        )
        self.reviews = reviews


@dataclass(frozen=True, slots=True)
class Costs:
    """One repository's spend. Built only by `spent`."""

    reviews: int
    """Every recorded review, whether or not it consulted a model."""

    billed: int
    """Reviews that consulted a model. **Never inferred from a token count being non-zero.**"""

    requests: int
    tokens_in: int
    tokens_out: int

    def __post_init__(self) -> None:
        if self.billed > self.reviews:
            raise ValueError("more billed reviews than reviews: the two counts disagree")
        if self.billed == 0 and (self.requests or self.tokens_in or self.tokens_out):
            raise ValueError(
                "tokens were spent by no billed review; the counts cannot both be right"
            )

    @property
    def per_review(self) -> tuple[float, float]:
        """Mean requests and output tokens per BILLED review. Raises when none were billed."""
        if self.billed == 0:
            raise NothingRecorded(self.reviews)
        return self.requests / self.billed, self.tokens_out / self.billed


def spent(conn: sqlite3.Connection, repo_id: int) -> Costs:
    """Read one repository's recorded spend. **A repository with no reviews is a valid answer.**"""
    row = conn.execute(
        "SELECT COUNT(*), "
        "  COALESCE(SUM(CASE WHEN request_count > 0 THEN 1 ELSE 0 END), 0), "
        "  COALESCE(SUM(request_count), 0), "
        "  COALESCE(SUM(tokens_in), 0), "
        "  COALESCE(SUM(tokens_out), 0) "
        "FROM review WHERE repo_id = ?",
        (repo_id,),
    ).fetchone()
    return Costs(
        reviews=int(row[0]),
        billed=int(row[1]),
        requests=int(row[2]),
        tokens_in=int(row[3]),
        tokens_out=int(row[4]),
    )
