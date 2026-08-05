"""Verification of the HTTP transport beneath the merge-metadata client.

WHAT: Asserts that a failed fetch is never written to the cache, and that the retry
      delay obeys GitHub's own `Retry-After` before falling back to exponential backoff.
WHY:  Split from `test_github_pulls.py`, which verifies the pulls client itself. These
      test `github_http`, a different module, and keeping them together took that file
      16 lines past the 200-line cap.

      Both properties here fail silently if wrong. Caching an empty payload turns a
      TRANSIENT 404 into a permanent exclusion no re-run can clear. A retry policy that
      gives up early converts a throttle into corpus attrition -- over a 31-hour run,
      neither leaves anything behind that names its own cause.
IMPORTS: phase0.github_http, pytest.
CONSUMED BY: `just test-phase0`. No network: every test builds its own HTTPError.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from phase0.github_http import _retry_delay, cache_payload


def test_a_failed_fetch_is_not_written_to_the_cache(tmp_path: Path) -> None:
    """Caching an empty payload makes a TRANSIENT failure permanent.

    Every later run sees a cache file, never re-fetches, and reads `{}` back as "this PR
    is gone" -- a `merge_metadata` exclusion no re-run could clear, indistinguishable from
    a repository that really was deleted. A genuine 404 costs one re-fetch per run, which
    is the right price for not writing down a failure as a fact.
    """
    path = tmp_path / "pr-1.json"

    cache_payload(path, {})
    assert not path.exists()

    cache_payload(path, [])
    assert not path.exists()

    cache_payload(path, {"merge_commit_sha": "abc"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"merge_commit_sha": "abc"}


def test_retry_delay_prefers_githubs_own_answer() -> None:
    """`Retry-After` is authoritative on secondary limits; guessing ignores it."""
    stated = urllib.error.HTTPError(
        "u",
        429,
        "too many",
        {"Retry-After": "42"},
        None,  # type: ignore[arg-type]
    )
    assert _retry_delay(stated, 0) == 42.0

    # Capped, so a hostile or mistaken header cannot stall a 31-hour run indefinitely.
    huge = urllib.error.HTTPError(
        "u",
        429,
        "too many",
        {"Retry-After": "99999"},
        None,  # type: ignore[arg-type]
    )
    assert _retry_delay(huge, 0) == 900.0


def test_retry_delay_backs_off_exponentially_without_a_header() -> None:
    """A fixed pause gave a secondary limit two minutes to clear across three attempts.

    Those limits are per-minute budgets that can need longer, and on a 31-hour run a
    retry policy that gives up early converts a throttle into attrition.
    """
    bare = urllib.error.HTTPError("u", 403, "forbidden", {}, None)  # type: ignore[arg-type]

    assert [_retry_delay(bare, n) for n in range(4)] == [30.0, 60.0, 120.0, 240.0]


def test_a_capped_retry_after_says_so(capsys) -> None:  # type: ignore[no-untyped-def]
    """Capping means disregarding what GitHub asked for, and that must leave a trace.

    A stated 3600 capped to 900 retries into a still-active limit and burns an attempt.
    Over a 31-hour run the only evidence would otherwise be a later failure with nothing
    attached explaining it.
    """
    asked_for_an_hour = urllib.error.HTTPError(
        "u",
        429,
        "too many",
        {"Retry-After": "3600"},
        None,  # type: ignore[arg-type]
    )

    assert _retry_delay(asked_for_an_hour, 0) == 900.0
    warned = capsys.readouterr().err
    assert "3600" in warned and "900" in warned


def test_an_uncapped_retry_after_is_silent() -> None:
    """No warning when nothing was disregarded -- an alarm that always fires is noise."""
    ordinary = urllib.error.HTTPError(
        "u",
        429,
        "too many",
        {"Retry-After": "45"},
        None,  # type: ignore[arg-type]
    )

    assert _retry_delay(ordinary, 0) == 45.0


def test_an_unparseable_retry_after_falls_back_to_backoff() -> None:
    """A malformed header is not a reason to abandon the retry."""
    junk = urllib.error.HTTPError(
        "u",
        429,
        "too many",
        {"Retry-After": "soon"},
        None,  # type: ignore[arg-type]
    )

    assert _retry_delay(junk, 1) == 60.0
