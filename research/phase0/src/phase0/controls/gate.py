"""Run the controls gate and report what it found.

WHAT: Measures the synthetic corpus with the real stages, computes per-mechanism
      detection, and writes results/controls.json.
WHY:  Split from corpus.py, which builds repositories. This module evaluates them,
      and evaluation is where the gate lives: `PHASE0_RUNBOOK.md` “Positive control” pooled RR >= 5,
      plus
      A11's per-mechanism table reported alongside so a pass carried entirely by
      `super()` is visible rather than implied.

      Exposure and outcome are derived by `run_pipeline.one_pr` and
      `scan_outcome.scan` — the same code the corpus run uses. A control that
      assigned its own answers would test the arithmetic and nothing else.
IMPORTS: phase0.analysis.build_table, classify_exposure, run_pipeline, scan_outcome, and
      controls.{corpus,analysis}.
CONSUMED BY: `python -m phase0.controls.gate`; tests/test_controls_corpus.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from phase0.analysis.build_table import Observation
from phase0.classify_exposure import Exposure
from phase0.controls.analysis import run_negative_controls, run_positive_control
from phase0.controls.corpus import DEFAULT_PER_MECHANISM, SyntheticPR, build_corpus
from phase0.controls.mechanisms import probe_all_mechanisms
from phase0.controls.reconcile import reconcile
from phase0.outcome.conclusion import table_coding
from phase0.outcome.scan import scan
from phase0.run_pipeline import one_pr


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


def broke_rate(measured: list[tuple[SyntheticPR, Observation]]) -> tuple[float, int]:
    """Detection rate over planted breaks the scanner could actually look at, and the
    number it could not.

    The denominator was every planted break, including any the scan returned UNSCANNABLE
    for. That reads a failure to look as a failure to detect, which pushes the positive
    control DOWN and would have been debugged as a weak classifier rather than as an
    unwalkable branch. Returning the excluded count alongside keeps the distinction
    visible instead of leaving the caller to infer it from a lower number.
    """
    planted = [o for s, o in measured if s.planted_break]
    coded = [table_coding(o.outcome) for o in planted]
    scannable = [c for c in coded if c is not None]
    if not scannable:
        return 0.0, len(planted)
    return sum(scannable) / len(scannable), len(planted) - len(scannable)


def report(per_mechanism: int = DEFAULT_PER_MECHANISM, timeout_s: int = 120) -> dict[str, object]:
    """Build, measure, and reduce to the gate's verdict plus its diagnostics."""
    root = Path(tempfile.mkdtemp(prefix="phase0-controls-"))
    built = build_corpus(root, per_mechanism=per_mechanism)
    measured = measure(built, timeout_s=timeout_s)
    observations = [o for _, o in measured]

    tally = detection_by_mechanism(measured)
    positive = run_positive_control(observations)
    negatives = run_negative_controls(observations)
    detection_rate, unscannable_planted = broke_rate(measured)

    return {
        "synthetic_repos": len(built),
        "clusters": len({o.repo_id for o in observations}),
        # Detection within the pooled corpus, which by A12 contains only
        # mechanisms the instrument can see.
        "detection_in_corpus": {k: list(v) for k, v in tally.items()},
        # The capability profile stays over ALL FOUR mechanisms, from the probe.
        # Reporting "firing" against the corpus would read 1/1 and hide A10.
        "capability_profile": {p.mechanism: p.detected for p in probe_all_mechanisms()},
        "mechanisms_firing_of_four": sum(1 for p in probe_all_mechanisms() if p.detected),
        # Rate over planted breaks the scan could look at, and the count it could not.
        # Pooling the second into the first reads an unwalkable branch as a blind
        # classifier, which is a different bug with a different fix.
        "planted_break_detection_rate": detection_rate,
        "planted_breaks_unscannable": unscannable_planted,
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
        "reconciliation": reconcile(measured),
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
