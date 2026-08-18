"""Read a repository's file-touch history from git, and refuse to guess when the read is unsound.

WHAT: `read_touches()` returns one `Touch` per (file, commit) pair from `git log --name-only`, and
      raises rather than returning a short list when the read did not complete.
WHY:  This is the input the whole product rests on. The ranking is a count of prior touches, so a
      history read that silently returns half the commits produces a confident ranking of the wrong
      files, and nothing downstream can tell.

      **THE EXIT CODE IS THE POINT.** `git log` on a blob-filtered clone can emit a plausible,
      truncated stream AND exit non-zero. Code that read the stream and ignored the code **voided
      four measurements** on this project: byte counts varied between runs of an identical command,
      and the largest truncated read looked exactly like a complete one. So the exit code is
      checked before the output is parsed, and a non-zero exit raises with the command and the
      repository on it.

      **A PARTIAL OR SHALLOW CLONE IS REFUSED UP FRONT, NOT REPAIRED.** `--name-only` needs trees;
      against a promisor remote the read lazily fetches them over the network and is not
      deterministic until the object store is warm. `git fetch --refetch` is the documented repair
      and it did NOT fix the one clone that failed this way. Refusing is a result; a slow wrong
      answer is not.

      **AN EMPTY HISTORY IS A VALUE, NOT AN ERROR.** A repository with no commits touching the
      paths asked for returns `[]`, and `rank/` treats that as the no-history case that misses at
      4.46%. "We failed to read" and "there is nothing here" must never be the same value.
IMPORTS: types (Touch). Nothing to its right in the layer order.
CONSUMED BY: store.touches, for the index; rank consumes the index, never this module.

      `Touch` MOVED to `types/history.py`: `store/` sits left of `ingest/` and must be able to
      name what it indexes, so the shared value object belongs to the leftmost layer.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.types.touch import Touch

# Declared, not defaulted. A full history read on a large repository is minutes, not the 30s
# house default, and a timeout that fires mid-read is indistinguishable from a short history.
HISTORY_TIMEOUT_S = 1800
PROBE_TIMEOUT_S = 30
# git's own escape, expanded to a NUL byte in the OUTPUT. It must stay the two-character
# sequence here: an actual NUL cannot be passed in argv, and execve rejects the call.
NUL_FORMAT = "%x00"
NUL = "\x00"


class HistoryReadFailed(RuntimeError):
    """A git read that did not complete. Carries the call site, never a bare message.

    Distinct from an empty history, which is a legitimate `[]`. This project has already shipped
    the confusion once: a repository that failed to read was counted as one that did not qualify,
    and the run printed a confident table over the survivors.
    """

    def __init__(self, repo_dir: Path, command: list[str], reason: str) -> None:
        self.repo_dir = repo_dir
        self.command = command
        self.reason = reason
        super().__init__(f"{repo_dir}: {' '.join(command)} — {reason}")


def _git(repo_dir: Path, args: list[str], timeout_s: int) -> subprocess.CompletedProcess[str]:
    """Run one git command with an explicit timeout, or raise with the call site attached."""
    command = ["git", "-C", str(repo_dir), *args]
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise HistoryReadFailed(repo_dir, command, f"timed out after {timeout_s}s") from exc
    except OSError as exc:
        raise HistoryReadFailed(repo_dir, command, f"could not run git: {exc}") from exc


def assert_readable(repo_dir: Path) -> None:
    """Raise unless this clone can be read deterministically. Checked before any history is read.

    Shallow and blob-filtered clones both produce reads that are wrong in ways no exit code
    reports on every invocation, so they are refused here rather than handled downstream.
    """
    if not (repo_dir / ".git").exists():
        raise HistoryReadFailed(repo_dir, ["git", "rev-parse"], "not a git repository")

    shallow = _git(repo_dir, ["rev-parse", "--is-shallow-repository"], PROBE_TIMEOUT_S)
    if shallow.returncode != 0:
        raise HistoryReadFailed(
            repo_dir,
            ["rev-parse", "--is-shallow-repository"],
            f"exit {shallow.returncode}: {shallow.stderr.strip()[:200]}",
        )
    if shallow.stdout.strip() == "true":
        raise HistoryReadFailed(
            repo_dir,
            ["rev-parse", "--is-shallow-repository"],
            "shallow clone — history is truncated and the ranking would count a prefix",
        )

    filtered = _git(
        repo_dir, ["config", "--get", "remote.origin.partialclonefilter"], PROBE_TIMEOUT_S
    )
    # exit 1 with no output is git's "key not set", which is the healthy case.
    if filtered.returncode == 0 and filtered.stdout.strip():
        raise HistoryReadFailed(
            repo_dir,
            ["config", "--get", "remote.origin.partialclonefilter"],
            f"partial clone (filter={filtered.stdout.strip()}) — --name-only would fetch trees "
            "lazily and the read is not deterministic until the object store is warm",
        )


def read_touches(repo_dir: Path, pathspec: str | None = None) -> list[Touch]:
    """Every (file, commit-time) pair in this repository's history, newest commit first.

    `pathspec` narrows the read the way git does — `"*.py"` for the Python surface. Merge commits
    are excluded: a merge touches every file of both sides and would swamp the touch counts with
    changes nobody made.

    Returns `[]` for a repository whose history touches nothing matching. Raises for a read that
    did not complete.
    """
    assert_readable(repo_dir)

    # A repository with no commits is the no-history case, detected structurally rather than by
    # matching git's wording. `git log` exits non-zero here, and without this it would be reported
    # as a failed read -- the exact confusion this module exists to prevent, in reverse.
    head = _git(repo_dir, ["rev-parse", "--verify", "HEAD"], PROBE_TIMEOUT_S)
    if head.returncode != 0:
        return []

    args = ["log", "--no-merges", "--name-only", f"--pretty=format:{NUL_FORMAT}%ct"]
    if pathspec:
        args += ["--", pathspec]
    result = _git(repo_dir, args, HISTORY_TIMEOUT_S)

    # The exit code is checked BEFORE the output is looked at. A truncated stream parses fine.
    if result.returncode != 0:
        raise HistoryReadFailed(
            repo_dir,
            args,
            f"exit {result.returncode} after {len(result.stdout)} bytes: "
            f"{result.stderr.strip()[:200]}",
        )

    touches: list[Touch] = []
    for block in result.stdout.split(NUL)[1:]:
        lines = block.split("\n")
        try:
            committed_at = int(lines[0].strip())
        except ValueError:
            # A commit whose timestamp we cannot read is not silently dated zero.
            raise HistoryReadFailed(
                repo_dir, args, f"unparseable commit timestamp: {lines[0]!r}"
            ) from None
        for name in lines[1:]:
            name = name.strip()
            if name:
                touches.append(Touch(path=name, committed_at=committed_at))
    return touches
