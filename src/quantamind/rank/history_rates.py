"""How often this repository fired in EARLIER periods, each judged against its own bar.

WHAT: `earlier_rates()` walks back through a repository's history a window at a time and returns
      the firing rate of each, oldest first.
WHY:  **Split from `firing.py` at the 200-line cap.** That module answers "what would this customer
      get"; this one answers "and has that been true before". The second question has its own
      failure mode and its own history of getting it wrong, which is written down here beside the
      code rather than crowding the estimate.
IMPORTS: rank.order, store.calibration. Left only.
CONSUMED BY: `rank/firing.py`.
"""

from __future__ import annotations

import sqlite3

from quantamind.rank.order import fires
from quantamind.store.calibration import cut

MIN_WINDOW = 30
"""Fewest changes an earlier window needs before its rate is reported at all."""


def earlier_rates(
    conn: sqlite3.Connection,
    repo_id: int,
    *,
    as_of: int,
    window: int,
    over: int,
    windows: int = 4,
) -> tuple[float, ...]:
    """Fire rate on successive windows before the calibration set, **each against its OWN floor**.

    Oldest first. Empty when the repository has no history before the calibration window, which is
    a real answer for a young repository and not a zero.
    """
    edge = as_of - window
    out: list[float] = []
    for step in range(windows, 0, -1):
        end = edge - (step - 1) * window
        rows = conn.execute(
            "WITH recent AS ("
            "  SELECT DISTINCT committed_at FROM touch"
            "  WHERE repo_id = ? AND committed_at < ? AND committed_at >= ?"
            "  ORDER BY committed_at DESC LIMIT ?"
            ") "
            "SELECT MAX(("
            "  SELECT COUNT(*) FROM touch prior"
            "  WHERE prior.repo_id = ? AND prior.path = changed.path"
            "    AND prior.committed_at >= ? AND prior.committed_at < ?"
            ")) AS top "
            "FROM recent JOIN touch changed"
            "  ON changed.repo_id = ? AND changed.committed_at = recent.committed_at "
            "GROUP BY recent.committed_at",
            (repo_id, end, end - window, over, repo_id, end - window, end, repo_id),
        ).fetchall()
        tops = [int(r[0]) for r in rows]
        if len(tops) < MIN_WINDOW:
            continue
        # **EACH WINDOW AGAINST ITS OWN FLOOR, AND THE ALTERNATIVE WAS BUG 2 IN A THIRD COSTUME.**
        # Holding today's floor fixed over older windows compares a top counted in one era against
        # a bar derived from another: `trpc/trpc` read 70%, 68%, 62%, 54% on periods when it was
        # simply busier, against 12% now. That measures ACTIVITY, not selectivity.
        own = cut(tops, 0.9)
        out.append(sum(1 for top in tops if fires({"unit": top}, own)) / len(tops))
    return tuple(out)
