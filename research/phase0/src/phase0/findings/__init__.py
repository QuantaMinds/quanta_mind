"""Measuring whether the findings the pipeline PUBLISHES are true of the code they point at.

WHAT: `pack` builds a blind, balanced labelling pack; `audit` refuses one that leaks its key;
      `sample` and `scoring` are the two commands an operator runs, in that order.
WHY:  A separate package from `handlabel`, which asks whether a PR broke something. Same
      discipline -- blind sheet, sealed key, controls that make a constant answer fail -- on a
      different unit of analysis, so sharing a package would put two populations behind one
      name and invite exactly the mix-up rule 14 is about.
IMPORTS: stdlib only.
CONSUMED BY: `just findings-draw`, `just findings-score`; tests/findings/.
"""
