"""Stratified draw: equal numbers of each classifier verdict, shuffled, URLs only.

WHAT: Runs the outcome classifier over eligible PRs until both buckets are full, then
      emits a blind sheet (`label_id`, `pr_url`) and a sealed key.
WHY:  A random draw at the base rate hands the labeller roughly two broken PRs in twenty.
      Marking everything CLEAN would then score about 18/20 and pass a gate that proved
      nothing. Ten of each makes always-CLEAN score 10/20 and fail, so the gate tests the
      classifier rather than the base rate.

      Balance costs representativeness on purpose: agreement here estimates the average
      of sensitivity and specificity, NOT agreement over the corpus. It is a validation
      quantity, not a prevalence one, and must never be read as "right 80% of the time".

      Repositories are shuffled and capped rather than PRs -- shuffling PRs would mean a
      clone each, and stopping when the buckets fill would concentrate the sample in
      whichever repositories came first.
IMPORTS: phase0.extract_prs, phase0.outcome.{conclusion,scan,window},
      phase0.pipeline.worktree, phase0.handlabel.{select,sheet}.
CONSUMED BY: phase0/sample_for_labelling.py; tests/handlabel/.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.handlabel.select import Candidate
from phase0.handlabel.sheet import Drawn, KeyRow
from phase0.outcome.conclusion import Outcome, unhandled
from phase0.outcome.scan import scan
from phase0.outcome.window import Exclusion
from phase0.pipeline.worktree import CloneFailed, cloned

# At most this many PRs from any one repository. Without it, a repository with 40
# eligible PRs could supply the whole sample and the gate would measure one project.
MAX_PER_REPO = 3


@dataclass(frozen=True, slots=True)
class _Scored:
    """A classified PR on its way into a bucket. Internal; never serialised blind."""

    candidate: Candidate
    verdict: str  # "BROKE" | "CLEAN"
    criterion: str
    evidence_sha: str


def _as_record(candidate: Candidate) -> PRRecord:
    """The classifier's input. `parent_sha` is unused by the outcome scan."""
    return PRRecord(
        pr_id=str(candidate.pr_id),
        repo=candidate.repo,
        language="python",
        parent_sha="",
        merged_sha=candidate.commit_shas[-1] if candidate.commit_shas else "",
        merged_at=candidate.merged_at,
        changed_files=candidate.changed_files,
        changed_symbols=(),
        arm="human",
    )


def _shuffled_by_repo(
    population: list[Candidate], rng: random.Random
) -> list[tuple[str, list[Candidate]]]:
    """Repositories in random order, each contributing at most MAX_PER_REPO PRs."""
    grouped: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in population:
        grouped[candidate.repo].append(candidate)
    repos = sorted(grouped)
    rng.shuffle(repos)
    picked: list[tuple[str, list[Candidate]]] = []
    for repo in repos:
        prs = sorted(grouped[repo], key=lambda c: c.pr_id)
        rng.shuffle(prs)
        picked.append((repo, prs[:MAX_PER_REPO]))
    return picked


def draw(
    population: list[Candidate],
    workspace: Path,
    *,
    n_broke: int,
    n_clean: int,
    seed: int,
    on_progress: object = None,
) -> Drawn:
    """Fill both buckets, then shuffle. Deterministic for a given seed and package.

    Raises:
        ValueError: if the population cannot fill either bucket. The gate is not
            weakened to fit -- an unfillable bucket means the base rate is far from
            what was assumed, which is itself a result worth stopping on.
    """
    rng = random.Random(seed)
    # Each entry carries its own verdict. An earlier version recovered the verdict by
    # testing bucket membership after shuffling, which would have mislabelled the key
    # the moment two PRs compared equal -- deriving an answer that is already known.
    buckets: dict[Outcome, list[_Scored]] = {Outcome.BROKE: [], Outcome.CLEAN: []}
    wanted = {Outcome.BROKE: n_broke, Outcome.CLEAN: n_clean}
    considered = 0
    repos_visited = 0
    # PRs the scan could not look at. They are not eligible for either bucket -- a
    # hand-labeller cannot check a verdict the instrument never reached -- and they are
    # counted rather than skipped so the draw can report what it passed over. Before the
    # base-branch fix these arrived as CLEAN and were labelled as though they had been
    # measured, which would have scored the gate against answers nobody computed.
    unscannable: dict[Exclusion, int] = defaultdict(int)

    for repo, candidates in _shuffled_by_repo(population, rng):
        if all(len(buckets[o]) >= wanted[o] for o in wanted):
            break
        repos_visited += 1
        try:
            with cloned(repo, workspace) as path:
                for candidate in candidates:
                    if all(len(buckets[o]) >= wanted[o] for o in wanted):
                        break
                    considered += 1
                    record = scan(path, _as_record(candidate))
                    # Exhaustive rather than a membership test. `buckets` holds two keys,
                    # so the version that indexed it with the verdict directly raised
                    # KeyError the moment a third state existed -- and a fourth would do
                    # it again. mypy rejects an unhandled state here at check time.
                    match record.outcome:
                        case Outcome.UNSCANNABLE:
                            unscannable[record.exclusion] += 1
                            continue
                        case Outcome.BROKE | Outcome.CLEAN:
                            bucket = buckets[record.outcome]
                        case _:
                            unhandled(record.outcome)
                    if len(bucket) < wanted[record.outcome]:
                        buckets[record.outcome].append(
                            _Scored(
                                candidate=candidate,
                                verdict=record.outcome.value.upper(),
                                criterion=record.criterion.value,
                                evidence_sha=record.evidence_sha,
                            )
                        )
                    if callable(on_progress):
                        on_progress(
                            repo,
                            candidate,
                            len(buckets[Outcome.BROKE]),
                            len(buckets[Outcome.CLEAN]),
                        )
        except CloneFailed:
            # An unreadable repository contributes nothing and is skipped. It is not
            # scored as CLEAN, which is what an untyped failure here would have meant.
            continue

    for outcome, want in wanted.items():
        if len(buckets[outcome]) < want:
            raise ValueError(
                f"only {len(buckets[outcome])} {outcome.value.upper()} PRs found in "
                f"{considered} examined across {repos_visited} repositories, need {want}. "
                f"Do not shrink the bucket to fit: a base rate this far from expectation "
                f"is a finding about the outcome rule, not a sampling inconvenience."
            )

    drawn = [row for outcome in (Outcome.BROKE, Outcome.CLEAN) for row in buckets[outcome]]
    rng.shuffle(drawn)

    blind = tuple((index, row.candidate.url) for index, row in enumerate(drawn, 1))
    key = tuple(
        KeyRow(
            label_id=index,
            pr_id=row.candidate.pr_id,
            repo=row.candidate.repo,
            number=row.candidate.number,
            verdict=row.verdict,
            criterion=row.criterion,
            evidence_sha=row.evidence_sha,
        )
        for index, row in enumerate(drawn, 1)
    )
    return Drawn(
        blind=blind,
        key=key,
        seed=seed,
        considered=considered,
        repos_visited=repos_visited,
        unscannable=dict(unscannable),
    )
