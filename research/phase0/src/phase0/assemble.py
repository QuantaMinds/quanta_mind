
"""Corpus rows to `PRRecord`, with the file-set gate that A24 made blocking.

WHAT: Given a clone and one candidate PR, resolves the parent, re-derives the changed
      files and symbols from `git diff parent..merged`, and refuses the PR when that
      disagrees with the corpus's own file list.
WHY:  Nothing built a `PRRecord` before this. The pieces existed -- merge metadata,
      parent resolution, the measurement -- with no path from the dataset to the thing
      they all consume.

      The order is forced by a circularity. Parent resolution needs a file list to tell
      a squash from a rebase, but the trustworthy file list is `git diff parent..merged`,
      which needs the parent. So the corpus's list is used ONLY as a heuristic input to
      shape detection, the real list is re-derived once the parent is known, and the two
      are then compared.

      That comparison is not a diagnostic. A24 measured the corpus attributing **92
      distinct `.py` files to a pull request that changed two**, and more than 30 files
      to 15.9% of PRs -- the merge-base diff, not the change. Left unchecked it makes
      `scan_outcome` match almost any later commit, manufacturing breakage in proportion
      to how far the branch had diverged. Since patch size already discriminates at
      AUC 0.957, that is the study's own confounder arriving as measurement error.

      So a PR whose two file sets disagree is **excluded and counted**, never analysed.
      An excluded PR is a number in the attrition table; an analysed one with the wrong
      file set is a wrong answer nobody can see.
IMPORTS: GitPython, phase0.{extract_prs,github_pulls,parent_commit,syntax}.
CONSUMED BY: run_pipeline.py; tests/test_assemble.py.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from phase0.syntax import definitions, parse

GIT_TIMEOUT_S = 120

# Share of the re-derived file set that the corpus's list must cover, and vice versa.
# Set from A24's measurement: the median PR has 4 files and agrees, while the long tail
# disagrees by an order of magnitude. Anything short of near-identity is a divergent
# base, not a rounding difference.
MIN_FILE_AGREEMENT = 0.6

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")


@dataclass(frozen=True, slots=True)
class Rejection:
    """Why a PR did not become a record. Counted, never silently dropped."""

    pr_id: str
    stage: str
    reason: str
    agreement: float = -1.0


def _git(clone: Path, *args: str) -> str:
    """Read-only git, with the timeout AGENTS.md requires on every subprocess."""
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


def touched_line_ranges(clone: Path, parent: str, merged: str, path: str) -> list[tuple[int, int]]:
    """Line ranges on the PARENT side that the change modified.

    `-U0` so the ranges are the edits themselves rather than edits plus context; context
    lines would attribute a change to whichever symbol happened to sit next to it.
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


def _module_name(path: str) -> str:
    stem = path[:-3] if path.endswith(".py") else path
    parts = [p for p in stem.replace("\\", "/").split("/") if p and p != "__init__"]
    return ".".join(parts)


def symbols_touched(source: str, ranges: list[tuple[int, int]], module: str) -> set[str]:
    """Qualified names of definitions whose body overlaps a changed range.

    Parsed at the PARENT, because the study asks what a caller could have known before
    the change landed. A symbol added by the PR has no pre-existing callers and is not
    what the exposure variable is about.
    """
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


def _function_nodes(root: object) -> list[object]:
    stack, out = [root], []
    while stack:
        node = stack.pop()
        if getattr(node, "type", "") == "function_definition":
            out.append(node)
        stack.extend(getattr(node, "children", []))
    return out


def file_agreement(corpus: frozenset[str], derived: frozenset[str]) -> float:
    """Jaccard overlap of the two file sets. 1.0 when they are identical.

    Both empty counts as agreement: a PR with no Python either side is consistent, and
    it is excluded upstream for having nothing to measure rather than for disagreeing.
    """
    if not corpus and not derived:
        return 1.0
    union = corpus | derived
    return len(corpus & derived) / len(union) if union else 1.0
