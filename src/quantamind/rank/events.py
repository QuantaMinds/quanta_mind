"""Which changes the ranking policy is measured on. One definition, three consumers.

WHAT: `admissible()` walks a commit history oldest-first and yields one `Event` per change that
      the validated experiment counts: 2 to 12 `.py` files, returned to within ninety days by a
      commit whose subject looks like a fix. `Rejections` counts every commit it passed over and
      why.
WHY:  This definition carries the p-value. `research/phase0/external/defect_return.py` measured
      top-three-by-fix-history at 1.21% miss against alphabetical's 3.12% ON EVENTS SHAPED LIKE
      THIS -- n = 2,400, six repositories the method never saw. A retrospective that invented its
      own definition would report a number that resembles the published one and is not it.

      **IT WAS WRITTEN OUT TWICE BEFORE THIS FILE EXISTED**, in `test_event_replay_gate.py` and
      `test_gate_2b_pinned_corpus.py`, and the two copies drifted: one matched fix-words
      case-sensitively under a comment claiming it matched the research, and admitted strictly
      fewer events for as long as it stood. A third copy inside the product would be the same
      pattern with a customer reading the output.

      **EVERY CONSTANT IS COPIED FROM `defect_return.py`, NOT CHOSEN HERE.** A parameter re-picked
      for a fresh corpus is a parameter tuned on it.

      **THE FIX-WORD MATCH IS CASE-INSENSITIVE.** `commit_stream.py` lowercases the subject before
      the research ever compares it, so `Fix parser` is admitted there and was rejected here.

      **REJECTIONS ARE COUNTED, NEVER SILENT.** Each clause can reject everything, and a run that
      admitted nothing prints the same "no events" as a repository that genuinely has none. The
      counts are what tell those apart.
IMPORTS: types.commit. Nothing from `ingest/` -- this receives a history, it does not read one.
CONSUMED BY: serve/retrospective.py; tests/live/test_event_replay_gate.py;
      tests/live/test_gate_2b_pinned_corpus.py.
"""

from __future__ import annotations

import collections
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from quantamind.types.commit import Commit
from quantamind.types.replay_outcome import MIN_DISCORDANT, MIN_EVENTS  # noqa: F401

# Copied from defect_return.py. Not chosen here.
WINDOW_SECONDS = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MIN_FILES, MAX_FILES = 2, 12
# 400 is the research's cap and it counts SURVIVORS of the flat-score skip, not admissions --
# `defect_return.py` appends an event and only then checks `len(events) >= 400`. The skip needs
# SCORES, which need the store, which `rank/events.py` may not reach. **So this cap cannot be
# applied here and is deliberately not this function's default.** It lives here as the number the
# scorer should use, and `serve/retrospective.py` is where it is applied.
SURVIVOR_CAP = 400
# The pre-registered floors live in `types/retrospective.py`, imported rather than restated: two
# copies of a number that must agree is the drift this module exists to stop.

TOO_FEW_FILES = "file count outside 2..12"
NO_RETURN = "no later fix returned to it"


OUT_OF_ORDER = "commit stamped before its predecessor"


class ReversedHistory(ValueError):
    """The history runs newest-first. Nothing can be measured from it and nothing is guessed."""

    def __init__(self, first: int, last: int) -> None:
        super().__init__(
            f"history ends at {last}, before it begins at {first}: it is newest-first. The "
            f"ninety-day scan walks forward and would admit almost nothing, which reads exactly "
            f"like a repository whose fixes are rare. `read_commits` passes --reverse; a caller "
            f"that sorted afterwards has undone it."
        )


@dataclass(frozen=True, slots=True)
class Event:
    """A change a later fix came back to, and the files that fix touched again.

    `at` is the bound: every score for this event must be computed over history strictly before
    it. `target` is the subset of the change's files a later fix returned to -- the thing a
    ranking is trying to put in its top three.
    """

    at: int
    paths: frozenset[str]
    target: frozenset[str]

    def __post_init__(self) -> None:
        if not self.target:
            raise ValueError("an event with no returned-to file is not an event")
        if not self.target <= self.paths:
            raise ValueError(f"target {sorted(self.target - self.paths)} is not in the change")


