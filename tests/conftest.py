"""Test-wide path setup, and one narrow rate-limit skip.

WHAT: Puts scripts/guard/ on sys.path so tests can import the guard modules, and converts a
      failure carrying GitHub's own "API rate limit exceeded" text into a NAMED skip.
WHY:  The guards are deliberately not part of the installable package -- they must
      run before quantamind is installable, which is why they import each other by bare
      name (`from discovery import ...`). That works when they are invoked as
      `python scripts/guard/check_x.py`, because Python puts the script's own
      directory on sys.path[0]. Under pytest there is no such directory, so it is
      added here rather than by mutating sys.path inside each test.
      **A RATE LIMIT IS A PROPERTY OF THE ENVIRONMENT, NOT A DEFECT IN THE CODE UNDER TEST.**
      Unauthenticated reads are 60 requests an hour and one full live run exhausts them, so
      `just verify` went red for a reason unrelated to the change being verified -- which trains
      a reader to ignore a red gate, and that is the more expensive failure.

      **THE MATCH IS DELIBERATELY NARROW.** Only GitHub's own phrase converts. A 401, a 404, a
      broken token or a genuine assertion still FAIL -- a skip that swallowed those would be the
      silent pass this project refuses. Verified by sabotage: a raised `HTTP 401` failed rather
      than skipping. `ingest/github_api` carries the auth reason into its message precisely so
      these stay distinguishable.
IMPORTS: stdlib (pathlib, sys) plus pytest. No project imports -- this runs at collection.
CONSUMED BY: pytest, for every tier under tests/.
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

import pytest

GUARD_DIR = Path(__file__).resolve().parent.parent / "scripts" / "guard"

if str(GUARD_DIR) not in sys.path:
    sys.path.insert(0, str(GUARD_DIR))


RATE_LIMITED = "API rate limit exceeded"
REMEDY = (
    "GitHub's UNAUTHENTICATED rate limit (60/hour) is exhausted, so this test could not reach the "
    "API. This is NOT a failure of the code under test. Set QUANTAMIND_PUBLIC_READ_TOKEN to raise "
    "the limit to 5,000/hour, or wait for the reset. A repository the App is installed on never "
    "takes this path, so no customer is affected by it."
)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    """Skip on GitHub's rate limit, and on nothing else."""
    outcome = yield
    raised = outcome.excinfo  # type: ignore[attr-defined]  # pytest exposes no typed accessor
    if raised is not None and RATE_LIMITED in str(raised[1]):
        outcome.force_exception(pytest.skip.Exception(REMEDY))  # type: ignore[attr-defined]
