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
# enough that the correlated count stays one bounded pass.
RECENT_CHANGES = 400


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


def baseline(
    conn: sqlite3.Connection,
    repo_id: int,
    *,
    as_of: int,
    quantile: float = 0.9,
    window: int = YEAR_SECONDS,
    over: int = RECENT_CHANGES,
) -> int:
    """The score a change's TOP file must reach to be in this repository's top decile OF CHANGES.

    **CALIBRATED OVER CHANGES, NOT OVER FILES, AND THE DIFFERENCE IS 62% AGAINST 11%.** Measured
    2026-08-20 on four repositories the rule was not built from:

    | firing rule | rate | spread |
    |---|---|---|
    | absolute threshold, as previously shipped | 91.3% | 83.0-97.0% |
    | top decile of this repository's FILES | 62.2% | 42.7-79.7% |
    | top decile of this repository's CHANGES | ~11% | 10.0-12.3% |

    **The file-calibrated version does not work, and the reason is selection.** A change's
    top-ranked file is the most-touched among the files that change touched, and changed files are
    drawn from the active part of the repository -- so it clears a repository-wide file decile most
    of the time. Calibrating over changes compares a change to other changes, which is the unit the
    rate is quoted over.

    **A PREDICTION WAS WRITTEN DOWN FIRST AND IT WAS WRONG.** Files were expected to fire LESS than
    functions, since a pull request holds fewer files than functions and fewer units get a chance to
    clear the bar. They fire MORE, for the selection reason above. Recorded because a refuted
    prediction is worth more than an unrecorded one.

    **AND THE RATE IS DEFINITIONAL, NOT DISCOVERED.** A top decile of changes fires on a tenth of
    changes because that is what a top decile is. The transferable finding is the CONTRAST an
    absolute threshold could not deliver: 11% of one repository against 53% of another.

    Returns 0 when there is no history to calibrate against, which leaves the gate firing on
    anything above zero rather than silencing a repository it cannot yet judge.
    """
    if as_of <= 0:
        raise UnboundedRankingError(f"as_of must be a positive timestamp, got {as_of}")
    if not 0.0 < quantile < 1.0:
        raise UnboundedRankingError(f"quantile must be in (0, 1), got {quantile}")
    tops = [
        int(row[0])
        for row in conn.execute(
            # **CONTEMPORANEOUS, NOT MERELY TRAILING.** Calibrating over "the last 400 changes"
            # reached ~1.5 years back on an active repository, so the floor described a busier era
            # than the change being judged and SILENCED two repositories entirely -- 0.0% of 300
            # changes on both. The calibration window is the same window the scores come from.
            "WITH recent AS ("
            "  SELECT DISTINCT committed_at FROM touch"
            "  WHERE repo_id = ? AND committed_at < ? AND committed_at >= ?"
            "  ORDER BY committed_at DESC LIMIT ?"
            ") "
            "SELECT MAX(("
            "  SELECT COUNT(*) FROM touch prior"
            "  WHERE prior.repo_id = ? AND prior.path = changed.path"
            "    AND prior.committed_at >= recent.committed_at - ?"
            "    AND prior.committed_at <  recent.committed_at"
            ")) AS top "
            "FROM recent JOIN touch changed"
            "  ON changed.repo_id = ? AND changed.committed_at = recent.committed_at "
            "GROUP BY recent.committed_at ORDER BY top",
            (repo_id, as_of, as_of - window, over, repo_id, window, repo_id),
        )
    ]
    if not tops:
        return 0
    return tops[min(len(tops) - 1, int(quantile * len(tops)))]


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
