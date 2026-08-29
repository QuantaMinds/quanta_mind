"""Work that has no commit yet — the change a developer is actually holding.

WHAT: Builds real repositories and asks `ingest/worktree.pending()` what is under review.
WHY:  **UNTRACKED FILES ARE THE ONES MOST LIKELY TO BE NEW CODE, AND `git diff` OMITS THEM.** A
      review built on `git diff` alone would silently skip every file the developer just created,
      which on a feature branch is most of what they wrote — and it would look like a complete
      review of a smaller change. That is the failure this file exists to prevent.

      **AND A CLEAN TREE IS NOT NOTHING TO REVIEW.** Work that is committed but not yet pushed is
      exactly the state "before making the PR" describes, so it falls through to the branch against
      its merge-base rather than reporting that there is nothing to look at.
IMPORTS: ingest.worktree.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.worktree import NothingPending, Pending, pending

GIT_TIMEOUT_S = 30


def _repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for args in (
        ["init", "--quiet", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "--quiet", "-m", "one"],
    ):
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )
    return root


def test_an_untracked_file_is_reviewed(tmp_path: Path) -> None:
    """**THE ONE `git diff` ALONE WOULD MISS**, and it is usually the new code."""
    clone = _repo(tmp_path / "a", {"kept.py": "x = 1\n"})
    (clone / "brand_new.py").write_text("def go() -> None:\n    pass\n", encoding="utf-8")

    found = pending(clone)

    assert "brand_new.py" in found.paths, (
        f"a file the developer just created was not reviewed: {found.paths}. `git diff` omits "
        "untracked files, so a review built on it alone skips most of a new feature"
    )
    assert "brand_new.py" in found.diff, "the new file's contents never reached the diff"


def test_an_edit_to_a_tracked_file_is_reviewed(tmp_path: Path) -> None:
    clone = _repo(tmp_path / "b", {"kept.py": "x = 1\n"})
    (clone / "kept.py").write_text("x = 2\n", encoding="utf-8")

    found = pending(clone)

    assert found.paths == ("kept.py",)
    assert "uncommitted" in found.origin


def test_a_clean_tree_falls_through_to_the_branch(tmp_path: Path) -> None:
    """Committed but not pushed is exactly the state "before making the PR" describes."""
    clone = _repo(tmp_path / "c", {"kept.py": "x = 1\n"})
    subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", "-b", "feature"],
        check=True,
        capture_output=True,
        timeout=GIT_TIMEOUT_S,
    )
    (clone / "added.py").write_text("y = 2\n", encoding="utf-8")
    for args in (["add", "-A"], ["commit", "--quiet", "-m", "two"]):
        subprocess.run(
            ["git", "-C", str(clone), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )

    found = pending(clone, base="main")

    assert found.paths == ("added.py",), f"the branch's own commits were not found: {found.paths}"
    assert "since main" in found.origin


def test_nothing_pending_is_named_rather_than_returned_empty(tmp_path: Path) -> None:
    """An empty review and "you have nothing to review" must not be the same value."""
    clone = _repo(tmp_path / "d", {"kept.py": "x = 1\n"})

    with pytest.raises(NothingPending):
        pending(clone, base="main")


def test_a_pending_with_no_paths_cannot_be_built() -> None:
    with pytest.raises(ValueError, match="NothingPending"):
        Pending((), "some diff", "somewhere")
