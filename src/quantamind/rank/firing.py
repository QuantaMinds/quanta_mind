"""How often this repository would be spoken on, computed from its own history before install.

WHAT: `estimate(conn, repo_id, as_of, over)` replays recent changes through the real firing gate
      and returns the share that would have fired, plus the state of the distribution.
WHY:  **THE FIRING RATE IS A PROPERTY OF THE CUSTOMER'S REPOSITORY, NOT OF THE PRODUCT.** Measured
      out-of-sample on four repositories the gate was not built from, it ranges **6.3% to 29.0%**.
      A document that says "fires on 10-12%" is describing an average of that, and an average is
      not what any individual customer gets.

      **A PERCENTILE RULE CAN SELECT NOTHING AT ALL, AND THAT SILENCE IS NOT LEGIBLE.** A
      repository whose change-top distribution is concentrated puts the decile at the hottest
      file's count, and nothing clears it. The coverage line would truthfully report that nothing
      was skipped — the review was complete and empty. **That is a third kind of silence**, beside
      `NO_HISTORY` and `FLAT_NONZERO`: not "we did not read this" but "this rule cannot select
      anything here, structurally." It is named `CONCENTRATED` rather than left as a rate of zero.

      **AND IT IS ANSWERABLE BEFORE THE CONTRACT.** The number can be computed from a clone alone,
      which is what the retrospective already does. A customer who would be spoken on twice in three
      hundred changes should learn that in the sales conversation, not in week three.
IMPORTS: store.touches, rank.order, types.ranking. Left only.
CONSUMED BY: `serve/retrospective.py` and the CLI.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum

from quantamind.rank.history_rates import earlier_rates
from quantamind.rank.order import fires
from quantamind.store.calibration import RECENT_CHANGES, baseline, window_for
from quantamind.store.touches import YEAR_SECONDS


class Selectivity(Enum):
    """What the gate can do on this repository. Every value renders; none is an absence."""

    SELECTIVE = "selective"
    """The gate fires on some changes and not others, which is what it is for."""

    CONCENTRATED = "concentrated"
    """**The distribution cannot be split.** A few files dominate, the decile lands at their count,
    and the gate would speak on almost nothing. Silence here is structural, not a judgement about
    any particular change, and saying so is the difference between an honest install and a customer
    who thinks the tool is broken."""

    ALWAYS = "always"
    """The gate would fire on nearly everything, which is the noise the product exists to reduce."""

    NO_HISTORY = "no_history"
    """Nothing to calibrate against. Distinct from a distribution that cannot be split."""


CONCENTRATED_AT = 0.02

UNSTABLE_AT = 0.10
"""Spread across a repository's own windows past which the headline rate is not worth quoting.

