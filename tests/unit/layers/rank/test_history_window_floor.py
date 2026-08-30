"""Verification that a window too thin to quote a rate from is skipped, not reported.

WHAT: Drives `rank/history_rates.earlier_rates` over windows above and below the sample floor,
      asserting how many rates come back.
WHY:  **THESE RATES ARE PRINTED TO A CUSTOMER IN ONE SENTENCE WITH THE HEADLINE RATE** — "would
      have spoken on 4% of your changes; across your history it ran 11% to 13%". A rate computed
      from a handful of changes in that sentence is a number with no support presented beside one
      that has some. `MIN_WINDOW` is what stops it, and it was freely mutable: at 0 every thin
      window is quoted, at 61 the honest ones are dropped too and the sentence loses its range.
      Both mutations left every tier of the suite green.

      **EMPTINESS IS A REAL ANSWER HERE.** A young repository with no history before the
      calibration window returns no rates at all, and that is not a zero — the caller renders the
      sentence differently. So the test asserts the COUNT of rates rather than that some came
      back, which is the only way "skipped for being thin" and "nothing to report" stay distinct.

      Thirty is written out; `MIN_WINDOW - 1` reads the value under test.
IMPORTS: pytest, quantamind.store.schema, quantamind.store.touches, quantamind.rank.history_rates.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.rank.history_rates import earlier_rates
from quantamind.store.schema import open_store
from quantamind.store.touches import ensure_repo

NOW = 1_700_000_000
WINDOW = 30 * 24 * 3600
FLOOR = 30
"""Fewest changes a window needs before its rate is quoted. Written out; see the docstring."""


def _store(tmp_path: Path) -> tuple[sqlite3.Connection, int]:
    conn = open_store(tmp_path / "s.db")
    return conn, ensure_repo(conn, "github.com", "o/r")


def _fill(conn: sqlite3.Connection, repo: int, *, per_window: int, windows: int) -> None:
    """`per_window` distinct changes in each window before the calibration edge."""
    rows = []
    for step in range(1, windows + 1):
        end = NOW - WINDOW - (step - 1) * WINDOW
        for n in range(per_window):
            stamp = end - WINDOW + 1 + n * (WINDOW // (per_window + 1))
            rows.append((repo, f"src/f{n % 5}.py", stamp))
    conn.executemany("INSERT INTO touch (repo_id, path, committed_at) VALUES (?, ?, ?)", rows)
    conn.commit()


def test_windows_above_the_floor_each_produce_a_rate(tmp_path: Path) -> None:
    """Four windows of forty changes: four rates, all of them proportions."""
    conn, repo = _store(tmp_path)
    _fill(conn, repo, per_window=FLOOR + 10, windows=4)

    rates = earlier_rates(conn, repo, as_of=NOW, window=WINDOW, over=400)

    assert len(rates) == 4
    assert all(0.0 <= rate <= 1.0 for rate in rates)


def test_windows_below_the_floor_produce_nothing_at_all(tmp_path: Path) -> None:
    """Twenty changes a window is not enough to quote. At MIN_WINDOW = 0 these are all reported."""
    conn, repo = _store(tmp_path)
    _fill(conn, repo, per_window=20, windows=4)

    assert earlier_rates(conn, repo, as_of=NOW, window=WINDOW, over=400) == ()


def test_a_repository_with_no_earlier_history_returns_empty(tmp_path: Path) -> None:
    """Empty is a real answer for a young repository, and must not be a zero."""
    conn, repo = _store(tmp_path)

    assert earlier_rates(conn, repo, as_of=NOW, window=WINDOW, over=400) == ()


def test_only_the_windows_that_clear_the_floor_are_counted(tmp_path: Path) -> None:
    """Two fat windows and two thin ones: two rates, not four and not none.

    This is the assertion that separates a working floor from one set to 0 or to 61 — both of
    the mutations that previously survived land on a different count here.
    """
    conn, repo = _store(tmp_path)
    _fill(conn, repo, per_window=FLOOR + 10, windows=2)
    rows = [(repo, f"src/g{n}.py", NOW - WINDOW - 2 * WINDOW - n * 3600 - 1) for n in range(5)]
    conn.executemany("INSERT INTO touch (repo_id, path, committed_at) VALUES (?, ?, ?)", rows)
    conn.commit()

    assert len(earlier_rates(conn, repo, as_of=NOW, window=WINDOW, over=400)) == 2
