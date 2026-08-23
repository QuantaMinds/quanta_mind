"""The whole endpoint path against a real pull request, stopping short of writing to it.

WHAT: Runs `deliver()` on a real, merged, public pull request with posting OFF — clone, fetch,
      GitHub reads, ranking, rendering — and asserts on what came back.
WHY:  **THE ENDPOINT AUTHENTICATED DELIVERIES AND REVIEWED NOTHING, AND EVERY UNIT TEST PASSED.**
      `work()` logged and returned; the pieces it should have joined were each covered on their
      own. **Only a test that runs the join can tell a joined pipeline from six working parts.**

      **POSTING IS OFF, AND THAT IS WHAT MAKES THIS RUNNABLE.** With `posting_enabled` false the
      rehearsal exercises everything except the write, so this can run against somebody else's
      repository on every commit without ever commenting on it. The write itself is covered by
      `test_github_comments_read.py` and by `post()`'s own idempotency, which is keyed on the head
      SHA and returns False rather than raising on a duplicate.

      **A MERGED, PINNED PULL REQUEST, NOT AN OPEN ONE.** An open pull request's head moves and its
      file list changes, so the assertions below would rot into flakes. This one is closed and
      cannot change.
IMPORTS: stdlib, pytest, quantamind.serve.review_delivery, quantamind.types.settings.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from quantamind.serve.review_delivery import Outcome, deliver
from quantamind.types.settings import Settings

REPO = "psf/requests"
NUMBER = 7497  # merged 2026-06-08; nine Python files, so the ranking actually runs


def _have_gh() -> bool:
    if shutil.which("gh") is None:
        return False
    done = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=30)
    return done.returncode == 0


pytestmark = pytest.mark.skipif(
    not _have_gh(), reason="needs an authenticated gh; this test reads a real pull request"
)


def test_the_join_runs_end_to_end_and_posts_nothing(tmp_path: Path) -> None:
    settings = replace(
        Settings(),
        database_path=str(tmp_path / "live.db"),
        clone_root=str(tmp_path / "clones"),
        posting_enabled=False,
    )
    done = deliver(REPO, NUMBER, "0" * 40, settings)

    # The point of the test: it got all the way through, and it did not write.
    assert done.outcome is not Outcome.POSTED, "posting was off and must have stayed off"
    assert done.outcome is not Outcome.DUPLICATE, "a duplicate check implies it tried to post"

    # A real clone exists, so the ranking read a real history rather than an empty one.
    assert (Path(settings.clone_root) / "psf" / "requests" / ".git").is_dir()

    # Typed silence: every changed file is accounted for in exactly one of the two lists.
    assert done.considered or done.skipped, (
        "the pull request changed files, so both lists being empty means the file list was lost "
        "between the API and the ranking — which is the silence this product refuses"
    )
    overlap = set(done.considered) & set(done.skipped)
    assert not overlap, f"a path cannot be both ranked and skipped: {sorted(overlap)[:3]}"

    if done.outcome is Outcome.REHEARSED:
        assert done.body, "REHEARSED means a comment was rendered; it must not be empty"
    else:
        assert done.body is None, f"{done.outcome.value} must carry no comment body"
    assert done.sentence(), "every outcome reports what it did"
