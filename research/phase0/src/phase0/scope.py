"""The file set. Computed once, consumed by both the census and the graph.

WHAT: Resolves a repository checkout plus a PR's changed files into one `Scope` —
      a package root and an ordered tuple of Python files.
WHY:  Amendment A3 in PHASE0_PREREGISTRATION.md, made mechanical rather than
      remembered. The census produces the denominator and PyCG produces the
      numerator, and they must agree on which files exist. If the census walks a
      wider set than PyCG was given, every call site outside PyCG's scope has no
      possible edge, every one of them reads as unresolved, and exposure inflates
      toward 100%. RUNBOOK section 6 Q4 lists that as a stop condition without
      naming the cause; this module is the cause, removed.

      Test files are deliberately IN scope. A test calling a changed symbol is a
      real caller, and tests resolve unusually well because they call directly --
      excluding them would strip the best-resolved callers from the denominator
      and inflate exposure. The MSR breaking-changes paper excluded them, but it
      was counting AST-level breakage, not callers.
IMPORTS: stdlib only (pathlib, dataclasses). No tree-sitter, no pycg -- both
      consumers import this, so it must not depend on either.
CONSUMED BY: census.py, run_graph.py, classify_exposure.py; tests/test_scope.py.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

# Directories that are not this project's source. Deliberately short: anything
# excluded here is excluded from the denominator too, so a wrong entry silently
# changes the coverage arithmetic.
NON_SOURCE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        "node_modules",
        "site-packages",
        "vendor",
        # A56. One unparseable file makes PyCG return SYNTAX_UNSUPPORTED for the WHOLE
        # package, and A7 then excludes the PR, so a file nobody would call source
        # removes a real unit from the study. Two causes were observed and only one is
        # about Python at all: `template_samples/sample.py` reads
        # `from {{ namespace }} import {{ client_name }}` -- Jinja2, which no interpreter
        # version parses -- and a `tests/` fixture used PEP 695 `type X[T] = ...`, valid
        # 3.12 that fails only because PyCG pins CPython 3.10.
        "templates",
        "template_samples",
        "tests",
        "third_party",
        "build",
        "dist",
    }
)


@dataclass(frozen=True, slots=True)
class Scope:
    """The files PyCG is given, which are exactly the files the census walks."""

    package_root: Path
    files: tuple[Path, ...]

    @property
    def file_count(self) -> int:
        return len(self.files)

    def module_of(self, path: Path) -> str:
        """The module name PyCG will use for this file.

        Relative to package_root and WITHOUT the package name itself: with
        `--package .../acme`, the file `acme/handlers.py` is `handlers`, and
        `acme/sub/deep.py` is `sub.deep`. Verified by running PyCG, not assumed --
        this convention decides every fully-qualified name in the graph, so a
        wrong guess here makes the join match nothing.
        """
        try:
            relative = path.relative_to(self.package_root)
        except ValueError:
            return ""
        parts = list(relative.parts)
        if not parts:
            return ""
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        return ".".join(parts)


def _is_source(path: Path) -> bool:
    """True for a Python file outside every non-source directory."""
    if path.suffix != ".py":
        return False
    return not any(part in NON_SOURCE_DIRS for part in path.parts)


def iter_python_files(root: Path) -> Iterator[Path]:
    """Every in-scope Python file beneath root, in deterministic order.

    Sorted because the file list is passed to PyCG on the command line, and an
    unstable order would make re-runs non-reproducible for no reason.
    """
    yield from (p for p in sorted(root.rglob("*.py")) if p.is_file() and _is_source(p))


def _package_root(repo: Path, changed: Iterable[Path]) -> Path:
    """The narrowest directory containing every changed file.

    PyCG's --package argument sets the root against which module names are
    resolved, so it decides what a fully-qualified name looks like. Getting it
    wrong does not fail loudly -- it renames every symbol in the graph, and the
    join in classify_exposure.py then matches nothing.
    """
    absolute = [repo / c for c in changed]
    directories = [p.parent for p in absolute]
    if not directories:
        return repo

    common = directories[0]
    for directory in directories[1:]:
        while common != common.parent and directory != common and common not in directory.parents:
            common = common.parent

    # Climb to the outermost enclosing package, so intra-package calls resolve.
    # The condition is on the PARENT: keep going while the directory above is
    # itself a package. Testing `common` instead walks straight past the top of
    # the package into the repository root, which does not fail — it silently
    # renames every symbol in the graph and the join then matches nothing.
    while common != repo and (common.parent / "__init__.py").is_file():
        common = common.parent

    return common if common.is_relative_to(repo) else repo


def resolve(repo: Path, changed_files: Iterable[str]) -> Scope | None:
    """Build the scope for one PR at one checkout.

    Returns None when nothing analysable remains -- a PR touching only
    documentation, configuration or deleted files. That is corpus attrition and
    is counted, not an error.
    """
    changed = [Path(c) for c in changed_files if c.endswith(".py")]
    if not changed:
        return None

    present = [c for c in changed if (repo / c).is_file()]
    if not present:
        return None

    root = _package_root(repo, present)
    files = tuple(iter_python_files(root))
    if not files:
        return None

    return Scope(package_root=root, files=files)
