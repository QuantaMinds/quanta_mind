"""The analysis concern: statistics, contingency tables, and the verdict.

WHAT: Groups `risk` (the interval methods), `build_table` (the 2x2s and arms) and
      `verdict` (the pre-registered thresholds).
WHY:  Split out when `build_table.py` crossed the 200-line cap. The three belong
      together: they are the only modules that touch the study's decision boundary, and
      keeping them in one package makes the boundary reviewable in one place.
IMPORTS: phase0.analysis.{risk,build_table,verdict}.
CONSUMED BY: run_pipeline.py, controls/; tests/test_build_table.py, tests/test_risk.py.
"""
