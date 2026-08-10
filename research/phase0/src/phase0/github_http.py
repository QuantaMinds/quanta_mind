"""The GitHub transport: one authenticated GET, with a bounded retry.

WHAT: `require_token` and `fetch`. Nothing that knows what a pull request is.
WHY:  Split from `github_pulls.py` when that file crossed the line cap with a third
      query on it. Transport and queries are different concerns, and only the transport
      has an opinion about credentials, retries and timeouts.

      `require_token` refuses to fall back to unauthenticated requests. 60 requests an
      hour looks exactly like a working run while silently dropping most of the corpus,
      which is the failure this project exists to make impossible.
IMPORTS: stdlib json, os, time, urllib. Nothing from phase0.
CONSUMED BY: github_pulls.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

TOKEN_VAR = "GITHUB_TOKEN"
API_ROOT = "https://api.github.com"
TIMEOUT_S = 30
MAX_RETRIES = 5
# Base for exponential backoff: 30, 60, 120, 240s. A fixed 60s pause across three
# attempts gave a secondary limit at most two minutes to clear, and GitHub's secondary
# limits are per-minute budgets that can need longer -- on a thirty-one hour run, a
# retry policy that gives up too early converts a transient throttle into attrition.
BACKOFF_BASE_S = 30
# Honoured when present: GitHub states how long to wait, and guessing ignores it.
RETRY_AFTER = "Retry-After"
# Ceiling on an honoured Retry-After, so a mistaken or hostile header cannot stall a
# 31-hour run. Exceeding it is PRINTED rather than applied quietly -- see `_retry_delay`.
RETRY_AFTER_CAP_S = 900.0


class MissingTokenError(RuntimeError):
    """Raised when no token is present. Never fall back to unauthenticated."""


def require_token() -> str:
    """The token, or a loud failure naming the scope it needs."""
    token = os.environ.get(TOKEN_VAR, "").strip()
    if not token:
        raise MissingTokenError(
            f"{TOKEN_VAR} is not set. The correlation test needs a GitHub token with the "
            f"`public_repo` scope to resolve each PR's parent commit -- AIDev does not "
            f"carry it (PHASE0_PREREGISTRATION.md amendment A2). Unauthenticated "
            f"requests are capped at 60/hour, which would look like a working run while "
            f"silently dropping most of the corpus."
        )
    return token


def cache_payload(path: Path, payload: object) -> None:
    """Write a fetch result to disk -- unless it is empty.

    Transport policy, not a query: what an empty RESULT means is this module's business.
    An empty payload means the fetch did not succeed, and caching it makes a transient
    failure permanent -- every later run finds a cache file, never re-fetches, and reads
    `{}` back as "this PR is gone". The corpus would carry a `merge_metadata` exclusion
    no re-run could clear, indistinguishable from a repository that really was deleted.

    A genuine 404 costs one re-fetch per run, which is the right price for refusing to
    write a failure down as a fact.
    """
    if not payload:
        return
    path.write_text(json.dumps(payload), encoding="utf-8")


def _retry_delay(error: urllib.error.HTTPError, attempt: int) -> float:
    """How long to wait: GitHub's own answer when it gives one, else exponential.

    `Retry-After` is authoritative and arrives on secondary limits. Without it, a
    primary-limit exhaustion is identifiable by `x-ratelimit-remaining: 0`, and nothing
    but time fixes it -- so the wait doubles rather than repeating a guess.
    """
    stated = error.headers.get(RETRY_AFTER) if error.headers else None
    if stated:
        try:
            asked = float(stated)
        except ValueError:
            return float(BACKOFF_BASE_S * (2**attempt))
        if asked > RETRY_AFTER_CAP_S:
            # Said out loud, because capping means DISREGARDING what GitHub told us.
            # A stated 3600 capped to 900 retries into a still-active limit and burns
            # an attempt, and over a 31-hour run the only trace would be a later
            # failure with no explanation attached to it.
            print(
                f"rate limit: GitHub asked for {asked:.0f}s, waiting {RETRY_AFTER_CAP_S}s "
                f"(capped); this retry may hit the same limit",
                file=sys.stderr,
                flush=True,
            )
        return min(asked, RETRY_AFTER_CAP_S)
    return float(BACKOFF_BASE_S * (2**attempt))


def fetch(url: str, token: str) -> Any:
    """One GET, with a bounded retry on rate limiting.

    Returns whatever the endpoint gives: `/pulls/{n}` is an object, `/pulls/{n}/commits`
    is an array. Coercing everything to a dict here silently turned the commit list into
    `{}`, which callers would read as "this PR has no commits" -- a wrong answer rather
    than a missing one.
    """
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "qmctx-phase0",
        },
    )
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload if isinstance(payload, (dict, list)) else {}
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return {}  # repository deleted or made private: corpus attrition
            if error.code in (403, 429) and attempt < MAX_RETRIES - 1:
                # 403 and 429 are BOTH rate limiting here, and a 403 from a secondary
                # limit is indistinguishable by status from a permissions 403. Retrying
                # is the safe reading: a real permissions failure costs a few wasted
                # waits and then raises, whereas treating a throttle as a permission
                # error would record transient, self-healing, rate-limit-shaped
                # attrition that nothing downstream could tell from a real exclusion.
                time.sleep(_retry_delay(error, attempt))
                continue
            raise
    return {}


def fetch_all(url: str, token: str, *, per_page: int = 100, max_pages: int = 30) -> list[Any]:
    """Every page of a list endpoint, concatenated. Raises rather than truncating.

    `/pulls/{n}/files` was fetched one page deep, so a PR touching more than `per_page`
    files yielded a SHORT LIST INDISTINGUISHABLE FROM A COMPLETE ONE. `verify_files`
    then compared the diff against a truncated authority, and its own guard skipped
    exactly the largest PRs to avoid the false rejection -- size selection relocated into
    the safeguard built to remove it.

    `max_pages` is a runaway bound, not a truncation: hitting it RAISES. A cap that
    returned what it had would restore the defect one layer out, which is the shape this
    project keeps re-learning.
    """
    out: list[Any] = []
    joiner = "&" if "?" in url else "?"
    for page in range(1, max_pages + 1):
        payload = fetch(f"{url}{joiner}per_page={per_page}&page={page}", token)
        if not isinstance(payload, list):
            # A dict here is `{}` from a 404, or an error object. Either way it is not a
            # page of results, and appending nothing would read as "the list ended".
            return out
        out.extend(payload)
        if len(payload) < per_page:
            return out
    raise RuntimeError(
        f"{url} still had results after {max_pages} pages of {per_page}. Returning the "
        f"first {len(out)} would be a truncated list that reads as a complete one."
    )
