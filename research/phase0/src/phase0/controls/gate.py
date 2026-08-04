"""Run the controls gate and report what it found.

WHAT: Measures the synthetic corpus with the real stages, computes per-mechanism
      detection, and writes results/controls.json.
WHY:  Split from corpus.py, which builds repositories. This module evaluates them,
      and evaluation is where the gate lives: RUNBOOK §2.1's pooled RR >= 5, plus
      A11's per-mechanism table reported alongside so a pass carried entirely by
      `super()` is visible rather than implied.

      Exposure and outcome are derived by `run_pipeline.one_pr` and
      `scan_outcome.scan` — the same code the corpus run uses. A control that
      assigned its own answers would test the arithmetic and nothing else.
IMPORTS: phase0.build_table, classify_exposure, run_pipeline, scan_outcome, and
      controls.{corpus,analysis}.
CONSUMED BY: `python -m phase0.controls.gate`; tests/test_controls_corpus.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from phase0.build_table import Observation
from phase0.classify_exposure import Exposure
from phase0.controls.analysis import run_negative_controls, run_positive_control
from phase0.controls.corpus import SyntheticPR, build_corpus
from phase0.run_pipeline import one_pr
from phase0.scan_outcome import Outcome, scan


def measure(
    built: list[SyntheticPR], timeout_s: int = 120
) -> list[tuple[SyntheticPR, Observation]]:
    """Derive exposure and outcome with the real stages. Nothing is assigned."""
    measured: list[tuple[SyntheticPR, Observation]] = []
    for synthetic in built:
        audit = one_pr(synthetic.repo_path, synthetic.record, 0, timeout_s)
        outcome = scan(synthetic.repo_path, synthetic.record)
        row = audit.symbols[0] if audit.symbols else None
        measured.append(
            (
                synthetic,
                Observation(
                    symbol=synthetic.record.changed_symbols[0],
                    repo_id=synthetic.record.repo_id,
                    outcome=outcome.outcome,
                    primary=_arm(row.primary if row else ""),
                    sensitivity_low=_arm(row.sensitivity_low if row else ""),
                    sensitivity_high=_arm(row.sensitivity_high if row else ""),
                    strata={"mechanism": synthetic.mechanism},
                ),
            )
        )
    return measured


def _arm(value: str) -> Exposure | None:
    return Exposure(value) if value else None


def detection_by_mechanism(
    measured: list[tuple[SyntheticPR, Observation]],
) -> dict[str, tuple[int, int]]:
    """Per-mechanism (detected, total) over the exposed arm only — A11's table."""
    tally: dict[str, tuple[int, int]] = {}
    for synthetic, observation in measured:
        if synthetic.record.pr_id.split("-")[-2] != "exp":
            continue
        detected, total = tally.get(synthetic.mechanism, (0, 0))
        hit = 1 if observation.primary is Exposure.EXPOSED else 0
        tally[synthetic.mechanism] = (detected + hit, total + 1)
    return dict(sorted(tally.items()))


def broke_rate(measured: list[tuple[SyntheticPR, Observation]]) -> float:
    """Sanity check: the outcome scanner must actually detect the planted fixes."""
    planted = [o for s, o in measured if s.planted_break]
    if not planted:
        return 0.0
    return sum(1 for o in planted if o.outcome is Outcome.BROKE) / len(planted)


def report(per_mechanism: int = 10, timeout_s: int = 120) -> dict[str, object]:
    """Build, measure, and reduce to the gate's verdict plus its diagnostics."""
    root = Path(tempfile.mkdtemp(prefix="phase0-controls-"))
    built = build_corpus(root, per_mechanism=per_mechanism)
    measured = measure(built, timeout_s=timeout_s)
    observations = [o for _, o in measured]

    tally = detection_by_mechanism(measured)
    positive = run_positive_control(observations)
    negatives = run_negative_controls(observations)

    return {
        "synthetic_repos": len(built),
        "clusters": len({o.repo_id for o in observations}),
        "detection_by_mechanism": {k: list(v) for k, v in tally.items()},
        "mechanisms_firing": sum(1 for _, (hit, _) in tally.items() if hit),
        "planted_break_detection_rate": broke_rate(measured),
        "positive_control": {
            "relative_risk": positive.relative_risk,
            "ci": [positive.ci_low, positive.ci_high],
            "passed": positive.passed,
            "detail": positive.detail,
        },
        "negative_controls": [
            {
                "name": n.name,
                "relative_risk": n.relative_risk,
                "ci": [n.ci_low, n.ci_high],
                "passed": n.passed,
                "detail": n.detail,
            }
            for n in negatives
        ],
        "gate_passed": positive.passed and all(n.passed for n in negatives),
    }


def main() -> int:
    """Write results/controls.json and return 0 only if the gate passed."""
    out = Path(__file__).resolve().parents[3] / "results" / "controls.json"
    result = report()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
