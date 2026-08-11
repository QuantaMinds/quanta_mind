"""Pilot metrics: attrition split by the covariates that decide whether it is differential.

WHAT: Turns per-PR attempt records into the shape report — admission by category, and
      attrition cross-tabulated against commit count, corpus file count, and
      A20's changed-lines quartile.
WHY:  A single attrition percentage is the wrong summary. The first smoke run lost 32%
      of PRs, and the dominant stage was `parent_commit`: shape detection fails when the
      corpus file list does not match the change, which happens when the branch base has
      diverged, which tracks patch size and commit count.

      That is differential exclusion on the study's own confounder, not noise. So the
      report cross-tabulates rather than totals, and the three categories are kept apart:
      `restricted` narrows the estimand, `resource` and `integrity` bias it.
IMPORTS: stdlib collections; phase0.handlabel.select, phase0.pilot.{attempt,quartile}.
      External lookups (stars, default branch) live in pilot/repo_facts.py.
CONSUMED BY: pilot/run.py; tests/pilot/test_compare.py.
"""

from __future__ import annotations

from collections import Counter

from phase0.handlabel.select import Candidate
from phase0.pilot.attempt import Attempt
from phase0.pilot.quartile import by_changed_lines

# Commit-count bands. Chosen before the run and kept coarse: with a few hundred PRs,
# quartiles cut from the data would move with it, and a moving boundary is a degree of
# freedom. 1 is a squash, 2-5 an ordinary branch, 6+ a long-lived one.
COMMIT_BANDS: tuple[tuple[str, int, int], ...] = (
    ("1", 1, 1),
    ("2-5", 2, 5),
    ("6-20", 6, 20),
    ("21+", 21, 10**9),
)

# Corpus-attributed .py file counts. The package's median is 4 and its p90 is 52, so the
# top band is where over-attribution lives.
FILE_BANDS: tuple[tuple[str, int, int], ...] = (
    ("1-4", 1, 4),
    ("5-15", 5, 15),
    ("16-50", 16, 50),
    ("51+", 51, 10**9),
)


def by_repo(population: list[Candidate]) -> dict[str, list[Candidate]]:
    """Candidates grouped by repository, so each is cloned once."""
    grouped: dict[str, list[Candidate]] = {}
    for candidate in population:
        grouped.setdefault(candidate.repo, []).append(candidate)
    return grouped


def _band(value: int, bands: tuple[tuple[str, int, int], ...]) -> str:
    for name, low, high in bands:
        if low <= value <= high:
            return name
    return "unknown"


def _cross(attempts: list[Attempt], bands: tuple[tuple[str, int, int], ...], field: str) -> dict:
    """Admission rate within each band, so a trend is visible rather than pooled away."""
    out: dict[str, dict[str, object]] = {}
    for name, _, _ in bands:
        # A row whose banding field was never measured is dropped, not banded. `_band`
        # would send None to "unknown", which then reads as a band alongside the real
        # ones; a PR we did not measure belongs in no band at all.
        rows = [
            a
            for a in attempts
            if getattr(a, field) is not None and _band(getattr(a, field), bands) == name
        ]
        if not rows:
            continue
        admitted = sum(1 for a in rows if a.admitted)
        out[name] = {
            "n": len(rows),
            "admitted": admitted,
            "admission_rate": round(admitted / len(rows), 4),
            "by_stage": dict(Counter(a.stage for a in rows if not a.admitted)),
        }
    return out


