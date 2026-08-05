"""What a completed draw contains: the blind sheet, the sealed key, and what was skipped.

WHAT: The result types for a hand-labelling draw -- one row per drawn PR on the blind
      side, one sealed answer per row on the key side, and the counts describing what the
      draw passed over to get there.
WHY:  Split from `draw.py`, which owns filling the buckets. This module owns what comes
      out. The separation matters more than usual here because the blind/sealed boundary
      is a correctness property: `blind` is typed as `(label_id, pr_url)` pairs so that no
      verdict can reach the labeller by accident, and keeping the type in its own module
      makes that boundary reviewable without reading the sampling logic.

      `unscannable` is reported rather than dropped. A PR whose outcome the instrument
      could not reach is not eligible for either bucket, and a draw that silently passed
      over such PRs would look identical to one that never met any -- which is how the
      base-branch defect stayed invisible in the first place.
IMPORTS: phase0.outcome.window for the Exclusion categories.
CONSUMED BY: handlabel/draw.py, phase0/sample_for_labelling.py; tests/handlabel/.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from phase0.outcome.window import Exclusion


@dataclass(frozen=True, slots=True)
class KeyRow:
    """The sealed answer for one drawn PR. Never reaches the blind sheet."""

    label_id: int
    pr_id: int
    repo: str
    number: int
    verdict: str  # "BROKE" | "CLEAN"
    criterion: str
    evidence_sha: str


@dataclass(frozen=True, slots=True)
class Drawn:
    """A completed draw: what the labeller sees, and what is sealed away."""

    blind: tuple[tuple[int, str], ...]  # (label_id, pr_url) -- nothing else, by type
    key: tuple[KeyRow, ...]
    seed: int
    considered: int
    repos_visited: int
    # PRs examined whose outcome could not be scanned, by category. Never eligible for a
    # bucket: a labeller cannot check a verdict the instrument never reached.
    unscannable: dict[Exclusion, int] = field(default_factory=dict)

    def bucket_sizes(self) -> dict[str, int]:
        """Counts by verdict. Safe to print: says how many, never which."""
        counts: dict[str, int] = defaultdict(int)
        for row in self.key:
            counts[row.verdict] += 1
        return dict(counts)

    def skipped_total(self) -> int:
        """How many examined PRs produced no verdict at all."""
        return sum(self.unscannable.values())
