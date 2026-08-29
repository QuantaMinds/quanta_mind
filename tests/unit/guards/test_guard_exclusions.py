"""Verification that a directory name cannot hide product code from every guard at once.

WHAT: Pins which paths `discovery` prunes, in both directions, and that the pruning that exists
      for performance is not lost to the narrowing.
WHY:  All 23 guards draw their population from `discovery.walk`, so one over-broad exclusion
      shrinks every one of them simultaneously and nothing reports it. `data` and `results` were
      excluded by bare NAME at any depth: source placed under `src/quantamind/data/` would have
      been unguarded, and no check would have said so.

      **THE PRUNING MUST SURVIVE THE FIX.** `walk` prunes during traversal rather than filtering
      after, because `rglob` on a multi-gigabyte clone under `research/phase0/data/` timed out
      the sixty-second pre-edit hook — and a guard that times out is a guard that gets switched
      off. So the test asserts the scratch directories are still skipped, not merely that product
      paths are now visible.
IMPORTS: pytest, scripts/guard/discovery.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard"))

from discovery import SCOPED_EXCLUDED_DIRS, SCOPED_TO, walk
from exclusions import is_excluded

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "path",
    [
        "research/phase0/data/clone/x.py",
        "research/phase0/results/run.json",
        "research/phase0/bench/results/z.py",
        "research/phase0/quote/results/a.json",
    ],
)
def test_research_scratch_is_still_pruned(path: str) -> None:
    """The reason the exclusion exists: multi-gigabyte clones and run outputs."""
    assert is_excluded(Path(path)) is True


@pytest.mark.parametrize(
    "path",
    [
        "src/quantamind/data/thing.py",
        "scripts/results/thing.py",
        "tests/data/fixture.py",
        "src/quantamind/results/thing.py",
    ],
)
def test_product_code_under_those_names_is_no_longer_hidden(path: str) -> None:
    """**THE BLIND SPOT.** A bare-name match hid these from all 23 guards with nothing saying so."""
    assert is_excluded(Path(path)) is False


@pytest.mark.parametrize(
    "name",
    [".git", ".venv", "__pycache__", "node_modules", "vendor", "dist", "build", ".verify-clone"],
)
def test_universally_excluded_names_still_are(name: str) -> None:
    """These are third-party or generated at any depth, so they stay unscoped."""
    assert is_excluded(Path(f"src/quantamind/{name}/x.py")) is True


def test_the_scope_is_declared_not_implied() -> None:
    assert frozenset({"data", "results"}) == SCOPED_EXCLUDED_DIRS, SCOPED_EXCLUDED_DIRS
    assert SCOPED_TO == ("research",), SCOPED_TO


def test_walk_still_prunes_rather_than_enumerating_everything() -> None:
    """A .venv of several thousand files must never appear, or the hook budget is gone."""
    found = list(walk(ROOT))
    assert found, "walk returned nothing at all"
    assert not any(".venv" in p.parts for p in found), "walk descended into .venv"
    assert not any(".verify-clone" in p.parts for p in found), "walk descended into the clone"


def test_scope_is_inherited_by_descendants() -> None:
    """`research/phase0/bench/martian/data/` is deep; the scope must reach it."""
    assert is_excluded(Path("research/a/b/c/d/data/x.py")) is True
    assert is_excluded(Path("other/a/b/c/d/data/x.py")) is False
