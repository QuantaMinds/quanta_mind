"""Branch naming guard.

WHAT: Fails when the current branch does not match the scheme in CONTRIBUTING.md:
      feat/ fix/ chore/ docs/ spike/, with fix/ requiring a leading issue number.
WHY:  One change, one branch, one PR. The prefix is what makes the history
      readable after a squash merge, and the issue number on fix/ is what ties a
      fix to the report that motivated it -- CONTRIBUTING.md requires a failing
      test referencing an issue, and a branch that cannot name the issue usually
      means there is not one.

      This runs in CI rather than as a hook because a hook fires on file edits,
      by which point the branch already exists. `main` is exempt: CI also runs on
      the protected branch after a merge.
IMPORTS: scripts/guard/discovery.py; stdlib re, subprocess. No project imports.
CONSUMED BY: .github/workflows/guards.yml.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from discovery import Violation, report

PATTERN = re.compile(r"^(feat|fix|chore|docs|spike)/[a-z0-9][a-z0-9._-]*$")

# fix/ must reference an issue: fix/412-super-chain-dropped
FIX_PATTERN = re.compile(r"^fix/\d+-[a-z0-9][a-z0-9._-]*$")

EXEMPT: frozenset[str] = frozenset({"main", "HEAD"})

GIT_TIMEOUT_S = 30


def current_branch(root: Path) -> str | None:
    """The checked-out branch name, or None in a detached or non-git tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def check(root: Path, branch: str) -> list[Violation]:
    """Validate one branch name against the scheme."""
    if branch in EXEMPT:
        return []

    target = root / "CONTRIBUTING.md"
    if not PATTERN.match(branch):
        return [
            Violation(
                target,
                1,
                "branch-name",
                f"branch {branch!r} does not match "
                f"(feat|fix|chore|docs|spike)/<lowercase-description>. "
                f"See CONTRIBUTING.md.",
            )
        ]
    if branch.startswith("fix/") and not FIX_PATTERN.match(branch):
        return [
            Violation(
                target,
                1,
                "branch-name-missing-issue",
                f"branch {branch!r} is a fix without an issue number. Use "
                f"fix/<issue>-<short>, e.g. fix/412-super-chain-dropped. A fix with no "
                f"issue usually means the failing test was never written down.",
            )
        ]
    return []


def main(argv: list[str]) -> int:
    """Check the current branch, or one named on the command line."""
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    branch = argv[2] if len(argv) > 2 else current_branch(root)

    if branch is None:
        print("[branch-name] not a git checkout, or detached HEAD; skipping")
        return 0

    return report(check(root, branch), root, "branch-name")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
