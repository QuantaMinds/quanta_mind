"""Turn scores into a `Ranking`: the budget, the allocation labels, and the firing percentile.

WHAT: `rank()` builds a `Ranking` from {path: prior count} — ordered, labelled DEEP/SHALLOW/COLD,
      and carrying whether this change is worth speaking on at all.
WHY:  `score.py` decides the ORDER, which is the half with the p-value. This module decides **how
      much of that order gets funded and whether we open our mouth**, and those are two different
      failures: a wrong order misses defects, a wrong threshold buries the customer in noise or
      goes silent for a month.

      **The firing rule is a PERCENTILE, not an absolute score.** An absolute threshold fired on
      11% of one repository and 53% of another — the same rule an order of magnitude apart in
      volume, because a busy repository's ordinary file outscores a quiet repository's hottest one.
      Percentiles self-calibrate to 10-12% across an 80x velocity range.

      **The percentile is computed against THIS change's own scores**, which is the honest
      available comparison and also the weakest part of this module: on a two-file change the
      percentile is nearly meaningless. A repository-wide distribution would be better and needs
      the store to carry one, so `fires()` takes the distribution as an argument rather than
      assuming it.

      **COLD units are returned, never dropped.** A cold unit produces no finding and no error,
      which is silence indistinguishable from a clean read — so it is a labelled row that renders
      into the coverage line. Dropping them also removes shadow evaluation's denominator.

      **Nothing here re-orders.** The sequence comes from `score.order()` untouched, because gate
      2a compares that sequence against the research ranker element by element.
      **THIS RANKS FILES, NOT FUNCTIONS, and `Site(path, line=0)` is what says so** — zero means
      the whole file. The measured policy is file-level: function-level top-three misses **8.84%**
      of the changes a later fix returns to against the file's **1.22%**, and matched at top-five
      it is still 3.50%. A `ChangedUnit` whose site names a line would be claiming a resolution the
      ranking does not have, so the path is both the site and the qualified name.
IMPORTS: types (Allocation, ChangedUnit, Language, Ranking, RankedUnit, Score, Site), rank.score.
CONSUMED BY: allocate, render, serve.
"""

from __future__ import annotations

from collections.abc import Mapping

from quantamind.rank.score import discriminate, order
from quantamind.types.change import ChangedUnit, Language
from quantamind.types.ranking import Allocation, Discrimination, RankedUnit, Ranking, Score
from quantamind.types.verdict import Site

# The budget the research measured: ranks 1-3 are funded. Top-3 file-level misses 1.22% of the
# changes a later fix returns to; top-5 would miss less and cost more, and the trade was decided
# in docs/findings/ALLOCATION_EVIDENCE_2026-08.md rather than here.
BUDGET = 3
DEEP_RANKS = 1
DEFAULT_THRESHOLD = 0.9


def percentiles(scores: Mapping[str, int]) -> dict[str, float]:
    """Each path's position in this change's own score distribution, in [0, 1].

    Ties share the HIGHEST percentile they could claim, so a file cannot be pushed below an
    equally-touched sibling by an accident of iteration order.
    """
    if not scores:
        return {}
    ordered_values = sorted(scores.values())
    n = len(ordered_values)
    out: dict[str, float] = {}
    for path, value in scores.items():
        at_or_below = sum(1 for v in ordered_values if v <= value)
        out[path] = at_or_below / n
    return out


