"""One commit, reduced to the three things any question about history needs.

WHAT: `Commit`, a frozen (timestamp, subject, paths) record.
WHY:  The subject is carried because the attribution rule reads it — a later commit whose subject
      looks like a fix, touching a file we ranked, is what fills `outcome`. Storing only a verdict
      would make the rule impossible to re-derive after it changes, and it has changed once
      already, flipping 67.9% of verdicts.

      `paths` is a frozenset because a commit touching the same file twice is still one touch of
      that file, and because the event definition intersects path sets.
IMPORTS: nothing. `types` is the leftmost layer.
CONSUMED BY: ingest.commits produces them; ingest.history derives Touch values from them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Commit:
    """A commit's time, its subject line, and the files it touched."""

    committed_at: int
    subject: str
    paths: frozenset[str]

    def __post_init__(self) -> None:
        if self.committed_at <= 0:
            raise ValueError(f"Commit.committed_at must be positive, got {self.committed_at}")
