"""Reading one repository's Python-file commit history, with failure that cannot hide.

WHAT: One function, `load`, returning a repository's non-merge commits over *.py as
      (sha, unix_time, lowercased_subject, files) oldest-first -- or raising.
WHY:  Split out of top3_recall.py when its first version silently dropped three of the
      largest repositories in the corpus. The reason is worth a file of its own: 27 of 35
      clones are blob:none, so a cold history read lazily fetches trees from the promisor
      remote over the network, and a network failure is indistinguishable from a small
      repository unless the reader refuses to return a value for it.
IMPORTS: stdlib only (subprocess). No research dependencies, so it runs on either
      interpreter.
CONSUMED BY: research/phase0/top3_recall.py.
"""

from __future__ import annotations

import subprocess


class GitReadFailed(Exception):
    """A history read that did not complete. Never convertible to "repo not eligible"."""

    def __init__(self, repo: str, returncode: int, stderr: str) -> None:
        super().__init__(f"{repo}: git exited {returncode}: {stderr[:200]}")
        self.repo, self.returncode, self.stderr = repo, returncode, stderr


def load(repo):
    """Read a repository's Python-file history, or raise. It never returns None.

    The first version returned None on a non-zero exit, and the caller could not tell that
    apart from "too few commits to be eligible" -- so a repository that failed to read was
    counted as a repository that did not qualify, and the run printed a confident table.
    That is how three of the largest repositories in this corpus vanished from one run and
    reappeared in the next: 27 of 35 clones are blob:none, and a cold read lazily fetches
    trees from the promisor remote over the network. The read is not deterministic until
    the object store is warm, and a network failure looked exactly like ineligibility.

    Ask what this prints when the thing it checks is broken. Before: the same table.

    One clone in this corpus failed for a second, unrelated reason, and it is recorded here
    because `git fetch --refetch` -- the documented repair -- did NOT fix it. apache_airflow
    carried a commit-graph file naming its old `main` tip, an object the refetch removed from
    the object database, so every walk aborted at the same sha. The read exited 128 after
    emitting 9.1, 9.9 and 10.3 MB on three invocations of one command; disabling the
    commit-graph for that clone produced 11.4 MB and exit 0. **Byte counts that vary between
    runs of an identical command are the signature**, and only the exit code makes them
    visible -- the largest truncated read still looked like a complete one.
    """
    out = subprocess.run(
        [
            "git",
            "-C",
            repo,
            "log",
            "--no-merges",
            "--name-only",
            "--pretty=format:%x00%H %ct %s",
            "--",
            "*.py",
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if out.returncode != 0:
        raise GitReadFailed(repo, out.returncode, out.stderr)
    commits = []
    for blk in out.stdout.split("\x00")[1:]:
        lines = blk.split("\n")
        head = lines[0].split(" ", 2)
        if len(head) < 2:
            continue
        try:
            ts = int(head[1])
        except ValueError:
            continue
        msg = head[2] if len(head) > 2 else ""
        files = sorted({ln for ln in lines[1:] if ln.endswith(".py")})
        if files:
            commits.append((head[0], ts, msg.lower(), files))
    commits.reverse()
    return commits
