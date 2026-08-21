"""How high a change's top file must score before this repository is worth speaking on.

WHAT: `baseline()` returns the floor for one repository at one moment; `cut()` picks it from a
      distribution of change-tops.
WHY:  **Split from `touches.py` at the 200-line cap, and it is the right seam.** That module is the
      touch INDEX -- what was changed and when. This is a POLICY question about that index: how
      selective the product should be. They change for different reasons, and the calibration is
      the part with a measured, contested history.
IMPORTS: stdlib sqlite3 only, plus the window constants from `touches`.
CONSUMED BY: `rank/firing.py` and `serve/run_review.py`.
"""

from __future__ import annotations

import sqlite3

from quantamind.store.touches import YEAR_SECONDS, UnboundedRankingError

# enough that the correlated count stays one bounded pass.
RECENT_CHANGES = 400


MIN_CALIBRATION = 150
"""Fewest changes the floor may be estimated from before the window is widened.

**A 90th percentile from 71 points is estimated from about 7 points above it.** `gin-gonic/gin`
holds only 71 changes in a year and fired on **29.0%** against a 10% target, while three larger
repositories landed at 6.3-13.0% — the floor was noise, not policy. Widening trades some
contemporaneity for a sample the tail can actually be read from, which is the right trade when the
alternative is a threshold set by a handful of observations.
"""

MAX_WINDOW_YEARS = 4
"""How far back the widening may reach. Beyond this the repository is a different codebase and a
contemporaneous floor stops meaning anything, so a short sample is reported rather than fabricated.
"""


class SpanMismatch(RuntimeError):
    """The bar and the score were measured over different spans. Never a silent zero."""


def assert_spans(reach: int, window: int) -> None:
    """The sample may reach further back; the MEASUREMENT may not.

    **THIS HAS HAPPENED TWICE AND BOTH TIMES THE SYMPTOM WAS A CLEAN, PLAUSIBLE ZERO.** First a
    calibration change's top was counted over its own prior year and compared against a top counted
    over today's year -- `sveltejs/svelte` fired on 0.0% of 300 changes. Then widening the sample to
    four years widened the COUNTING window with it, making the floor a four-year count against a
    one-year score -- `gin-gonic/gin` fired on 0.0%. Neither raised anything. Both looked like a
    repository that simply had nothing to say.

    A sentence in a docstring did not stop the second one, so it is an assertion now.
    """
    if reach < window:
        raise SpanMismatch(
            f"the calibration sample reaches {reach}s but touches are counted over {window}s. "
            f"The sample may reach further back than the measurement; it may never reach less."
        )


def window_for(
    conn: sqlite3.Connection, repo_id: int, *, as_of: int, window: int = YEAR_SECONDS
) -> tuple[int, int]:
    """(window actually used, changes it contains). Widens only until the sample is usable.

    Returns the FIRST window holding at least `MIN_CALIBRATION` changes, or the widest allowed when
    no window does. The count is returned rather than discarded because a floor estimated from 40
    changes and one estimated from 400 are different claims, and the caller reports which it had.
    """
    for years in range(1, MAX_WINDOW_YEARS + 1):
        span = window * years
        n = int(
            conn.execute(
                "SELECT COUNT(*) FROM (SELECT DISTINCT committed_at FROM touch "
                "WHERE repo_id = ? AND committed_at < ? AND committed_at >= ?)",
                (repo_id, as_of, as_of - span),
            ).fetchone()[0]
        )
        if n >= MIN_CALIBRATION or years == MAX_WINDOW_YEARS:
            return span, n
    return window, 0


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
    # **TWO WINDOWS, AND CONFLATING THEM IS BUG 2 IN A NEW COSTUME.**
    #   `reach`  — how far back to go to find ENOUGH CHANGES to estimate a tail from.
    #   `window` — the span touches are COUNTED over, which must match what the scorer uses.
    # Widening `window` too made the floor a four-year count compared against a one-year score, and
    # `gin-gonic/gin` went from 29.0% to **0.0%**. The sample can reach further back; the
    # measurement may not.
    reach, _n = window_for(conn, repo_id, as_of=as_of, window=window)
    assert_spans(reach, window)
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
            # **BOTH SIDES COUNTED IN THE SAME WINDOW, AND THAT IS THE FIX.** Counting each
            # calibration change's top in ITS OWN prior year, then comparing it against a top
            # counted in TODAY's year, compares two different quantities. On a cooling repository
            # the floor lags above everything the present can produce: `sveltejs/svelte` fired on
            # **0.0% of 300 changes** with floors of 199-237 against tops of 2-206. The floor now
            # answers "among recent changes, what does a top-decile one look like BY TODAY'S
            # COUNTS", which is the same question asked of the change being judged.
            "SELECT MAX(("
            "  SELECT COUNT(*) FROM touch prior"
            "  WHERE prior.repo_id = ? AND prior.path = changed.path"
            "    AND prior.committed_at >= ? AND prior.committed_at < ?"
            ")) AS top "
            "FROM recent JOIN touch changed"
            "  ON changed.repo_id = ? AND changed.committed_at = recent.committed_at "
            "GROUP BY recent.committed_at ORDER BY top",
            (repo_id, as_of, as_of - reach, over, repo_id, as_of - window, as_of, repo_id),
        )
    ]
    if not tops:
        return 0
    return cut(tops, quantile)


def cut(tops: list[int], quantile: float) -> int:
    """The threshold whose ACTUAL fired share lands closest to `1 - quantile`.

    **TIES MAKE THE NAIVE INDEX A KNIFE-EDGE, AND ON A SMALL REPOSITORY IT IS THE WHOLE ANSWER.**
    `tops[int(0.9 * n)]` returns a value, and on integer touch counts many changes share it. On
    `gin-gonic/gin` every one of the 87 firings was an EXACT TIE at the floor: `>=` fired on 29.0%
    of changes and `>` fired on **0.0%**. The rule was deciding a quarter of the corpus on which
    comparison operator was written.

    A decile of a discrete distribution cannot always be hit exactly. Choosing the cut whose
    realised share is nearest the target is what "the top decile" means when values repeat, and it
    removes the operator from the answer.
    """
    target = 1.0 - quantile
    n = len(tops)
    best, best_gap = tops[-1], 2.0
    for candidate in sorted(set(tops)):
        if candidate <= 0:
            continue
        share = sum(1 for t in tops if t >= candidate) / n
        gap = abs(share - target)
        if gap < best_gap:
            best, best_gap = candidate, gap
    return best
