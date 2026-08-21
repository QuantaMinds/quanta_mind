"""The prior-touch index: write history into it, and count touches strictly before a change.

WHAT: `ensure_repo()` registers a repository, `index()` writes `Touch` values into the store, and
      `counts()` returns, for each path asked about, how many touches fall in the window ending
      just before a given commit.
WHY:  The ranking is this count and nothing else. **The window is half-open — `[as_of - window,
      as_of)` — and the exclusive upper bound is the whole product.** A ranking that can see any
      commit at or after the change it is ranking is not a prediction, it is a lookup, and a
      retrospective built on one looks brilliant and means nothing.

      **`as_of` is required and has no default.** A default would be the present, every caller that
      forgot it would silently rank against today's history, and the resulting numbers would be
      indistinguishable from correct ones. The bound is a parameter the caller must state.

      **The count matches the research ranker exactly**: `bisect_left(ts) - bisect_left(ts - YEAR)`
      over sorted timestamps is `committed_at >= as_of - window AND committed_at < as_of`. Gate 2a
      requires the productionised ordering to reproduce `defect_return.py`'s, and an off-by-one on
      this boundary would change it.

      **Re-indexing the same history is idempotent.** `touch` has no natural key, so a repository
      ingested twice would double every count and double them evenly — an error that moves no
      ranking, passes every ordering test, and corrupts the percentile that decides whether we fire.
IMPORTS: types (Touch), store.schema. Nothing to its right.
CONSUMED BY: rank, which receives the counts and never opens a database.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence

from quantamind.types.touch import Touch

# The research ranker's window, in seconds. Changing it changes the policy that has the p-value.
YEAR_SECONDS = 365 * 86400


# How many recent changes the firing decile is calibrated over. Enough to be stable, few


class UnboundedRankingError(ValueError):
    """A count was asked for without an `as_of` bound, or with a bound that cannot be honoured.

    Raised rather than defaulted. This is the one error in the store that protects a claim rather
    than a data structure.
    """


def ensure_repo(conn: sqlite3.Connection, host: str, name: str, clone_filter: str = "") -> int:
    """The row id for this repository, inserting it the first time. Idempotent."""
    if "/" not in name:
        raise ValueError(f"repository name must be owner/name, got {name!r}")
    conn.execute(
        "INSERT OR IGNORE INTO repo (host, name, clone_filter, first_seen) "
        "VALUES (?, ?, ?, strftime('%s','now'))",
        (host, name, clone_filter),
    )
    row = conn.execute("SELECT id FROM repo WHERE host = ? AND name = ?", (host, name)).fetchone()
    if row is None:  # pragma: no cover - INSERT OR IGNORE then SELECT cannot both miss
        raise RuntimeError(f"repo {host}:{name} vanished between insert and select")
    conn.commit()
    return int(row[0])


def index(conn: sqlite3.Connection, repo_id: int, touches: Iterable[Touch]) -> int:
    """Replace this repository's touch index with `touches`. Returns the number written.

    **Replace, not append.** Git history for a path is a fact about the repository, not an event
    stream we accumulate: re-reading it and appending would double every count. The delete and the
    insert share one transaction, so a crash leaves the previous index rather than half of one.
    """
    rows = [(repo_id, t.path, t.committed_at) for t in touches]
    with conn:  # one transaction: either the new index is in, or the old one still is
        conn.execute("DELETE FROM touch WHERE repo_id = ?", (repo_id,))
        conn.executemany("INSERT INTO touch (repo_id, path, committed_at) VALUES (?, ?, ?)", rows)
    return len(rows)


def counts(
    conn: sqlite3.Connection,
    repo_id: int,
    paths: Sequence[str],
    *,
    as_of: int,
    window: int = YEAR_SECONDS,
) -> Mapping[str, int]:
    """Prior-touch count per path over `[as_of - window, as_of)`. Every path gets an entry.

    A path with no history returns 0 rather than being absent: "never touched" is a score, and the
    ranker's no-history case depends on being able to see that every path scored zero.
    """
    if as_of <= 0:
        raise UnboundedRankingError(f"as_of must be a positive timestamp, got {as_of}")
    if window <= 0:
        raise UnboundedRankingError(f"window must be positive, got {window}")
    if not paths:
        return {}

    out = dict.fromkeys(paths, 0)
    marks = ",".join("?" for _ in paths)
    rows = conn.execute(
        f"SELECT path, COUNT(*) FROM touch "
        f"WHERE repo_id = ? AND path IN ({marks}) "
        f"AND committed_at >= ? AND committed_at < ? GROUP BY path",
        (repo_id, *paths, as_of - window, as_of),
    )
    for path, n in rows:
        out[str(path)] = int(n)
    return out
