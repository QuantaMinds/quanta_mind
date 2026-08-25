"""Two git reads that must agree with `commit_stream`, and a guard that refuses when they do not.

WHAT: `touched_lines(clone, sha, path)` returns the line numbers a commit changed in a file.
      `shas_matching(clone, commits)` returns the hashes for exactly the commits `stream()` kept,
      or None when the two reads do not line up.
WHY:  **A SECOND `git log` DOES NOT RETURN THE SAME COMMITS AS THE FIRST.** `stream()` keeps only
      commits touching a `.py` file; a plain log keeps everything — 50,095 against 34,360 on
      ansible. Zipping them pairs commit *i* of one with commit *i* of the other and measures a
      real diff against an unrelated one, which produces a NUMBER rather than an error.

      **SO THE GUARD RETURNS None AND THE CALLER SKIPS THE REPOSITORY.** The first run of the
      actionability measurement hit this on all six and reported zero events, which is the correct
      behaviour: a refusal that is visible beats a plausible figure computed from mismatched pairs.

      **`--unified=0` IN `touched_lines`, AND IT IS NOT AN OPTIMISATION.** Three lines of context
      either side would manufacture overlap between edits that never met, and overlap is the whole
      quantity being measured.
IMPORTS: stdlib only.
CONSUMED BY: `actionability.py`, `one_example.py`.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def touched_lines(clone: pathlib.Path, sha: str, path: str) -> set[int]:
    """Line numbers this commit changed in this file, on the NEW side.

    `--unified=0` so the hunk header is the changed range and not the range plus context: three
    lines of context on either side would manufacture overlap between edits that never met.
    """
    done = subprocess.run(
        ["git", "-C", str(clone), "show", "--unified=0", "--format=", sha, "--", path],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if done.returncode != 0:
        return set()
    out: set[int] = set()
    for line in done.stdout.splitlines():
        found = HUNK.match(line)
        if found:
            start = int(found.group(2))
            out |= set(range(start, start + int(found.group(3) or 1)))
    return out


def shas_matching(clone: pathlib.Path, commits: list) -> list[str] | None:
    """Commit hashes for exactly the commits `stream()` kept, in the same order.

    Re-reads the log with the SAME filters and pairs on (timestamp, subject). Returns None when the
    two reads do not line up, because a misaligned pairing measures a real diff against an
    unrelated one and reports a number rather than an error.
    """
    done = subprocess.run(
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            str(clone),
            "log",
            "--reverse",
            "--no-merges",
            "--name-only",
            "--format=%x00%H%x01%ct%x01%s",
        ],
        capture_output=True,
        timeout=1800,
    )
    if done.returncode != 0:
        return None
    out: list[str] = []
    for chunk in done.stdout.decode("utf-8", errors="replace").split("\x00"):
        if not chunk.strip():
            continue
        head, _, body = chunk.partition("\n")
        sha, _, rest = head.partition("\x01")
        ts, _, _msg = rest.partition("\x01")
        if not any(line.strip().endswith(".py") for line in body.splitlines()):
            continue
        try:
            int(ts)
        except ValueError:
            continue
        out.append(sha)
    return out if len(out) == len(commits) else None
