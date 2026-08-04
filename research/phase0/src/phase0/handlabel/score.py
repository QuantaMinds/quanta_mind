"""Agreement between the human labels and the classifier — computed last, on purpose.

WHAT: Reads the completed labels, runs `scan_outcome` over the same PRs, and reports
      raw agreement against `PHASE0_PREREGISTRATION.md` “Timeline” >=16/20 gate, plus Cohen's kappa
      and the label
      distribution as diagnostics.
WHY:  Raw agreement is the pre-registered gate and is not changed here. But raw
      agreement alone can certify a classifier that has learned nothing: if all twenty
      PRs happen to be clean — plausible, since the base rate of a revert-or-fix inside
      seven days is well under half — then answering "clean" every time scores 20/20.
      That is the degeneracy `controls/analysis.py` already refuses to score as a pass
      in the negative controls, appearing again at a different layer.

      So kappa is reported alongside, because it is exactly the correction for chance
      agreement given the observed margins, and the source paper we are checking
      ourselves against reports kappa = 0.79 for the same kind of exercise. It is a
      diagnostic and NOT a gate: adding a second threshold after the fact would move a
      decision boundary, which this study does not do. If the sample turns out to be
      single-class, the honest report is "this gate had no discriminating power", not a
      pass and not a fail.
IMPORTS: phase0.extract_prs, phase0.scan_outcome, phase0.handlabel.select.
CONSUMED BY: `just handlabel-score`; tests/test_handlabel.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from phase0.handlabel.select import Selection
from phase0.scan_outcome import Outcome

VALID_LABELS = {"broke": Outcome.BROKE, "clean": Outcome.CLEAN}
GATE_MINIMUM = 16  # day-2 gate, `PHASE0_PREREGISTRATION.md` “Timeline”. Never relaxed.
_LINE = re.compile(r"^\s*(\d+)\s*[:.]\s*(broke|clean)\s*$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Agreement:
    """The gate's result, with everything needed to see whether it meant anything."""

    total: int
    agreed: int
    human_broke: int
    machine_broke: int
    both_broke: int
    manifest_sha256: str

    @property
    def rate(self) -> float:
        return self.agreed / self.total if self.total else 0.0

    @property
    def is_discriminating(self) -> bool:
        """False when the human labelled every PR the same way.

        Agreement on a single-class sample says nothing about the classifier, so the
        report must say so rather than presenting a number that looks like a pass.
        """
        return 0 < self.human_broke < self.total

    @property
    def kappa(self) -> float:
        """Cohen's kappa. NaN when a margin is empty, which `is_discriminating` flags."""
        n = self.total
        if not n:
            return float("nan")
        observed = self.rate
        p_broke = (self.human_broke / n) * (self.machine_broke / n)
        p_clean = ((n - self.human_broke) / n) * ((n - self.machine_broke) / n)
        expected = p_broke + p_clean
        if expected >= 1.0:
            return float("nan")
        return (observed - expected) / (1.0 - expected)

    @property
    def passed(self) -> bool:
        """`PHASE0_PREREGISTRATION.md` “Timeline” gate, unchanged: >=16 of 20 agree. Read next to
        `is_discriminating`.
        """
        return self.agreed >= GATE_MINIMUM and self.total >= 20

    def describe(self) -> str:
        lines = [
            f"manifest      {self.manifest_sha256}",
            f"agreement     {self.agreed}/{self.total} ({self.rate:.0%})"
            f"   gate: >={GATE_MINIMUM}  ->  {'PASS' if self.passed else 'FAIL'}",
            f"human broke   {self.human_broke}/{self.total}",
            f"machine broke {self.machine_broke}/{self.total}   both: {self.both_broke}",
            f"kappa         {self.kappa:.3f}   (diagnostic, not a gate)",
        ]
        if not self.is_discriminating:
            lines.append(
                "WARNING: every PR carries the same human label, so this agreement "
                "figure is achievable by a classifier that always answers the same "
                "way. It is not evidence either direction. Draw a larger sample."
            )
        return "\n".join(lines)


def read_labels(path: Path, expected: int) -> dict[int, Outcome]:
    """Parse `<index>: broke|clean`, refusing anything incomplete.

    Refusing is the point. A partially filled sheet scored against whatever is present
    would let the gate be satisfied by labelling only the easy ones.
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Fill in the sheet from `just handlabel-sheet` first — "
            f"the labels must exist before the classifier is run."
        )
    labels: dict[int, Outcome] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = _LINE.match(raw)
        if match is None:
            raise ValueError(f"{path}:{number}: expected `<index>: broke|clean`, got {raw!r}")
        labels[int(match.group(1))] = VALID_LABELS[match.group(2).lower()]

    missing = sorted(set(range(1, expected + 1)) - labels.keys())
    if missing:
        raise ValueError(
            f"{path}: missing labels for {missing}. All {expected} must be labelled "
            f"before scoring; a partial sheet would let the gate be met on the easy ones."
        )
    return labels


def score(
    selection: Selection,
    human: dict[int, Outcome],
    machine: dict[int, Outcome],
) -> Agreement:
    """Compare the two label sets over the drawn sample, keyed by sheet index."""
    total = len(selection.candidates)
    agreed = human_broke = machine_broke = both = 0
    for index in range(1, total + 1):
        theirs, ours = human[index], machine[index]
        agreed += theirs is ours
        human_broke += theirs is Outcome.BROKE
        machine_broke += ours is Outcome.BROKE
        both += theirs is Outcome.BROKE and ours is Outcome.BROKE
    return Agreement(
        total=total,
        agreed=agreed,
        human_broke=human_broke,
        machine_broke=machine_broke,
        both_broke=both,
        manifest_sha256=selection.manifest_sha256,
    )
