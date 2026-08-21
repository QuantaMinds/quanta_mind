"""Replay the ranker over a repository's own history and report what it would have said.

WHAT: `replay()` reads a clone, indexes its touches, walks every admissible event, scores each one
      against history strictly before it, and returns an `Outcome` -- the ranker, the alphabetical
      control and exact chance, whole and stratified.
WHY:  This is the sales instrument and the first thing a sceptic runs. It needs a clone and
      nothing else: no App install, no webhook, no token, no code leaving the machine.

      **THE BOUND IS THE PRODUCT.** `as_of=event.at` scores each event over `[at - 365d, at)`,
      half-open, so a change cannot see itself or anything after it. A retrospective that leaks
      looks brilliant and means nothing, and no customer can audit it -- which makes this the
      strongest incentive in the whole project to get it wrong.
      `tests/live/test_retrospective_leakage.py` rebuilds the index from only the commits before
      each event and requires an identical ranking, then sabotages the bound and requires that to
      fail.

      **IT REPORTS AGAINST CHANCE, NOT ONLY ALPHABETICAL.** See `rank/baseline.py`: the
      alphabetical control's strength varies by repository layout, so it is not a stable anchor.

      **AND IT REPORTS THE DEGENERATE STRATUM SEPARATELY.** 68.6% of events on the pinned corpus
      touch three or fewer files, where a budget of three reads everything and no arm can miss.
      Pooling them dilutes the effect threefold. The headline belongs to the informative stratum.

      **NOTHING HERE COMPARES ITSELF TO THE PUBLISHED FIGURE.** A run on one repository can
      neither confirm nor refute it; `render/replay_report.py` states both provenances and does no
      arithmetic across them.
IMPORTS: ingest.commits, rank.{baseline,events,order,score}, store.{schema,touches},
      types.{replay_outcome,ranking,touch}. Rightmost layer; imports left only.
CONSUMED BY: serve/cli.py; tests/live/test_retrospective_leakage.py.
"""

from __future__ import annotations

import collections
from pathlib import Path

from quantamind.ingest.commits import read_commits
from quantamind.rank.baseline import chance_hit
from quantamind.rank.events import Rejections, admissible
from quantamind.rank.order import BUDGET
from quantamind.rank.score import discriminate, order
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.change import REVIEWABLE_SUFFIXES
from quantamind.types.ranking import Discrimination
from quantamind.types.replay_outcome import DEGENERATE_AT, Outcome, Stratum
from quantamind.types.touch import Touch

FLAT_SCORES = "every file scored the same"
PATHSPEC: tuple[str, ...] = tuple(f"*{s}" for s in REVIEWABLE_SUFFIXES)


class _Tally:
    """Running counts for one slice. Not exported; `Stratum` is the value that leaves here."""

    __slots__ = ("alpha", "chance", "hits", "n")

    def __init__(self) -> None:
        self.n = self.hits = self.alpha = 0
        self.chance = 0.0

    def add(self, hit: bool, alpha: bool, chance: float) -> None:
        self.n += 1
        self.hits += hit
        self.alpha += alpha
        self.chance += chance

    def stratum(self, label: str) -> Stratum:
        return Stratum(
            label=label,
            events=self.n,
            hits=self.hits,
            alpha_hits=self.alpha,
            chance_hits=self.chance,
        )


def replay(clone: Path, repo: str, store_path: Path, cap: int | None = None) -> Outcome:
    """Rank every admissible event in `clone` against history strictly before it.

    `store_path` is the caller's to choose and to throw away. The index is a derived artefact of
    the clone, never a durable one: a live test that wrote it inside a fixture stranded itself the
    first time `SCHEMA_VERSION` moved.
    """
    # **DERIVED FROM `REVIEWABLE_SUFFIXES`, NOT HARDCODED.** This read `"*.py"`, which silently
    # returned an empty history for every repository that is not Python -- a retrospective that
    # reports nothing looks exactly like a repository with no history.
    commits = read_commits(clone, pathspec=PATHSPEC)
    if not commits:
        raise ValueError(f"{clone}: no Python history to replay; a retrospective needs commits")

    conn = schema.open_store(store_path)
    try:
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        touch_store.index(
            conn,
            repo_id,
            [Touch(path=p, committed_at=c.committed_at) for c in commits for p in c.paths],
        )

        rejections = Rejections()
        whole, small, large = _Tally(), _Tally(), _Tally()
        discordant: collections.Counter[str] = collections.Counter()
        flat = 0

        for event in admissible(commits, rejections):
            paths = sorted(event.paths)
            # THE BOUND. Half-open on `event.at`, so the change cannot see itself.
            scores = dict(touch_store.counts(conn, repo_id, paths, as_of=event.at))
            if discriminate(scores) is not Discrimination.ORDERED:
                # The research drops these: with no spread there is nothing for a ranking to do,
                # and keeping them would inflate every arm identically.
                flat += 1
                continue

            hit = bool(set(order(scores)[:BUDGET]) & event.target)
            alpha = bool(set(paths[:BUDGET]) & event.target)
            chance = chance_hit(len(event.paths), len(event.target), BUDGET)
            whole.add(hit, alpha, chance)
            (small if len(event.paths) <= DEGENERATE_AT else large).add(hit, alpha, chance)
            if hit != alpha:
                discordant["ranker" if hit else "control"] += 1
            # THE CAP COUNTS SURVIVORS, applied here and not in `admissible()`, because the skip
            # above is what it counts past. See `rank/events.SURVIVOR_CAP`.
            if cap is not None and whole.n >= cap:
                break
    finally:
        conn.close()

    rejections.counts[FLAT_SCORES] = flat
    return Outcome(
        repo=repo,
        whole=whole.stratum("all events"),
        degenerate=small.stratum(f"<={DEGENERATE_AT} files"),
        informative=large.stratum(f">{DEGENERATE_AT} files"),
        b=discordant["ranker"],
        c=discordant["control"],
        rejected=dict(rejections.counts),
        skipped_flat=flat,
    )
