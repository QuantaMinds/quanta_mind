"""Reject two modules that claim the same name, and modules nothing imports.

WHAT: Two checks over each package. Duplicate basenames across a package tree, and
      modules unreachable from any import inside their own tree.
WHY:  A stale `assemble.py` survived a split and a commit. `git mv` was not used, so git
      tracked both copies; nothing imported the old name; every guard passed. The copy
      that stayed behind was missing `CATEGORIES` and the `no_symbols` rejection — the
      two things the entire attrition analysis rests on. It was caught only because the
      directory-fanout count happened to tip over, which is not what that rule is for.

      This is the third instance of one pattern in this codebase: an absence that is not
      typed, so it reads as a result. An uncomputable control scored as a pass. A
      type-mismatched join returned zero rows and read as "no data". A stale duplicate
      read as the live module. Each was found by accident; this closes the class.

      Both checks are deliberately syntactic. Resolving imports properly needs the
      package installed, and guards run before that — `discovery.py` says so. A
      basename collision inside one package is almost always a mistake, and a module
      nobody names is either dead or about to be edited by mistake.
IMPORTS: scripts.guard.discovery, stdlib ast.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

from coverage import assert_examined, guarded, refuse_path_argument
from discovery import Violation, iter_python_files, project_root, report

# Package roots scanned independently. A name may legitimately repeat across them —
# `tests/pipeline/test_assemble.py` mirrors `src/phase0/pipeline/assemble.py` on purpose.
PACKAGE_ROOTS = ("src", "research/phase0/src")

# **DIRECTORIES SEVERAL SCRIPTS PUT ON sys.path TOGETHER.** A repeated basename ACROSS package
# roots is fine -- tests mirror sources on purpose. A repeated basename across these is not: they
# are flat directories added by `sys.path.insert(0, ...)` in the same file, so which one wins is
# decided by INSERT ORDER and nothing reports the choice. `bench/corpus.py` and `quote/corpus.py`
# both exist; `run_gate.py` listed bench first, so `import corpus` silently got quote's, whose API
# differs. There is no error -- the wrong module loads and the failure surfaces somewhere else, or
# does not surface at all and a plausible number is computed from the wrong data.
SYS_PATH_GROUP = ("research/phase0/bench", "research/phase0/quote", "research/phase0/vertex")

# Conventional files nothing imports by name. Command-line entry points are detected
# structurally instead — see `_is_entry_point`.
UNIMPORTED_BY_DESIGN = frozenset({"__init__", "__main__", "conftest"})


def _is_entry_point(path: Path) -> bool:
    """True for a module run as `python -m`, which nothing is expected to import.

    Detected from the `if __name__ == "__main__":` guard rather than an allow-list. A
    list would need maintaining, and the first time somebody forgot to update it the
    guard would report a real entry point as dead code — which trains people to ignore
    it, and an ignored guard enforces nothing.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
        ):
            return True
    return False


def _module_names(path: Path) -> set[str]:
    """Every bare module name this file imports, however it spells the import."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.update(node.module.split("."))
            found.update(alias.name for alias in node.names)
    return found


def duplicate_basenames(root: Path) -> list[Violation]:
    """Two modules with the same name inside one package tree."""
    violations: list[Violation] = []
    for package in PACKAGE_ROOTS:
        base = root / package
        if not base.is_dir():
            continue
        by_name: dict[str, list[Path]] = defaultdict(list)
        for path in iter_python_files(base):
            if path.stem not in UNIMPORTED_BY_DESIGN:
                by_name[path.stem].append(path)
        for name, paths in sorted(by_name.items()):
            if len(paths) > 1:
                others = ", ".join(str(p.relative_to(root)) for p in paths[1:])
                violations.append(
                    Violation(
                        paths[0],
                        1,
                        "duplicate-module",
                        f"{name!r} is defined more than once in {package}: also {others}. "
                        f"One of them is stale, and callers cannot tell which.",
                    )
                )
    return violations


def unreferenced_modules(root: Path) -> list[Violation]:
    """Modules no sibling imports. Usually a leftover from a move."""
    violations: list[Violation] = []
    for package in PACKAGE_ROOTS:
        base = root / package
        if not base.is_dir():
            continue
        files = list(iter_python_files(base))
        referenced: set[str] = set()
        for path in files:
            referenced |= _module_names(path)
        # Anything outside the package may import it too, so scan the whole repository
        # for the name before calling a module dead.
        for path in iter_python_files(root):
            if not path.is_relative_to(base):
                referenced |= _module_names(path)

        for path in sorted(files):
            if path.stem in UNIMPORTED_BY_DESIGN or path.stem in referenced:
                continue
            if _is_entry_point(path):
                continue
            violations.append(
                Violation(
                    path,
                    1,
                    "unreferenced-module",
                    f"nothing imports {path.stem!r}. Either it is a leftover from a "
                    f"move, or its consumer was deleted — say which by removing it or "
                    f"importing it.",
                )
            )
    return violations


def shared_path_collisions(root: Path) -> list[Violation]:
    """One module name in two directories that get added to sys.path together."""
    seen: dict[str, Path] = {}
    out: list[Violation] = []
    for rel in SYS_PATH_GROUP:
        d = root / rel
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name == "__init__.py":
                continue
            first = seen.get(f.stem)
            if first is None:
                seen[f.stem] = f
                continue
            out.append(
                Violation(
                    f,
                    1,
                    "module-identity",
                    f"`{f.stem}` also exists at {first.relative_to(root)}. Both directories are "
                    f"put on sys.path by the same scripts, so `import {f.stem}` resolves by "
                    f"INSERT ORDER and nothing reports which one won. Rename one, or import it "
                    f"by an explicit path.",
                )
            )
    return out


def main() -> int:
    root = project_root()
    found = duplicate_basenames(root) + unreferenced_modules(root) + shared_path_collisions(root)
    assert_examined("python modules", sum(1 for _ in root.rglob("*.py")), 40, root)
    return report(found, root, "module-identity")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "module-identity") or guarded(lambda: main()))
