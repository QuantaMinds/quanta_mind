"""The session record's one check, driven through `build_record` against real repositories.

WHAT: Asserts that the hook and `check_docs_sync` hold ONE `MAP_PATH` object, that it names a
      file that exists, and that the record prints `yes`, `no`, and "the map is missing" as three
      different things.
WHY:  **27 OF 27 SESSION RECORDS REPORTED `updated: no`, AND NONE COULD HAVE REPORTED ANYTHING
      ELSE.** `a38c2d1` moved the map to `docs/engineering/CODEBASE.md`, updated the `MAP_PATH` in
      `check_docs_sync.py`, and missed the second copy in the hook, which went on holding
      `"docs/CODEBASE.md"`. `touched_map = MAP_PATH in changed` was then False for eighteen days
      whatever the session did, and every session touching `src/` printed the warning. **A perfect
      zero from a comparison that could not return anything else** — `AGENTS.md` rule 14's clean
      zero, and the same shape as `candidate in ours_caught` in the corrections log.

      **EQUALITY BETWEEN THE TWO CONSTANTS IS NOT THE TEST; EXISTENCE IS.** Two constants spelling
      the same wrong path agree perfectly and measure nothing. The assertion that separates a
      working check from the broken one is that its subject is really on disk.

      **AND `build_record` IS CALLED RATHER THAN ITS OUTPUT RECOMPUTED.** Entry 3 of the
      corrections log is a validation tool that rebuilt its input instead of consuming it and
      certified a classifier the study does not run. A test that re-derived this line from
      `MAP_PATH` would pass against a hook still holding the wrong constant.
IMPORTS: scripts/guard/hooks/hook_session_end.py, scripts/guard/records/check_docs_sync.py.
      No product imports.
CONSUMED BY: `just check`.
SEE ALSO: `tests/unit/guards/test_document_identity.py`, the other half of the same rename.
"""

from __future__ import annotations

import subprocess
import sys
from functools import partial
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))
sys.path.insert(0, str(ROOT / "scripts" / "guard" / "hooks"))

import hook_session_end  # noqa: E402
from records.check_docs_sync import MAP_PATH  # noqa: E402

ABSENT = "does not exist, so the line above is not a measurement"


def _write(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _repo(root: Path, *changed: str, seed_map: bool = True) -> None:
    """A two-commit repository: `main` carrying the map, then a branch touching each named path."""
    run = partial(subprocess.run, cwd=root, check=True, capture_output=True, timeout=30)
    run(["git", "init", "-q", "-b", "main"])
    run(["git", "config", "user.email", "t@example.com"])
    run(["git", "config", "user.name", "t"])
    _write(root, "seed.txt", "seed\n")
    if seed_map:
        _write(root, MAP_PATH.as_posix(), "# map\n")
    run(["git", "add", "-A"])
    run(["git", "commit", "-qm", "seed"])
    run(["git", "checkout", "-qb", "feat/x"])
    for name in changed:
        _write(root, name, "edited\n")
    run(["git", "add", "-A"])
    run(["git", "commit", "-qm", "edit"])


def test_the_hook_and_the_docs_guard_hold_one_map_path_object() -> None:
    """Two strings that must agree are two strings that will not. This is why it is an import."""
    assert hook_session_end.MAP_PATH is MAP_PATH


def test_the_map_path_is_the_one_codebase_map_the_tree_actually_holds() -> None:
    """`updated: no` is the honest answer for a session that did not touch the map, AND the only
    answer a wrong path can give. This compares the constant against the tree rather than asking
    whether it happens to point at something: a second `CODEBASE.md` appearing elsewhere would
    make `MAP_PATH` name one of two, which is the collision `citations/identity.py` forbids.
    """
    found = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs").rglob("CODEBASE.md"))

    assert found == [MAP_PATH.as_posix()], (
        f"the tree holds {found} and the constant says {MAP_PATH.as_posix()!r}. Every check "
        f"comparing a changed path against it reports the same thing whether or not the map "
        f"was updated — which is how 27 of 27 session records came to say 'updated: no'."
    )


@pytest.mark.parametrize(
    ("touched", "expected"),
    [
        ((MAP_PATH.as_posix(),), "yes"),
        (("src/quantamind/rank/order.py",), "no"),
    ],
)
def test_the_record_reports_the_map_both_ways_against_a_real_repository(
    touched: tuple[str, ...], expected: str, tmp_path: Path
) -> None:
    """The VALUE, not the mechanism: `yes` has to be REACHABLE, and for eighteen days it was not."""
    _repo(tmp_path, *touched)
    record = hook_session_end.build_record(tmp_path)

    assert record is not None
    name, body = record
    assert name == "session-feat-x.md"
    assert f"- `{MAP_PATH.as_posix()}` updated: {expected}" in body, body
    assert ABSENT not in body, body


def test_a_missing_map_is_reported_as_missing_rather_than_as_not_updated(tmp_path: Path) -> None:
    """The two states that printed identically for eighteen days now print differently.

    **THE WHOLE MECHANISM IS SABOTAGED, NOT THE ENTRY POINT.** The map is absent from the tree
    rather than the constant being edited in place, so this fails the day somebody moves
    `CODEBASE.md` again without moving `MAP_PATH` with it — which is the thing that happened.
    """
    _repo(tmp_path, "src/quantamind/rank/order.py", seed_map=False)
    record = hook_session_end.build_record(tmp_path)

    assert record is not None
    body = record[1]
    assert ABSENT in body, body
    assert "check_docs_sync.MAP_PATH" in body


def test_the_record_names_the_file_that_wrote_it(tmp_path: Path) -> None:
    """It cited `scripts/guard/hook_session_end.py` for eighteen days, one directory too high.

    A `.py` path with no line number is invisible to `guard:citations/resolve`, which checks
    `file.py:NNN` against the file's length and bare `.md` paths against the tree. This is the
    only thing that reads it.
    """
    _repo(tmp_path, "src/quantamind/rank/order.py")
    record = hook_session_end.build_record(tmp_path)

    assert record is not None
    cited = "scripts/guard/hooks/hook_session_end.py"
    assert cited in record[1], record[1]
    assert (ROOT / cited).is_file()
