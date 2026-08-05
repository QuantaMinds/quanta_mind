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
import time
import urllib.error
import urllib.request
from typing import Any

TOKEN_VAR = "GITHUB_TOKEN"
API_ROOT = "https://api.github.com"
TIMEOUT_S = 30
MAX_RETRIES = 3
RATE_LIMIT_PAUSE_S = 60


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
            if error.code in (403, 429) and attempt < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_PAUSE_S)
                continue
            if error.code == 404:
                return {}  # repository deleted or made private: corpus attrition
            raise
    return {}
