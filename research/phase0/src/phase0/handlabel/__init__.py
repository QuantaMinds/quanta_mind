"""The 20-PR gate: does the outcome classifier agree with a human?

WHAT: Four modules kept separate so the order is enforced by code rather than intent --
      `select` fixes the population, `draw` buckets by classifier verdict and seals the
      answers, `labels` reads what the human wrote, `score` compares afterwards.
WHY:  The gate requires agreement on at least 16 of 20, hand-labelled BEFORE any
      classifier output is seen. That ordering is the whole value of the exercise and is
      the easiest thing in this project to compromise without noticing.

      The sample is stratified: ten PRs the classifier called BROKE, ten it called CLEAN,
      shuffled, exported as URLs only. At the corpus base rate a random twenty holds
      about two broken PRs, so labelling everything CLEAN would score ~18/20 and pass a
      gate that proved nothing. Balanced, always-CLEAN scores 10/20 and fails.

      The labeller works from the pull request on GitHub, not from a rendered window of
      the classifier's own evidence. An earlier version of this package rendered the
      seven-day commit window -- exactly the classifier's input -- which would have made
      agreement partly true by construction. The human must be free to use evidence the
      rule cannot see: linked issues, CI runs, discussion.
IMPORTS: phase0.handlabel.{select,draw,labels,score,files}.
CONSUMED BY: phase0/sample_for_labelling.py, phase0/score_labelling.py; tests/handlabel/.
"""

from __future__ import annotations

from phase0.handlabel.draw import Drawn, KeyRow, draw
from phase0.handlabel.labels import HumanLabel, read_labels
from phase0.handlabel.score import Agreement, Disagreement, score
from phase0.handlabel.select import Candidate, eligible_prs

__all__ = [
    "Agreement",
    "Candidate",
    "Disagreement",
    "Drawn",
    "HumanLabel",
    "KeyRow",
    "draw",
    "eligible_prs",
    "read_labels",
    "score",
]
