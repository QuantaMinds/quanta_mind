"""Which directories the guards never look inside, and which only under `research/`.

WHAT: `EXCLUDED_DIRS`, the scoped pair, and `is_excluded(path)`.
WHY:  Split from `discovery.py`, which walks and filters. This decides WHAT is out of bounds;
      that decides how to reach the rest. The seam matters because every one of the 23 guards
      draws its population through here, so a change to this file changes all of them at once —
      and it should be reviewable without reading a traversal.

      **`data` AND `results` ARE SCOPED, NOT BARE NAMES.** They matched at any depth, so a
      directory with either name hid its contents from every guard simultaneously with nothing
      reporting it: source under `src/quantamind/data/` would simply have been unguarded. Every
      such directory in this repository is under `research/phase0/`, so scoping them costs no
      pruning — the harness clones that once timed out the pre-edit hook are still skipped.
IMPORTS: stdlib pathlib. No project imports.
CONSUMED BY: `discovery.py`, `check_structure.py`, `records/check_docs_sync.py`;
             tests/unit/test_guard_exclusions.py.
"""

from __future__ import annotations

from pathlib import Path

EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        # Generated and unbounded like the other caches; the cap was firing on it.
        ".hypothesis",
        "vendor",
        "martian",  # Martian's benchmark data, vendored off /private/tmp. Not ours to police.
        "node_modules",
        "htmlcov",
        "dist",
        "build",
        ".verify-clone",
    }
)

# **`data` AND `results` ARE EXCLUDED ONLY BENEATH `research/`, NOT BY NAME ANYWHERE.**
# They were bare names, so a directory with either name hid its contents from ALL 23 guards at
# any depth, with nothing reporting it -- source under `src/quantamind/data/` would simply have
# been unguarded. Every such directory in this repository is under `research/phase0/`, so
# scoping costs no pruning: the harness clones and run outputs that made the pre-edit hook time
# out are still skipped, and the blind spot over product code is closed.
SCOPED_TO: tuple[str, ...] = ("research",)
SCOPED_EXCLUDED_DIRS: frozenset[str] = frozenset({"data", "results"})

# Extensions subject to the length and structure rules. Markdown and text are
# deliberately absent: docs are exempt.


def is_excluded(path: Path) -> bool:
    """True if any path component is an excluded directory.

    A scoped name counts only when the path also passes through the root it is scoped to, so
    `research/phase0/data/` is excluded and a hypothetical `src/quantamind/data/` is not.
    """
    parts = path.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    return any(part in SCOPED_EXCLUDED_DIRS for part in parts) and any(
        part in SCOPED_TO for part in parts
    )
