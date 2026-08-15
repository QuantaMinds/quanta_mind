"""Read a repository's commit stream as (timestamp, message, .py files), oldest first.

WHAT: One `git log --name-only` per repository, decoded defensively, exit code asserted.
WHY:  Split from `defect_return.py` at the 200-line cap, and it is the right seam -- this is the
      only part that touches git, and it is where both failures of this measurement lived. A
      corrupt commit-graph made git exit 128 on a clone that looked fine, and a non-UTF-8 byte in
      a commit message crashed the decode. Either one, handled quietly, would have dropped a
      repository and shrunk the denominator into something that reads as a smaller sample.
IMPORTS: stdlib only (subprocess).
CONSUMED BY: `defect_return.py` in this package.
"""

from __future__ import annotations

import subprocess


class ReadFailed(RuntimeError):
    """A git read that did not exit zero. Never silently a zero-length history."""


def stream(path: str) -> list[tuple[int, str, frozenset[str]]]:
    """(timestamp, message, .py files) oldest-first.

    `--name-only` needs tree objects, not blobs, so this is sound on a blob-filtered clone --
    unlike `git log -p`, which exits non-zero on one and emits a truncated patch stream. The exit
    code is asserted either way, because a truncated history and a short history print the same.
    """
    p = subprocess.run(
        # core.commitGraph=false is the documented repair for the corruption this project has
        # already hit once: git resolves a commit present in the graph file but absent from the
        # object database and exits 128. `git fetch --refetch` did NOT fix it that time.
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            path,
            "log",
            "--reverse",
            "--no-merges",
            "--name-only",
            "--format=%x00%ct%x01%s",
        ],
        capture_output=True,
        timeout=1800,
    )
    if p.returncode != 0:
        raise ReadFailed(f"{path}: git log exited {p.returncode}: {p.stderr[:160]!r}")
    # Decoded here rather than by subprocess: real commit messages carry non-UTF-8 bytes, and a
    # decode error must not be allowed to drop a repository.
    text = p.stdout.decode("utf-8", errors="replace")
    out: list[tuple[int, str, frozenset[str]]] = []
    for chunk in text.split("\x00"):
        if not chunk.strip():
            continue
        head, _, body = chunk.partition("\n")
        ts, _, msg = head.partition("\x01")
        try:
            when = int(ts)
        except ValueError:
            continue
        files = frozenset(ln for ln in body.split("\n") if ln.endswith(".py") and ln.strip())
        if files:
            out.append((when, msg.lower(), files))
    return out
