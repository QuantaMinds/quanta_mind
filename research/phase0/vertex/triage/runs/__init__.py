"""The runners for the execution-gate experiments, split from the components at the fan-out cap.

  fetch_aged.py     draws pull requests old enough to have an outcome, guarded by `corpus_age`
  execution_run.py  the gate on the easy corpus (2010-2012)  -> 27.8% wrong
  execution_hard.py the same gate on the hard corpus         -> 52.4% wrong, fails the bar

Kept together because the pair is the experiment: one run alone could not distinguish the gate
from the corpus, and running both is what showed the 27.8% did not transfer.
"""

from __future__ import annotations
