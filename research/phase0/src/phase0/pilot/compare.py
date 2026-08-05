"""Did the fix correct the measurement, or only change it?

WHAT: `compare` — the breakage rate split by base branch, the unreachable-merge
      prevalence at admission versus after the gate, and corpus composition against a
      pre-fix baseline. `python -m phase0.pilot.compare <baseline.json> <journal.md>`.
WHY:  A re-run after a measurement fix produces a different number whether or not the fix
      was correct, so the number alone proves nothing. Three comparisons that do:

      **Split by the stratum the defect selected on.** The base-branch bug only ever
      touched PRs merging off the default branch. If the two rates differ materially the
      population genuinely differs and this becomes a stratum for the full run; if they
      match, the fix was purely corrective and that can be said. Either way it is the
      check that distinguishes a corrected number from a merely different one.

      **Prevalence before the gate, not after it.** The outcome scan only sees survivors,
      so an unreachable-merge count taken there reports the residue.

      **Composition, because A16's confounder is measured on the corpus.** If admission
      moved, the number the full run's interpretation rests on moved with it.

      One denominator trap is handled explicitly. The baseline counted clone failures at
      REPOSITORY level and emitted no PR rows; the current runner emits one row per PR, on
      purpose, so the denominator stops moving with the weather. Differencing those
      directly would report a corpus shift that is really a definition change, so the new
      run is reduced twice and only the baseline-matching reduction is compared.

      Churn in both directions needs a per-PR baseline journal. When only the aggregate
      exists the result says so rather than printing a number it cannot support -- a
      net-flat rate hiding a large two-way churn means something quite different from a
      corpus that did not move.
IMPORTS: phase0.pilot.{attempt,report}, phase0.pipeline.journal.
CONSUMED BY: `python -m phase0.pilot.compare`; tests/pilot/test_compare.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from phase0.pilot.attempt import Attempt
from phase0.pilot.gradient import parent_gradient
from phase0.pilot.report import report
from phase0.pipeline import journal

# A gap this wide or wider means the two arms are different populations, not one
# population measured twice. Fixed here rather than chosen after seeing the split.
MATERIAL_GAP = 0.05

CLONE_FAILED = "clone_failed"


def _bands(old: dict, new: dict, key: str) -> dict[str, object]:
    """Admission rate per band, old against new, with the delta made explicit."""
    out: dict[str, object] = {}
    for band in dict.fromkeys(list(old.get(key, {})) + list(new.get(key, {}))):
        before, after = old.get(key, {}).get(band), new.get(key, {}).get(band)
        if not before or not after:
            out[band] = {
                "n_old": before["n"] if before else None,
                "n_new": after["n"] if after else None,
            }
            continue
        out[band] = {
            "n_old": before["n"],
            "n_new": after["n"],
            "rate_old": before["admission_rate"],
            "rate_new": after["admission_rate"],
            "delta": round(after["admission_rate"] - before["admission_rate"], 4),
        }
    return out


def _churn(baseline_attempts: list[Attempt], attempts: list[Attempt]) -> dict[str, object]:
    """Newly admitted and newly rejected, separately.

    A shape fix is expected to recover PRs whose parent was mis-detected AND to reject
    PRs previously admitted on a WRONG parent. The second is a correction that costs
    power, and a net figure reports neither.
    """
    if not baseline_attempts:
        return {"available": False, "reason": "no per-PR baseline journal; only the aggregate"}
    before = {a.pr_id: a for a in baseline_attempts}
    after = {a.pr_id: a for a in attempts}
    shared = sorted(set(before) & set(after))
    gained = [p for p in shared if after[p].admitted and not before[p].admitted]
    lost = [p for p in shared if before[p].admitted and not after[p].admitted]
    return {
        "available": True,
        "compared": len(shared),
        "newly_admitted": len(gained),
        "newly_rejected": len(lost),
        "net": len(gained) - len(lost),
        "newly_rejected_detail": [f"{before[p].repo}#{p}->{after[p].stage}" for p in lost],
    }


def compare(
    baseline: dict, attempts: list[Attempt], baseline_attempts: list[Attempt] | None = None
) -> dict[str, object]:
    """The three comparisons, plus the denominator correction that makes the third valid."""
    repos = len({a.repo for a in attempts})
    as_recorded = report(attempts, 0, repos)

    dropped = [a for a in attempts if a.stage == CLONE_FAILED]
    comparable = report([a for a in attempts if a.stage != CLONE_FAILED], 0, repos)

    on = as_recorded.get("breakage_rate_default_branch")
    off = as_recorded.get("breakage_rate_other_branch")
    gap = abs(on - off) if isinstance(on, float) and isinstance(off, float) else None

    return {
        "breakage_rate": {
            "default_branch": on,
            "other_branch": off,
            "n_default": as_recorded.get("scanned_on_default"),
            "n_other": as_recorded.get("scanned_off_default"),
            "pooled": as_recorded.get("breakage_rate"),
            "unscannable_excluded": as_recorded.get("outcome_unscannable"),
            "absolute_gap": round(gap, 4) if gap is not None else None,
            # None is not "similar". One empty arm cannot answer the question at all.
            "verdict": None
            if gap is None
            else ("stratum" if gap >= MATERIAL_GAP else "corrective"),
        },
        "merge_on_base": {
            "all_attempts": as_recorded.get("merge_on_base_all_attempts"),
            "admitted_only": as_recorded.get("merge_on_base_admitted"),
        },
        "churn": _churn(baseline_attempts or [], attempts),
        "composition": {
            "clone_failed_rows_removed": len(dropped),
            "clone_failed_repos": sorted({a.repo for a in dropped}),
            "admission_rate_old": baseline["admission_rate"],
            "admission_rate_new": comparable["admission_rate"],
            "stages_old": baseline.get("rejected_by_stage"),
            "stages_new": comparable.get("rejected_by_stage"),
            "by_commit_count": _bands(baseline, comparable, "attrition_by_commit_count"),
            "by_corpus_file_count": _bands(baseline, comparable, "attrition_by_corpus_file_count"),
        },
        # Whether A28's replacement removed the MECHANISM, not merely the count. A
        # falling attrition rate proves nothing on its own; a gradient that still climbs
        # with commit count means a file-set dependence survives somewhere.
        "parent_commit_gradient": parent_gradient(attempts),
        "file_set_disagreement_by_changed_lines": as_recorded.get(
            "file_set_disagreement_by_changed_lines"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """`compare.py <baseline.json> <journal.md> [baseline_journal.md]`."""
    args = argv if argv is not None else sys.argv[1:]
    if not 2 <= len(args) <= 3:
        print(main.__doc__)
        return 2
    baseline = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    attempts = journal.read_attempts(Path(args[1]))
    prior = journal.read_attempts(Path(args[2])) if len(args) == 3 else []
    print(json.dumps(compare(baseline, attempts, prior), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
