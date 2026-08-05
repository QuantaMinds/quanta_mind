"""Did the size gradient in `parent_commit` failure actually flatten?

WHAT: `parent_gradient` — the `parent_commit` rejection rate per commit-count band, and
      whether it still rises with size.
WHY:  A2's detection rule told squash from rebase using the corpus file list, and the
      corpus attributes 92 `.py` files to some three-file PRs. So detection failed on
      exactly the PRs whose file lists were wrong, at 17-70% across commit-count bands —
      differential exclusion on patch size, which is the study's own confounder. A28
      replaced that with the subject sequence, which reads nothing from the corpus.

      The check that the replacement WORKED is not that attrition fell. Attrition falls
      whether the recovered parents are right or wrong, and a rule that resolves a wrong
      parent recovers PRs enthusiastically. Correctness is settled by hand-verification
      against `merge_commit_sha`'s first parent (A28). What THIS module settles is
      whether the mechanism is gone: if failure still climbs monotonically with commit
      count, some file-set dependence remains and the confounder still enters here.

      Monotone is judged on bands with enough units to mean anything. Two PRs in the 21+
      band produce a rate of 0.0 or 0.5 or 1.0 and would drive the verdict on noise, so
      thin bands are reported and excluded from the trend rather than silently included.
IMPORTS: phase0.pilot.attempt, phase0.pilot.report for the pre-registered bands.
CONSUMED BY: pilot/compare.py; tests/pilot/test_gradient.py.
"""

from __future__ import annotations

from itertools import pairwise

from phase0.pilot.attempt import Attempt
from phase0.pilot.report import COMMIT_BANDS

PARENT_STAGE = "parent_commit"
CLONE_FAILED = "clone_failed"

# Below this a band's rate is one or two PRs and cannot carry a trend. Fixed here rather
# than chosen once the bands are in front of us.
MIN_BAND_N = 5


def _band_of(value: int) -> str:
    for name, low, high in COMMIT_BANDS:
        if low <= value <= high:
            return name
    return "unknown"


def parent_gradient(attempts: list[Attempt]) -> dict[str, object]:
    """Per-band `parent_commit` failure, and whether it still rises with commit count."""
    bands: dict[str, dict[str, object]] = {}
    for name, _, _ in COMMIT_BANDS:
        rows = [a for a in attempts if _band_of(a.commit_count) == name]
        if not rows:
            continue
        failed = sum(1 for a in rows if a.stage == PARENT_STAGE)
        # A band can be populated and still be unrepresentative. Clone timeouts remove
        # the largest repositories, and the largest repositories hold the multi-commit
        # PRs -- so a flat rate in the 21+ band could mean "the mechanism is gone" or
        # "the hard cases never arrived", and those look identical without this column.
        lost = [a for a in rows if a.stage == CLONE_FAILED]
        reachable = [a for a in rows if a.stage != CLONE_FAILED]
        bands[name] = {
            "n": len(rows),
            "parent_commit_failures": failed,
            "failure_rate": round(failed / len(rows), 4),
            # Stated per band, so a verdict computed over three of four bands cannot be
            # read as if it covered all of them.
            "counted_in_trend": len(rows) >= MIN_BAND_N,
            "lost_to_clone_timeout": len(lost),
            "repos_lost": sorted({a.repo for a in lost}),
            "distinct_repos_present": len({a.repo for a in reachable}),
            # The share of the band that never reached the rule at all. A high value here
            # makes the band's failure rate a statement about survivors, not about size.
            "share_lost": round(len(lost) / len(rows), 4),
        }

    trend = [
        (name, float(band["failure_rate"]))  # type: ignore[arg-type]
        for name, band in bands.items()
        if band["counted_in_trend"]
    ]
    # Monotone non-decreasing AND actually higher at the top. `>=` on its own calls a FLAT
    # gradient rising -- and flat is exactly the outcome A28 predicts, so the check would
    # report "mechanism may remain" on the evidence that the mechanism is gone. Wrong in
    # the safe direction, but an alarm that fires on success is one nobody keeps heeding.
    rising = (
        all(b >= a for (_, a), (_, b) in pairwise(trend)) and trend[-1][1] > trend[0][1]
        if len(trend) >= 2
        else None
    )

    return {
        "bands": bands,
        "bands_in_trend": [name for name, _ in trend],
        # None is not "flat". Fewer than two usable bands means the question was not
        # answered, and a verdict of "flattened" from one band would be the same false
        # reassurance the rest of this instrument keeps producing.
        "still_rises_with_size": rising,
        "verdict": None
        if rising is None
        else ("mechanism may remain" if rising else "gradient flattened"),
        "pooled_failure_rate": round(
            sum(1 for a in attempts if a.stage == PARENT_STAGE) / len(attempts), 4
        )
        if attempts
        else None,
    }
