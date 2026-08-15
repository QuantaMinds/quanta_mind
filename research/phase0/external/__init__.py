"""Tests of the ranking half on repositories it was not developed against.

Separated from the rest of `research/phase0/` because everything here runs on clones that are
deliberately NOT the original eight. Those eight have carried six allocation variants, a holdout,
a corpus study and a cost run; whatever they say next about themselves is already known.

  defect_return.py  the V0 policy against an alphabetical control, off-corpus

Research only. Nothing in `src/` imports this.
"""

from __future__ import annotations
