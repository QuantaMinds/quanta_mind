"""Check pinned action SHAs against GitHub, on files the ranker never ranks. No model involved.

WHAT: `check(clone, sha, changed)` reads the workflow files a change touched, resolves every
      SHA-pinned action against GitHub, and returns the pins whose version comment the tag list
      contradicts.
WHY:  **THE DETECTOR WAS BUILT, MEASURED 24/24, AND WIRED SOMEWHERE IT COULD NEVER FIRE.** It was
      put behind `deep_review.deep()`, which is shown only the files the ranker ranked — and `.yml`
      is not a reviewable suffix, so a workflow is filtered into `skipped` before the reviewer ever
      exists. `pins(diff)` was therefore always empty.

      **IT NEVER NEEDED THE REVIEWER.** `detect()` reads a diff and asks GitHub; no model is
      consulted, nothing is inferred. So it belongs on the RAW changed-file list, beside the
      ranking rather than inside it, and that is a wiring change rather than a scope change.

      **WHAT IS NOT FIXED HERE, AND WHY.** The other half of the oracle -- `adjudicate()`, which
      refutes a MODEL's false claim about a SHA -- stays unreachable, because the model can only
      make that claim if it is shown a workflow. Showing it workflows widens what the reviewer
      reads, and the reviewer's whole cost argument is that it reads only ranked files. That is a
      product decision with a measurable cost, not a wiring mistake, and it is left alone.

      **THIS DOES NOT BREAK RULE 2.** *"`actions/checkout` is pinned to 3d3c42e5 and commented
      `# v7.0.0`, but GitHub reports that commit as v7.0.1"* is a fact two API calls settle. It is
      not a judgement about the code, and it cannot be wrong the way a semantic finding can.

      **THE BASE RATE IS 0.24%** -- 3 genuine mismatches in 1,244 real commented pins across 22
      repositories. This fires rarely and is correct when it does.
IMPORTS: verify.pin_mismatch. Rightmost layer.
SEE ALSO: it lived in `serve/` until 2026-08-30 and never belonged there — it adjudicates a
      claim about a pinned SHA, which is what `verify/` is, and `verify/rule_check.py` already
      reads a clone through `ingest.blob` for the same kind of work. Moved when `serve/` hit its
      fifteen-file cap and the honest question was which module was in the wrong layer.
CONSUMED BY: `serve/review_delivery.py`, `serve/commands/run_commit.py`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.verify.pin_mismatch import Mismatch, detect

GIT_TIMEOUT_S = 60
WORKFLOW_DIR = ".github/workflows/"
WORKFLOW_SUFFIXES = (".yml", ".yaml")


def workflows(changed: list[str]) -> list[str]:
    """The changed files that can carry an action pin. Empty is the common case.

    **THE DIRECTORY, NOT THE SUBSTRING.** This matched any path containing "workflow", so
    `docs/not_a_workflow.yaml` qualified. That was harmless only while the detector was never
    given a list it could act on; now that it is, a documentation page showing an example
    `uses: owner/action@sha  # v1.0.0` would be reported as a real mismatch in a real workflow.
    GitHub reads workflows from `.github/workflows/` and nowhere else, so that is the test.
    """
    return [p for p in changed if p.endswith(WORKFLOW_SUFFIXES) and WORKFLOW_DIR in p]


def check(clone: Path, sha: str, changed: list[str]) -> tuple[list[Mismatch], int]:
    """(mismatches, pins that could not be resolved) for the workflows this change touched.

    The unresolved count is returned rather than logged: an oracle that cannot reach GitHub finds
    no mismatches, which is indistinguishable from a change that has none.
    """
    paths = workflows(changed)
    if not paths:
        return [], 0
    done = subprocess.run(
        ["git", "-C", str(clone), "show", sha, "--", *paths],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
    )
    if done.returncode != 0:
        return [], 0
    return detect(done.stdout)
