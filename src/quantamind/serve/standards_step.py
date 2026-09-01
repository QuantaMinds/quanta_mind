"""Apply the repository's declared standards to one change, and post the resulting status.

WHAT: `applied(clone, sha, paths, store, repo, number, settings)` returns `(checks, judged)` and
      posts the commit status. One call, both halves, exactly one status.
WHY:  **THE JUDGE IS CONSTRUCTED HERE AND INJECTED, NEVER REACHED FOR INSIDE `verify/`.**
      `AGENTS.md` rule 7 claimed the layer order stopped `verify` importing `infer` and it did not,
      because `infer` sits to the LEFT and the import runs leftward.
      `scripts/guard/check_conventions.py:FORBIDDEN` refuses that pair by name now. This module
      supplies the judge as a parameter, the way `verify/consumers.py` is given its clone.

      **THE STATUS IS COMPUTED FROM `checks` ALONE.** A model's verdict never moves a commit status:
      a status blocks a merge, and blocking on a claim measured 66.7-82.1% wrong would make the
      product an obstacle rather than a check. `judged` travels to the comment and stops.

      **SPLIT OUT OF `serve/review_delivery.py` FOR THE 200-LINE CAP, AND IT IS A REAL SEAM.**
      `deliver()` orchestrates: clone, rank, review, render, post. "Enforce the customer's declared
      standards" is one step of that with its own inputs and its own output, and it was the only
      step whose model wiring lived inline.
IMPORTS: serve.{blocking_status,rule_judge}, types.{settings,standards.checked,standards.judged},
      verify.rule_check. Leftward and sideways from `serve/`.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from quantamind.serve.blocking_status import announce
from quantamind.serve.rule_judge import judge_with
from quantamind.types.settings import Settings
from quantamind.types.standards.checked import Checked
from quantamind.types.standards.judged import Judged
from quantamind.verify.rule_check import enforce


def applied(
    clone: Path,
    sha: str,
    paths: Sequence[str],
    store: Path,
    repo: str,
    number: int,
    settings: Settings,
) -> tuple[tuple[Checked, ...], tuple[Judged, ...]]:
    """Run every declared standard over the change, post the status, return both halves."""
    checks, judged = enforce(clone, sha, list(paths), store, repo, number, judge_with(settings))
    # **`checks` ONLY.** See the module docstring: a model verdict does not block a merge.
    announce(repo, sha, checks, enabled=settings.posting_enabled)
    return checks, judged
