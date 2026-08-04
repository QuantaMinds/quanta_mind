"""Clone once per repository; one worktree per parent commit.

WHAT: Clones a repository into a scratch directory, hands out a detached worktree
      per commit, and removes everything afterwards.
WHY:  Three costs decide whether the run finishes.

      1. ~3,300 PRs live in a few hundred repositories. Cloning per PR is the
         single largest avoidable cost in the study, so the clone is per repo and
         the PRs inside it iterate against it.
      2. `git worktree add` rather than `git checkout`. Checkout serialises every
         PR in a repository behind one working tree; worktrees share the object
         store and can be created concurrently, so a repository with 40 PRs does
         not become 40 sequential checkouts.
      3. Clone, run, delete. Keeping every clone would mean hundreds of
         gigabytes; disk exhaustion halfway through a multi-day run is a slow and
         confusing failure, and it arrives at hour 30, not hour 1.
IMPORTS: GitPython, stdlib shutil. Nothing from phase0.
CONSUMED BY: run_pipeline.py; tests/test_worktree.py.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from git import Repo
from git.exc import GitError, ODBError

GIT_ERRORS = (GitError, ODBError, ValueError)

CLONE_TIMEOUT_S = 900


class CloneFailed(RuntimeError):
    """The repository could not be obtained. Corpus attrition, counted upstream."""


@contextmanager
def cloned(repo_full_name: str, workspace: Path, keep: bool = False) -> Iterator[Path]:
    """Clone a repository for the duration of the block, then delete it.

    Full history, not shallow: the outcome scan walks seven days FORWARD from the
    merge and A2's rebase rule walks BACKWARD over replayed commits. A shallow
    clone has neither.
    """
    target = workspace / repo_full_name.replace("/", "__")
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)

    try:
        Repo.clone_from(
            f"https://github.com/{repo_full_name}.git",
            target,
            kill_after_timeout=CLONE_TIMEOUT_S,
        )
    except GIT_ERRORS as exc:
        shutil.rmtree(target, ignore_errors=True)
        raise CloneFailed(f"{repo_full_name}: {exc}") from exc

    try:
        yield target
    finally:
        if not keep:
            shutil.rmtree(target, ignore_errors=True)


@contextmanager
def at_commit(repo_path: Path, sha: str, slot: str) -> Iterator[Path | None]:
    """A detached worktree at `sha`, removed on exit.

    Yields None when the commit is unavailable -- deleted, rewritten, or never
    fetched. That is attrition and the caller records it; it must not raise,
    because one missing commit cannot be allowed to end a multi-day run.
    """
    tree = repo_path.parent / f"{repo_path.name}--wt-{slot}"
    created = False
    try:
        try:
            Repo(repo_path).git.worktree("add", "--detach", "--force", str(tree), sha)
            created = True
        except GIT_ERRORS:
            yield None
            return
        yield tree
    finally:
        if created:
            try:
                Repo(repo_path).git.worktree("remove", "--force", str(tree))
            except GIT_ERRORS:
                shutil.rmtree(tree, ignore_errors=True)
