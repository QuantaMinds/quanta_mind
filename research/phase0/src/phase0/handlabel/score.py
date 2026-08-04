"""Compare human labels against the sealed key -- the step that must run last.

WHAT: Reads `human_labels.csv` and `_key.csv`, and reports agreement against the
      pre-registered floor, Cohen's kappa, the 2x2, and every disagreement itemised.
WHY:  Separate from drawing so producing the questions and producing the answers are two
      commands a person runs in order, not one that could emit both. `read_labels`
      refuses an incomplete file, so this cannot be run early to "just have a look".

      `UNSURE` scores as disagreement and is reported separately. It is information, not
      failure: a PR the labeller could not resolve in ten minutes is one the seven-day
      rule almost certainly cannot resolve either, and a run with many of them is a
      finding about how much breakage is determinable from history at all.

      Reading the sheet lives in `labels.py`; this module only compares.

      Kappa is reported as context, never as a gate. Twenty items is thin, and adding a
      second threshold after the design is fixed would move a decision boundary --
      tightening is as much a degree of freedom as loosening.
IMPORTS: phase0.handlabel.draw, phase0.handlabel.labels.
CONSUMED BY: phase0/score_labelling.py; tests/handlabel/.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from phase0.handlabel.draw import KeyRow
from phase0.handlabel.labels import HumanLabel

GATE_MINIMUM = 16  # of 20. Pre-registered; never relaxed to fit a result.


@dataclass(frozen=True, slots=True)
class Disagreement:
    """One PR the human and the classifier read differently."""

    label_id: int
    repo: str
    number: int
    human: str
    machine: str
    human_reasoning: str
    machine_criterion: str
    machine_evidence: str

    @property
    def direction(self) -> str:
        """Which way the rule erred, which is what decides how to fix it."""
        if self.human == "UNSURE":
            return "undetermined"
        if self.machine == "BROKE":
            return "rule too loose"
        return "rule too tight"


@dataclass(frozen=True, slots=True)
class Agreement:
    """The gate's result, with everything needed to see whether it meant anything."""

    total: int
    agreed: int
    both_broke: int
    both_clean: int
    machine_broke_human_clean: int
    machine_clean_human_broke: int
    unsure: int
    minutes_median: float
    disagreements: tuple[Disagreement, ...] = field(default_factory=tuple)

    @property
    def rate(self) -> float:
        return self.agreed / self.total if self.total else 0.0

    @property
    def passed(self) -> bool:
        """The pre-registered floor, unchanged."""
        return self.agreed >= GATE_MINIMUM and self.total >= 20

    @property
    def kappa(self) -> float:
        """Cohen's kappa over the resolved rows. NaN when a margin is empty.

        `UNSURE` rows are excluded here but still counted as disagreement in `rate`.
        Coding them as one class or the other would invent a judgement the labeller
        explicitly declined to make.
        """
        n = self.total - self.unsure
        if n <= 0:
            return float("nan")
        machine_broke = self.both_broke + self.machine_broke_human_clean
        human_broke = self.both_broke + self.machine_clean_human_broke
        observed = (self.both_broke + self.both_clean) / n
        expected = (machine_broke / n) * (human_broke / n) + ((n - machine_broke) / n) * (
            (n - human_broke) / n
        )
        if expected >= 1.0:
            return float("nan")
        return (observed - expected) / (1.0 - expected)

    def matrix(self) -> str:
        return (
            "                 human BROKE   human CLEAN\n"
            f"machine BROKE  {self.both_broke:>12}  {self.machine_broke_human_clean:>13}\n"
            f"machine CLEAN  {self.machine_clean_human_broke:>12}  {self.both_clean:>13}"
        )

    def describe(self) -> str:
        resolved = self.total - self.unsure
        lines = [
            f"agreement     {self.agreed}/{self.total} ({self.rate:.0%})"
            f"   gate: >={GATE_MINIMUM}  ->  {'PASS' if self.passed else 'FAIL'}",
            f"kappa         {self.kappa:.3f}   (context, not a threshold; n={resolved})",
            f"unsure        {self.unsure}   (scored as disagreement)",
            f"median mins   {self.minutes_median:.1f}",
            "",
            self.matrix(),
        ]
        if self.disagreements:
            lines += ["", "disagreements:"]
            for item in self.disagreements:
                lines += [
                    f"  [{item.label_id}] {item.repo}#{item.number}"
                    f"  human={item.human} machine={item.machine}  ({item.direction})",
                    f"      human:   {item.human_reasoning}",
                    f"      machine: {item.machine_criterion} {item.machine_evidence[:12]}",
                ]
        return "\n".join(lines)


def score(key: list[KeyRow], human: dict[int, HumanLabel]) -> Agreement:
    """Compare the two label sets, keyed by `label_id`."""
    agreed = both_broke = both_clean = loose = tight = unsure = 0
    disagreements: list[Disagreement] = []
    durations: list[float] = []

    for row in sorted(key, key=lambda r: r.label_id):
        mine, theirs = row.verdict, human[row.label_id].verdict
        durations.append(human[row.label_id].minutes)
        if theirs == "UNSURE":
            unsure += 1
        elif theirs == mine:
            agreed += 1
            both_broke += mine == "BROKE"
            both_clean += mine == "CLEAN"
            continue
        elif mine == "BROKE":
            loose += 1
        else:
            tight += 1
        disagreements.append(
            Disagreement(
                label_id=row.label_id,
                repo=row.repo,
                number=row.number,
                human=theirs,
                machine=mine,
                human_reasoning=human[row.label_id].reasoning,
                machine_criterion=row.criterion,
                machine_evidence=row.evidence_sha,
            )
        )

    ordered = sorted(durations)
    median = ordered[len(ordered) // 2] if ordered else 0.0
    return Agreement(
        total=len(key),
        agreed=agreed,
        both_broke=both_broke,
        both_clean=both_clean,
        machine_broke_human_clean=loose,
        machine_clean_human_broke=tight,
        unsure=unsure,
        minutes_median=median,
        disagreements=tuple(disagreements),
    )
