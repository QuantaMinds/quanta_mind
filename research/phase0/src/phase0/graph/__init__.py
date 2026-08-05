"""The call-graph instrument: running PyCG, and typing the ways it fails.

WHAT: Groups `run_graph` (the subprocess and its result) and `pycg_failure` (the
      `GraphStatus` taxonomy that says why a graph is missing).
WHY:  These two are the instrument, and the instrument is the part of the study whose
      limits are the finding. Keeping them together makes the failure taxonomy
      reviewable beside the thing that produces it -- a graph that came back empty and a
      graph we never managed to build must never be the same value, and that guarantee
      is easier to check when both halves sit in one package.
IMPORTS: phase0.graph.{run_graph,pycg_failure}.
CONSUMED BY: classify_exposure.py, pipeline/measure.py, run_pipeline.py, controls/.
"""

from __future__ import annotations

from phase0.graph.pycg_failure import GraphStatus
from phase0.graph.run_graph import DEFAULT_TIMEOUT_S, GraphResult, run

__all__ = ["DEFAULT_TIMEOUT_S", "GraphResult", "GraphStatus", "run"]
