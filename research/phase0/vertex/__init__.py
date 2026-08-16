"""Live measurements against Vertex AI, on the project's own GCP credits.

Separated from the rest of `research/phase0/` because everything here bills a real API, and
because it is the first evidence in this project that touches the *review* half of the product
rather than the ranking half.

  fetch_prs.py  real merged pull requests with diffs and the full source of changed files
  units.py      maps a diff's changed lines onto enclosing functions, via `ast`
  cost.py       bills the product's real prompt and compares it to the priced estimate

Gemini only. Claude on Vertex is offered but not subscribed for this project, and will not be.

Consumed by nothing in `src/`. Research only.
"""

from __future__ import annotations
