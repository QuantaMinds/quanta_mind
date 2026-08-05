"""The outcome concern: did a revert or a fix land within the window, and could we look?

WHAT: Groups `window` (which branch, which commits, and why a walk was impossible),
      `signals` (the message and file-overlap rules), `record` (the verdict type) and
      `scan` (the walk itself).
WHY:  Split out when `scan.py` crossed the 200-line cap and src/phase0/ hit the 15-file
      directory cap at the same moment. The four belong together: they are the only
      modules that decide the dependent variable, and the study's most consequential
      defect to date lived in the seam between two of them -- the walk started at the
      clone's HEAD while the verdict type had no way to say "I could not look".

      The package boundary is also a warning. Nothing here may import
      `classify_exposure`: the exposure pass and the outcome pass must not see each
      other, or the correlation measures the instrument agreeing with itself.
IMPORTS: phase0.outcome.{window,signals,conclusion,scan}.
CONSUMED BY: run_pipeline.py, analysis/build_table.py, controls/gate.py,
      handlabel/draw.py, pilot/run.py; tests/test_scan_outcome.py.
"""

from __future__ import annotations
