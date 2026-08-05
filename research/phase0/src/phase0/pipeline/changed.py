"""What a change actually touched, read from the tree rather than from the corpus.

WHAT: Files and symbols between two commits, plus the overlap measure that decides
      whether the corpus's own file list can be trusted for a given PR.
WHY:  Split from `assemble.py` because reading a diff and deciding whether a PR is
      admissible are different concerns, and only the second is a judgement.

      Everything here is deliberately derived from `git diff parent..merged`. A24
      measured the corpus attributing **92 distinct `.py` files to a pull request that
      changed two**, and more than 30 files to 15.9% of PRs -- it records the merge-base
      diff, not the change. Believing it would make the outcome scan match almost any
      later commit, in proportion to how far the branch had diverged.

      Symbols are parsed at the PARENT. The exposure variable asks what a caller could
      have known before the change landed, so a symbol the PR introduces has no
      pre-existing callers and is not what is being measured.
IMPORTS: stdlib subprocess, re; phase0.syntax.
CONSUMED BY: pipeline/assemble.py; tests/pipeline/test_assemble.py.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tree_sitter import Node

from phase0.syntax import definitions, parse

GIT_TIMEOUT_S = 120

# `@@ -12,3 +12,4 @@` -- the old-side range is what maps onto the parent's symbols.
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")


def _git(clone: Path, *args: str) -> str:
    """Read-only git. Returns empty on failure: a missing path is data, not an error."""
    result = subprocess.run(
        ["git", "-C", str(clone), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT_S,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def changed_python_files(clone: Path, parent: str, merged: str) -> tuple[str, ...]:
    """The `.py` files the change actually touched, from the tree, not the corpus."""
    out = _git(clone, "diff", "--name-only", f"{parent}..{merged}")
    return tuple(sorted(line for line in out.splitlines() if line.endswith(".py")))


def source_at(clone: Path, commit: str, path: str) -> str:
    """A file's contents at a commit, or empty when it did not exist there."""
    return _git(clone, "show", f"{commit}:{path}")


def touched_line_ranges(clone: Path, parent: str, merged: str, path: str) -> list[tuple[int, int]]:
    """Line ranges on the PARENT side that the change modified.

    `-U0` so the ranges are the edits themselves and not edits plus context; context
    lines would attribute a change to whichever symbol happened to sit beside it.
    """
    out = _git(clone, "diff", "-U0", f"{parent}..{merged}", "--", path)
    ranges: list[tuple[int, int]] = []
    for line in out.splitlines():
        found = HUNK.match(line)
        if found:
            start = int(found.group(1))
            length = int(found.group(2) or "1")
            if length:
                ranges.append((start, start + length - 1))
    return ranges


def module_name(path: str) -> str:
    """`src/pkg/mod.py` -> `src.pkg.mod`; `pkg/__init__.py` -> `pkg`."""
    stem = path[:-3] if path.endswith(".py") else path
    parts = [p for p in stem.replace("\\", "/").split("/") if p and p != "__init__"]
    return ".".join(parts)


def _function_nodes(root: Node) -> list[Node]:
    stack, out = [root], []
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            out.append(node)
        stack.extend(node.children)
    return out


def symbols_touched(source: str, ranges: list[tuple[int, int]], module: str) -> set[str]:
    """Qualified names of definitions whose body overlaps a changed range."""
    if not ranges or not source.strip():
        return set()
    try:
        root, raw = parse(source)
    except (ValueError, RuntimeError):
        return set()

    by_short = definitions(root, raw)
    if not by_short:
        return set()

    found: set[str] = set()
    for node in _function_nodes(root):
        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        short = raw[name_node.start_byte : name_node.end_byte].decode("utf-8", "replace")
        first, last = node.start_point[0] + 1, node.end_point[0] + 1
        if any(first <= end and start <= last for start, end in ranges):
            qualified = by_short.get(short, short)
            found.add(f"{module}.{qualified}" if module else qualified)
    return found


def file_agreement(corpus: frozenset[str], derived: frozenset[str]) -> float:
    """Jaccard overlap of the two file sets. 1.0 when they are identical.

    Both empty counts as agreement: a PR with no Python either side is consistent, and
    is excluded upstream for having nothing to measure rather than for disagreeing.
    """
    if not corpus and not derived:
        return 1.0
    union = corpus | derived
    return len(corpus & derived) / len(union) if union else 1.0
