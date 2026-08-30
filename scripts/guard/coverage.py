"""How much a guard examined, and the floor below which that is a failure.

WHAT: `assert_examined(what, count, floor, where)` returns the count, or raises `NothingExamined`.
WHY:  **A GUARD THAT EXAMINED NOTHING PRINTS THE SAME WORD AS A GUARD THAT FOUND NOTHING WRONG.**
      An audit of all 24 guards found five reporting a coverage count and exiting 0 when it was
      zero -- 590 paragraphs, 82 documented invocations, 35 subprocess call sites among them. Each
      would report success the day a moved directory or a narrowed glob broke its discovery, which
      is `AGENTS.md` rule 14's "a filter admitting NOTHING must raise" turned on the filters.

      Kept out of `discovery.py`, which finds files. This decides whether finding none is a
      result or a fault, and that is a different question asked by a different caller.
IMPORTS: stdlib pathlib and sys. No project imports.
CONSUMED BY: `check_subprocess_timeouts.py`, `records/check_documented_recipes.py`;
             any guard that reports a count.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


class NothingExamined(RuntimeError):
    """A guard that examined nothing. Carries what it was looking for and where."""


MARKERS = ("AGENTS.md", "justfile")


def is_project(root: Path) -> bool:
    """Whether `root` is inside this repository rather than a fixture or a temp tree.

    A floor is a fact about THIS repository's contents. Applied to a fixture with three files it
    fails every time, so the guards' own unit tests would have to carry twenty invocations each
    to satisfy a check that says nothing about them.

    **IT WALKS UP, BECAUSE SEVERAL GUARDS ARE ROOTED AT A SUBDIRECTORY.** The first version
    tested the markers IN `root`, so `check_assert_quality`, rooted at `tests/`, never saw them
    and had its floor waived on every run — the check silently not applying, which is the exact
    defect this module was written to stop, reintroduced by its own guard clause.
    """
    here = root.resolve()
    for candidate in (here, *here.parents):
        # **THE WALK STOPS AT THE FIRST `.git`.** Without this, any repository CLONED INSIDE the
        # project counts as the project: `.verify-clone` holds pallets/flask, and pointing a
        # guard at it produced a floor breach for a tree that has nothing to do with us. Found by
        # running the suite against four external repositories, not by any test.
        if (candidate / ".git").exists():
            return all((candidate / marker).exists() for marker in MARKERS)
        if all((candidate / marker).exists() for marker in MARKERS):
            return True
    return False


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


def guarded(outcome: Callable[[], int]) -> int:
    """Run a guard's `main`, turning a floor breach into a guard-shaped failure.

    **A GUARD MUST FAIL IN ITS OWN VOCABULARY, NOT PYTHON'S.** `assert_examined` raises so the
    run cannot continue, and an unhandled raise prints a traceback — which is what every floored
    guard did when pointed at a foreign repository. The exit code was right and the output was a
    stack trace, so a reader could not tell a coverage floor from a crash. Found by running the
    whole suite against `pallets/flask`, not by any test.

    The raise is kept because the tests assert on it and because stopping is correct; this turns
    it into the `[name] ...` line every other failure prints.
    """
    try:
        return outcome()
    except NothingExamined as bare:
        print(f"[coverage] {bare}", file=sys.stderr)
        return 1


def refuse_path_argument(argv: list[str], label: str) -> int | None:
    """`2` when the caller named a tree this guard cannot read, else `None`.

    **A GUARD THAT IGNORES THE PATH IT WAS GIVEN REPORTS ON A TREE THE CALLER NEVER ASKED
    ABOUT.** Ten guards resolve their subject from the working directory and discarded
    `argv[1]` in silence, so `check_schema_shape.py /some/other/repo` printed
    `[schema-shape] ok` about THIS repository -- a pass with the wrong provenance and nothing
    in the output to reveal it.

    **NAMING THE DIRECTORY THE GUARD IS ALREADY IN IS NOT AN ERROR.** `just check` invokes
    every guard as `... .py .` from the repository root, so refusing any argument at all broke
    the gate. The question is not whether an argument was passed but whether it points
    somewhere else: the same tree is the invocation the justfile documents, a different tree is
    a question this guard cannot answer.
    """
    if len(argv) <= 1:
        return None
    asked = Path(argv[1]).resolve()
    if asked == Path.cwd().resolve():
        return None
    print(
        f"[{label}] reads the repository it runs in and cannot check {asked}. "
        f"Refusing rather than reporting on {Path.cwd().name} under another name.",
        file=sys.stderr,
    )
    return 2
