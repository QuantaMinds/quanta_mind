"""The outcome of one delivery, and the counts behind it.

WHAT: `Outcome`, the six things a delivery can end as, and `Delivered`, which carries them
      with what they were computed from.
WHY:  **NEVER A BARE SUCCESS.** Each value names a different reason the pipeline stopped, and
      a caller that could only ask "did it work" would treat a change with no readable files
      the same as one we posted on. `reading` and `examined` carry the allocation and the
      model pass so a reader can tell a review that found nothing from one that never ran.
IMPORTS: allocate.depth for `Reading`, types.deep for `Deep`. Leftward from `serve`.
CONSUMED BY: `serve/review_delivery.py`, and the live tests.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from quantamind.allocate.depth import Reading
from quantamind.types.deep import Deep


class Outcome(enum.Enum):
    """What became of one delivery. Six values, none of them silence."""

    POSTED = "posted"
    REHEARSED = "rehearsed — posting is off; the comment above was not sent"
    DUPLICATE = "already commented on this commit"
    NOTHING_TO_SAY = "ranked, and no file stood out enough to be worth a comment"
    NO_READABLE_FILES = "every changed file is in a language this product does not read"
    NO_FILES = "the pull request changed no files we could read from the API"


@dataclass(frozen=True, slots=True)
class Delivered:
    """The outcome, and the counts behind it. Never a bare success."""

    outcome: Outcome
    considered: tuple[str, ...]
    skipped: tuple[str, ...]
    body: str | None
    reading: Reading | None = None
    """What the model was given and what it was not. `None` before the ranking has run."""

    examined: Deep | None = None
    """The model's pass, or `None` when none was consulted. **NOT the same as finding nothing**:
    `Deep.consulted` separates "asked and it said nothing" from "never asked"."""

    def sentence(self) -> str:
        """One line for the log, stating what happened and what it was computed from."""
        return (
            f"{self.outcome.value} — {len(self.considered)} file(s) ranked, "
            f"{len(self.skipped)} skipped as unreadable"
        )
