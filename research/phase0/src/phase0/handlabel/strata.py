"""The sampling design of the blind draw: cells, bands, the per-repository cap, order.

WHAT: `Cell`, `band_of`, `cells_for`, `shuffled_by_repo`, `unfillable` — everything that
      decides WHICH units a draw may take, separated from the loop that takes them.
WHY:  A draw balanced on verdict alone can come back with every BROKE PR from one star
      band. That matters here because the bands break at different rates — measured on
      200 agent repositories, `<500` at 34.25% against `>=500` at 24.22%, Fisher
      p = 0.0594 — so a rule that is DIFFERENTIALLY LOOSE on small repositories would
      produce exactly that gap, and an unbalanced draw makes it invisible rather than
      merely underpowered. Twenty PRs cannot resolve it either way; a balanced twenty at
      least lets the disagreements be counted per band.

      A repository with no star count gets NO band. It is skipped and counted, never
      folded into `<500`: "we do not know its size" and "it is small" are different
      facts, and pooling them is what A52 records going wrong one layer up.
IMPORTS: stdlib random/collections; phase0.handlabel.select for `Candidate`;
      phase0.outcome.conclusion for `Outcome`. Nothing that touches the network -- which
      is the point: `draw` clones, so everything decidable WITHOUT a clone lives here and
      is tested. Four wrong fields once survived inside `draw` because nothing called it.
CONSUMED BY: handlabel/draw.py; tests/handlabel/test_strata.py.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import NamedTuple

from phase0.handlabel.select import Candidate
from phase0.outcome.conclusion import Outcome

# A15's floor. The human arm's own floor is 503 stars with 0% below it, so this is the
# boundary that decides whether an agent-arm PR has any human counterpart at all.
STAR_FLOOR = 500

# At most this many PRs from any one repository. Without it, a repository with 40
# eligible PRs could supply the whole sample and the gate would measure one project.
MAX_PER_REPO = 3

BAND_LOW = "<500"
BAND_HIGH = ">=500"


class Cell(NamedTuple):
    """One bucket of the draw. Both fields are part of the key, never derived later."""

    outcome: Outcome
    band: str


def band_of(stars: int) -> str | None:
    """Which band a repository sits in, or None when its size was never recorded.

    None rather than a default band: a PR whose repository has no star count cannot be
    placed, and placing it anyway would put an unmeasured unit into a stratum that is
    supposed to mean something about size.
    """
    if stars < 0:
        return None
    return BAND_HIGH if stars >= STAR_FLOOR else BAND_LOW


def cells_for(n_broke: int, n_clean: int) -> dict[Cell, int]:
    """The quota per cell, splitting each verdict evenly across the two bands.

    Raises:
        ValueError: if either total is odd. A 5/4 split is not a stratified draw, it is
            an unbalanced one with a stratum label, and rounding it silently is how a
            design decision becomes an accident.
    """
    for name, total in (("n_broke", n_broke), ("n_clean", n_clean)):
        if total % 2:
            raise ValueError(f"{name}={total} cannot split evenly across two star bands")
    return {
        Cell(Outcome.BROKE, BAND_LOW): n_broke // 2,
        Cell(Outcome.BROKE, BAND_HIGH): n_broke // 2,
        Cell(Outcome.CLEAN, BAND_LOW): n_clean // 2,
        Cell(Outcome.CLEAN, BAND_HIGH): n_clean // 2,
    }


def shuffled_by_repo(
    population: list[Candidate], rng: random.Random
) -> list[tuple[str, list[Candidate]]]:
    """Repositories in random order, each contributing at most MAX_PER_REPO PRs."""
    grouped: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in population:
        grouped[candidate.repo].append(candidate)
    repos = sorted(grouped)
    rng.shuffle(repos)
    picked: list[tuple[str, list[Candidate]]] = []
    for repo in repos:
        prs = sorted(grouped[repo], key=lambda c: c.pr_id)
        rng.shuffle(prs)
        picked.append((repo, prs[:MAX_PER_REPO]))
    return picked


def unfillable(cell: Cell, got: int, want: int, considered: int, repos: int) -> str:
    """Why a cell would not fill — and the two causes that look identical from inside.

    The message this replaced said only that a base rate far from expectation is "a
    finding about the outcome rule". TRUE on a first draw from an undepleted pool, FALSE
    on a fourth, where the cause is depletion by design — one message, two opposite
    meanings, sending a future reader to investigate a classifier that is working.
    """
    kind = f"{cell.outcome.value.upper()} {cell.band}"
    share = f"{got / considered:.1%}" if considered else "no candidates examined"
    return (
        f"only {got} {kind} in {considered} examined across {repos} repos, need {want} "
        f"({share}). Do not shrink the bucket. TWO CAUSES, OPPOSITE MEANINGS: (a) on a "
        f"FIRST draw from an undepleted pool this is a finding about the OUTCOME RULE; "
        f"(b) on a LATER draw it is DEPLETION -- a stratified draw takes {kind} faster "
        f"than the pool holds it, and three draws took this corpus 37.07% -> 33.33% "
        f"BROKE, which says nothing about the rule. Compare the residual pool's rate to "
        f"the corpus rate. If depleted, WALK MORE REPOSITORIES: re-seeding reshuffles "
        f"the same pool, and raising MAX_PER_REPO ({MAX_PER_REPO}) defeats the cap that "
        f"stops one repository supplying the sample."
    )
