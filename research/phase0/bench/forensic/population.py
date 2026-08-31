"""Refuse a membership test whose two sides never intersect, instead of reporting its zero.

WHAT: `assert_intersects(what, left, right)` raises `PopulationMismatch` when NOTHING in `left`
      appears in `right`. Callers use it around any filter whose result is a count.
WHY:  **`candidate in ours_caught` was false for all 194 candidates**, because that key holds
      GOLDEN comments and the loop was feeding it candidates. Both sides are `str`, so no type
      checker could see it, nothing raised, and the resulting 68/32 split looked exactly like a
      finding. Four analyses were built on it. → `docs/engineering/CORRECTIONS.md` entry 7.

      **A filter that admits nothing across a whole pass is a statement about the two sets, not
      about the data.** It is the third clean zero in this project to mean a broken comparison
      rather than an empty result -- 0 in-window commits where there were 1,298, and 0 commits
      from a repository holding 1,990 under a pathspec git does not expand. Each printed a
      plausible number and each was believed for a while.

      **THE EMPTY CASE IS NOT AN ERROR AND MUST NOT BE ONE.** An arm that genuinely matched
      nothing is a real result. What cannot happen is EVERY element failing when the sets are
      supposed to overlap, so the caller states the expectation and this refuses to guess.
IMPORTS: stdlib only.
CONSUMED BY: `label_candidates.py`; any forensic filter whose output is a count.
"""

from __future__ import annotations

from collections.abc import Iterable


class PopulationMismatch(RuntimeError):
    """Two sets that should overlap do not overlap at all. Carries both sides' sizes."""


def assert_intersects(what: str, left: Iterable[str], right: Iterable[str]) -> int:
    """Size of the intersection. Raises when it is empty and both sides are non-empty.

    Returns the count rather than None so the caller can report what the check did, which is the
    difference between a check and a comment claiming one.
    """
    a, b = set(left), set(right)
    if not a or not b:
        # One side empty is a real, reportable result: nothing was emitted, or nothing expected.
        return 0
    both = a & b
    if not both:
        raise PopulationMismatch(
            f"{what}: {len(a)} on the left, {len(b)} on the right, and NOT ONE appears in both. "
            f"A filter admitting nothing across a whole pass is a statement about the two sets, "
            f"not about the data — name the population on both sides of the `in`. "
            f"left e.g. {sorted(a)[0][:70]!r}; right e.g. {sorted(b)[0][:70]!r}"
        )
    return len(both)
