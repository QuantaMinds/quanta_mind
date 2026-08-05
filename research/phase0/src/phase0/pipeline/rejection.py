"""Why a PR left the corpus, and at what level that matters.

WHAT: `Rejection` and the category map. Nothing else.
WHY:  Its own module so both `assemble` (which produces rejections) and `verify_files`
      (which produces them too) can name the type without importing each other. A
      deferred import inside a function would have worked and would have widened the
      return type to `object`, which is how a typed absence stops being typed.

      The three categories are different claims and must never be pooled into one
      attrition number: `restricted` narrows the estimand, the other two bias it.
IMPORTS: stdlib dataclasses. Nothing from phase0.
CONSUMED BY: pipeline/assemble.py, pipeline/verify_files.py; the pilot's report.
"""

from __future__ import annotations

from dataclasses import dataclass

#   resource   -- the unit exists, we could not obtain it. Missing data.
#   integrity  -- obtained, but the corpus's account of it cannot be trusted. Missing
#                 data, and the reason correlates with patch size, so A17's bounds must
#                 cover it rather than treat it as noise.
#   restricted -- nothing to measure. Not missing data: the estimand does not cover this
#                 unit, which narrows the claim rather than biasing it.
CATEGORIES: dict[str, str] = {
    # A repository we could not clone must produce a record per PR, not the absence of
    # one. Absent rows shrink the denominator, so the same corpus scanned twice gave 33
    # records once and 34 the next -- a 3% swing at that size, and nothing reported it.
    # Kept apart because they select differently. A timeout removes the LARGEST
    # repositories -- 11.5x median size difference -- so it selects on the study's own
    # confounder; a repository that no longer exists selects on nothing and has no size
    # to measure. `clone_failed` remains for journals written before the split.
    "clone_failed": "resource",
    "clone_timeout": "resource",
    "repo_gone": "resource",
    "merge_metadata": "resource",
    "no_merge_sha": "resource",
    "parent_commit": "integrity",
    "file_set": "integrity",
    "no_python": "restricted",
    "no_symbols": "restricted",
}


@dataclass(frozen=True, slots=True)
class Rejection:
    """Why a PR did not become a record. Counted, never silently dropped."""

    pr_id: str
    stage: str
    reason: str
    agreement: float = -1.0

    @property
    def category(self) -> str:
        """`resource`, `integrity` or `restricted` -- see CATEGORIES.

        The default is deliberate but not safe: an unmapped stage becomes `resource`,
        which understates the bound if the real cause was `integrity`. Add new stages to
        the map rather than relying on it.
        """
        return CATEGORIES.get(self.stage, "resource")
