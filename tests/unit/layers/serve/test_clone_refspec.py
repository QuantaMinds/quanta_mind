"""A repository with a branch under `pr/` must still clone. It could not, and the failure was total.

WHAT: Builds a real local repository carrying BOTH a branch named `pr/1` and a `refs/pull/1/head`,
      then runs the refspec pair `working_clone.ensure()` fetches with.
WHY:  **THIS IS A REAL REPOSITORY'S REAL FAILURE, NOT A HYPOTHETICAL.** Pull heads used to map to
      `refs/remotes/origin/pr/*`, which is the same destination git computes for a branch called
      `pr/1`. Git refuses the ENTIRE fetch:

          fatal: Cannot fetch both refs/heads/pr/1 and refs/pull/1/head to refs/remotes/origin/pr/1

      `ensure()` turns a non-zero fetch into `CloneFailed` and never falls back to a stale clone --
      correctly -- so for such a repository the webhook's delivery path could not obtain a clone at
      all, and every review of it failed. discourse/discourse hit it on the first live run of the
      shape harness.

      **IT IS A LOCAL REPOSITORY ON PURPOSE.** The bug is in a refspec, git settles it offline, and
      a test that needed the network to prove a string collision would not be run.
**WHAT THIS DOES NOT COVER, SAID PLAINLY:** it drives the refspec, not `ensure()`. `ensure()`
      builds `https://github.com/{repo}` and so cannot be pointed at a local repository, which
      means the collision is pinned here and the wiring of it is pinned only by the live delivery
      test. If someone changes the refspec string in `working_clone.py` without changing it here,
      these tests still pass — they are a guard on the git behaviour, not on the call site.
IMPORTS: quantamind.serve.working_clone. Nothing mocked; git does the work.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

BRANCHES = "+refs/heads/*:refs/remotes/origin/*"


# **A COMMIT NEEDS AN IDENTITY AND A CI RUNNER HAS NONE.** `git commit` fails with
# `fatal: empty ident name` where no `user.name` is set, so this fixture passed on every
# developer's machine and failed on GitHub Actions. Same shape as the ambient
# `http.extraheader` in `test_git_credentials.py`, same lesson: a test that borrows the
# machine's git configuration is testing the machine.
#
# **IT CANNOT BE REPRODUCED ON A MAC**, which is why it reached CI at all — macOS supplies a
# full name from the user record where a Linux runner has none, so `GIT_CONFIG_GLOBAL=/dev/null`
# still commits here. CI is the only oracle for this one, and saying so beats claiming a local
# check that did not happen. Supplied per-process; nothing is written to any config.
IDENTITY = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, **IDENTITY},
    )


def upstream_with_a_pr_branch(tmp_path: Path) -> Path:
    """A repository holding a branch `pr/1` AND a `refs/pull/1/head`, which is the collision."""
    up = tmp_path / "up"
    up.mkdir()
    assert git(up, "init", "-q", ".").returncode == 0
    assert git(up, "commit", "-q", "--allow-empty", "-m", "x").returncode == 0
    assert git(up, "branch", "pr/1").returncode == 0
    assert git(up, "update-ref", "refs/pull/1/head", "HEAD").returncode == 0
    refs = git(up, "for-each-ref", "--format=%(refname)").stdout
    assert "refs/heads/pr/1" in refs and "refs/pull/1/head" in refs, f"fixture is wrong: {refs}"
    return up


def test_the_old_refspec_is_the_one_git_refuses(tmp_path: Path) -> None:
    """**THE NEGATIVE CONTROL.** Without it, the test below could pass for any other reason."""
    up = upstream_with_a_pr_branch(tmp_path)
    work = tmp_path / "old"
    assert (
        subprocess.run(
            ["git", "clone", "-q", "--no-checkout", str(up), str(work)], timeout=120
        ).returncode
        == 0
    )
    done = git(
        work, "fetch", "--prune", "origin", BRANCHES, "+refs/pull/*/head:refs/remotes/origin/pr/*"
    )
    assert done.returncode != 0, "the old refspec fetched cleanly — this repo does not collide"
    assert "Cannot fetch both" in done.stderr


def test_a_pr_branch_no_longer_breaks_the_fetch(tmp_path: Path) -> None:
    """The shipped refspec, on the repository that broke the old one."""
    up = upstream_with_a_pr_branch(tmp_path)
    work = tmp_path / "new"
    assert (
        subprocess.run(
            ["git", "clone", "-q", "--no-checkout", str(up), str(work)], timeout=120
        ).returncode
        == 0
    )
    done = git(
        work, "fetch", "--prune", "origin", BRANCHES, "+refs/pull/*/head:refs/remotes/pull/*"
    )
    assert done.returncode == 0, f"the shipped refspec still collides: {done.stderr[:200]}"
    assert git(work, "rev-parse", "refs/remotes/pull/1").returncode == 0, (
        "the fetch succeeded but the pull head is not resolvable, so nothing can review it"
    )
