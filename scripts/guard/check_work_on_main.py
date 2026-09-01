"""Work on `main` is caught however it was made, not only when a tool made it.

WHAT: fails when `main` is checked out and carries uncommitted changes to tracked files, or
      commits that `origin/main` does not have. Silent on any other branch, and silent on a clean
      `main` that matches its remote — which is what CI sees after a merge.
WHY:  **`hook_pre_edit.py` DENIES WRITES ON `main` AND IS SCOPED TO `"matcher": "Write|Edit"`.**
      It never sees `Bash`, so `sed -i`, a heredoc, `python -c` or `cat >` edits `main` with the
      hook none the wiser. That is not hypothetical: this guard exists because
      `docs/engineering/CORRECTIONS.md` entry 14 was written onto `main` through a Bash heredoc,
      by the same author who had just filed an entry about rules with no mechanism behind them.

      **A HOOK CANNOT COVER BASH AND A GUARD DOES NOT HAVE TO.** Enumerating every shell
      construction that writes a file is a losing game — a hook would have to understand `tee`,
      `>>`, `install`, `git checkout --`, and whatever is invented next. This looks at the RESULT
      instead: whatever produced the change, the tree is dirty or the branch is ahead, and both are
      visible to `git`. Detection after the fact rather than prevention before it, which is weaker
      and is the strongest thing available.

      **IT DOES NOT FIRE IN CI.** After a merge, `main` is clean and equal to `origin/main`, so a
      workflow checking out `main` sees nothing. A guard that failed every CI run on the default
      branch would be turned off within a day.

      **UNCOMMITTED CHANGES AND UNPUSHED COMMITS ARE SEPARATE FINDINGS.** They are different
      mistakes — one is "you are editing the wrong branch", the other is "you have already
      committed to it" — and the second needs a different remedy, so they are not collapsed into
      one message about "work on main".
IMPORTS: scripts/guard/discovery.py; stdlib subprocess.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from discovery import Violation, report

PROTECTED = "main"
REMOTE = "origin/main"
GIT_TIMEOUT_S = 30


def _git(root: Path, *args: str) -> str | None:
    """One git command's stdout, or None when git could not answer."""
    try:
        done = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def check_work_on_main(root: Path) -> list[Violation]:
    """Uncommitted changes or unpushed commits while `main` is checked out."""
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != PROTECTED:
        return []

    violations: list[Violation] = []
    # **`--name-only`, NOT `--porcelain`.** Porcelain's two-column status prefix is fixed-width and
    # begins with a space for an unstaged change, and `_git` strips its output — so ` M AGENTS.md`
    # arrived as `M AGENTS.md` and a slice past the prefix reported `GENTS.md`. A helper that
    # normalises whitespace is right for every other caller and wrong for a format whose first
    # column IS whitespace. `--name-only` has no prefix to mis-slice, so the class is gone rather
    # than the instance. Untracked files are excluded on purpose: a scratch file on main is not a
    # change to main, and refusing it would be noise.
    dirty = _git(root, "diff", "--name-only", "HEAD")
    if dirty:
        names = dirty.splitlines()
        touched = names[:5]
        more = len(names) - len(touched)
        violations.append(
            Violation(
                root / "AGENTS.md",
                1,
                "uncommitted-on-main",
                f"{len(names)} tracked file(s) modified while `main` is checked out: "
                f"{', '.join(touched)}{f' and {more} more' if more > 0 else ''}. "
                f"AGENTS.md rule 9: branch per change. `hook_pre_edit` denies Write and Edit here "
                f"and cannot see Bash, which is how this got past it before.",
            )
        )

    # `origin/main` may be absent in a fresh clone or a CI checkout; that is not a violation.
    ahead = _git(root, "rev-list", "--count", f"{REMOTE}..HEAD")
    if ahead and ahead.isdigit() and int(ahead) > 0:
        violations.append(
            Violation(
                root / "AGENTS.md",
                1,
                "committed-to-main",
                f"{ahead} commit(s) on `main` that {REMOTE} does not have. Rule 9 forbids direct "
                f"commits to main; move them to a branch with `git branch <name> && git reset "
                f"--hard {REMOTE}` before they are pushed.",
            )
        )
    return violations


def main(root: Path) -> int:
    return report(check_work_on_main(root), root, "work-on-main")


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
