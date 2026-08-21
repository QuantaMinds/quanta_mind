"""Derive the file-touch history the ranking counts over, from the commit stream.

WHAT: `read_touches()` returns one `Touch` per (file, commit) pair.
WHY:  The ranking is a count of these and nothing else. It is a derivation over `ingest.commits`
      rather than a second `git log`, because two readers meant two decode policies and two places
      for the exit code to be forgotten — and this module previously had the weaker pair. It used
      `text=True`, which decodes strictly and raises `UnicodeDecodeError` from inside subprocess on
      a repository carrying a non-UTF-8 filename: an unhandled crash rather than a typed failure.

      **An empty history is a value, not an error.** A repository whose history touches nothing
      matching returns `[]`, and `rank` treats that as the no-history case that misses at 4.46%.
      "We failed to read" and "there is nothing here" must never be the same value.

      Order is not guaranteed to callers: `store.touches` indexes by timestamp and the ranker
      counts over a window, so neither depends on it. `ingest.commits` is where order is a contract.
IMPORTS: types (Touch), ingest.commits. Nothing to its right in the layer order.
CONSUMED BY: store.touches, for the index; rank consumes the index, never this module.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from quantamind.ingest.commits import HistoryReadFailed, assert_readable, read_commits
from quantamind.types.touch import Touch

__all__ = ["HistoryReadFailed", "assert_readable", "read_touches"]


def read_touches(repo_dir: Path, pathspec: str | Sequence[str] | None = None) -> list[Touch]:
    """Every (file, commit-time) pair in this repository's history.

    `pathspec` narrows the read the way git does — `"*.py"` for the Python surface. Merge commits
    are excluded upstream: a merge touches every file of both sides and would swamp the counts with
    changes nobody made.
    """
    return [
        Touch(path=path, committed_at=commit.committed_at)
        for commit in read_commits(repo_dir, pathspec)
        for path in sorted(commit.paths)
    ]