def report(attempts: list[Attempt], clone_failures: int, repos: int) -> dict[str, object]:
    """Everything the pilot is for, and no point estimate of an effect."""
    admitted = [a for a in attempts if a.admitted]
    rejected = [a for a in attempts if not a.admitted]
    # `is not None`, not `or 0`. Both are measured on every admitted row today, so an
    # absent one means a journal that did not record it -- and substituting 0 would put a
    # PR that changed an unknown number of files into the "changed nothing" bucket, which
    # is the shape of error this field was just fixed for.
    symbols = sorted(a.changed_symbols for a in admitted if a.changed_symbols is not None)
    files = sorted(a.derived_files for a in admitted if a.derived_files is not None)
    # UNSCANNABLE is excluded from the denominator, not counted clean. Folding it in
    # would restore the exact bias the base-branch fix removed, one layer up.
    scanned = [a for a in admitted if a.outcome in ("broke", "clean")]
    unscannable = [a for a in admitted if a.outcome == "unscannable"]
    broke = [a for a in scanned if a.outcome == "broke"]
    # Excluded from BOTH, never folded into off-default. `not base_is_default` used to
    # sweep an unchecked repository into the off-default arm, where it would have read as
    # a measurement -- the same error UNSCANNABLE gets kept out of the clean cell for.
    on_default = [a for a in scanned if a.base_on_default == "yes"]
    off_default = [a for a in scanned if a.base_on_default == "no"]
    base_unknown = [a for a in scanned if a.base_on_default not in ("yes", "no")]
    # The ARM travels INSIDE the band counts, and mixed arms raise. A star band read
    # without its arm is how A15 came to be retired: the 90-repository pilot's bands were
    # all >=500, that was read as "the agent arm self-selected into the human band through
    # attrition", and the pilot was the HUMAN arm -- which A15 itself states is >=500 BY
    # CONSTRUCTION. The evidence was the premise restated, and it is unfalsifiable: for
    # the human arm there is no observation that could have come out below 500.
    #
    # A sibling key would drift; nesting it means a consumer cannot read a band without
    # reading whose band it is. Second occurrence of the arm-confusion class, so it gets
    # a mechanism rather than vigilance -- the same reasoning as `arm.verify` asserting
    # before the first clone.
    arms = {a.arm for a in admitted if a.arm}
    if len(arms) > 1:
        raise ValueError(
            f"star bands computed over MIXED arms {sorted(arms)}: a pooled band is not a "
            f"property of either arm, and reading one as if it were is the A15 defect."
        )
    star_bands: dict[str, object] = {
        # "" means UNRECORDED -- a journal written before the arm column -- never a claim
        # that the arm is unknown to the study.
        "arm": next(iter(arms), ""),
        **Counter(
            "unknown" if a.stars < 0 else ("<500" if a.stars < 500 else ">=500") for a in admitted
        ),
    }
    repo_counts = Counter(a.repo for a in admitted)

    return {
        "repositories_visited": repos,
        "clone_failures": clone_failures,
        "prs_attempted": len(attempts),
        "records_built": len(admitted),
        "admission_rate": round(len(admitted) / len(attempts), 4) if attempts else 0.0,
        "rejected_by_stage": dict(Counter(a.stage for a in rejected)),
        "rejected_by_category": dict(Counter(a.category for a in rejected)),
        "attrition_by_commit_count": _cross(attempts, COMMIT_BANDS, "commit_count"),
        # Kept under its original name so pre-fix runs stay comparable, but it bands on the
        # CORPUS's claim, which is not a measurement: verified against GitHub, the corpus
        # said 104, 65 and 40 `.py` files for PRs whose real file lists were 2, 9 and 2
        # with zero `.py` among them. A25 reads this table to decide whether attrition
        # tracks patch size; on these bands it cannot.
        "attrition_by_corpus_file_count": _cross(attempts, FILE_BANDS, "corpus_py_files"),
        # The same banding over GitHub's own count. Rows predating the column are dropped
        # rather than banded, so this table is empty on an old journal instead of wrong.
        "attrition_by_github_file_count": _cross(attempts, FILE_BANDS, "github_py_files"),
        # A20, pre-registered and previously unimplemented. Commit count and file count
        # are correlates of patch size; changed lines is the variable A20 names, and
        # `file_set` is the gate it names. A rising rate across quartiles makes A16's
        # stratified RR the only quotable result.
        "file_set_disagreement_by_changed_lines": by_changed_lines(attempts),
        "median_changed_files": files[len(files) // 2] if files else 0,
        "median_changed_symbols": symbols[len(symbols) // 2] if symbols else 0,
        "distinct_repos_in_records": len(repo_counts),
        "top_repo_share": round(max(repo_counts.values()) / len(admitted), 4) if admitted else 0.0,
        "star_band": star_bands,
        # The power projection. `a >= 20` in the exposed arm is the binding constraint,
        # and the corpus is skewed toward small single-commit changes by the attrition
        # above -- the end of the distribution least likely to break anything. A rate
        # near 3% means the planned corpus is underpowered and the window or the size
        # has to change before the full run, not after.
        "outcome_unscannable": len(unscannable),
        # Split by base branch: if the two rates differ materially the population really
        # differs and this becomes a stratum, rather than the fix having merely moved a
        # number. If they match, the fix was purely corrective and that can be said.
        "breakage_rate_default_branch": round(
            sum(a.outcome == "broke" for a in on_default) / len(on_default), 4
        )
        if on_default
        else None,
        "breakage_rate_other_branch": round(
            sum(a.outcome == "broke" for a in off_default) / len(off_default), 4
        )
        if off_default
        else None,
        "scanned_on_default": len(on_default),
        "scanned_off_default": len(off_default),
        # Reported, not silently dropped. A non-zero count here means some repository's
        # default branch could not be looked up, so the off-default share -- which the
        # analysis stratifies on -- is computed over a smaller denominator than
        # `outcome_scanned`. Silence would make the two look like the same population.
        "base_branch_unknown": len(base_unknown),
        "outcome_scanned": len(scanned),
        "outcome_broke": len(broke),
        "breakage_rate": round(len(broke) / len(scanned), 4) if scanned else None,
        # Prevalence of unreachable merges over EVERY attempt, not over the scanned
        # survivors. The four agentops PRs that exposed the case were rejected at
        # `no_python` before any scan ran, so a scan-time count would report the residue.
        # A17's accounting reads this one.
        "merge_on_base_all_attempts": dict(Counter(a.merge_on_base for a in attempts)),
        "merge_on_base_admitted": dict(Counter(a.merge_on_base for a in admitted)),
    }