Set from the measurement rather than chosen: `vuejs/core` and `trpc/trpc` sit at 5 points and their
rates are usable; `sveltejs/svelte` at 16 and `facebook/react` at 10 move enough that a single
number misleads. The boundary is where the observed repositories actually separate.
"""
ALWAYS_AT = 0.50


@dataclass(frozen=True, slots=True)
class Estimate:
    """What a customer would actually get, before they install anything."""

    changes: int
    fired: int
    floor: int
    selectivity: Selectivity
    calibrated_on: int = 0
    """How many changes the floor was estimated from. Reported, not gated on.

    **A MINIMUM-SIZE FLOOR WAS PROPOSED AND THE MEASUREMENT REFUSED IT.** Across five repositories
    the calibration size does not predict stability: `sveltejs/svelte` calibrates on **703** changes
    and its rate swings **16 points** between periods, while `vuejs/core` calibrates on **243** and
    swings **5**. `facebook/react` has the largest sample of all at 808 and swings 10. Refusing to
    report below some sample size would have been a rule with nothing behind it.
    """

    spread: tuple[float, ...] = ()
    """The rate on earlier windows of this repository, **OLDEST FIRST**.

    **These are a sequence, not a range, and reading them as a range loses the finding.** Five of
    seven repositories move three of four steps in one direction: `facebook/react` runs
    3-7-5-11-13% and `sveltejs/svelte` runs 23-27-16-15-11%. Neither is imprecision. **The rate is
    a property of the repository's own activity, and it drifts.** So the headline is the MOST
    RECENT window rather than an average, and the direction is reported beside it.
    """

    @property
    def direction(self) -> str:
        """`rising`, `falling` or `steady`, from first window to last."""
        if len(self.spread) < 3:
            return "steady"
        move = self.spread[-1] - self.spread[0]
        return "rising" if move > 0.03 else "falling" if move < -0.03 else "steady"

    @property
    def rate(self) -> float:
        return self.fired / self.changes if self.changes else 0.0

    def sentence(self) -> str:
        """How often a change reaches the top decile; it said "would have spoken" after A4."""
        if self.selectivity is Selectivity.NO_HISTORY:
            return "No history to calibrate on: this repository cannot be ranked yet."
        if self.selectivity is Selectivity.CONCENTRATED:
            return (
                f"{self.fired} of your last {self.changes} changes reached your top decile. "
                f"A few files dominate your history, so a top-decile rule cannot separate them — "
                f"almost nothing here will be marked as standing out. That is a property of the "
                f"repository, and you should know it before installing rather than after."
            )
        if self.selectivity is Selectivity.ALWAYS:
            return (
                f"{self.fired} of your last {self.changes} changes reached your top decile "
                f"— {self.rate:.0%}. Marking close to every change as standing out is the noise "
                f"this product exists to reduce. It should not be installed here as configured."
            )
        line = (
            f"{self.fired} of your last {self.changes} changes reached your top decile "
            f"— {self.rate:.0%}. Every change is reviewed; that fraction is flagged."
        )
        if self.spread:
            track = " to ".join(f"{r:.0%}" for r in self.spread)
            line += f" Across your history, oldest to newest, it ran {track}."
            if self.direction != "steady":
                line += (
                    f" It has been {self.direction}, so the figure above — your most recent"
                    f" window — is the one to plan on, not the average."
                )
            elif max(self.spread) - min(self.spread) >= UNSTABLE_AT:
                line += (
                    " That moves around without a direction, so treat the figure above as"
                    " approximate."
                )
        return line


def estimate(
    conn: sqlite3.Connection,
    repo_id: int,
    *,
    as_of: int,
    over: int = RECENT_CHANGES,
    window: int = YEAR_SECONDS,
) -> Estimate:
    """Replay recent changes through the real gate. **Not a model of it — the gate itself.**"""
    floor = baseline(conn, repo_id, as_of=as_of, window=window, over=over)
    _reach, calibrated = window_for(conn, repo_id, as_of=as_of, window=window)
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
        ")) AS top, COUNT(DISTINCT changed.path) AS files "
        "FROM recent JOIN touch changed"
        "  ON changed.repo_id = ? AND changed.committed_at = recent.committed_at "
        # **ORDERED, BECAUSE THESE ARE A SEQUENCE AND NOT A BAG.** Without it SQLite returns the
        # groups in whatever order it likes, and a trend read off an unordered list is noise
        # wearing a direction. An earlier report of these windows was printed newest-first and
        # read as oldest-first, which inverted the conclusion for two repositories.
        "GROUP BY recent.committed_at ORDER BY recent.committed_at",
        (repo_id, as_of, as_of - window, over, repo_id, as_of - window, as_of, repo_id),
    ).fetchall()
    # File count from the QUERY -- the replay passes one unit, so len(scores) would read 1.
    tops, counts = [int(r[0]) for r in rows], [int(r[1]) for r in rows]
    if not tops or max(tops) == 0:
        return Estimate(len(tops), 0, floor, Selectivity.NO_HISTORY, calibrated)

    fired = sum(
        1 for top, n in zip(tops, counts, strict=True) if fires({"unit": top}, floor, files=n)
    )
    rate = fired / len(tops)
    # **THE EARLIER WINDOWS MUST BE DISJOINT FROM THE CALIBRATION SET, AND THE FIRST VERSION WAS
    # NOT.** Slicing `tops` — the very changes the floor was derived from — measures which quarter
    # of the calibration window holds the high-scoring changes. About a tenth of that set clears its
    # own decile by construction, so the newest slice and the floor share a period and could agree
    # for that reason rather than because the repository changed.
    #
    # These windows are drawn from BEFORE the calibration window and scored against TODAY's floor.
    # Holding the bar fixed and varying only the period is what isolates a change in the
    # repository's behaviour from a change in the bar.
    spread = earlier_rates(conn, repo_id, as_of=as_of, window=window, over=over)
    if rate <= CONCENTRATED_AT:
        state = Selectivity.CONCENTRATED
    elif rate >= ALWAYS_AT:
        state = Selectivity.ALWAYS
    else:
        state = Selectivity.SELECTIVE
    return Estimate(len(tops), fired, floor, state, calibrated, spread)
