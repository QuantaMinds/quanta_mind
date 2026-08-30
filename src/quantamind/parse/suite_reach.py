"""How much of a repository's own source its own tests import — measured, not assumed.

WHAT: `reach(clone)` returns a `Reach`: how many library-source modules exist, how many a test
      file imports, and the share. `NoSource` is raised when the tree holds no Python at all.
WHY:  **THIS IS THE HONEST ANSWER TO "WOULD THIS PRODUCT SERVE YOU WELL".** `docs/plans/product/
      product-build.md` B8 says the free-tier criteria "select for repositories where the product
      works" and that eligibility should be "a measured answer about their repository instead of
      a sales rule". A repository whose own suite reaches little of its own source is one where a
      review has less to stand on, and that is checkable rather than advertised.

      **IT COUNTS IMPORTS, NOT MENTIONS, AND THAT DIFFERENCE WAS 12 TO 43 POINTS.** Measured
      2026-08-30 across nineteen repositories: matching a module's name as text over-reported
      because `__init__` and `__main__` appear in any test mentioning a dunder, because short
      stems collide — sphinx's `ru`, `it` and `pt` are LOCALE files — and because documentation
      examples were counted as source. `typer` read 98% by mention and 91% of that "source" was
      `docs_src/tutorial/...` snippets.

      **NO SUITE IS A RESULT; NO SOURCE IS A FAILURE.** A repository with code and no tests really
      does have zero reach, and a prospect deserves to be told so. A tree with no Python at all is
      a broken clone — `git-lfs` absent left an empty working tree while `git clone` exited 0 and
      `git ls-tree HEAD` still listed 154 Python files — and reporting that as 0% would describe
      this instrument rather than the repository.
IMPORTS: stdlib only. Nothing to its right.
CONSUMED BY: `serve/onboarding.py`, after a clone exists.
SEE ALSO: `research/phase0/external/covered_source.py` is its twin, kept because research runs on
      a different interpreter and asks a different question — the share across a CANDIDATE CORPUS
      rather than for one customer. An edit to either is a prompt to look at the other.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

TEST_PART = re.compile(r"(^|/)(tests?|testing|spec)(/|$)|(^|/)test_[^/]*\.py$|_test\.py$")
NOT_LIBRARY = re.compile(r"(^|/)(docs?|docs_src|examples?|samples?|benchmarks?|scripts?)(/|$)")
VENDORED = re.compile(r"(^|/)(\.git|\.venv|venv|node_modules|vendor|build|dist)(/|$)")


class NoSource(RuntimeError):
    """The tree holds no Python at all — a broken clone, not a repository without tests."""


@dataclass(frozen=True, slots=True)
class Reach:
    """What a repository's suite imports of its own source."""

    modules: int
    reached: int
    has_suite: bool

    @property
    def share(self) -> float:
        """Reached over library modules. Zero when a repository truly has no suite."""
        return self.reached / self.modules if self.modules else 0.0

    def sentence(self) -> str:
        """One line a prospect can read. Never a bare number without its denominator."""
        if not self.has_suite:
            return (
                f"no test file found beside {self.modules} source module(s). A review here has "
                f"nothing to check its claims against."
            )
        return (
            f"{self.reached} of {self.modules} source module(s) are imported by this "
            f"repository's own tests ({self.share:.0%})."
        )


def is_library(path: str) -> bool:
    """Source a claim could be about: not a test, not documentation, not vendored."""
    if VENDORED.search(path) or TEST_PART.search(path) or NOT_LIBRARY.search(path):
        return False
    return path.endswith(".py")


def is_test(path: str) -> bool:
    return bool(TEST_PART.search(path)) and not VENDORED.search(path)


def _imported(clone: Path, tests: list[Path]) -> set[str]:
    """Every module name a test imports, parsed. Dunders dropped — every package carries them."""
    found: set[str] = set()
    for path in tests:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.update(alias.name.split("."))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    found.update(node.module.split("."))
                found.update(alias.name for alias in node.names)
    return {name for name in found if not name.startswith("__")}


def reach(clone: Path) -> Reach:
    """How much of this repository's source its own tests import.

    **A TREE WITH NO PYTHON RAISES RATHER THAN RETURNING ZERO.** That state is a clone that did
    not check out, and a zero share would describe the read instead of the repository.
    """
    library: list[str] = []
    tests: list[Path] = []
    any_python = False
    for path in clone.rglob("*.py"):
        rel = path.relative_to(clone).as_posix()
        if VENDORED.search(rel):
            continue
        any_python = True
        if is_test(rel):
            tests.append(path)
        elif is_library(rel):
            library.append(rel)

    if not any_python:
        raise NoSource(f"{clone}: no Python file in the tree; a share here would describe the read")

    stems = [s for s in (Path(p).stem for p in library) if not s.startswith("__")]
    if not tests:
        return Reach(modules=len(stems), reached=0, has_suite=False)
    imported = _imported(clone, tests)
    return Reach(len(stems), sum(1 for stem in stems if stem in imported), has_suite=True)