def fires(scores: Mapping[str, int], baseline: int | None = None) -> bool:
    """Whether this change is worth speaking on.

    **`baseline` IS THIS REPOSITORY'S TOP-DECILE TOUCH COUNT, AND WITHOUT IT THIS RULE IS THE ONE
    THE RESEARCH REJECTED.** `docs/findings/RETROSPECTIVE_SWEEP_2026-08.md` measured the firing rule
    and its heading is *"The firing rule that works: a percentile, not a threshold"* -- an absolute
    threshold fired on **11% of cartography and 53% of Skyvern**, an order of magnitude apart for
    the same rule. With `baseline=None` this falls back to `max(scores) > 0`, which is that rejected
    threshold at its loosest setting: measured on `trpc/trpc` it fired on **198 of 200** real
    changes, 99.0%, against a documented 10-12%.

    **The fallback is kept and is NOT the default anyone should ship**, because a caller with no
    repository index still needs an answer, and returning False there would silence a ranking that
    is perfectly good. `serve/run_review.py` passes the baseline.

    False when there is nothing to rank: with every file at zero the ordering is alphabetical, and
    speaking would present `sort(filenames)` as a judgement about risk. Staying quiet is the
    honest behaviour, and the caller can still tell WHY -- `Ranking.discrimination` separates
    NO_HISTORY from FLAT_NONZERO, so silence is never a bare absence.

    **This is the 4.61% of changes the ranker cannot help with**, and the number has a source:
    `research/phase0/external/degenerate_rate.json` classifies 9,600 out-of-sample events as 157
    no-history and 286 flat-history, and (157 + 286) / 9,600 = 4.61%. A previous edit of this
    docstring deleted the figure as unsourced after grepping for the literal string rather than
    for the artefact that produces it -- removing a correct citation is the same defect as
    inventing one, and it was committed here.
    """
    if discriminate(scores) is Discrimination.NO_HISTORY:
        return False
    top = max(scores.values(), default=0)
    if baseline is None:
        return top > 0
    # At or above the repository's own top decile. `>=` rather than `>`: the baseline IS a touch
    # count some file has, and a file tying the decile boundary is in the decile.
    return top >= baseline and top > 0


class NothingToRank(ValueError):
    """`rank()` was called with no scores at all.

    Raised rather than returning an empty `Ranking`, because an empty ranking is a PUBLISHED
    artefact: it renders into a comment that says we looked and found nothing worth ordering. A
    caller whose diff fetch returned nothing would produce exactly that comment, and the customer
    could not tell the two apart. "This change touched no rankable files" is a decision the caller
    must record deliberately, not a value it can fall into.
    """


def rank(
    scores: Mapping[str, int],
    *,
    budget: int = BUDGET,
    threshold: float = DEFAULT_THRESHOLD,
    language: Language = Language.PYTHON,
    baseline: int | None = None,
) -> Ranking:
    """Every changed path, ordered and labelled. Cold units included by design."""
    if not scores:
        raise NothingToRank(
            "rank() received no scores. If the change genuinely touched no rankable files, "
            "record that deliberately; an empty ranking publishes as a clean review"
        )
    if budget < 0:
        raise ValueError(f"budget cannot be negative, got {budget}")
    ordered = order(scores)
    pcts = percentiles(scores)
    split = discriminate(scores)
    units: list[RankedUnit] = []
    for position, path in enumerate(ordered, start=1):
        if split is Discrimination.NO_HISTORY:
            # Nothing was ranked, so no position was chosen. Labelling the alphabetically-first
            # file DEEP would be inventing a decision -- and this is the slice that misses most.
            #
            # FLAT_NONZERO is deliberately NOT here. `feat-rank-fix-history.md` requires every
            # unit in a non-discriminating change to be "read, but not because we ranked it", and
            # in this codebase COLD means NOT READ -- `funded()` excludes it. The rule is honoured
            # in `render/coverage_line.py` instead, which says in those words that the ranking
            # could not separate the files and the order is alphabetical. Moving the flat case to
            # COLD here renders "Read: ." and funds nothing, which is a different claim entirely.
            allocation = Allocation.COLD
        elif position <= DEEP_RANKS:
            allocation = Allocation.DEEP
        elif position <= budget:
            allocation = Allocation.SHALLOW
        else:
            allocation = Allocation.COLD
        units.append(
            RankedUnit(
                unit=ChangedUnit(
                    site=Site(path=path, line=0),
                    qualified_name=path,
                    language=language,
                ),
                rank=position,
                score=Score(value=float(scores[path]), percentile=pcts[path]),
                allocation=allocation,
            )
        )
    return Ranking(
        units=tuple(units),
        fired=fires(scores, baseline),
        threshold_percentile=threshold,
        discrimination=split,
    )
