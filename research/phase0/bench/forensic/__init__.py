"""The forensic pass: why the correct-rate is what it is, measured rather than argued.

Five modules that answer one question and share one dataset. They live together because each was
written to correct the one before it: `label_candidates` exists because the per-candidate labels
were never stored and four analyses had guessed them; `judge_variance` because an apparent +32
swing had to be shown to be a metric definition rather than noise; `redundancy` because the first
version of that table put two different judges in one column.
"""
