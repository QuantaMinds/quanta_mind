"""How much of a change the model reads, and — named, never implied — what it does not.

WHAT: `plan(ranking, changed)` returns a `Reading`: the paths the model will be shown, the paths it
      will not, and why. `Depth` says which of three situations produced that split.
WHY:  **THIS LAYER IS NAMED IN `AGENTS.md` AND WAS AN EMPTY DIRECTORY.** The order is
      `rank -> allocate -> infer`, and `allocate/` held nothing but `__init__.py` -- so the
      ranking had no consumer that spent anything, and inference was reachable only from the CLI.

      **THE OLD GATE MUTED THE REVIEWS WE COULD MOST AFFORD.** `rank.order.fires()` returns False
      when `files <= BUDGET` (3), because on three files an ORDERING saves the reader nothing. For
      a ranking that was correct. For a reviewer it is inverted: a three-file change is the
      cheapest possible deep read, the whole diff fits in one prompt, and it was exactly the case
      that produced no comment at all. `Depth.FULL` is that case, read entirely.

      **THE RANKING BECOMES THE COST LEVER, WHICH IS THE HONEST USE OF THE CLAIM THAT
      REPLICATED.** Top-three-by-fix-history misses 1.21% of the files a later fix returns to
      against alphabetical's 3.12%, on six repositories the method never saw. That is a claim about
      WHICH FILES TO READ FIRST. It is not, and never was, a claim about when to stay silent --
      which is what it had been wired to decide.

      **`Depth.UNRANKED` IS A THIRD VALUE RATHER THAN A FALLBACK IN FOCUSED'S CLOTHES.**
      `Ranking.funded()` returns EMPTY on `Discrimination.NO_HISTORY`, deliberately: with
      every score tied, `(-score, path)` degenerates to alphabetical order, and publishing
      `sort(filenames)` as a judgement about risk is the failure it refuses. This layer must
      still read something, so it reads a bounded slice in diff order and SAYS SO on the value.
      A reader who cannot tell
      "history chose these" from "we had to pick" has been told a ranking happened when none did --
      and this is the slice that misses most, 4.46% against 1.21%.

      **`unread` IS CARRIED, NOT INFERRED FROM A SUBTRACTION SOMEWHERE ELSE.** A reviewer that
      reads 3 of 40 files and does not say which 37 it skipped is claiming a coverage it does not
      have. "The residual is the product": what we did not look at is the thing the customer is
      paying us to know about.
IMPORTS: `types.ranking` only. Leftward, and nothing from `infer` -- this layer decides the budget
      and must not be able to consult the thing it is budgeting for.
CONSUMED BY: `serve/review_delivery.py` (phase A2 of `docs/plans/product/product-build.md`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from quantamind.types.ranking import Ranking

# **CHOSEN, NOT MEASURED, AND IT IS A COST BOUND.** No artefact in this repository measures where
# reading a whole change stops paying; what this number does is cap the prompt a small change can
# produce. It is a parameter so a caller can move it, and A6 in the product build checklist
# (`docs/plans/product/product-build.md`) reports cost per pull request -- which is the evidence
# that would justify changing it.
FULL_CEILING = 10


class Depth(Enum):
    """Which situation produced this reading. Three values, none of them an absence."""

    FULL = "full"
    FOCUSED = "focused"
    UNRANKED = "unranked"


@dataclass(frozen=True, slots=True)
class Reading:
    """What the model is shown, what it is not, and the reason — all three or none.

    **`why` IS MANDATORY FOR THE SAME REASON AN EDGE CARRIES PROVENANCE.** An allocation with no
    stated reason cannot be told apart from an accident afterwards, and the number of files read is
    the single biggest driver of both cost and coverage.
    """

    depth: Depth
    paths: tuple[str, ...]
    unread: tuple[str, ...]
    why: str

    def __post_init__(self) -> None:
        if not self.why.strip():
            raise ValueError("Reading.why is empty; an allocation must state what decided it")
        both = set(self.paths) & set(self.unread)
        if both:
            raise ValueError(f"a path is both read and unread: {sorted(both)[:3]}")
        for name, group in (("paths", self.paths), ("unread", self.unread)):
            if len(set(group)) != len(group):
                raise ValueError(f"Reading.{name} contains a duplicate path")
        if self.unread and not self.paths:
            raise ValueError(
                f"reading nothing while leaving {len(self.unread)} file(s) unread is not an "
                f"allocation, it is a silence — emit a Depth that says what was decided"
            )

    def considered(self) -> int:
        """Every file this change put in front of the allocator. Read plus unread, never a guess."""
        return len(self.paths) + len(self.unread)


def plan(ranking: Ranking, changed: Sequence[str], *, ceiling: int = FULL_CEILING) -> Reading:
    """Decide what the model reads for one change.

    **THE UNION IS THE INVARIANT.** `paths + unread` is exactly what was handed in, deduplicated:
    a file cannot be dropped between the diff and the budget without one of the two lists growing.
    A reviewer that quietly loses files reports a coverage it did not earn, and nothing downstream
    can tell that from a change that genuinely touched fewer.
    """
    if ceiling < 1:
        raise ValueError(f"ceiling must admit at least one file, got {ceiling}")
    files = tuple(dict.fromkeys(changed))
    if not files:
        return Reading(Depth.FULL, (), (), "the change touched no file we can read")

    if len(files) <= ceiling:
        return Reading(
            Depth.FULL,
            files,
            (),
            f"{len(files)} file(s), at or under the {ceiling}-file ceiling — the whole change "
            f"is read, because at this size an ordering saves the reader nothing and the "
            f"entire diff fits in one prompt",
        )

    within = set(files)
    warm = tuple(
        path
        for path in dict.fromkeys(unit.unit.site.path for unit in ranking.funded())
        if path in within
    )
    if warm:
        return Reading(
            Depth.FOCUSED,
            warm,
            tuple(path for path in files if path not in set(warm)),
            f"{len(files)} files exceed the {ceiling}-file ceiling — reading the {len(warm)} "
            f"that fix history ranked highest, and naming the rest as unread",
        )

    slice_at = min(ceiling, len(files))
    return Reading(
        Depth.UNRANKED,
        files[:slice_at],
        files[slice_at:],
        f"{len(files)} files and no fix history to rank them by — reading the first {slice_at} "
        f"in diff order. This is NOT a judgement about risk, and must not be rendered as one",
    )
