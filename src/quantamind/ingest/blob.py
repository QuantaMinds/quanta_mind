"""The contents of one file as it stood at one commit.

WHAT: `at(clone, sha, path)` returns the file's text at that commit, or `None` when the path does
      not exist there. `BlobUnreadable` when git failed for any other reason.
WHY:  **A RULE IS CHECKED AGAINST THE CODE AS THE CHANGE LEAVES IT, NOT AS IT IS ON DISK.** The
      working tree of a shared clone is whatever the last fetch left; a review that read it would
      be judging a commit nobody proposed. `git show <sha>:<path>` is the only version of the file
      the pull request actually asks for.

      **ABSENT AND UNREADABLE ARE DIFFERENT ANSWERS.** A path deleted by the change does not exist
      at the head commit, and that is a fact about the change rather than a failure — there is no
      code left for a standard to apply to. A git invocation that failed for any other reason
      raises, because returning `None` for both would let a broken clone read as a repository full
      of deletions, and every rule would quietly pass.

      **TEXT, WITH UNDECODABLE BYTES REPLACED RATHER THAN RAISING.** A checked-in binary reaching
      this is a caller's mistake, not an outage, and `errors="replace"` keeps one stray blob from
      failing a whole delivery. What comes back will not parse as Python, which the rule checker
      already reports as `UNCHECKABLE` rather than as a pass.
IMPORTS: stdlib only. Same layer as the rest of `ingest/`.
CONSUMED BY: `serve/review_delivery.py`, for the rule checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

BLOB_TIMEOUT_S = 30
ABSENT = ("does not exist", "exists on disk, but not in", "path does not exist")


class BlobUnreadable(RuntimeError):
    """git failed for a reason that is not "the file is not there". Carries what it said."""

    def __init__(self, sha: str, path: str, reason: str) -> None:
        super().__init__(f"{path} at {sha[:12]}: {reason}")
        self.sha, self.path, self.reason = sha, path, reason


def at(clone: Path, sha: str, path: str) -> str | None:
    """The text of `path` at `sha`, or `None` if it does not exist there."""
    done = subprocess.run(
        ["git", "-C", str(clone), "show", f"{sha}:{path}"],
        capture_output=True,
        timeout=BLOB_TIMEOUT_S,
    )
    if done.returncode == 0:
        return done.stdout.decode("utf-8", errors="replace")
    stderr = done.stderr.decode("utf-8", errors="replace").strip()
    if any(marker in stderr for marker in ABSENT):
        return None
    raise BlobUnreadable(sha, path, stderr[:160] or f"git exited {done.returncode}")
