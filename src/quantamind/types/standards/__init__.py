"""A standard a repository declares, and the two kinds of verdict it can receive.

WHAT: `rule.py` is the declaration; `checked.py` is what a PARSER decided about it; `judged.py` is
      what a MODEL said about it.
WHY:  **THE THREE ARE ONE CONCERN AND THE SPLIT BETWEEN THE LAST TWO IS THE PRODUCT.** A `Checked`
      can be re-run on the same commit and shown to give the same answer; a `Judged` cannot. Keeping
      them in one package makes the difference legible to the next reader, and keeping them in two
      TYPES makes it impossible to blur — there is no field to set, no shared table, no shared
      renderer. D1c asks that they never render alike; this is where that becomes structural.
IMPORTS: types.verdict. Nothing else.
CONSUMED BY: `verify/`, `store/`, `render/`, `serve/`.
"""
