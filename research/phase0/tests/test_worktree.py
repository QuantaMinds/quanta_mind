"""Verification that a clone directory is really gone before we clone into it.

WHAT: Pins `_remove_tree` against the read-only files git writes into `.git/objects`,
      and pins that a removal which did not work raises instead of returning.
WHY:  `shutil.rmtree(..., ignore_errors=True)` was used here and did nothing on Windows:
      git's object files are read-only, unlink raises EACCES, and the flag swallows it.
      The directory survived, the next clone failed with "destination path already
      exists", and 19 of 20 PRs in the hand-labelling draw came back as unreadable
      history — a failure that named the wrong cause entirely and would have been
      recorded as corpus attrition.

      The first test below fails on the old implementation, which is the only reason it
      is worth having.
IMPORTS: pytest, phase0.pipeline.worktree.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

from phase0.pipeline.worktree import CloneFailed, _remove_tree


def _readonly_tree(root: Path) -> Path:
    """A directory shaped like the part of a clone that resists deletion."""
    objects = root / "repo" / ".git" / "objects"
    objects.mkdir(parents=True)
    blob = objects / "cafebabe"
    blob.write_bytes(b"object")
    os.chmod(blob, stat.S_IREAD)
    return root / "repo"


def test_a_read_only_object_file_does_not_survive_removal(tmp_path: Path) -> None:
    """The bug, directly: git's objects are read-only and rmtree refuses them."""
    target = _readonly_tree(tmp_path)
    _remove_tree(target, strict=True)
    assert not target.exists()


def test_ignore_errors_is_why_this_helper_exists(tmp_path: Path) -> None:
    """Documents the failure the helper replaces, on this platform only.

    On POSIX a read-only *file* in a writable directory is removable, so the old call
    would have worked and there is nothing to demonstrate. The bug was Windows-specific,
    which is exactly why it survived review.
    """
    target = _readonly_tree(tmp_path)
    shutil.rmtree(target, ignore_errors=True)
    if os.name == "nt":
        assert target.exists(), "expected the silent no-op this helper exists to prevent"
    _remove_tree(target, strict=True)
    assert not target.exists()


def test_a_missing_target_is_not_an_error(tmp_path: Path) -> None:
    """Nothing to remove is success, and must not create anything either."""
    absent = tmp_path / "never-existed"
    _remove_tree(absent, strict=True)
    assert not absent.exists()
    assert list(tmp_path.iterdir()) == []


def test_strict_removal_raises_rather_than_leaving_a_stale_clone(tmp_path: Path) -> None:
    """A clone we could not delete must never be silently reused.

    Reusing one means analysing a tree that is not the tree the PR landed on, and the
    exposure classification would be wrong with nothing to show for it.
    """
    target = tmp_path / "repo"
    target.mkdir()
    (target / "file").write_text("x", encoding="utf-8")

    def _refuse(*_args: object, **_kwargs: object) -> None:
        raise OSError(13, "Permission denied")

    original = shutil.rmtree
    shutil.rmtree = _refuse  # type: ignore[assignment]
    try:
        with pytest.raises(CloneFailed, match="could not remove a stale clone"):
            _remove_tree(target, strict=True)
    finally:
        shutil.rmtree = original  # type: ignore[assignment]


def test_lenient_removal_swallows_the_same_failure(tmp_path: Path) -> None:
    """Cleanup on the way out must not mask an exception already in flight.

    Safe because the strict pass on the next attempt catches anything left behind.
    """
    target = tmp_path / "repo"
    target.mkdir()
    (target / "left-behind").write_text("survivor", encoding="utf-8")

    def _refuse(*_args: object, **_kwargs: object) -> None:
        raise OSError(13, "Permission denied")

    original = shutil.rmtree
    shutil.rmtree = _refuse  # type: ignore[assignment]
    try:
        _remove_tree(target, strict=False)
    finally:
        shutil.rmtree = original  # type: ignore[assignment]

    # The tree is untouched. That is the point: lenient removal returns without raising
    # AND without having removed anything, so the guarantee that a stale clone is never
    # reused rests entirely on the strict pass above, not on this one.
    assert [p.name for p in target.iterdir()] == ["left-behind"]
    assert (target / "left-behind").read_text(encoding="utf-8") == "survivor"
