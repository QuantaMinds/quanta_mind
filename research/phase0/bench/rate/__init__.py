"""How many findings a review publishes per change, measured with its denominator named.

WHAT: `measure.py` runs the real pipeline over a list of commits and records, per change,
      whether the model was consulted at all and what survived each gate.
WHY:  A6 reported 0.686 published findings per change and said the figure was "stable across
      two samples". Two later samples on the same repository and pipeline appeared to give
      0.46 and 0.25 -- but those were computed over every commit attempted, while A6 divided
      by changes measured. **Two rates over two denominators are not evidence of instability,
      they are a broken comparison**, and A6's own commit set is unrecoverable because its
      script was a heredoc. This package exists so the next such number carries its
      denominator instead of needing one reconstructed afterwards.
IMPORTS: stdlib, quantamind.{serve,infer}. Run with the ROOT project's interpreter.
CONSUMED BY: an operator, by hand.
"""
