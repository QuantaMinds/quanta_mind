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

import subprocess
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from git import Repo
from git.exc import GitError, ODBError

from phase0.pipeline.removal import CloneFailed, _remove_tree, sweep

GIT_ERRORS = (GitError, ODBError, ValueError)


# Re-exported: removal owns them, but "talking about clones" is this module.
__all__ = ["CLONE_TIMEOUT_S", "CloneFailed", "at_commit", "cloned", "sweep"]

CLONE_TIMEOUT_S = 900


@contextmanager
def cloned(repo_full_name: str, workspace: Path, keep: bool = False) -> Iterator[Path]:
    """Clone a repository for the duration of the block, then delete it.

    Full history, not shallow: the outcome scan walks seven days FORWARD from the
    merge and A2's rebase rule walks BACKWARD over replayed commits. A shallow
    clone has neither.

    FULL CONTENTS too, and that is a decision rather than a default. A29 added
    `--filter=blob:none` to recover eight repositories that exceeded the clone timeout
    and were the largest -- an 11.5x median size difference, so the exclusion selected
    on the study's own confounder. A31 pre-registered a stop rule before the re-run, the
    known-answer PR came back wrong, and the strategy was ABANDONED rather than patched.

    A blobless clone supplies file CONTENTS only by lazy fetch, and a diff over blobs
    that never arrived is EMPTY rather than wrong. Measured: twelve rejections at
    `derived=0`, three of them labelled `no_python` where GitHub lists 104, 65 and 40
    `.py` files, 17 of 17 scored PRs CLEAN at p=0.0049, and the one PR the probe had
    scored BROKE deriving zero symbols. The harness's own failure wearing a corpus label.

    **The cost of not using it is stated, not hidden:** the eight largest repositories
    stay excluded at `clone_timeout`, A17 keeps that bound, and the 21-plus commit band
    stays unresolved. A worse corpus and a defensible one. `scripts/guard/
    check_no_partial_clone.py` enforces this, because A31 was honoured in prose for a
    day while the flag stayed in this function and two arms were walked under it.
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
                # No --filter. See the docstring and A31: a partial clone defers file
                # contents, and a diff over blobs that never arrived reads as "this PR
                # touched no Python" rather than as a fetch that failed.
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
