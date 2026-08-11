"""Is this worktree actually complete, or did the checkout stop partway?

WHAT: `missing_python` — the `.py` files git says exist at a commit that are ABSENT from
      the worktree checked out at it. `CheckoutUnverifiable` when git could not be asked.
WHY:  A checkout can fail PARTWAY and leave a tree that looks ordinary. `git-lfs` is the
      case that prompted this: `fatal: <path>: smudge filter lfs failed` terminates the
      checkout at the FIRST LFS object, and every file ordered after it is absent whether
      or not it is LFS-tracked -- which is why git reports progress as a percentage
      (`Checking out files: 1% (60/5925)`) rather than naming what it skipped.

      The pilot walk is immune and that was verified, not assumed: every derivation there
      reads the object database (`git diff`, `git show`), and `worktree.cloned` runs
      `git clone` under `check=True`, so a non-zero exit excludes the repository whole.
      **The exposure pass has neither protection.** `run_pipeline.one_pr` materialises a
      real worktree through `worktree.at_commit` and `measure` reads it off the
      filesystem via `scope.resolve`. A partial tree there yields fewer analysable files
      with nothing saying so -- an understated exposure DENOMINATOR, which is the
      quantity the whole coverage claim rests on.

      Added before the exposure pass runs rather than after, because a silent shortfall
      found later is indistinguishable from a repository that genuinely holds less Python.

      **This does NOT reuse `changed._git`.** That helper returns `""` on failure, so a
      `ls-tree` that failed would produce an empty expected set and this check would
      report "nothing missing" -- the same output as a complete tree. Failure raises
      here instead: "we could not look" and "nothing is absent" are different answers.
IMPORTS: stdlib subprocess/pathlib/dataclasses. Nothing from phase0 -- this is a leaf.
CONSUMED BY: run_pipeline.one_pr; tests/pipeline/test_checkout_complete.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

GIT_TIMEOUT_S = 60


class CheckoutUnverifiable(Exception):
    """git could not list the commit's tree. NOT the same as an empty tree."""


def _tree_paths(clone: Path, sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(clone), "ls-tree", "-r", "--name-only", sha],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT_S,
        check=False,
    )
    if result.returncode != 0:
        raise CheckoutUnverifiable(
            f"ls-tree {sha[:10]} failed: {result.stderr.strip()[:200] or 'no stderr'}"
        )
    return result.stdout.splitlines()


def missing_python(tree: Path, clone: Path, sha: str) -> tuple[str, ...]:
    """`.py` paths present in the commit's tree but absent from the worktree.

    Empty means the checkout is complete for Python. It never means "we could not
    check" -- that raises.

    Raises:
        CheckoutUnverifiable: git would not list the tree, so completeness is unknown.
    """
    expected = [path for path in _tree_paths(clone, sha) if path.endswith(".py")]
    return tuple(sorted(path for path in expected if not (tree / path).exists()))
