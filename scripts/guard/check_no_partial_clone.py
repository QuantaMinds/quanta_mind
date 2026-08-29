"""Reject a `--filter` on any git clone. A partial clone defers file contents.

WHAT: Scans every `git clone` argument list in the source trees for a `--filter`
      option, in any form: a literal `--filter=blob:none`, a separated
      `"--filter", "blob:none"`, or an f-string building either.
WHY:  A29 adopted `--filter=blob:none` to recover eight repositories that exceeded the
      clone timeout. A31 pre-registered a stop rule BEFORE the re-run, the known-answer
      PR came back wrong, and the strategy was ABANDONED rather than patched. The
      amendment log recorded the withdrawal. **The flag stayed in the code.**

      That commit touched thirteen files -- documentation and results, no source. For a
      day the repository's own amendment log said one thing and `pipeline/worktree.py`
      did another, and two pilot arms were walked under the abandoned strategy. Its
      documented failure mode is that a diff over blobs which never arrived is EMPTY
      rather than wrong, so the harness records `no_python` -- a claim about the
      repository -- when the truth is a lazy fetch returned nothing. An agent-arm
      `no_python` rate of 18.1% against the human arm's 4.0% was read as a population
      difference. It is this bug's signature.

      This is a different failure class from every other guard here. The others catch
      code producing a wrong VALUE. This catches code and documentation DISAGREEING,
      with the documentation authoritative and unenforced -- a rule that was a wish, in
      a project whose whole thesis is that unenforced claims decay silently.

      Deliberately general rather than blobless-specific. `--filter=tree:0` and
      `--filter=blob:limit=1m` defer contents the same way and would reintroduce the
      same class; a guard naming only `blob:none` would pass the next variant.
IMPORTS: scripts/guard/discovery.py; stdlib ast. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import ast
import sys

from coverage import assert_examined
from discovery import Violation, iter_python_files, project_root, report

SCANNED_ROOTS = ("src", "research/phase0/src", "scripts")
FILTER = "--filter"
# The one file allowed to mention the flag: the guard describing what it bans, and the
# test proving it fires. Matched on path suffix so a rename has to be deliberate.
SELF = "scripts/guard/check_no_partial_clone.py"


def _mentions_filter(node: ast.AST) -> bool:
    """True if this expression can produce a string beginning `--filter`.

    Constants and f-strings both, because `f"--filter={mode}"` is the obvious way to
    reintroduce this while passing a check that only compares literals.
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and node.value.startswith(FILTER)
    if isinstance(node, ast.JoinedStr):
        first = node.values[0] if node.values else None
        return (
            isinstance(first, ast.Constant)
            and isinstance(first.value, str)
            and first.value.startswith(FILTER)
        )
    return False


def _is_clone_command(elements: list[ast.expr]) -> bool:
    """True if this list is a git clone argument vector."""
    literals = [
        e.value for e in elements if isinstance(e, ast.Constant) and isinstance(e.value, str)
    ]
    return "git" in literals and "clone" in literals


def check(root_names: tuple[str, ...] = SCANNED_ROOTS) -> list[Violation]:
    root = project_root()
    violations: list[Violation] = []
    for name in root_names:
        base = root / name
        if not base.is_dir():
            continue
        for path in iter_python_files(base):
            if str(path).replace("\\", "/").endswith(SELF):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.List, ast.Tuple)):
                    continue
                if not _is_clone_command(list(node.elts)):
                    continue
                for element in node.elts:
                    if _mentions_filter(element):
                        violations.append(
                            Violation(
                                path=path,
                                line=getattr(element, "lineno", node.lineno),
                                rule="partial-clone",
                                detail=(
                                    "git clone carries a --filter. A partial clone defers file "
                                    "CONTENTS, so a diff over blobs that never arrived is empty "
                                    "and gets recorded as 'no_python' -- a claim about the "
                                    "repository. Abandoned by A31; see worktree.cloned."
                                ),
                            )
                        )
    return violations


# **A FLOOR, NOT A TARGET.** 29 source files carry a clone call today. Set well below that, so
# it fires when discovery collapses rather than when the count drifts.
CLONE_FILE_FLOOR = 10


def main() -> int:
    root = project_root()
    found = check()
    assert_examined(
        "files scanned for a git clone",
        sum(1 for _ in iter_python_files(root)),
        CLONE_FILE_FLOOR,
        root,
    )
    return report(found, root, "no-partial-clone")


if __name__ == "__main__":
    sys.exit(main())
