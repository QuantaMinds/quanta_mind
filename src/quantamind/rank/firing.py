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

from quantamind.rank.order import fires
from quantamind.store.calibration import RECENT_CHANGES, baseline
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
ALWAYS_AT = 0.50


@dataclass(frozen=True, slots=True)
class Estimate:
    """What a customer would actually get, before they install anything."""

    changes: int
    fired: int
    floor: int
    selectivity: Selectivity

    @property
    def rate(self) -> float:
        return self.fired / self.changes if self.changes else 0.0

    def sentence(self) -> str:
        """One line for a human, naming the number rather than a claimed band."""
        if self.selectivity is Selectivity.NO_HISTORY:
            return "No history to calibrate on: this repository cannot be ranked yet."
        if self.selectivity is Selectivity.CONCENTRATED:
            return (
                f"On your last {self.changes} changes this would have spoken {self.fired} time(s). "
                f"A few files dominate your history, so a top-decile rule cannot separate them — "
                f"it would be almost always silent here. That is a property of the repository, and "
                f"you should know it before installing rather than after."
            )
        if self.selectivity is Selectivity.ALWAYS:
            return (
                f"On your last {self.changes} changes this would have spoken {self.fired} time(s) "
                f"— {self.rate:.0%}. That is close to every change, which is the noise this "
                f"product exists to reduce. It should not be installed here as configured."
            )
        return (
            f"On your last {self.changes} changes this would have spoken {self.fired} time(s) "
            f"— {self.rate:.0%}."
        )


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
        (repo_id, as_of, as_of - window, over, repo_id, as_of - window, as_of, repo_id),
    ).fetchall()
    tops = [int(r[0]) for r in rows]
    if not tops or max(tops) == 0:
        return Estimate(len(tops), 0, floor, Selectivity.NO_HISTORY)

    fired = sum(1 for top in tops if fires({"unit": top}, floor))
    rate = fired / len(tops)
    if rate <= CONCENTRATED_AT:
        state = Selectivity.CONCENTRATED
    elif rate >= ALWAYS_AT:
        state = Selectivity.ALWAYS
    else:
        state = Selectivity.SELECTIVE
    return Estimate(len(tops), fired, floor, state)
