"""How many golden changes carry human context, and what effect a paired arm could detect.

WHAT: prints the exposed population over the golden corpus and the exact McNemar power at that n.
      Reproduces every number in `d6b-human-context-preregistration.md`.
WHY:  **THE POWER CALCULATION IS THE RESULT HERE, AND IT WAS DONE BEFORE THE RUN.** Design
      fourteen records "the power calculation, which had not been done" as one of its own failures;
      this is that step, executed first. At n = 33 the smallest detectable net effect is +32%, and
      no lever in this project's history has moved anything by that, so the arm was not run.

      **IT USES THE PRODUCT'S OWN READERS**, not a reimplementation. A feasibility number produced
      by different code from the one that would run the experiment measures a different thing —
      the failure this repository has recorded as "two code paths, one column".
IMPORTS: stdlib; quantamind.ingest.context.tickets. Reads the golden corpus and calls `gh`.
CONSUMED BY: `docs/plans/preregistrations/reviewer/d6b-human-context-preregistration.md`.
"""

from __future__ import annotations

import collections
import json
import pathlib
from math import comb

from quantamind.ingest.context.tickets import behind

GOLDEN = pathlib.Path("research/phase0/bench/martian/data/golden_comments")
MIN_CONTEXT_CHARS = 120
"""Characters of stated goal plus ticket titles below which the two arms cannot differ.

Fixed before any outcome was seen. A change whose context is a bare `#412` gives the context arm
nothing the control lacks."""


def exposed() -> tuple[int, int, list[tuple[str, int, int]]]:
    """(usable, total, detail). **Uses `tickets.behind`, the reader the experiment would use.**"""
    tally: collections.Counter[str] = collections.Counter()
    usable: list[tuple[str, int, int]] = []
    for path in sorted(GOLDEN.iterdir()):
        for item in json.loads(path.read_text(encoding="utf-8")):
            parts = item["url"].rstrip("/").split("/")
            repo, number = f"{parts[3]}/{parts[4]}", int(parts[-1])
            context = behind(repo, number)
            text = " ".join(
                (context.stated.text() + " " + " ".join(t.title for t in context.tickets)).split()
            )
            if len(text) >= MIN_CONTEXT_CHARS:
                usable.append((repo, number, len(text)))
            else:
                tally["too thin"] += 1
    return len(usable), len(usable) + tally["too thin"], usable


def _mcnemar(better: int, worse: int) -> float:
    """Exact two-sided McNemar p for one discordant split."""
    total = better + worse
    if total == 0:
        return 1.0
    smaller = min(better, worse)
    tail = sum(comb(total, i) for i in range(smaller + 1)) / 2**total
    return float(min(1.0, 2 * tail))


def power(helps: float, hurts: float, changes: int) -> float:
    """P(reaching p < 0.05) for a true effect, computed exactly rather than simulated."""
    discordant = helps + hurts
    if discordant == 0:
        return 0.0
    share = helps / discordant
    reached = 0.0
    for count in range(changes + 1):
        p_count = comb(changes, count) * discordant**count * (1 - discordant) ** (changes - count)
        for better in range(count + 1):
            p_split = comb(count, better) * share**better * (1 - share) ** (count - better)
            if _mcnemar(better, count - better) < 0.05:
                reached += p_count * p_split
    return reached


def main() -> int:
    usable, total, _ = exposed()
    print(f"exposed population: {usable} of {total} ({100 * usable / total:.0f}%)\n")
    print(f"{'helps':>7} {'hurts':>7} {'net':>7} {'power':>8}")
    for helps, hurts in ((0.10, 0.05), (0.15, 0.05), (0.20, 0.05), (0.30, 0.05), (0.30, 0.00)):
        print(f"{helps:7.0%} {hurts:7.0%} {helps - hurts:+7.0%} {power(helps, hurts, usable):8.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
