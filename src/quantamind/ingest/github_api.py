"""One authenticated call to GitHub, so the token is resolved in one place and not three.

WHAT: `call(repo, path, method, body, accept)` performs one API request as the App installation
      covering `repo`, returning raw bytes. `ApiFailed` carries the method, path and what GitHub
      said.
WHY:  **THE TOKEN LOOKUP WAS COPIED INTO TWO MODULES BEFORE THIS EXISTED.** `ingest/diff.py` and
      `ingest/github_comments.py` each grew their own `_token()` that loaded `Settings`, checked
      the App was configured and wrapped `AuthFailed` -- the same twelve lines, differing only in
      which exception they raised. A third caller would have copied it again, and the first time
      the rule changed one of them would have kept the old one.

      **RAW BYTES, NOT PARSED JSON.** A pull request's patch is read with the
      `application/vnd.github.v3.diff` media type and is not JSON at all. A helper that parsed
      would need a way to opt out, which is a parameter that exists to be forgotten; callers that
      want JSON call `json.loads` themselves and the one that wants a patch does not.

      **IT RAISES ON EVERY NON-2XX.** GitHub answers 404 both for "no such repository" and for "you
      cannot see this one", and an empty body on a failed read is indistinguishable from a change
      that touched nothing. Returning a value on failure is how a broken read becomes a quiet
      no-op, which this project has already paid for four times.
IMPORTS: stdlib (json, urllib) plus `ingest.app_auth` and `types.settings`. Same layer, public
      surface only.
CONSUMED BY: `ingest/diff.py`, `ingest/github_comments.py`.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from quantamind.ingest import app_auth
from quantamind.types.settings import load

BASE = "https://api.github.com"
TIMEOUT_S = 30
JSON = "application/vnd.github+json"


class ApiFailed(RuntimeError):
    """Carries the call and GitHub's own words. Never a bare failure."""

    def __init__(self, method: str, path: str, reason: str) -> None:
        super().__init__(f"{method} {path}: {reason}")
        self.method, self.path, self.reason = method, path, reason


def token_for(repo: str) -> str:
    """An installation token for `repo`, or a refusal naming the missing configuration.

    **REFUSING IS THE POINT.** The only way to reach GitHub without an App is as whoever
    authenticated the `gh` CLI, which is the behaviour the App replaced.
    """
    settings = load()
    if not (settings.app_id and settings.app_key_path):
        raise ApiFailed(
            "auth",
            repo,
            "no GitHub App configured; set QUANTAMIND_APP_ID and QUANTAMIND_APP_KEY_PATH",
        )
    try:
        return app_auth.token(repo, settings.app_id, Path(settings.app_key_path))
    except app_auth.AuthFailed as exc:
        raise ApiFailed("auth", repo, f"could not mint an installation token: {exc}") from None


def call(
    repo: str,
    path: str,
    *,
    method: str = "GET",
    body: str | None = None,
    accept: str = JSON,
) -> bytes:
    """One authenticated request. Raw bytes on 2xx, `ApiFailed` on anything else."""
    request = urllib.request.Request(
        f"{BASE}/{path}",
        data=None if body is None else body.encode(),
        method=method,
        headers={
            "Authorization": f"Bearer {token_for(repo)}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "quantamind",
            **({"Content-Type": JSON} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as reply:
            return bytes(reply.read())
    except urllib.error.HTTPError as exc:
        detail = (exc.read() or b"").decode("utf-8", "replace")[:160]
        raise ApiFailed(method, path, f"HTTP {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ApiFailed(method, path, str(exc)[:160]) from None
