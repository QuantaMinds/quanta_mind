"""Verification that a corpus list anywhere under research/ is checked, not only one file.

WHAT: Pins `check_burned_corpora.pools` — it finds corpus-shaped literals whatever they are named
      and wherever they live — and pins that a repository already measured cannot be queued again.
WHY:  **NINE BURNED REPOSITORIES SAT IN A CORPUS LIST AND THIS GUARD PRINTED `ok`.**
      `research/phase0/bench/forensic/execution_corpus.py` names its pool `CANDIDATES`, not
      `REPOS`, and lives outside `quote/corpus.py`. The guard read one file and one name, so
      `aio-libs/aiohttp`, `encode/httpx`, `pydantic/pydantic` and six more were queued for a fresh
      corpus having already been measured on.

      **THE GUARD WAS POINTED AT THE FILE THE LAST MISTAKE HAPPENED IN**, which is how a check
      stops covering the rule it was written for. The rule is "a repository measured twice is a
      design tuned on its own test set"; the population is every corpus, not one file's.
IMPORTS: pytest, scripts/guard/records/check_burned_corpora.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "guard" / "records"))

import check_burned_corpora as guard

POOL = 'CANDIDATES = (\n    "acme/one",\n    "acme/two",\n)\n'
PROSE = 'CANDIDATES = (\n    "not a repo",\n    "also/not/a/repo/x",\n)\n'
"""A constant of prose, not a corpus. A guard reading it as one would refuse real work."""


def _research(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        target = root / "research" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return root


def test_a_pool_named_candidates_is_found(tmp_path: Path) -> None:
    """The literal that was invisible. Not called REPOS, not in quote/corpus.py."""
    found = guard.pools(_research(tmp_path, {"phase0/bench/execution_corpus.py": POOL}))

    assert list(found.values()) == [["acme/one", "acme/two"]]
    assert "CANDIDATES" in next(iter(found))


def test_the_file_and_the_literal_are_both_named(tmp_path: Path) -> None:
    """A reader must be able to go straight to the list, not search for it."""
    found = guard.pools(_research(tmp_path, {"phase0/bench/execution_corpus.py": POOL}))

    where = next(iter(found))
    assert "execution_corpus.py" in where
    assert where.endswith("::CANDIDATES")


def test_a_list_of_something_else_is_not_a_pool(tmp_path: Path) -> None:
    """The false-positive direction: a constant of prose must not be read as a corpus."""
    found = guard.pools(
        _research(
            tmp_path,
            {
                "phase0/other.py": PROSE,
            },
        )
    )

    assert found == {}


def test_a_tree_with_no_pools_finds_nothing_rather_than_raising(tmp_path: Path) -> None:
    """No corpus lists is a real state for a fresh checkout."""
    assert guard.pools(_research(tmp_path, {"phase0/thing.py": "X = 1\n"})) == {}


def test_this_repository_has_no_repository_queued_twice() -> None:
    """The live check, on the real tree. This is what failed at nine before the guard could see."""
    root = Path(__file__).resolve().parents[3]
    burned = {
        r for names in guard.literals((root / guard.CORPUS).read_text()).values() for r in names
    }
    queued = {r for names in guard.pools(root).values() for r in names}

    assert burned & queued == set(), f"already measured and queued again: {sorted(burned & queued)}"
