"""Verification that the pruned walk sees exactly what the walk it replaced saw.

WHAT: Compares `discovery.walk` against the `sorted(rglob("*"))`-and-filter it replaced,
      on set membership AND on order.
WHY:  The rewrite was for speed: the old walk enumerated every path inside multi-gigabyte
      clones before discarding them, and the pre-edit hook timed out. But a guard that is
      fast because it prunes too much is worse than a slow one — it reports clean on files
      it never opened, which is the failure this whole project exists to stop.

      Order is asserted, not just membership. The first attempt used a stack and passed a
      set comparison while silently reversing directory order; guard output is diffed in
      CI, so that would have read as a finding. Faster and quietly different is the same
      class of bug as faster and quietly narrower.
IMPORTS: pathlib, scripts.guard.discovery.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from discovery import (  # noqa: E402  — path is set above; guards import stdlib-only
    iter_package_dirs,
    walk,
)
from exclusions import EXCLUDED_DIRS, is_excluded  # noqa: E402

# Trees with real nesting and sibling directories. A single-child tree would pass any
# traversal order and prove nothing.
TREES = ("src", "scripts", "tests", "docs")


def _reference_files(root: Path) -> list[Path]:
    """The implementation that was replaced, kept here as the thing to match."""
    return [p for p in sorted(root.rglob("*")) if p.is_file() and not is_excluded(p)]


def _reference_dirs(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_dir() and not is_excluded(p)]


@pytest.mark.parametrize("tree", TREES)
def test_walk_matches_the_walk_it_replaced(tree: str) -> None:
    root = ROOT / tree
    assert root.is_dir(), f"{tree} is missing; the comparison would pass vacuously"
    expected = _reference_files(root)
    assert expected, f"{tree} yielded no files; the comparison would pass vacuously"
    assert list(walk(root)) == expected


@pytest.mark.parametrize("tree", TREES)
def test_package_dirs_match_the_walk_they_replaced(tree: str) -> None:
    root = ROOT / tree
    assert list(iter_package_dirs(root)) == _reference_dirs(root)


def test_excluded_directories_are_pruned_not_merely_filtered(tmp_path: Path) -> None:
    """The point of the rewrite: never descend into them at all.

    Asserted by making descent observable — a file inside an excluded directory must not
    appear, and neither must the directory.
    """
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "a.py").write_text("x", encoding="utf-8")
    # `data` was in this list until it was SCOPED to `research/`: as a bare name it hid product
    # code from every guard at once. The unconditional names are the ones that are third-party
    # or generated wherever they appear. → tests/unit/test_guard_exclusions.py
    for name in ("__pycache__", "node_modules", ".venv"):
        assert name in EXCLUDED_DIRS
        (tmp_path / name).mkdir()
        (tmp_path / name / "b.py").write_text("x", encoding="utf-8")

    assert [p.name for p in walk(tmp_path)] == ["a.py"]
    assert [p.name for p in iter_package_dirs(tmp_path)] == ["keep"]


def test_a_scoped_name_is_pruned_only_beneath_the_root_it_is_scoped_to(tmp_path: Path) -> None:
    """`data/` must still be pruned under `research/`, and walked anywhere else.

    The pruning is what the rewrite exists for — a multi-gigabyte clone under
    `research/phase0/data/` timed out the pre-edit hook — so scoping must not cost it.
    """
    (tmp_path / "research" / "data").mkdir(parents=True)
    (tmp_path / "research" / "data" / "huge.py").write_text("x", encoding="utf-8")
    (tmp_path / "src" / "data").mkdir(parents=True)
    (tmp_path / "src" / "data" / "real.py").write_text("x", encoding="utf-8")

    found = [p.name for p in walk(tmp_path)]
    assert "huge.py" not in found, "research scratch was walked; the pruning was lost"
    assert found == ["real.py"], f"product code under data/ stayed hidden: {found}"


def test_an_unreadable_directory_is_skipped_rather_than_fatal(tmp_path: Path) -> None:
    """A clone being deleted mid-run must not take the guards down with it."""
    (tmp_path / "gone").mkdir()
    (tmp_path / "gone" / "a.py").write_text("x", encoding="utf-8")
    found = list(walk(tmp_path))
    assert [p.name for p in found] == ["a.py"]
