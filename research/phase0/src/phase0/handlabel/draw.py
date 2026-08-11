"""Stratified draw: equal numbers of each classifier verdict, shuffled, URLs only.

WHAT: Runs the outcome classifier over eligible PRs until both buckets are full, then
      emits a blind sheet (`label_id`, `pr_url`) and a sealed key.
WHY:  A random draw at the base rate hands the labeller roughly two broken PRs in twenty,
      so always-CLEAN would score about 18/20 and prove nothing. The cells fill equally
      instead; `handlabel/strata.py` owns which cells there are and why.

      Balance costs representativeness on purpose: agreement here estimates the average
      of sensitivity and specificity, NOT agreement over the corpus. It is a validation
      quantity, not a prevalence one, and must never be read as "right 80% of the time".

      Repositories are shuffled and capped rather than PRs: shuffling PRs would mean a
      clone each, and stopping when the cells fill would concentrate the sample.
IMPORTS: phase0.extract_prs, phase0.outcome.{conclusion,scan,window},
      phase0.pipeline.worktree, phase0.handlabel.{select,sheet,strata}.
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
from phase0.handlabel.strata import Cell, band_of, cells_for, unfillable
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
    band: str  # "<500" | ">=500" -- part of the cell key, never re-derived later


def record_for(candidate: Candidate, records: dict[str, PRRecord]) -> PRRecord | None:
    """The pipeline's OWN record, or None when this candidate was never admitted.

    Returns the stored object rather than building one. `_as_record` used to rebuild the
    scan's input here and got `base_ref`, `arm` and `merged_sha` wrong -- three defects the
    pipeline had already fixed -- so the gate certified a classifier the study does not
    run. Named rather than inlined because `draw` clones over the network and cannot be
    tested offline, and nothing exercised `draw` at all while that drift survived.
    """
    return records.get(str(candidate.pr_id))


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
    records: dict[str, PRRecord],
    stars: dict[str, int],
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
    wanted = cells_for(n_broke, n_clean)
    buckets: dict[Cell, list[_Scored]] = {cell: [] for cell in wanted}
    considered = 0
    repos_visited = 0
    # Repositories whose size was never recorded. They cannot be placed in a band, so
    # they are skipped and COUNTED -- never folded into `<500`, which would put an
    # unmeasured unit into a stratum that is supposed to mean something about size.
    unbanded = 0
    # PRs the scan could not look at. They are not eligible for either bucket -- a
    # hand-labeller cannot check a verdict the instrument never reached -- and they are
    # counted rather than skipped so the draw can report what it passed over. Before the
    # base-branch fix these arrived as CLEAN and were labelled as though they had been
    # measured, which would have scored the gate against answers nobody computed.
    unscannable: dict[Exclusion, int] = defaultdict(int)

    for repo, candidates in _shuffled_by_repo(population, rng):
        if all(len(buckets[c]) >= wanted[c] for c in wanted):
            break
        band = band_of(stars.get(repo, -1))
        if band is None:
            unbanded += len(candidates)
            continue
        repos_visited += 1
        try:
            with cloned(repo, workspace) as path:
                for candidate in candidates:
                    if all(len(buckets[c]) >= wanted[c] for c in wanted):
                        break
                    # The pipeline's OWN record, never a reconstruction.
                    source = record_for(candidate, records)
                    if source is None:
                        continue
                    considered += 1
                    record = scan(path, source)
                    # Exhaustive rather than a membership test. `buckets` holds two keys,
                    # so the version that indexed it with the verdict directly raised
                    # KeyError the moment a third state existed -- and a fourth would do
                    # it again. mypy rejects an unhandled state here at check time.
                    match record.outcome:
                        case Outcome.UNSCANNABLE:
                            unscannable[record.exclusion] += 1
                            continue
                        case Outcome.BROKE | Outcome.CLEAN:
                            cell = Cell(record.outcome, band)
                        case _:
                            unhandled(record.outcome)
                    if len(buckets[cell]) < wanted[cell]:
                        buckets[cell].append(
                            _Scored(
                                candidate=candidate,
                                verdict=record.outcome.value.upper(),
                                criterion=record.criterion.value,
                                evidence_sha=record.evidence_sha,
                                band=band,
                            )
                        )
                    if callable(on_progress):
                        on_progress(
                            repo,
                            candidate,
                            sum(len(v) for c, v in buckets.items() if c.outcome is Outcome.BROKE),
                            sum(len(v) for c, v in buckets.items() if c.outcome is Outcome.CLEAN),
                        )
        except CloneFailed:
            # An unreadable repository contributes nothing and is skipped. It is not
            # scored as CLEAN, which is what an untyped failure here would have meant.
            continue

    for cell, want in wanted.items():
        if len(buckets[cell]) < want:
            raise ValueError(
                unfillable(cell, len(buckets[cell]), want, considered, repos_visited, MAX_PER_REPO)
            )

    drawn = [row for cell in wanted for row in buckets[cell]]
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
