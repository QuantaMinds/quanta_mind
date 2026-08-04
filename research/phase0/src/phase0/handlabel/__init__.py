"""The day-2 gate: does the outcome classifier agree with a human on 20 PRs?

WHAT: Three steps kept in separate modules so the order is enforced by the code rather
      than by intent — `select` fixes which PRs, `sheet` renders the evidence a human
      needs with no verdict in it, and `score` compares afterwards.
WHY:  §7's day-2 gate requires agreement on >=16 of 20, hand-labelled **before** any
      classifier output is seen. That ordering is the whole value of the gate and it is
      the easiest thing in this project to compromise without noticing — one glance at a
      `broke`/`clean` column and the exercise measures nothing but recall of what you
      just read.

      So `sheet` does not import `scan_outcome` or `fix_signals` at all, and a test
      asserts that it does not. It is not a convention to be remembered; the sheet
      literally cannot render a verdict, because the code that computes one is not
      reachable from it.
IMPORTS: phase0.handlabel.{select,sheet,score}.
CONSUMED BY: `just handlabel-sheet`, `just handlabel-score`; tests/test_handlabel.py.
"""

from __future__ import annotations

from phase0.handlabel.score import Agreement, score
from phase0.handlabel.select import Selection, select_prs
from phase0.handlabel.sheet import render_sheet

__all__ = ["Agreement", "Selection", "render_sheet", "score", "select_prs"]
