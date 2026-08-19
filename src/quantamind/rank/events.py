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
MAX_EVENTS = 400
# The pre-registered floors live in `types/retrospective.py`, imported rather than restated: two
# copies of a number that must agree is the drift this module exists to stop.

TOO_FEW_FILES = "file count outside 2..12"
NO_RETURN = "no later fix returned to it"


class UnorderedHistory(ValueError):
    """Commits are not oldest-first, so the ninety-day window cannot be walked by breaking out."""

    def __init__(self, position: int, earlier: Commit, later: Commit) -> None:
        super().__init__(
            f"commit {position} is stamped {later.committed_at}, before its predecessor "
            f"{earlier.committed_at} ({earlier.committed_at - later.committed_at}s earlier). "
            f"The window scan stops at the first commit past ninety days, so a history that goes "
            f"backwards truncates it and reports too few events rather than failing."
        )
        self.position = position


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
    commits: Sequence[Commit], rejections: Rejections | None = None, cap: int = MAX_EVENTS
) -> Iterator[Event]:
    """Yield each admissible event, oldest first, at most `cap` of them.

    Raises `UnorderedHistory` unless `commits` is oldest-first. `read_commits` passes `--reverse`
    but does NOT verify the result, and this docstring used to claim that it did -- a statement
    about another module's behaviour, written where nothing could check it.

    **The check is not defensive padding.** `returns_to()` BREAKS out of the ninety-day scan at
    the first commit past the window, which is only sound if timestamps rise. A rebase, a
    cherry-pick or clock skew on one commit truncates the search silently, and the result is
    fewer admissible events -- indistinguishable from a repository whose fixes are genuinely
    rare. Reversed entirely, it admits nothing at all and reads as a clean run.

    The cap is the research's: without it the largest repository dominates a pooled figure.
    """
    for position in range(1, len(commits)):
        if commits[position].committed_at < commits[position - 1].committed_at:
            raise UnorderedHistory(position, commits[position - 1], commits[position])
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
        if yielded >= cap:
            return
