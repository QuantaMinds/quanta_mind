"""Measurements over the corpus of real OSS code-review comments.

Separated from the rest of `research/phase0/` because these read GitHub's review API rather
than git history, and because the corpus turned out to need its own hygiene: a third of the
inline review comments on active Python repositories are written by other AI review bots, and
`fetch.py` is the only reader here that records who wrote a comment.

  fetch.py         draws both sampling schemes, carrying the author
  report.py        bot prevalence, and the recency comparison on human comments only
  checkability.py  the FAILED keyword classifier, kept because its residual is the result

Consumed by nothing in `src/`. Research only.
"""

from __future__ import annotations
