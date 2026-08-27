"""Read a repository's commit stream, oldest first, and refuse a clone that cannot be read soundly.

WHAT: `read_commits()` returns one `Commit` per non-merge commit, oldest first, with the files it
      touched. `assert_readable()` is the clone check every reader in this layer shares.
WHY:  This is the only place in the product that runs `git log`, which makes it the only place the
      three failures of this read can be handled — and all three have happened here before.

      **The exit code is checked before the output is parsed.** `git log` on a damaged clone emits
      a plausible, truncated stream AND exits non-zero. Reading the stream and ignoring the code
      voided four measurements: byte counts varied between runs of an identical command, and the
      largest truncated read looked exactly like a complete one.

      **Output is decoded from bytes with `errors="replace"`, never `text=True`.** Real commit
      subjects and real filenames carry non-UTF-8 bytes; `text=True` decodes strictly and raises
      `UnicodeDecodeError` from inside subprocess, which is an unhandled crash rather than a typed
      failure. A decode error must not be allowed to drop a repository.

      **`core.commitGraph=false`.** A commit-graph file naming a tip absent from the object
      database makes git resolve it and exit 128 on a clone that looks fine. `git fetch --refetch`,
      the documented repair, did not fix the one clone that failed this way; disabling the graph
      did.

      **Oldest first (`--reverse`).** Every question asked of this stream is "what happened before
      this point" or "what happened within N days after it", and both are wrong if the order is
      reversed. The event definition walks forward from a commit and stops at a window boundary.
IMPORTS: types (Commit). Nothing to its right in the layer order.
CONSUMED BY: ingest.history derives Touch values; the ranker's replay gate reads events from it.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

from quantamind.types.commit import Commit

# Declared, not defaulted. A full history read on a large repository is minutes, not the 30s house
# default, and a timeout firing mid-read is indistinguishable from a short history.
HISTORY_TIMEOUT_S = 1800
PROBE_TIMEOUT_S = 30
# TWO PAIRS, deliberately. `%x00`/`%x01` are git's escapes and must stay two-character sequences
# in argv -- an actual NUL cannot be passed to execve, and the call fails with "embedded null
# byte". The raw characters are what the OUTPUT is split on. This module reintroduced the bug that
# `history.py` had already been fixed for, and the tests caught it the same way twice.
REC_FMT, FIELD_FMT = "%x00", "%x01"
REC, FIELD = "\x00", "\x01"


class HistoryReadFailed(RuntimeError):
    """A git read that did not complete. Carries the call site, never a bare message.

    Distinct from an empty history, which is a legitimate `[]`. This project has shipped the
    confusion once: a repository that failed to read was counted as one that did not qualify, and
    the run printed a confident table over the survivors.
    """

    def __init__(self, repo_dir: Path, command: list[str], reason: str) -> None:
        self.repo_dir, self.command, self.reason = repo_dir, command, reason
        super().__init__(f"{repo_dir}: {' '.join(command)} — {reason}")


def _git(repo_dir: Path, args: list[str], timeout_s: int) -> subprocess.CompletedProcess[bytes]:
    """Run one git command with an explicit timeout, capturing BYTES. Raises with the call site."""
    command = ["git", "-c", "core.commitGraph=false", "-C", str(repo_dir), *args]
    try:
        return subprocess.run(command, capture_output=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise HistoryReadFailed(repo_dir, command, f"timed out after {timeout_s}s") from exc
    except OSError as exc:
        raise HistoryReadFailed(repo_dir, command, f"could not run git: {exc}") from exc


def assert_readable(repo_dir: Path) -> None:
    """Raise unless this clone can be read deterministically. Checked before any history is read.

    Shallow and blob-filtered clones both produce reads that are wrong in ways no exit code reports
    on every invocation, so they are refused here rather than handled downstream.
    """
    if not (repo_dir / ".git").exists():
        raise HistoryReadFailed(repo_dir, ["git", "rev-parse"], "not a git repository")

    shallow = _git(repo_dir, ["rev-parse", "--is-shallow-repository"], PROBE_TIMEOUT_S)
    if shallow.returncode != 0:
        raise HistoryReadFailed(
            repo_dir,
            ["rev-parse", "--is-shallow-repository"],
            f"exit {shallow.returncode}: {shallow.stderr.decode('utf-8', 'replace')[:200]}",
        )
    if shallow.stdout.decode("utf-8", "replace").strip() == "true":
        raise HistoryReadFailed(
            repo_dir,
            ["rev-parse", "--is-shallow-repository"],
            "shallow clone — history is truncated and the ranking would count a prefix",
        )

    filtered = _git(
        repo_dir, ["config", "--get", "remote.origin.partialclonefilter"], PROBE_TIMEOUT_S
    )
    # git config exits 0 when the key is set, 1 when it is absent, and 2 or more on a real error
    # -- an unreadable or malformed config file. Treating every non-zero exit as "absent" would
    # read a broken clone as a healthy one, which is the failure this whole function exists to
    # prevent, so only exit 1 is the quiet case.
    if filtered.returncode not in (0, 1):
        raise HistoryReadFailed(
            repo_dir,
            ["config", "--get", "remote.origin.partialclonefilter"],
            f"exit {filtered.returncode} reading git config, so whether this is a partial clone "
            f"is UNKNOWN: {filtered.stderr.decode('utf-8', 'replace').strip()[:160]}",
        )
    if filtered.returncode == 0 and filtered.stdout.strip():
        raise HistoryReadFailed(
            repo_dir,
            ["config", "--get", "remote.origin.partialclonefilter"],
            f"partial clone (filter={filtered.stdout.decode('utf-8', 'replace').strip()}) — "
            "--name-only would fetch trees lazily and the read is not deterministic",
        )


def read_commits(
    repo_dir: Path, pathspec: str | Sequence[str] | None = None, *, since: str = ""
) -> list[Commit]:
    """Every non-merge commit touching `pathspec`, OLDEST FIRST, with its subject and files.

    `since` narrows the read to `<since>..HEAD`, excluding `since` itself.

    **THE BOUND IS A COMMIT, NOT A TIME.** Git history is not chronologically ordered -- a rebase
    lands commits dated OLDER than ones already read -- so a `--since=<date>` bound would skip them
    silently and every count downstream would be low. Reachability cannot be fooled that way.

    Returns `[]` for a repository with no commits — detected structurally rather than by matching
    git's wording. Raises for a read that did not complete.
    """
    assert_readable(repo_dir)
    if _git(repo_dir, ["rev-parse", "--verify", "HEAD"], PROBE_TIMEOUT_S).returncode != 0:
        return []

    args = ["log", "--reverse", "--no-merges", "--name-only", f"--format={REC_FMT}%ct{FIELD_FMT}%s"]
    if pathspec:
        # --full-history, because a pathspec turns on history simplification and that DROPS
        # commits which really did touch the path: when a merge is TREESAME to one parent git
        # follows only that parent and discards the other side, non-merge commits included.
        # Measured on the pinned corpus it lost 3 to 151 commits per repository, and 23 of 430
        # for `celery/__init__.py` alone. The score IS the touch count, so those are ranking
        # errors, not bookkeeping ones. `tests/live/test_counts_match_git.py` already used
        # --full-history as its ORACLE and passed, because its repositories have flatter
        # histories than these -- the oracle was right and the reader was wrong.
        # **A SEQUENCE BECOMES SEVERAL PATHSPECS, NOT ONE BRACE GLOB.** `:(glob)**/*{py,ts}` looked
        # right and returned ZERO commits on a repository with 1,990 of them -- git's glob magic has
        # no brace expansion, so the pattern matched nothing and the read reported an empty history,
        # which is indistinguishable from a repository that has none. Caught by running it against a
        # real clone rather than trusting the syntax.
        specs = [pathspec] if isinstance(pathspec, str) else list(pathspec)
        if since:
            args.append(f"{since}..HEAD")
        args += ["--full-history", "--", *specs]
    elif since:
        args.append(f"{since}..HEAD")
    result = _git(repo_dir, args, HISTORY_TIMEOUT_S)
    if result.returncode != 0:
        raise HistoryReadFailed(
            repo_dir,
            args,
            f"exit {result.returncode} after {len(result.stdout)} bytes: "
            f"{result.stderr.decode('utf-8', 'replace').strip()[:200]}",
        )

    out: list[Commit] = []
    for chunk in result.stdout.decode("utf-8", "replace").split(REC):
        if not chunk.strip():
            continue
        head, _, body = chunk.partition("\n")
        stamp, _, subject = head.partition(FIELD)
        try:
            when = int(stamp.strip())
        except ValueError:
            raise HistoryReadFailed(repo_dir, args, f"unparseable timestamp: {stamp!r}") from None
        paths = frozenset(line.strip() for line in body.split("\n") if line.strip())
        out.append(Commit(committed_at=when, subject=subject, paths=paths))
    return out
