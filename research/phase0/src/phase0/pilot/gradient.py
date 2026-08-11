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
from phase0.pipeline.rejection import CLONE_STAGES

PARENT_STAGE = "parent_commit"

# Below this a band's rate is one or two PRs and cannot carry a trend. Fixed here rather
# than chosen once the bands are in front of us.
MIN_BAND_N = 5

# How far above the pooled rate the largest band must sit to count as concentrated. Two
# is deliberately blunt: the failure this exists to catch was 12.8x, and a threshold tuned
# finely enough to argue about would be a threshold chosen after seeing the data.
TOP_BAND_MULTIPLE = 2.0


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
        lost = [a for a in rows if a.stage in CLONE_STAGES]
        reachable = [a for a in rows if a.stage not in CLONE_STAGES]
        bands[name] = {
            "n": len(rows),
            "parent_commit_failures": failed,
            "failure_rate": round(failed / len(rows), 4),
            # Stated per band, so a verdict computed over three of four bands cannot be
            # read as if it covered all of them.
            "counted_in_trend": len(rows) >= MIN_BAND_N,
            # NOT `lost_to_clone_timeout`, which is what this was called while holding
            # `repo_gone` and `clone_failed` rows too -- a field name asserting a cause
            # its value does not carry. Rule 14 applied to a key rather than a comment.
            "lost_to_clone_failure": len(lost),
            "repos_lost": sorted({a.repo for a in lost}),
            "distinct_repos_present": len({a.repo for a in reachable}),
            # Which repositories the FAILURES came from, not just the band. A band rate is
            # a size effect only if several projects produce it: all three failures in the
            # human arm's 21-plus band were `featureform/enrichmcp`, a repository that
            # rewrote its history, so the band said 25% and the corpus said nothing.
            "failure_repos": sorted({a.repo for a in rows if a.stage == PARENT_STAGE}),
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

    # Losses that carry no commit count cannot be attributed to a band. Journals written
    # before that was fixed record 0 for every clone failure, so `share_lost` reads 0.0
    # in every band while the losses are real. Reported at the top level: a zero share
    # beside a non-zero count here means NOT MEASURED, not NOTHING LOST.
    unbanded = sum(
        1 for a in attempts if a.stage in CLONE_STAGES and _band_of(a.commit_count) == "unknown"
    )
    pooled = (
        round(sum(1 for a in attempts if a.stage == PARENT_STAGE) / len(attempts), 4)
        if attempts
        else None
    )
    # Monotonicity was the only test, and it answers the wrong question. The CONCERN is
    # whether failure concentrates on the largest PRs; `rising` asks whether it climbs at
    # every step. A spike confined to the top band answers yes to the first and no to the
    # second, and that is exactly what the human arm produced: 25.0% at 21-plus against
    # 1.96% below it, P = 0.0060, reported as "gradient flattened".
    top = trend[-1] if trend else None
    elevated = bool(top and pooled and top[1] >= TOP_BAND_MULTIPLE * pooled)

    # ...and elevation alone would then have chased a phantom. All three failures in that
    # band were ONE repository, which rewrote its history -- see
    # `results/handverify_21plus.md`. A rate produced by a single project is not a size
    # effect, and the honest output is neither verdict. Refused rather than guessed, the
    # same way a trend is refused below MIN_BAND_N.
    top_band = bands.get(top[0]) if top else None
    top_repos = len(top_band["failure_repos"]) if top_band else 0  # type: ignore[arg-type]
    # Conditional on ELEVATION. A band with one failure is single-repo by arithmetic, and
    # refusing a verdict there would withhold an answer wherever the top band is quiet --
    # which is most of the time, and is the outcome A28 predicts. The refusal is for a
    # spike that cannot be attributed, not for the absence of one.
    single_repo_top = bool(
        elevated and top_band and top_band["parent_commit_failures"] and top_repos < 2
    )

    if rising is None:
        verdict = None
    elif single_repo_top:
        verdict = "single_repo_band, verdict unavailable"
    elif rising:
        verdict = "mechanism may remain"
    elif elevated:
        verdict = "top band elevated"
    else:
        verdict = "gradient flattened"

    return {
        "bands": bands,
        "unbanded_clone_failures": unbanded,
        "share_lost_is_trustworthy": unbanded == 0,
        "bands_in_trend": [name for name, _ in trend],
        # None is not "flat". Fewer than two usable bands means the question was not
        # answered, and a verdict of "flattened" from one band would be the same false
        # reassurance the rest of this instrument keeps producing.
        "still_rises_with_size": rising,
        "top_band_elevated": elevated,
        "top_band_failure_repos": top_repos,
        "top_band_is_single_repo": single_repo_top,
        "verdict": verdict,
        "pooled_failure_rate": pooled,
    }
