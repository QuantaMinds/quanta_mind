"""What a reader who knew nothing would have scored. The invariant comparison.

WHAT: `chance_hit(files, targets, budget)` is the probability that reading `budget` files chosen
      uniformly at random from a change of `files` touches at least one of its `targets`.
WHY:  **Alphabetical ordering is not a stable control and must not be the only one.**
      `docs/plans/preregistrations/ranker/defect-return-external-preregistration.md` measured it:
      in `home-assistant/core` the alphabetical arm beat chance by +1.75, because
      `components/<name>/__init__.py` sorts first and is also the churn-heavy file, so the control
      accidentally encoded importance. In five other repositories it sat at or below chance. A
      baseline whose strength depends on directory layout cannot anchor a claim.

      Chance depends on nothing but the arithmetic of the change, which is why the
      pre-registration calls it the invariant comparison and the one to quote.

      **IT ALSO DISSOLVES THE DEGENERATE CASE CORRECTLY.** When a change touches three or fewer
      files a budget of three reads all of them, so every arm hits and no ordering can be wrong.
      A file-count stratum split handles that coarsely; this handles it continuously and exactly,
      returning 1.0 whenever there are too few non-target files to fill the budget.

      **THE FORMULA IS COPIED FROM `research/phase0/claims/stats.py`, NOT DERIVED HERE.**
      Reimplemented rather than imported because rule 11 keeps `research/` out of the product, and
      a baseline re-derived for the product is a baseline that can quietly disagree with the one
      the published figure used. `tests/unit/layers/test_rank_baseline.py` checks it against
      hand-computed values.
IMPORTS: stdlib only (math). Nothing from any layer.
CONSUMED BY: serve/retrospective.py.
"""

from __future__ import annotations

from math import comb

DEFAULT_BUDGET = 3


def chance_hit(files: int, targets: int, budget: int = DEFAULT_BUDGET) -> float:
    """P(a random read of `budget` files touches at least one of the `targets`).

    Raises rather than clamping on impossible inputs: a change with fewer files than targets, or a
    negative budget, means the caller built the event wrong, and returning a plausible probability
    for it would put a fabricated baseline in a customer-facing number.
    """
    if files <= 0:
        raise ValueError(f"a change with {files} files is not an event")
    if not 0 < targets <= files:
        raise ValueError(f"{targets} returned-to file(s) in a change of {files}")
    if budget < 0:
        raise ValueError(f"budget cannot be negative, got {budget}")
    # Too few non-target files to fill the budget: some target is read no matter what.
    if files - targets < budget:
        return 1.0
    return 1.0 - comb(files - targets, budget) / comb(files, budget)
