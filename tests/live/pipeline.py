"""Clone real repositories and run the whole product over their merged pull requests.

WHAT: `clone_all()` fetches repositories, `ranked_pulls()` yields one `(repo, number, files,
      ranking)` per merged pull request with Python changes, and `Skips` records every one that was
      passed over and why.
WHY:  Two live tests ask different questions of the same expensive setup — one about the pipeline's
      invariants, one about what the customer is shown — and `tests/live/test_end_to_end.py`
      crossed the file-length cap holding both. Splitting the question is the point; re-cloning to
      do it would not be.

      **Skips are returned, never swallowed.** A silent `continue` is how a live test keeps passing
      while covering nothing: if a GitHub response shape changed, every pull request would be
      skipped and only a bare total would notice.
IMPORTS: quantamind.ingest.history, quantamind.store.{schema,touches}, quantamind.rank.order.
CONSUMED BY: the live tests in this directory.
"""

from __future__ import annotations

import collections
import json
import sqlite3
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from quantamind.ingest.diff import DiffReadFailed, base_commit, changed_files
from quantamind.ingest.history import read_touches
from quantamind.rank.order import rank
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.ranking import Ranking
from quantamind.types.touch import Touch

# One repository in active development and one in a quiet period, deliberately: the quiet one is
# where the ranker must stay silent, and a corpus of only busy repositories never exercises that.
REPOS = ("pallets/flask", "encode/httpx")
MAX_PRS = 12


@dataclass(frozen=True)
class Ranked:
    """One real pull request, ranked, with everything a test needs to interrogate it."""

    repo: str
    number: int
    changed: list[str]
    ranking: Ranking
    scores: dict[str, int]
    as_of: int
    conn: sqlite3.Connection
    repo_id: int
    touches: list[Touch]


@dataclass
class Skips:
    """Every pull request passed over, with the reason. Printed by the caller, never discarded."""

    counts: collections.Counter[str] = field(default_factory=collections.Counter)

    def record(self, reason: str) -> None:
        self.counts[reason] += 1

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def gh(args: list[str]) -> list[dict[str, object]]:
    done = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=180)
    assert done.returncode == 0, f"gh api {args[0]} failed loudly: {done.stderr[:200]}"
    parsed = json.loads(done.stdout)
    assert isinstance(parsed, list), (
        f"gh api {args[0]} returned {type(parsed).__name__}, not a list"
    )
    return parsed


def clone_all(base: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for repo in REPOS:
        dest = base / repo.replace("/", "_")
        done = subprocess.run(
            ["git", "clone", "-q", f"https://github.com/{repo}.git", str(dest)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert done.returncode == 0, f"clone of {repo} failed: {done.stderr[:200]}"
        out[repo] = dest
    return out


def ranked_pulls(clones: dict[str, Path], skips: Skips) -> Iterator[Ranked]:
    """Yield a real ranking per merged pull request, through every layer the product has."""
    for repo, clone in clones.items():
        touches = read_touches(clone, pathspec="*.py")
        assert len(touches) > 500, f"{repo}: {len(touches)} touches — the read looks truncated"

        conn = schema.open_store(clone / "e2e.db")
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        assert touch_store.index(conn, repo_id, touches) == len(touches)

        pulls = [
            p for p in gh([f"repos/{repo}/pulls?state=closed&per_page=40"]) if p.get("merged_at")
        ][:MAX_PRS]
        assert pulls, f"{repo}: no merged pull requests returned by the API"

        for pull in pulls:
            number = int(str(pull["number"]))
            # THROUGH THE PRODUCT, not by hand. ingest/diff.py owns both reads, and the seam it
            # covers is which commit bounds the window -- the base, never the head.
            changed = changed_files(repo, number)
            if not changed:
                skips.record("no python files changed")
                continue
            try:
                base = base_commit(repo, number, clone)
            except DiffReadFailed:
                # A fork, or a branch force-pushed since. Not a pipeline failure, but a coverage
                # hole, so it is counted rather than passed over.
                skips.record(f"{repo}: base commit not in clone")
                continue
            as_of = base.committed_at
            scores = dict(touch_store.counts(conn, repo_id, changed, as_of=as_of))
            yield Ranked(
                repo=repo,
                number=number,
                changed=changed,
                ranking=rank(scores),
                scores=scores,
                as_of=as_of,
                conn=conn,
                repo_id=repo_id,
                touches=touches,
            )
        # The connection is deliberately left open: the caller may rebuild indexes from it.
