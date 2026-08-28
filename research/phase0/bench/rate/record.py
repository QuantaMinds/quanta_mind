"""One change's trip through the pipeline, and the rate that trip belongs to.

WHAT: `ChangeRecord` is what happened to one commit. `report(records)` prints the published
      rate over every denominator a reader might mean, all three named.
WHY:  Separated from `measure.py`, which drives the real pipeline and therefore imports
      `quantamind` -- unavailable on the research interpreter, so anything importing it cannot
      be covered by `just test-phase0`. The arithmetic is the part that was wrong before and
      the part worth pinning, so it lives where a test can reach it.

      **A RATE IS A FRACTION AND THE ARGUMENT IS ALWAYS ABOUT ITS BOTTOM HALF.** The same six
      findings read as 1.500, 1.000 or 0.600 across the three denominators here. A6 reported
      0.686 per change; two later samples appeared to give 0.46 and 0.25 and were taken as
      instability, when they had simply been divided by every commit attempted rather than by
      the changes on which the model was asked anything.
IMPORTS: stdlib only.
CONSUMED BY: `bench/rate/measure.py`; tests/rate/test_rate_report.py.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# Every way a commit can stop short of being measured. Each is a different statement about the
# pipeline, so each is counted rather than skipped with a `continue`.
OUTCOMES = ("measured", "empty-diff", "no-funded-files", "no-timestamp", "model-failed")


@dataclass(frozen=True, slots=True)
class ChangeRecord:
    """What happened to one commit, including the ways it did not finish."""

    sha: str
    outcome: str
    raw: int = 0
    kept: int = 0
    unanchored: int = 0
    refuted: int = 0
    withdrawn: int = 0

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError(f"{self.outcome!r} is not one of {OUTCOMES}")

    @property
    def measured(self) -> bool:
        return self.outcome == "measured"


def rates(records: list[ChangeRecord]) -> dict[str, tuple[int, float]]:
    """(denominator, rate) for each meaning of "per change". Empty denominators are omitted.

    Returned rather than printed so a caller can assert on it: the defect this module exists
    to prevent was a number quoted without the denominator it came from.
    """
    measured = [r for r in records if r.measured]
    reached = [r for r in records if r.outcome in {"measured", "empty-diff"}]
    kept = sum(r.kept for r in measured)
    out: dict[str, tuple[int, float]] = {}
    for name, pool in (
        ("changes measured (the model was asked)", measured),
        ("changes reaching the model stage", reached),
        ("every commit attempted", records),
    ):
        if pool:
            out[name] = (len(pool), kept / len(pool))
    return out


def report(records: list[ChangeRecord]) -> str:
    """The counted outcomes, the totals, and the rate under each denominator."""
    seen = Counter(r.outcome for r in records)
    measured = [r for r in records if r.measured]
    raw = sum(r.raw for r in measured)
    kept = sum(r.kept for r in measured)

    lines = [f"COMMITS ATTEMPTED  {len(records)}"]
    lines += [f"  {name:<16} {seen[name]}" for name in OUTCOMES if seen[name]]
    lines += ["", f"RAW FINDINGS       {raw}", f"KEPT FINDINGS      {kept}", ""]
    lines.append("KEPT PER CHANGE, by what the denominator means:")
    for name, (n, rate) in rates(records).items():
        lines.append(f"  {name:<44}{n:>3}  {rate:.3f}")
    if raw:
        lines += [
            "",
            f"GATE REJECTION     {(raw - kept) / raw:.1%} of raw dropped — "
            f"unanchored {sum(r.unanchored for r in measured)}, "
            f"refuted {sum(r.refuted for r in measured)}, "
            f"withdrawn {sum(r.withdrawn for r in measured)}",
        ]
    return "\n".join(lines)
