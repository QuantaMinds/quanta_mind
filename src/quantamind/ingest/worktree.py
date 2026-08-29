"""The change a developer has made but not yet committed, or not yet pushed.

WHAT: `pending(clone)` returns what is uncommitted; `unpushed(clone, base)` returns what a branch
      adds over its merge-base. Both give the changed paths and the diff, and say which they found.
WHY:  **A REVIEW THAT NEEDS A COMMIT ARRIVES TOO LATE TO BE CHEAP.** By the time a pull request
      exists the developer has stopped, context-switched, and asked other people to look. The
      cheapest place to be wrong about a change is the machine that made it, ten seconds after
      writing it, where a wrong finding costs nothing and a right one costs one edit.

      **UNCOMMITTED FIRST, THEN THE BRANCH, BECAUSE THAT IS THE ORDER OF WHAT IS AT RISK.** Edits
      in the working tree are what the developer is holding right now. A clean tree means the work
      is committed but not yet proposed, and the branch against its merge-base is that change.

      **UNTRACKED FILES ARE INCLUDED, AND THEY ARE THE MOST LIKELY TO BE NEW CODE.** `git diff`
      omits them entirely, so a review that used it alone would silently skip every file the
      developer just created — which on a feature branch is most of what they wrote.

      **NOTHING LEAVES THE MACHINE ON THIS PATH.** No API call, no pull request, no clone. That is
      also the honest answer to "can this run air-gapped", and it is why the local path can read a
      convention file the endpoint structurally cannot.
IMPORTS: stdlib only. Same layer as the rest of `ingest/`.
CONSUMED BY: `serve/run_commit.py`, for `quantamind review` without a commit.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

GIT_TIMEOUT_S = 120


class NothingPending(RuntimeError):
    """No uncommitted work and no unpushed commits. Not an error — a state worth naming."""


@dataclass(frozen=True, slots=True)
class Pending:
    """What is under review, and where it came from. `origin` renders into the report."""

    paths: tuple[str, ...]
    diff: str
    origin: str

    def __post_init__(self) -> None:
        if not self.paths:
            raise ValueError("a Pending with no paths is NothingPending; raise that instead")


def _git(clone: Path, *args: str, ok: tuple[int, ...] = (0,)) -> str:
    """git's stdout, or empty when it failed.

    **`ok` EXISTS BECAUSE `git diff --no-index` EXITS 1 WHEN THE FILES DIFFER**, which for a diff
    is success. Treating that as failure discarded the contents of every untracked file — the
    review then listed a new file by name and showed the model none of its code, which reads as a
    clean review of a file nobody looked at. Caught by a test, not by reading.
    """
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    return done.stdout if done.returncode in ok else ""


def _uncommitted(clone: Path) -> tuple[list[str], str]:
    """Tracked edits plus untracked files. **Untracked is where new code lives.**"""
    tracked = [p for p in _git(clone, "diff", "--name-only", "HEAD").splitlines() if p.strip()]
    untracked = [
        p
        for p in _git(clone, "ls-files", "--others", "--exclude-standard").splitlines()
        if p.strip()
    ]
    diff = _git(clone, "diff", "HEAD")
    for path in untracked:
        # `git diff` cannot show a file git does not know about, so it is diffed against nothing.
        diff += _git(clone, "diff", "--no-index", "--", "/dev/null", path, ok=(0, 1))
    return sorted(set(tracked) | set(untracked)), diff


def pending(clone: Path, base: str = "") -> Pending:
    """Whatever this developer has that nobody has reviewed. Uncommitted first, then the branch."""
    paths, diff = _uncommitted(clone)
    if paths:
        return Pending(tuple(paths), diff, "uncommitted changes in your working tree")

    target = base or _default_branch(clone)
    merge_base = _git(clone, "merge-base", "HEAD", target).strip()
    if not merge_base:
        raise NothingPending(f"no uncommitted work, and no merge-base with {target!r}")
    committed = [
        p
        for p in _git(clone, "diff", "--name-only", f"{merge_base}..HEAD").splitlines()
        if p.strip()
    ]
    if not committed:
        raise NothingPending(f"no uncommitted work, and nothing on this branch beyond {target}")
    return Pending(
        tuple(sorted(committed)),
        _git(clone, "diff", f"{merge_base}..HEAD"),
        f"commits on this branch since {target}",
    )


def _default_branch(clone: Path) -> str:
    """`main` unless the repository says otherwise. Guessing wrong only changes the base."""
    head = _git(clone, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
    if head:
        return head.rsplit("/", 1)[-1]
    return "main" if _git(clone, "rev-parse", "--verify", "--quiet", "main").strip() else "master"
