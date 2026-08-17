"""The model as triager of a sound analyzer's alarms, rather than as the finder.

Separated because it is a different architecture, not another variant of the failed one. Four fixes
failed with the model generating candidates, at a 7.2% base rate no filter can exceed; every system
in the literature with strong measured precision inverts the roles -- the Tencent study eliminates
94-98% of false positives with the analyzer finding and the model classifying, and states plainly
that an LLM's capacity to discover new bugs is bounded by the analyzer's.

  alarms.py      ruff raises candidates on defect classes only, inside the funded units
  triage_run.py  the model judges each alarm, one at a time

Research only. The bar is unchanged: under 50% wrong among promoted alarms, blind adjudication,
pre-registered in `docs/plans/preregistrations/triage-preregistration.md`.
"""

from __future__ import annotations
