"""The controls: the gate that outranks the thesis.

`PHASE0_RUNBOOK.md` “Positive control” calls the positive control the most important gate in the
study — you
cannot interpret a null from an instrument you have not shown can produce a
positive, because you would probably believe it.

Three modules, three concerns:

- `mechanisms.py` — the four unresolvable-caller mechanisms, and a probe reporting
  which of them the exposure variable can see at all
- `corpus.py` — builds synthetic repositories and derives exposure and outcome
  with the real pipeline, never assigning either
- `analysis.py` — the risk-ratio arithmetic and the pre-registered thresholds

Re-exported here so `from phase0.controls import …` keeps working across the split.
"""

from __future__ import annotations

from phase0.controls.analysis import (
    NEGATIVE_CONTROL_MAX_RR,
    NONSENSE,
    POSITIVE_CONTROL_MIN_RR,
    POSITIVE_CONTROL_N,
    ControlResult,
    run_negative_controls,
    run_positive_control,
)
from phase0.controls.mechanisms import (
    MECHANISMS,
    RESOLVABLE,
    MechanismProbe,
    probe_all_mechanisms,
    probe_mechanism,
)

__all__ = [
    "MECHANISMS",
    "NEGATIVE_CONTROL_MAX_RR",
    "NONSENSE",
    "POSITIVE_CONTROL_MIN_RR",
    "POSITIVE_CONTROL_N",
    "RESOLVABLE",
    "ControlResult",
    "MechanismProbe",
    "probe_all_mechanisms",
    "probe_mechanism",
    "run_negative_controls",
    "run_positive_control",
]