@dataclass(slots=True)
class Rejections:
    """Every commit passed over, with the reason. Printed by the caller, never discarded."""

    counts: collections.Counter[str] = field(default_factory=collections.Counter)

    def record(self, reason: str) -> None:
        self.counts[reason] += 1

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def returns_to(commits: Sequence[Commit], index: int) -> frozenset[str]:
    """The files of commit `index` that a later fix-shaped commit touches again within the window.

    Case-INSENSITIVE on the subject, matching `commit_stream.py`, which lowercases before the
    research compares. The walk stops at the first commit past the window because the history is
    oldest-first, so everything after it is further away.
    """
    origin = commits[index]
    files = origin.paths
    returned: set[str] = set()
    for later in commits[index + 1 :]:
        if later.committed_at - origin.committed_at > WINDOW_SECONDS:
            break
        if any(word in later.subject.lower() for word in FIXWORDS):
            returned |= later.paths & files
    return frozenset(returned)


def admissible(
    commits: Sequence[Commit], rejections: Rejections | None = None, limit: int | None = None
) -> Iterator[Event]:
    """Yield each admissible event, oldest first, at most `cap` of them.

    `read_commits` passes `--reverse` but does NOT verify the result, and this docstring once
    claimed that it did -- a statement about another module's behaviour, written where nothing
    could check it.

    **REAL HISTORIES ARE NOT MONOTONIC AND THAT IS NOT AN ERROR.** `--reverse` orders by graph
    traversal, so author and committer dates run backwards across merges, rebases and clock skew.
    Every repository in the pinned corpus does it: 1 to 64 inversions each, 0.01% to 0.20% of
    commits, the worst a 56-day jump in scrapy.

    `returns_to()` BREAKS out of the ninety-day scan at the first commit past the window, so an
    inversion truncates that scan early and the event is admitted with a smaller target set.
    **`defect_return.py` does exactly the same** -- `if ts2 - ts > WINDOW: break` -- so this is
    the validated policy's own behaviour, and raising here would make the product stricter than
    the measurement gate 2b holds it to. It is COUNTED instead, under `OUT_OF_ORDER`, so the
    retrospective prints it rather than absorbing it.

    A history that is backwards END TO END is a different thing: that is a caller who re-sorted,
    it can measure nothing, and it raises `ReversedHistory`.

    **`limit` COUNTS ADMISSIONS AND IS NOT THE RESEARCH'S CAP.** It defaults to None -- yield
    everything -- because the research's 400 counts events that SURVIVED the flat-score skip, and
    that skip cannot be evaluated here: it needs scores, which need the store, which this layer
    may not reach. Capping admissions instead loses events unevenly, because each repository has
    its own flat-score rate:

        ansible 392 of 400   celery 391   django 370   pandas 397   scikit-learn 360   scrapy 368

    Pooled that is 2,278 against 2,400, and the shortfall runs from 0.75% (pandas) to 10%
    (scikit-learn). **It does not merely shrink the sample, it REWEIGHTS the repositories inside a
    pooled figure**, and it stops earlier in history -- five weeks earlier on scrapy. Gate 2b would
    fail against the checked-in artefact for a reason having nothing to do with the definition.
    """
    # GLOBALLY backwards is a caller error and stops everything. LOCALLY backwards is git, and
    # it is counted instead -- see the docstring. Measured on the pinned corpus: 1 to 64
    # inversions per repository, 0.01% to 0.20% of commits, worst jump 56 days.
    if len(commits) > 1 and commits[-1].committed_at < commits[0].committed_at:
        raise ReversedHistory(commits[0].committed_at, commits[-1].committed_at)
    if rejections is not None:
        for position in range(1, len(commits)):
            if commits[position].committed_at < commits[position - 1].committed_at:
                rejections.record(OUT_OF_ORDER)
    yielded = 0
    for position, commit in enumerate(commits):
        if not MIN_FILES <= len(commit.paths) <= MAX_FILES:
            if rejections is not None:
                rejections.record(TOO_FEW_FILES)
            continue
        target = returns_to(commits, position)
        if not target:
            if rejections is not None:
                rejections.record(NO_RETURN)
            continue
        yield Event(at=commit.committed_at, paths=frozenset(commit.paths), target=target)
        yielded += 1
        if limit is not None and yielded >= limit:
            return
