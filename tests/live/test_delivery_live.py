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
from quantamind.store import tenancy
from quantamind.store.reviews import recent
from quantamind.store.schema import open_store
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
        # **A DIRECTORY, NOT A FILE.** `QUANTAMIND_DATABASE_PATH` became a TENANT ROOT when
        # per-repository stores landed; `store/tenancy.py` derives `<root>/<owner>/<name>.db`
        # from it. This test still passed a file, so `store_for` created `live.db` as a
        # DIRECTORY and the assertion below then opened a directory as a database. The unit
        # tests never caught it because they pass a file where production passes a root.
        database_path=str(tmp_path / "stores"),
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

    # **The review must be ON DISK, not merely computed.** `review` and `ranked_unit` sat in the
    # schema with zero writers, so the pipeline ran and left no trace it had; a dashboard has
    # nothing to draw on until this row exists.
    tenant = tenancy.store_for(Path(settings.database_path), *REPO.split("/", 1))
    assert tenant.is_file(), (
        f"no store at {tenant}. The delivery must write into the tenant's own file, not the "
        f"root: one corrupt page or one bad migration would otherwise take every tenant."
    )
    conn = open_store(tenant)
    try:
        repo_id = int(conn.execute("SELECT id FROM repo").fetchone()[0])
        stored = recent(conn, repo_id)
        assert stored, "the review ran but nothing was recorded"
        assert stored[0].pr_number == NUMBER
        assert stored[0].units == len(done.considered), (
            "every ranked unit must be stored, COLD ones included — a table holding only the "
            "units we spoke about cannot be asked whether the quiet ones were right"
        )
        assert 0 <= stored[0].read <= stored[0].units

        # A redelivery is a normal event and must not double any count.
        deliver(REPO, NUMBER, "0" * 40, settings)
        again = recent(conn, repo_id)
        assert len(again) == len(stored), "a redelivery added a second review row"
        assert again[0].units == stored[0].units, "a redelivery doubled the ranked units"
    finally:
        conn.close()
