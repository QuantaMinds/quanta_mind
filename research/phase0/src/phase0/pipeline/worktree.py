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

import os
import shutil
import stat
import subprocess
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from git import Repo
from git.exc import GitError, ODBError

GIT_ERRORS = (GitError, ODBError, ValueError)

CLONE_TIMEOUT_S = 900


class CloneFailed(RuntimeError):
    """The repository could not be obtained. Corpus attrition, counted upstream."""


def _clear_readonly(func, path, _exc):  # type: ignore[no-untyped-def]  # shutil.onerror
    """Windows marks git's object files read-only, so unlink fails with EACCES."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _remove_tree(target: Path, *, strict: bool) -> None:
    """Delete a clone, refusing to pretend it worked.

    `shutil.rmtree(..., ignore_errors=True)` was used here and silently did nothing on
    Windows: git's object files are read-only, unlink raises EACCES, and the flag
    swallows it. The directory survived, the NEXT clone failed with "destination path
    already exists", and 19 of 20 PRs came back as unreadable history -- a failure that
    named the wrong cause entirely.

    Strict on the way in, because reusing a stale clone would analyse the wrong tree.
    Lenient on the way out -- but the reason first written here, "a leftover is caught
    by the strict pass on the next attempt", was wrong. The next attempt is a DIFFERENT
    repository, so nothing ever checked, and 1.6 GB of clones accumulated over 41
    repositories. `sweep` is what actually catches them, and it reports the count rather
    than tidying quietly.
    """
    if not target.exists():
        return
    try:
        shutil.rmtree(target, onerror=_clear_readonly)
    except OSError as exc:
        if strict:
            raise CloneFailed(f"{target}: could not remove a stale clone: {exc}") from exc
        return
    if strict and target.exists():
        raise CloneFailed(f"{target}: stale clone survived removal; refusing to reuse it")


def sweep(workspace: Path) -> int:
    """Delete clones a previous run left behind, and say how many there were.

    `cloned` removes leniently on the way out, and the justification written there --
    "a leftover is caught by the strict pass on the next attempt" -- was wrong. The next
    attempt is a DIFFERENT repository, so nothing ever checked. 1.6 GB accumulated over
    41 repositories before anyone looked, and the docstring above warns that disk
    exhaustion arrives at hour thirty of a multi-day run.

    Returning the count rather than cleaning quietly: a run that had to sweep leftovers
    is a run whose previous attempt failed to release file handles, and that is worth
    seeing rather than tidying away.
    """
    if not workspace.is_dir():
        return 0
    swept = 0
    for entry in sorted(workspace.iterdir()):
        if entry.is_dir():
            _remove_tree(entry, strict=False)
            swept += not entry.exists()
    return swept


@contextmanager
def cloned(repo_full_name: str, workspace: Path, keep: bool = False) -> Iterator[Path]:
    """Clone a repository for the duration of the block, then delete it.

    Full history, not shallow: the outcome scan walks seven days FORWARD from the
    merge and A2's rebase rule walks BACKWARD over replayed commits. A shallow
    clone has neither.
    """
    target = workspace / repo_full_name.replace("/", "__")
    _remove_tree(target, strict=True)

    # `git` directly rather than Repo.clone_from(kill_after_timeout=…): GitPython
    # raises "'kill_after_timeout' feature is not supported on Windows" on every call,
    # so the whole study was unrunnable on this platform and every clone came back as
    # attrition. subprocess.run's timeout is portable, and AGENTS.md requires one on
    # every subprocess — dropping the flag to make it work would have removed it.
    try:
        # core.longpaths: Windows caps paths at 260 chars without it, and two AutoGPT
        # PRs failed checkout on a deeply nested frontend route. That surfaced as
        # "unable to access <path>" mid-clone, i.e. as corpus attrition concentrated in
        # repositories with deep trees -- a selection effect, not a random one.
        subprocess.run(
            [
                "git",
                "-c",
                "core.longpaths=true",
                "clone",
                "--quiet",
                f"https://github.com/{repo_full_name}.git",
                str(target),
            ],
            check=True,
            timeout=CLONE_TIMEOUT_S,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        _remove_tree(target, strict=False)
        raise CloneFailed(f"{repo_full_name}: clone exceeded {CLONE_TIMEOUT_S}s") from exc
    except (subprocess.CalledProcessError, OSError) as exc:
        _remove_tree(target, strict=False)
        detail = getattr(exc, "stderr", "") or str(exc)
        raise CloneFailed(f"{repo_full_name}: {str(detail).strip()[:300]}") from exc

    try:
        yield target
    finally:
        if not keep:
            _remove_tree(target, strict=False)


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
        # Closed on every path: an open Repo keeps the pack files mapped on Windows, and
        # the clone this worktree belongs to then cannot be deleted at all.
        with closing(Repo(repo_path)) as repo:
            try:
                repo.git.worktree("add", "--detach", "--force", str(tree), sha)
                created = True
            except GIT_ERRORS:
                yield None
                return
        yield tree
    finally:
        if created:
            try:
                with closing(Repo(repo_path)) as repo:
                    repo.git.worktree("remove", "--force", str(tree))
            except GIT_ERRORS:
                _remove_tree(tree, strict=False)
