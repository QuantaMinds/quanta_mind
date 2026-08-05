"""Facts about a repository that come from outside this process.

WHAT: Star counts from AIDev's `repository` table, and a repository's default branch
      from the `gh` CLI.
WHY:  Split from `report.py`, which turns attempts into metrics. Fetching a fact and
      interpreting one are different jobs, and only this side has to decide what to do
      when the source is unreachable -- which is the interesting half.

      The two failures here are deliberately not symmetric, because they are not the
      same kind of failure. A missing `repository.parquet` yields an empty mapping and
      the star band reports `unknown`, visibly different from a band that was measured.
      A missing `gh` binary RAISES, because its answer is compared to `base_ref` and
      stored as a BOOLEAN: an empty string would silently make every PR in the run read
      `base_is_default=False`, and the off-default share is a population finding the
      analysis reads. One absent tool would have manufactured 100% off-default.

      `default_branch` used to promise "empty when the lookup fails" in a docstring while
      `subprocess.run` raised `FileNotFoundError` straight through it. The pilot died at
      the first repository. A docstring is not an exception handler.
IMPORTS: pandas, stdlib pathlib/subprocess.
CONSUMED BY: pilot/run.py, pilot/report.py; tests/pilot/test_repo_facts.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

GH_TIMEOUT_S = 60

_DEFAULTS: dict[str, str] = {}


class GhUnavailable(RuntimeError):
    """The `gh` CLI is not on PATH, so no default branch can be looked up at all.

    Our environment, not the corpus, so it stops the run rather than becoming a value.
    """


def star_counts(table: Path) -> dict[str, int]:
    """Star count per repository, keyed by `owner/name`.

    Returns empty when the table is absent rather than failing. The band then reports
    `unknown`, which is visibly different from reporting a band that was never measured.
    """
    if not table.is_file():
        return {}
    frame = pd.read_parquet(table)
    return {str(r.full_name): int(r.stars) for r in frame.itertuples() if r.full_name}


def default_branch(repo: str) -> str:
    """The repository's default branch, cached. Empty when the lookup for THIS repo fails.

    An empty answer mislabels one repository's rows; a missing `gh` would mislabel every
    row in the run, so the two are separated rather than sharing a return value. A
    timeout is not cached, because it is transient and the next repository may succeed.
    """
    if repo not in _DEFAULTS:
        try:
            out = subprocess.run(
                ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
                capture_output=True,
                text=True,
                timeout=GH_TIMEOUT_S,
                check=False,
            )
        except OSError as exc:
            raise GhUnavailable(
                f"`gh` could not be run ({type(exc).__name__}: {exc}). It is required for "
                f"the default-branch label; see ENVIRONMENT.lock."
            ) from exc
        except subprocess.TimeoutExpired:
            return ""
        _DEFAULTS[repo] = out.stdout.strip()
    return _DEFAULTS[repo]
