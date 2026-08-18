"""Changed lines per file for one commit, and the check that git answered completely.

WHAT: `shas()` maps a timestamp to a commit id; `numstat()` returns changed lines per `.py` file
      for one commit, or None when git would not answer.
WHY:  Split from `reviewer_effort.py` at the 200-line cap, and it is the right seam for the same
      reason `commit_stream.py` was: this is the only part that touches git, and it is where the
      failure lives. `--numstat` reads PATCH CONTENT, and every clone here is `blob:none`.
      `git log -p` exits non-zero on one and emits a truncated patch stream -- the defect that
      voided four measurements in this project.

      So the exit code is asserted and a short answer returns None rather than an empty dict. A
      commit with no `.py` changes and a commit git refused to read must not produce the same
      value, which is the same rule the product's `Unresolved` exists to enforce.
IMPORTS: stdlib only (subprocess).
CONSUMED BY: `reviewer_effort.py` in this package.
"""

from __future__ import annotations

import subprocess


class ReadFailed(RuntimeError):
    """A git read that did not exit zero. Never silently an empty patch."""


def shas(path: str) -> dict[int, str]:
    """{timestamp: commit id}, so an event scored from `--name-only` can be re-read for sizes.

    Collisions are possible -- two commits can share a second -- and the later one wins. That is
    acceptable here because the sample is used for a size ratio, not for identity, and a wrong
    commit would only add noise to that ratio rather than bias it in a direction.
    """
    p = subprocess.run(
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            path,
            "log",
            "--reverse",
            "--no-merges",
            "--format=%ct %H",
        ],
        capture_output=True,
        timeout=1800,
    )
    if p.returncode != 0:
        raise ReadFailed(f"{path}: git log --format exited {p.returncode}")
    out: dict[int, str] = {}
    for ln in p.stdout.decode("utf-8", "replace").split("\n"):
        bits = ln.split()
        if len(bits) == 2:
            try:
                out[int(bits[0])] = bits[1]
            except ValueError:
                continue
    return out


def numstat(path: str, sha: str, expected: frozenset[str]) -> dict[str, int] | None:
    """Changed lines per `.py` file, or None if git answered incompletely.

    `expected` is the file set the same commit produced under `--name-only`, which needs trees
    and is sound on a blob-filtered clone. If `--numstat` returns a different set, the patch
    stream was truncated -- the caller must drop the commit and count it, never absorb it.
    """
    p = subprocess.run(
        ["git", "-c", "core.commitGraph=false", "-C", path, "show", "--numstat", "--format=", sha],
        capture_output=True,
        timeout=120,
    )
    if p.returncode != 0:
        return None
    out: dict[str, int] = {}
    for ln in p.stdout.decode("utf-8", "replace").split("\n"):
        parts = ln.strip().split("\t")
        if len(parts) != 3 or not parts[2].endswith(".py"):
            continue
        try:
            out[parts[2]] = int(parts[0]) + int(parts[1])
        except ValueError:
            continue  # a rename or a binary file reports '-'
    if set(out) != set(expected):
        return None
    return out
