"""A change with no governed file still reports, because a required check cannot stay silent.

WHAT: Asserts `serve.review.pin_review.only()` announces the gate, so a delivery carrying no
      reviewable file leaves a commit status behind rather than nothing.
WHY:  **THIS IS THE REGRESSION TEST FOR A MERGE THAT COULD NOT HAPPEN.** `main` requires
      `quantamind/declared-rules`. `QuantaMinds/quanta_mind#104` was documentation only, so
      `review_delivery.deliver()` returned through this path before any status was posted. Every CI
      job was green and the pull request sat `MERGEABLE / BLOCKED` on a check that was not failing —
      it was **absent**, which GitHub renders as `pending` forever.

      **"NOTHING TO CHECK HERE" AND "NO ANSWER YET" WERE THE SAME BLANK SPACE**, on the one surface
      that holds a merge. That is the distinction this product sells, missing from its own gate.

      **THE TEST IS ON THIS FUNCTION RATHER THAN ON `deliver()` DELIBERATELY.** `deliver()` needs a
      clone, a token and a GitHub API; the defect lives in one branch of one function, and a test
      that needed all of that to reach it would be skipped in exactly the runs that matter.
IMPORTS: pytest, quantamind.serve.review.pin_review, quantamind.serve.blocking_status.
"""

from __future__ import annotations

from typing import Any

import pytest

from quantamind.serve.review import pin_review

HEAD = "a" * 40


@pytest.fixture
def posted(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, ...]]:
    """Every commit status the run wrote, captured at the publishing boundary."""
    seen: list[tuple[Any, ...]] = []

    def _spy(repo: str, sha: str, state: str, description: str) -> None:
        seen.append((repo, sha, state, description))

    monkeypatch.setattr("quantamind.ingest.publish.commit_status.post", _spy, raising=True)
    monkeypatch.setattr("quantamind.serve.review.pin_review.publish", lambda *a, **k: True)
    return seen


def test_a_change_with_no_reviewable_file_still_posts_a_status(
    posted: list[tuple[Any, ...]],
) -> None:
    """**SABOTAGE 2 FROM THE PLAN.** Restore the early return and this must fail by name."""
    pin_review.only("acme/widgets", 104, HEAD, pins="", enabled=True)

    assert len(posted) == 1, "a documentation-only change left no status, so it could never merge"
    _repo, _sha, state, description = posted[0]
    assert state == "success"
    assert description == "no declared rule governed any file in this change"


def test_the_status_names_the_state_rather_than_claiming_a_pass(
    posted: list[tuple[Any, ...]],
) -> None:
    """The old decision refused a green tick here. The description is what makes it honest."""
    pin_review.only("acme/widgets", 104, HEAD, pins="", enabled=True)

    description = posted[0][3].lower()
    for claim in ("compliant", "all rules passed", "no violations"):
        assert claim not in description, f"the tick claimed {claim!r} where nothing was checked"


def test_a_rehearsal_writes_no_status(posted: list[tuple[Any, ...]]) -> None:
    """`POSTING_ENABLED=0` must still touch nothing — the gate is computed and printed, not sent."""
    pin_review.only("acme/widgets", 104, HEAD, pins="", enabled=False)

    assert posted == [], "a rehearsal wrote to somebody else's pull request"
