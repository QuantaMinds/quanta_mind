"""Remember which webhook deliveries we have processed, so a replay cannot make us act twice.

WHAT: `begin()` claims a delivery and says whether to process it; `complete()` marks it finished.
WHY:  **GitHub does not sign a timestamp.** Its signature covers the body and nothing else, so a
      captured delivery stays valid forever and anyone who records one can replay it indefinitely.
      Verification proves the bytes came from GitHub; it cannot prove they are arriving for the
      first time. Replay protection is an application-level defence and there was none.

      **The key is `X-GitHub-Delivery`**, which GitHub documents as "a globally unique identifier
      (GUID) to identify the event".

      **`begin()` and `complete()` are separate calls, and that is the whole design.** A redelivery
      REUSES the original GUID — GitHub retries with the same identifier — so recording on receipt
      would make a legitimate retry look like a replay and we would drop the work GitHub is telling
      us we failed. A delivery with no `completed_at` is therefore retryable; one with a
      `completed_at` is not.

      **This is defence in depth, not the only defence.** The effect we produce is already
      idempotent: `ingest.github_comments.post()` will not post twice for one head SHA. This stops
      the wasted work and the replay, and the comment layer stops the duplicate.
IMPORTS: store.schema. Nothing to its right.
CONSUMED BY: serve, once an HTTP binding exists.
"""

from __future__ import annotations

import sqlite3
import time


def begin(conn: sqlite3.Connection, delivery_id: str, event: str) -> bool:
    """True when this delivery should be processed. False when it is already finished.

    An unfinished previous attempt returns True: GitHub redelivers with the SAME GUID when we
    failed, and refusing that would discard exactly the work it is retrying.
    """
    if not delivery_id.strip():
        raise ValueError(
            "a delivery with no X-GitHub-Delivery header cannot be deduplicated. Refusing to "
            "process it rather than treating an unidentifiable delivery as a fresh one"
        )
    row = conn.execute(
        "SELECT completed_at FROM delivery WHERE delivery_id = ?", (delivery_id,)
    ).fetchone()
    if row is not None:
        return row[0] is None  # started and never finished -> a retry is legitimate
    with conn:
        conn.execute(
            "INSERT INTO delivery (delivery_id, event, started_at) VALUES (?, ?, ?)",
            (delivery_id, event, int(time.time())),
        )
    return True


def complete(conn: sqlite3.Connection, delivery_id: str) -> None:
    """Mark a delivery finished. After this, the same GUID is a replay and is refused."""
    with conn:
        updated = conn.execute(
            "UPDATE delivery SET completed_at = ? WHERE delivery_id = ?",
            (int(time.time()), delivery_id),
        )
    if updated.rowcount == 0:
        raise ValueError(
            f"complete() called for delivery {delivery_id!r}, which begin() never claimed. "
            "Marking work finished that was never started would let the next replay through"
        )
