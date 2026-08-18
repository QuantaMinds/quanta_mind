"""One file, touched by one commit, at one time — the only fact the ranking is computed from.

WHAT: `Touch`, a frozen (path, timestamp) pair.
WHY:  It lives in `types/` rather than beside the git reader that produces it because `store/` sits
      LEFT of `ingest/` in the layer order and must be able to name what it indexes. A value object
      shared by two layers belongs to the leftmost one; putting it in `ingest/` would have forced
      `store/` to import rightward, which is the one direction the layer guard forbids.

      `committed_at` is a Unix timestamp in UTC. The 365-day ranking window is arithmetic on
      instants, and a local time zone would move the window under the reader.
IMPORTS: nothing. `types` is the leftmost layer.
CONSUMED BY: ingest.history produces them; store.touches indexes them; rank counts them.

      NAMED FOR THE TYPE, not for the subject: `types/history.py` collided with
      `ingest/history.py`, and two modules sharing a name is the case where callers cannot tell
      which is stale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Touch:
    """A file, and the time of a commit that touched it."""

    path: str
    committed_at: int

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("Touch.path is empty; a touch with no file cannot be counted")
        if self.committed_at <= 0:
            raise ValueError(f"Touch.committed_at must be positive, got {self.committed_at}")
