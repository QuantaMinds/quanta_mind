"""Columns written from the clock rather than from the repository. One list, two consumers.

WHAT: `VOLATILE` names every column whose value changes between two identical builds.
WHY:  `assert_deterministic.py` must exclude them or it compares clock readings, and a golden pack
      for `verify-data` can never match a build containing them — so both need the same list.

      **Two copies of a list that must agree is the drift pattern in miniature.** It lives here so
      there is one, and both consumers print it, so it cannot grow without someone reading it.
IMPORTS: nothing.
CONSUMED BY: scripts/verify/assert_deterministic.py, and verify-data when a golden pack exists.
"""

from __future__ import annotations

VOLATILE: dict[str, set[str]] = {
    # store.touches.ensure_repo writes strftime('%s','now'). Two builds a second apart differ,
    # which is how the determinism check spent a week measuring clock speed.
    "repo": {"first_seen"},
    # store.deliveries stamps both from time.time().
    "delivery": {"started_at", "completed_at"},
    # store.reviews stamps when WE reviewed, which is genuinely a clock reading and not data.
    # Every other column of `review` is derived from the diff and the history, so only this one
    # is excluded -- a whole-table exclusion would hide a real change in fire_decision.
    "review": {"created_at"},
    # store.lifecycle stamps when we LOOKED, which is a clock reading. `merged_at` is NOT here:
    # it is GitHub's timestamp for an event that happened, and two builds must agree on it.
    "lifecycle": {"observed_at"},
    "prod_signal": {"observed_at"},
}


def rendered() -> str:
    """The exclusions as one line, for printing on every run."""
    return ", ".join(f"{t}.{c}" for t, cs in sorted(VOLATILE.items()) for c in sorted(cs))
