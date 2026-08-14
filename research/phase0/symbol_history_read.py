"""Reading a repository's history at SYMBOL level, with failure that cannot hide.

WHAT: `stream`, returning commits as (sha, time, subject, files, symbols) oldest-first, and
      the `ReadFailed` it raises rather than returning an empty list.
WHY:  Split from gate3c_paired.py at the 200-line cap, and this is the natural seam: reading
      patch bodies is a different concern from comparing two rankings, and it is the concern
      that has failed before. `git log -p` exits non-zero on a blob-filtered clone and emits a
      partial patch stream -- identical invocations once returned 710 and 918 commits against
      3,313 -- so the exit code is asserted here and the caller cannot proceed on a partial read.
IMPORTS: stdlib only (re, subprocess). Runs on either interpreter.
CONSUMED BY: research/phase0/gate3c_paired.py.
"""

from __future__ import annotations

import re
import subprocess

YEAR = 365 * 86400
HUNK = re.compile(r"^@@ .*@@\s*(?:async\s+)?def\s+([A-Za-z_]\w*)")


class ReadFailed(Exception):
    pass


def stream(repo: str) -> list[tuple[str, int, str, set[str], set[str]]]:
    """Commits oldest-first as (sha, ts, subject, files, symbols). Raises rather than returns."""
    p = subprocess.run(
        [
            "git",
            "-C",
            repo,
            "log",
            "--no-merges",
            "-U0",
            "-p",
            "--pretty=format:%x00%H %ct %s",
            "--",
            "*.py",
        ],
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if p.returncode != 0:
        raise ReadFailed(f"{repo}: git exited {p.returncode}: {p.stderr[:160]}")
    out = []
    for blk in p.stdout.split("\x00")[1:]:
        lines = blk.split("\n")
        head = lines[0].split(" ", 2)
        if len(head) < 2:
            continue
        try:
            ts = int(head[1])
        except ValueError:
            continue
        msg = (head[2] if len(head) > 2 else "").lower()
        cur, syms, files = None, set(), set()
        for ln in lines[1:]:
            if ln.startswith("+++ b/"):
                cur = ln[6:]
                if cur.endswith(".py"):
                    files.add(cur)
            elif ln.startswith("@@") and cur and cur.endswith(".py"):
                m = HUNK.match(ln)
                if m:
                    syms.add(f"{cur}::{m.group(1)}")
        if files:
            out.append((head[0], ts, msg, files, syms))
    out.reverse()
    return out
