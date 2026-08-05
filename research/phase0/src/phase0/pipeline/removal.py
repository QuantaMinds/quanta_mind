r"""Delete a clone, and refuse to pretend it worked.

WHAT: `_extended`, `_remove_tree` and `sweep` -- removing a git working tree on Windows.
WHY:  Split from `worktree.py`, which owns cloning. Removal earned its own module by
      being wrong twice, in ways that both read as success.

      `shutil.rmtree(..., ignore_errors=True)` silently did nothing: git's object files
      are read-only, unlink raises EACCES, and the flag swallows it. The directory
      survived, the NEXT clone failed with "destination path already exists", and 19 of
      20 PRs came back as unreadable history.

      Then the deep-path case. `core.longpaths=true` lets git CREATE paths past 260
      characters and does nothing for Python's own filesystem calls, so a clone that
      succeeded could not be removed -- turning a deep tree into a permanent, repeating
      clone failure. `_extended` writes the \?\ form so deletion is not capped.

      `sweep` returns a COUNT rather than claiming success in a comment. A cleanup path
      here once said "a leftover is caught by the strict pass on the next attempt"; the
      next attempt was a different repository, nothing ever checked, and 1.6 GB
      accumulated.
IMPORTS: stdlib os, shutil, stat, pathlib.
CONSUMED BY: pipeline/worktree.py; tests/test_worktree.py.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


class CloneFailed(RuntimeError):
    """The repository could not be obtained. Corpus attrition, counted upstream."""


def _clear_readonly(func, path, _exc):  # type: ignore[no-untyped-def]  # shutil.onerror
    """Windows marks git's object files read-only, so unlink fails with EACCES."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _extended(target: Path) -> str:
    """Windows extended-length form, so deletion is not capped at 260 characters.

    `core.longpaths=true` lets git CREATE these paths; it does nothing for Python's own
    filesystem calls, which still fail with WinError 3 on anything deeper. So a clone
    that succeeded could not be removed, and the strict pass then refused to reuse the
    directory -- turning a deep tree into a permanent, repeating clone failure.
    """
    resolved = str(target.resolve())
    # The prefix is the four characters \\?\ — a UNC-style escape, not a regex. Written
    # wrong the first time as \?\, which Windows rejects outright, so every removal
    # failed instead of only the deep ones.
    prefix = "\\\\?\\"
    if os.name == "nt" and not resolved.startswith(prefix):
        return prefix + resolved
    return resolved


def _remove_tree(target: Path, *, strict: bool) -> None:
    """Delete a clone, refusing to pretend it worked.

    `shutil.rmtree(..., ignore_errors=True)` was used here and silently did nothing on
    Windows: git's object files are read-only, unlink raises EACCES, and the flag
    swallows it. The directory survived, the NEXT clone failed with "destination path
    already exists", and 19 of 20 PRs came back as unreadable history -- a failure that
    named the wrong cause entirely.

    Strict on the way in, because reusing a stale clone would analyse the wrong tree.
    Lenient on the way out -- but the reason first written here, "a leftover is caught
    by the strict pass on the next attempt", was wrong. The next attempt is a DIFFERENT
    repository, so nothing ever checked, and 1.6 GB of clones accumulated over 41
    repositories. `sweep` is what actually catches them, and it reports the count rather
    than tidying quietly.
    """
    if not target.exists():
        return
    try:
        shutil.rmtree(_extended(target), onerror=_clear_readonly)
    except OSError as exc:
        if strict:
            raise CloneFailed(f"{target}: could not remove a stale clone: {exc}") from exc
        return
    if strict and target.exists():
        raise CloneFailed(f"{target}: stale clone survived removal; refusing to reuse it")


def sweep(workspace: Path) -> int:
    """Delete clones a previous run left behind, and say how many there were.

    `cloned` removes leniently on the way out, and the justification written there --
    "a leftover is caught by the strict pass on the next attempt" -- was wrong. The next
    attempt is a DIFFERENT repository, so nothing ever checked. 1.6 GB accumulated over
    41 repositories before anyone looked, and the docstring above warns that disk
    exhaustion arrives at hour thirty of a multi-day run.

    Returning the count rather than cleaning quietly: a run that had to sweep leftovers
    is a run whose previous attempt failed to release file handles, and that is worth
    seeing rather than tidying away.
    """
    if not workspace.is_dir():
        return 0
    swept = 0
    for entry in sorted(workspace.iterdir()):
        if entry.is_dir():
            _remove_tree(entry, strict=False)
            swept += not entry.exists()
    return swept
