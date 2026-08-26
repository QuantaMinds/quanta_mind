"""The stretch of history a change may be measured against, bounded by the change itself.

WHAT: `Window`, and `ending_at(stamp, days, site)` which turns a commit's own `%cI` timestamp into
      the `--since`/`--until` pair every backward-looking git read must carry.
WHY:  **A WINDOW THAT ENDS NOW INSTEAD OF AT THE CHANGE IS THE DEFECT THIS MODULE EXISTS TO STOP.**
      `ingest/change_shape.py` used `--since=30.days.ago`, which is relative to when the process
      runs. Measured on real clones: django `2936a0a9` reported 6 recent commits to its files where
      3 of the 6 landed AFTER the change, and flask `c17f3793` reported 0 against a true 2, because
      that clone's history ended six months before the run and the window was simply EMPTY — which
      reads identically to "nobody has touched this file".

      It is separate from `change_shape` because bounding time and counting files are two concerns,
      and because this is the half that was wrong. A pure function over a timestamp can be given a
      known answer and checked; the same logic inlined beside four git calls cannot.

      **THERE IS NO WALL-CLOCK FALLBACK.** An unreadable timestamp raises. Defaulting to "now" is
      the original bug, and a default that reintroduces the defect is worse than an error.
IMPORTS: stdlib only (dataclasses, datetime). Left of rank; no sibling internals.
CONSUMED BY: `ingest/change_shape.py`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


class WindowUnreadable(RuntimeError):
    """A commit's own time could not be parsed, so no window can be bounded. Carries the site."""

    def __init__(self, site: str, stamp: str) -> None:
        super().__init__(f"{site}: could not read the commit's own time from {stamp!r}")
        self.site, self.stamp = site, stamp


@dataclass(frozen=True, slots=True)
class Window:
    """A closed interval of history ending at the change under review."""

    moment: dt.datetime
    """The change's own committer time. The window's right edge, and what `when` is read from."""

    args: tuple[str, ...]
    """`--since`/`--until`, ready to splat into a `git log` call."""


def moment_of(stamp: str) -> dt.datetime | None:
    """Git's `%cI` as a datetime, or None when unreadable.

    **`fromisoformat` REJECTS THE `Z` SUFFIX BEFORE PYTHON 3.11** and `%cI` emits it for UTC
    commits. It raised on a real repository the first time this ran live — not in any unit test,
    because the fixtures all carried numeric offsets.
    """
    if not stamp:
        return None
    try:
        return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def ending_at(stamp: str, days: int, *, site: str) -> Window:
    """The `days`-long window closing at `stamp`. Raises rather than falling back to wall-clock.

    **`--until` IS INCLUSIVE**, so the change under review sits inside its own window. Callers
    counting commits must drop it by identity: a change counted among its own recent churn is
    evidence about itself.
    """
    moment = moment_of(stamp)
    if moment is None:
        raise WindowUnreadable(site, stamp)
    opened = moment - dt.timedelta(days=days)
    return Window(moment, (f"--since={opened.isoformat()}", f"--until={stamp}"))
