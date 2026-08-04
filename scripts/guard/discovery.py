"""Shared source-file discovery for every guard script.

WHAT: Enumerates the files each guard is allowed to inspect, and defines the single
      authoritative exclusion list (vendored code, caches, virtualenvs, docs).
WHY:  Every guard previously walked the tree itself. They drifted, and a guard that
      silently skips a directory is exactly the class of silent failure this project
      exists to eliminate. One walker, one exclusion list, one place to audit.
IMPORTS: stdlib only (pathlib, typing). No project imports — guards must run before
      the package is installable.
CONSUMED BY: every module in scripts/guard/.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Directories never inspected. Vendored code is third-party and exempt from our
# style rules; caches are generated; docs are exempt from the line cap by policy.
EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "vendor",
        "node_modules",
        "htmlcov",
        "dist",
        "build",
        # Scratch corpora. The research harness clones real third-party repositories
        # into research/phase0/data/ and deletes them when the run ends. While a run is
        # in flight the guards were walking into them and crashing -- on a 300-character
        # AutoGPT path, and on a read-only sqlmesh file mid-deletion. Every hook then
        # fails for reasons that have nothing to do with the edit that triggered it,
        # which is how guards get switched off.
        "data",
        "results",
    }
)

# Extensions subject to the length and structure rules. Markdown and text are
# deliberately absent: docs are exempt.
SOURCE_SUFFIXES: frozenset[str] = frozenset({".py", ".pyi", ".toml", ".yaml", ".yml"})

# The declared layer order. Index position defines what may import what.
LAYER_ORDER: tuple[str, ...] = (
    "types",
    "discover",
    "ingest",
    "resolve",
    "probe",
    "label",
    "store",
    "serve",
)


@dataclass(frozen=True, slots=True)
class Violation:
    """A single guard failure, rendered as one line of CI output."""

    path: Path
    line: int
    rule: str
    detail: str

    def render(self, root: Path) -> str:
        rel = self.path.relative_to(root) if self.path.is_relative_to(root) else self.path
        return f"{rel}:{self.line}: [{self.rule}] {self.detail}"


def project_root() -> Path:
    """The repository root, independent of the current working directory.

    Claude Code sets CLAUDE_PROJECT_DIR for hook commands. Falling back to cwd is
    wrong for hooks: an agent that has cd'd into research/phase0 would resolve
    paths against that directory, and the hook would silently do nothing or fail.
    A hook that does not run is a rule that is not enforced, which is the whole
    failure mode this directory exists to prevent.
    """
    declared = os.environ.get("CLAUDE_PROJECT_DIR")
    if declared:
        candidate = Path(declared)
        if candidate.is_dir():
            return candidate.resolve()
    return Path.cwd().resolve()


def is_excluded(path: Path) -> bool:
    """True if any path component is an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_source_files(root: Path) -> Iterator[Path]:
    """Yield every inspectable source file beneath root, in deterministic order.

    Deterministic ordering matters: guard output is diffed in CI, and a nondeterministic
    walk produces spurious diffs that train people to ignore guard output.
    """
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        yield path


def iter_python_files(root: Path) -> Iterator[Path]:
    """Yield only Python source files."""
    for path in iter_source_files(root):
        if path.suffix == ".py":
            yield path


# Prose lives in .md and .lock as much as in .py, and a reference that stops resolving
# does so wherever it was written. check_no_vague_refs.py needs the wider net.
TEXT_SUFFIXES: frozenset[str] = SOURCE_SUFFIXES | frozenset({".md", ".lock", ".cfg"})
TEXT_STEMS: frozenset[str] = frozenset({"justfile", "Justfile", "Makefile"})


def iter_text_files(root: Path) -> Iterator[Path]:
    """Yield every human-readable tracked file, source and prose alike."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_excluded(path):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_STEMS:
            yield path


def iter_package_dirs(root: Path) -> Iterator[Path]:
    """Yield every non-excluded directory beneath root."""
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not is_excluded(path):
            yield path


def layer_of(path: Path, package_root: Path) -> str | None:
    """Return the layer name a file belongs to, or None if it sits outside the layers.

    Assumes the layout src/qmctx/<layer>/... declared in ARCHITECTURE.md section 5.
    """
    try:
        rel = path.relative_to(package_root)
    except ValueError:
        return None
    if not rel.parts:
        return None
    candidate = rel.parts[0]
    return candidate if candidate in LAYER_ORDER else None


def report(violations: list[Violation], root: Path, rule_name: str) -> int:
    """Print violations and return a process exit code.

    Returns 0 when clean, 1 otherwise. Guards never raise on violations — a traceback
    hides the finding, and the finding is the point.
    """
    if not violations:
        print(f"[{rule_name}] ok")
        return 0
    print(f"[{rule_name}] {len(violations)} violation(s):", flush=True)
    for violation in violations:
        print(f"  {violation.render(root)}", flush=True)
    return 1
