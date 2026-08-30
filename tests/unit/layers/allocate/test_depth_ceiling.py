"""Verification that the read-everything ceiling is the number the allocator ships with.

WHAT: Drives `allocate/depth.plan` across `FULL_CEILING` — the change size below which every
      file is read rather than ranked — and pins the union invariant on both sides of it.
WHY:  **`FULL_CEILING` DECIDES WHETHER RANKING HAPPENS AT ALL.** Below it every changed file is
      read and the ranker's decision is irrelevant; above it the budget applies and files go
      unread. Raising it to 21 silently doubles the changes on which this product does nothing
      it claims to do, and the mutation left every tier of the suite green.

      **THE UNION IS THE INVARIANT AND IT IS ASSERTED ON BOTH BRANCHES.** `paths + unread` must
      be exactly what was handed in: a reviewer that quietly loses a file reports a coverage it
      did not earn, and nothing downstream can tell that from a change that touched fewer files.
      A ceiling test that only counted paths would miss a leak between the branches.

      Ten is written out; `FULL_CEILING + 1` reads the value under test.
IMPORTS: pytest, quantamind.allocate.depth, quantamind.rank.order.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.allocate.depth import FULL_CEILING, Depth, plan
from quantamind.rank.order import rank

CEILING = 10
"""The size at or below which everything is read. See the module docstring."""


def _files(n: int) -> list[str]:
    return [f"src/f{i:02d}.py" for i in range(n)]


def _plan(n: int):
    files = _files(n)
    return plan(rank(dict.fromkeys(files, 1)), files)


def test_the_ceiling_is_ten_files() -> None:
    assert FULL_CEILING == CEILING


def test_a_change_at_the_ceiling_is_read_whole() -> None:
    """Ten files: everything read, nothing unread, so ranking changes nothing."""
    reading = _plan(CEILING)

    assert reading.depth is Depth.FULL
    assert len(reading.paths) == CEILING
    assert reading.unread == ()


def test_a_change_one_file_over_the_ceiling_is_not_read_whole() -> None:
    """Eleven files: the budget applies. This is the boundary a raised ceiling would move."""
    reading = _plan(CEILING + 1)

    assert reading.depth is not Depth.FULL


@pytest.mark.parametrize("count", [1, CEILING, CEILING + 1, 40])
def test_every_file_handed_in_comes_back_read_or_unread(count: int) -> None:
    """The union invariant, on both sides of the ceiling. A lost file is unearned coverage."""
    reading = _plan(count)

    assert sorted([*reading.paths, *reading.unread]) == sorted(_files(count))


def test_a_ceiling_that_admits_nothing_is_refused() -> None:
    """Zero would read no file at all while reporting a plan. Catches FULL_CEILING = 0."""
    files = _files(3)

    with pytest.raises(ValueError, match="at least one file"):
        plan(rank(dict.fromkeys(files, 1)), files, ceiling=0)
