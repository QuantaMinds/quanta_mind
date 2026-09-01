"""A review comment, and a standard somebody might be repeating in them.

WHAT: `Comment` is one review comment with its author and the change it was made on. `Proposal` is
      a point made more than once. **A `Proposal` is evidence for a human, never a rule.**
WHY:  **D1d, AND THESE TYPES CARRY THE TWO THINGS THE MEASUREMENT SAID MATTER MOST.**
      → `docs/findings/standards/D1D_REVIEWER_REPETITION_YIELD_2026-08.md`

      **`machine` — A BOT'S COMMENT IS NOT A TEAM'S STANDARD.** The first real run of the mining
      command proposed three standards and all three were this product's own review comments,
      repeated across heads. `research/phase0/corpus/human_attention.py` had already recorded that
      about a third of inline comments in public repositories are AI-written. Set from GitHub's own
      `user.type` and never guessed from the prose: a heuristic on the body misfires on a human
      quoting a bot, and on a bot that writes well.

      **`distinct_pulls` RETURNS `None`, AND THAT IS THE WHOLE POINT OF THE PROPERTY.** Four of
      thirteen real clusters were one reviewer restating themselves inside a single thread. "Said
      on two changes" and "we could not tell which changes" must never be the same value — the
      invariant this project states for `Unresolved` and for `Outcome.UNCHECKABLE`, here again.
IMPORTS: stdlib dataclasses. Nothing from any layer.
CONSUMED BY: `ingest/standards/mined.py`, `render/mined_rules.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MIN_OCCURRENCES = 2
"""**A FLOOR, EXPLICITLY NOT A SUFFICIENT CONDITION.** Eight of thirteen clusters at this threshold
were restatements or change-specific. `distinct_pulls` is what separates them, where it is known."""


@dataclass(frozen=True, slots=True)
class Comment:
    """One review comment, with the change it was made on.

    `pull` is `None` when the source could not supply it. **That is a different answer from a
    number**, and `Proposal.distinct_pulls` carries the distinction rather than defaulting.
    """

    body: str
    path: str = ""
    pull: int | None = None
    author: str = ""
    """Login of whoever wrote it. Empty when the source did not say."""

    machine: bool = False
    """Whether a bot wrote it. **Set from GitHub's own `user.type`, never guessed from the text.**

    A heuristic on the body would misfire on a human quoting a bot, and on a bot that writes well.
    GitHub knows, so we ask it; a source that cannot say leaves this False and the report says the
    comments were not filtered."""


@dataclass(frozen=True, slots=True)
class Proposal:
    """A point a reviewer made more than once. **Evidence for a human, never a rule.**"""

    text: str
    """The longest comment in the cluster — the fullest statement of the point."""

    occurrences: int
    evidence: tuple[Comment, ...] = field(default=())

    @property
    def distinct_pulls(self) -> int | None:
        """How many different changes this was said on, or `None` when the source did not say.

        **`None` IS NOT `1` AND IS NOT `0`.** A proposal we could not check for cross-change
        repetition is weaker than one we could, and a reviewer reading the report must be able to
        see which they are looking at.
        """
        pulls = {c.pull for c in self.evidence if c.pull is not None}
        if len(pulls) != len({c.pull for c in self.evidence}):
            return None  # at least one comment carried no pull number
        return len(pulls) or None

    @property
    def across_changes(self) -> bool:
        """Whether this was said on more than one change. **False when unknown.**"""
        known = self.distinct_pulls
        return known is not None and known >= MIN_OCCURRENCES

    def paths(self) -> tuple[str, ...]:
        """The files it was said about, deduplicated and ordered."""
        return tuple(sorted({c.path for c in self.evidence if c.path}))
