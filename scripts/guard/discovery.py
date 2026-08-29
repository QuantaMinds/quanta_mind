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

from exclusions import (
    EXCLUDED_DIRS,
    SCOPED_EXCLUDED_DIRS,
    SCOPED_TO,
)

# Directories never inspected. Vendored code is third-party and exempt from our
# style rules; caches are generated; docs are exempt from the line cap by policy.
SOURCE_SUFFIXES: frozenset[str] = frozenset({".py", ".pyi", ".toml", ".yaml", ".yml"})

# The declared layer order. Index position defines what may import what.
#
# The review pipeline left to right. `verify` cannot import `infer`, so the layer adjudicating
# the model's claims cannot start trusting them -- which no naming convention can enforce.
LAYER_ORDER: tuple[str, ...] = (
    "types",
    "store",
    "ingest",
    "parse",
    "rank",
    "allocate",
    "infer",
    "verify",
    "render",
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


def walk(root: Path, *, scoped: bool = False) -> Iterator[Path]:
    """Every file beneath root, in deterministic order, PRUNING excluded directories.

    Pruning during the walk rather than filtering after it. `rglob("*")` enumerates
    everything first, so with a multi-gigabyte clone under `data/` the guards spent
    minutes listing paths they were about to discard -- and the pre-edit hook, which has
    a sixty-second budget, simply timed out. A guard that times out is a guard that gets
    switched off.

    Pre-order, entries sorted by name, so the sequence is byte-identical to the
    `sorted(rglob("*"))` it replaces. That is not cosmetic: guard output is diffed in
    CI, and an ordering change would look like a finding. A stack-based version passed
    the set comparison and silently reordered everything, which is the same
    faster-and-quietly-different failure this walk was written to avoid.
    """
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return  # vanished mid-walk, or unreadable; not this guard's business
    for entry in entries:
        if entry.is_dir():
            if entry.name in EXCLUDED_DIRS:
                continue
            # Scope is inherited: once beneath `research/`, every descendant is in scope.
            inside = scoped or entry.name in SCOPED_TO
            if inside and entry.name in SCOPED_EXCLUDED_DIRS:
                continue
            yield from walk(entry, scoped=inside)
        elif entry.is_file():
            yield entry


def iter_source_files(root: Path) -> Iterator[Path]:
    """Yield every inspectable source file beneath root."""
    for path in walk(root):
        if path.suffix in SOURCE_SUFFIXES:
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
    for path in walk(root):
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_STEMS:
            yield path


def iter_package_dirs(root: Path) -> Iterator[Path]:
    """Yield every non-excluded directory beneath root, pruning as it goes."""
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return
    for entry in entries:
        if entry.is_dir() and entry.name not in EXCLUDED_DIRS:
            yield entry
            yield from iter_package_dirs(entry)


def layer_of(path: Path, package_root: Path) -> str | None:
    """Return the layer name a file belongs to, or None if it sits outside the layers.

    Assumes the layout src/quantamind/<layer>/... declared in ARCHITECTURE.md section 5.
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
