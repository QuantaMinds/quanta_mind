"""What the model is shown, what it is not, and that nothing falls between the two.

WHAT: Exercises `allocate/depth.plan()` on the three situations it distinguishes, and the
      conservation invariant that `paths + unread` is exactly what was handed in.
WHY:  **THE FAILURE THIS GUARDS IS A FILE THAT VANISHES BETWEEN THE DIFF AND THE BUDGET.** A
      reviewer that silently drops files reports a coverage it did not earn, and nothing
      downstream can tell that from a change that genuinely touched fewer. So every test asserts
      on the UNION, not just on what was read.

      **AND IT ASSERTS THAT `UNRANKED` IS DISTINGUISHABLE FROM `FOCUSED`.** With no fix history
      every score ties and the order degenerates to alphabetical; a reading that presented that as
      a ranking would be publishing `sort(filenames)` as a judgement about risk.
IMPORTS: allocate.depth, types.{change,ranking,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.allocate.depth import FULL_CEILING, Depth, Reading, plan
from quantamind.types.change import ChangedUnit, Language
from quantamind.types.ranking import Allocation, Discrimination, RankedUnit, Ranking, Score
from quantamind.types.verdict import Site


def _unit(path: str, rank: int, allocation: Allocation) -> RankedUnit:
    return RankedUnit(
        unit=ChangedUnit(site=Site(path, 1), qualified_name=f"q{rank}", language=Language.PYTHON),
        rank=rank,
        score=Score(value=float(40 - rank), percentile=0.9),
        allocation=allocation,
    )


def _ranked(paths: list[str]) -> Ranking:
    return Ranking(
        units=tuple(_unit(p, i + 1, Allocation.DEEP) for i, p in enumerate(paths)),
        discrimination=Discrimination.ORDERED,
    )


def _no_history(paths: list[str]) -> Ranking:
    return Ranking(
        units=tuple(_unit(p, i + 1, Allocation.COLD) for i, p in enumerate(paths)),
        discrimination=Discrimination.NO_HISTORY,
    )


def test_a_small_change_is_read_entirely() -> None:
    """The case the old gate MUTED. `fires()` returned False at three files or fewer, which is
    the cheapest possible deep read — the whole diff fits in one prompt."""
    changed = ["a.py", "b.py", "c.py"]
    reading = plan(_ranked(changed), changed)

    assert reading.depth is Depth.FULL
    assert list(reading.paths) == changed, "a change under the ceiling must be read whole"
    assert reading.unread == (), f"nothing may be skipped at this size, got {reading.unread}"


def test_a_large_change_reads_what_history_ranked_and_names_the_rest() -> None:
    changed = [f"f{i}.py" for i in range(FULL_CEILING + 5)]
    reading = plan(_ranked(changed[:3]), changed)

    assert reading.depth is Depth.FOCUSED
    assert list(reading.paths) == changed[:3], "the funded paths are what the model reads"
    assert len(reading.unread) == len(changed) - 3, (
        "every file the budget could not fund must be NAMED as unread — the residual is the "
        f"product, and this one lost files: {reading.unread}"
    )


def test_no_fix_history_still_reads_and_refuses_to_call_it_a_ranking() -> None:
    """`Ranking.funded()` is empty on NO_HISTORY by design. The reviewer must still speak, and
    must not dress the slice it had to pick as a judgement about risk."""
    changed = [f"f{i}.py" for i in range(FULL_CEILING + 5)]
    reading = plan(_no_history(changed), changed)

    assert reading.depth is Depth.UNRANKED, (
        f"a change with no history read as {reading.depth}; FOCUSED here would publish diff "
        f"order as though fix history had chosen it"
    )
    assert reading.paths, "a reviewer that reads nothing is silence, which this product refuses"
    assert "NOT a judgement about risk" in reading.why


@pytest.mark.parametrize("size", [1, 3, FULL_CEILING, FULL_CEILING + 1, FULL_CEILING + 20])
def test_every_changed_file_is_either_read_or_named_unread(size: int) -> None:
    """**THE CONSERVATION INVARIANT.** A file cannot be lost between the diff and the budget."""
    changed = [f"f{i}.py" for i in range(size)]
    for ranking in (_ranked(changed[:3]), _no_history(changed)):
        reading = plan(ranking, changed)
        assert set(reading.paths) | set(reading.unread) == set(changed), (
            f"{size} file(s) went in and {reading.considered()} came out at {reading.depth}; "
            f"missing: {sorted(set(changed) - set(reading.paths) - set(reading.unread))[:3]}"
        )
        assert reading.considered() == size


def test_a_repeated_path_is_counted_once() -> None:
    reading = plan(_ranked(["a.py"]), ["a.py", "a.py", "b.py"])
    assert reading.considered() == 2, f"a duplicate path was double-counted: {reading}"


def test_a_reading_cannot_be_built_without_a_reason() -> None:
    with pytest.raises(ValueError, match="why is empty"):
        Reading(Depth.FULL, ("a.py",), (), "   ")


def test_a_path_cannot_be_both_read_and_unread() -> None:
    with pytest.raises(ValueError, match="both read and unread"):
        Reading(Depth.FOCUSED, ("a.py",), ("a.py",), "overlapping")


def test_reading_nothing_while_skipping_files_is_refused() -> None:
    """Silence and a decision must never be the same value on the wire."""
    with pytest.raises(ValueError, match="it is a silence"):
        Reading(Depth.FOCUSED, (), ("a.py", "b.py"), "read nothing at all")
