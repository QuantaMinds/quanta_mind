"""A20's pre-registered metric: file-set disagreement rate by changed-lines quartile.

WHAT: `by_changed_lines` — cuts attempts into quartiles of changed lines and reports the
      `file_set` rejection rate within each, with the cut points printed alongside.
WHY:  Pre-registered in `PHASE0_PREREGISTRATION.md` “Missing patch text, traced to A16's
      confounder” and not implemented until now. The pilot banded attrition by commit
      count and corpus file count, which are CORRELATES of patch size; A20 names changed
      lines, and names the `file_set` gate specifically. Reporting a correlate and calling
      the metric done is how a pre-registration becomes decorative.

      What it decides: step 5's consistency gate turns a suspected wrong parent into
      counted attrition, and A20 requires that attrition be read BY SIZE. If disagreement
      rises across quartiles, A16's stratified RR is not merely co-primary but the only
      quotable result, and A17's bounds must be computed over the size-stratified
      exclusion rather than the pooled one.

      Quartiles are cut from the observed distribution, unlike `COMMIT_BANDS`, which are
      fixed precisely so a boundary cannot move with the data. That tension is real and
      resolved in favour of the pre-registration: A20 says quartile, so the cut points are
      REPORTED, which makes a moving boundary visible instead of merely absent.

      Attempts with no measured size are their own band. Folding a missing `changed_lines`
      into the lowest quartile would put every unmeasured PR in the band least likely to
      show disagreement, which is the direction that hides the effect.
IMPORTS: stdlib statistics; phase0.pilot.attempt.
CONSUMED BY: pilot/report.py; tests/pilot/test_quartile.py.
"""

from __future__ import annotations

from phase0.pilot.attempt import Attempt

DISAGREEMENT_STAGE = "file_set"


def _cuts(values: list[int]) -> tuple[int, int, int]:
    """Q1, Q2, Q3 by nearest-rank. Explicit rather than via `statistics.quantiles`, which
    interpolates and would invent a cut point no PR actually has."""
    ordered = sorted(values)
    n = len(ordered)
    return (
        ordered[max(0, (n + 3) // 4 - 1)],
        ordered[max(0, (n + 1) // 2 - 1)],
        ordered[max(0, (3 * n + 3) // 4 - 1)],
    )


def by_changed_lines(attempts: list[Attempt]) -> dict[str, object]:
    """File-set disagreement rate per quartile of changed lines, plus the cut points.

    The denominator is every attempt in the band, so the rate answers "how often did the
    consistency gate fire on PRs this size" rather than "what share of rejections were
    this size" -- the second moves with the size distribution and says nothing.
    """
    measured = [a for a in attempts if a.changed_lines >= 0]
    unmeasured = [a for a in attempts if a.changed_lines < 0]
    if not measured:
        return {"quartiles": {}, "cut_points": None, "unmeasured": len(unmeasured)}

    q1, q2, q3 = _cuts([a.changed_lines for a in measured])
    bands: dict[str, list[Attempt]] = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    for attempt in measured:
        size = attempt.changed_lines
        if size <= q1:
            bands["Q1"].append(attempt)
        elif size <= q2:
            bands["Q2"].append(attempt)
        elif size <= q3:
            bands["Q3"].append(attempt)
        else:
            bands["Q4"].append(attempt)

    quartiles: dict[str, dict[str, object]] = {}
    for name, rows in bands.items():
        if not rows:
            continue
        disagreed = sum(1 for a in rows if a.stage == DISAGREEMENT_STAGE)
        sizes = sorted(a.changed_lines for a in rows)
        quartiles[name] = {
            "n": len(rows),
            "file_set_rejections": disagreed,
            "disagreement_rate": round(disagreed / len(rows), 4),
            "changed_lines_range": [sizes[0], sizes[-1]],
        }

    return {
        "quartiles": quartiles,
        "cut_points": {"q1": q1, "q2": q2, "q3": q3},
        # Reported, never folded into Q1. A PR whose size we failed to read is not a
        # small PR, and putting it in the band least likely to disagree hides the trend.
        "unmeasured": len(unmeasured),
    }
