"""How much a guard examined, and the floor below which that is a failure.

WHAT: `assert_examined(what, count, floor, where)` returns the count, or raises `NothingExamined`.
WHY:  **A GUARD THAT EXAMINED NOTHING PRINTS THE SAME WORD AS A GUARD THAT FOUND NOTHING WRONG.**
      An audit of all 24 guards found five reporting a coverage count and exiting 0 when it was
      zero -- 590 paragraphs, 82 documented invocations, 35 subprocess call sites among them. Each
      would report success the day a moved directory or a narrowed glob broke its discovery, which
      is `AGENTS.md` rule 14's "a filter admitting NOTHING must raise" turned on the filters.

      Kept out of `discovery.py`, which finds files. This decides whether finding none is a
      result or a fault, and that is a different question asked by a different caller.
IMPORTS: stdlib pathlib. No project imports.
CONSUMED BY: `check_subprocess_timeouts.py`, `records/check_documented_recipes.py`;
             any guard that reports a count.
"""

from __future__ import annotations

from pathlib import Path


class NothingExamined(RuntimeError):
    """A guard that examined nothing. Carries what it was looking for and where."""


MARKERS = ("AGENTS.md", "justfile")


def is_project(root: Path) -> bool:
    """Whether `root` is this repository rather than a test fixture or a temp tree.

    A floor is a fact about THIS repository's contents. Applied to a fixture with three files it
    fails every time, so the guards' own unit tests would have to carry twenty invocations each
    to satisfy a check that says nothing about them.
    """
    return all((root / marker).exists() for marker in MARKERS)


def assert_examined(what: str, count: int, floor: int, where: Path) -> int:
    """Return `count`, or raise when a guard examined fewer things than it must.

    **A GUARD THAT EXAMINES NOTHING PRINTS THE SAME WORD AS A GUARD THAT FOUND NOTHING WRONG.**
    Five guards reported a coverage count and exited 0 when it was zero: 590 paragraphs, 82
    documented invocations, 35 subprocess call sites, and so on -- each would report success the
    day a moved directory or a narrowed glob broke its discovery. That is `AGENTS.md` rule 14's
    "a filter admitting NOTHING must raise", applied to the filters themselves.

    The floor is a repository fact, not a target: it is set below today's count and exists to
    catch discovery collapsing, not to police the number drifting down by one.
    """
    if not is_project(where):
        # **SAID, NOT SKIPPED.** Waiving a check in silence is the defect this module exists for.
        print(f"[coverage] floor for {what} not applied: {where} is not the project root")
        return count
    if count < floor:
        raise NothingExamined(
            f"{what}: examined {count} under {where}, and this guard requires at least {floor}. "
            f"Discovery is broken -- a moved directory, a narrowed glob, or a rename. A guard "
            f"reporting success on nothing is worse than no guard."
        )
    return count
