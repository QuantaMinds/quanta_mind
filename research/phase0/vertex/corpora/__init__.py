"""Stored inputs and verdicts for the review-half measurements.

Separated from the harness at the directory fan-out cap. These are the artefacts every reported
number is recomputed from by `research/phase0/verify_claims.py`, which is why they are kept rather
than regenerated: a corpus that cannot reproduce its own figure is the defect this project has
already hit with truncated comment bodies.

  pr_corpus.json / pr_corpus_fresh.json   the pull requests, with full file sources
  verdicts.json, enriched_verdicts.json, fresh_verdicts.json   blind adjudications
  vertex_cost.json                        the billed C3 run

Research only.
"""

from __future__ import annotations
