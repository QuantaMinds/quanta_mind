"""Recompute every headline number from its stored artefact and check it against what was reported.

Separated from the measurement harnesses because it is the opposite job: they produce numbers, this
one refuses to trust them. It reads only the result files under `../results/`, so a claim that has
drifted from its data fails here rather than in a document nobody re-reads.

  stats.py   Wilson, exact McNemar, Cohen's kappa, hypergeometric chance
  verify.py  one assertion per reported figure

This project has shipped a wrong number three ways -- a cost table that priced one call for three,
a kappa of 0.66 reported as 0.92, and an anchor check reading 98.1% while the anchors were still
wrong. Run `python3 verify.py` from this directory before quoting anything.
"""

from __future__ import annotations
