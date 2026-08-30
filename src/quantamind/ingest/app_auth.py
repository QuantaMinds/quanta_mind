"""Mint an installation access token, so the product comments as itself and not as a person.

WHAT: `token(repo, app_id, key_path)` returns a GitHub App installation access token for `repo`,
      cached until shortly before it expires. `AuthFailed` carries what GitHub said.
WHY:  **`ingest/github_comments.py` SHELLED OUT TO THE `gh` CLI, WHICH COMMENTS AS WHOEVER RAN
      `gh auth login`.** That is a developer tool, not a product: one identity, one account's rate
      limit, and a comment signed by a person rather than by the reviewer. An installation token is
      scoped to the repositories an App was installed on, expires in an hour, and carries only the
      permissions the App declared.

      **STDLIB ONLY, BECAUSE `pyproject.toml` DECLARES `dependencies = []`.** A GitHub App JWT is
      RS256, which stdlib cannot sign -- `hmac` is HS256 and there is no RSA in the standard
      library. Rather than take the first runtime dependency, this signs with `openssl`, which is
      the same choice `infer/gemini.py` already makes when it mints a Vertex token with `gcloud`.
      Verified end to end against a live App: JWT accepted, installation resolved, token issued
      with `pull_requests: write`.

      **THE KEY IS READ FROM DISK AT USE AND NEVER HELD IN `Settings`.** Same reasoning as the
      webhook secret in `serve/commands/run_endpoint.py`: a credential in a settings object
      reaches a config
      dump or a log the first time anyone prints one. The path is configuration; the key is not.

      **A TOKEN IS CACHED UNTIL A MINUTE BEFORE IT EXPIRES, NOT UNTIL IT EXPIRES.** A token that is
      valid when checked and stale when it arrives produces a 401 on a delivery that was otherwise
      fine, and the retry looks like a GitHub outage.
IMPORTS: stdlib only (base64, json, subprocess, time, urllib). Same layer as `github_comments`,
      which consumes it; no sibling internals.
CONSUMED BY: `ingest/github_comments.py`.
"""

from __future__ import annotations

import base64
import calendar
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
SIGN_TIMEOUT_S = 30
HTTP_TIMEOUT_S = 30
JWT_LIFETIME_S = 540
"""Nine minutes. GitHub rejects an App JWT whose `exp` is more than ten minutes ahead."""

CLOCK_SKEW_S = 60
"""`iat` is backdated by this much: GitHub rejects a JWT issued in ITS future, and a client clock
a few seconds fast is a 401 that looks like a bad key."""

REFRESH_MARGIN_S = 60


class AuthFailed(RuntimeError):
    """Carries the step that failed and what GitHub said. Never a bare failure."""

    def __init__(self, step: str, reason: str) -> None:
        super().__init__(f"{step}: {reason}")
        self.step, self.reason = step, reason


_cache: dict[str, tuple[str, float]] = {}


def _b64(raw: bytes) -> bytes:
    """Base64url without padding, which is what JWT requires and `urlsafe_b64encode` does not do."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def app_jwt(app_id: str, key_path: Path) -> str:
    """An RS256 JWT proving we hold the App's private key.

    **SIGNED BY `openssl`, NOT BY A LIBRARY.** See the module docstring: the alternative is this
    project's first runtime dependency, for one signature.
    """
    if not key_path.is_file():
        raise AuthFailed("read key", f"no private key at {key_path}")
    now = int(time.time())
    header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = json.dumps(
        {"iat": now - CLOCK_SKEW_S, "exp": now + JWT_LIFETIME_S, "iss": app_id},
        separators=(",", ":"),
    )
    signing_input = header + b"." + _b64(claims.encode())
    done = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key_path)],
        input=signing_input,
        capture_output=True,
        timeout=SIGN_TIMEOUT_S,
    )
    if done.returncode != 0 or not done.stdout:
        raise AuthFailed("sign jwt", f"openssl exited {done.returncode}: {done.stderr[:160]!r}")
    return (signing_input + b"." + _b64(done.stdout)).decode()


def _call(path: str, bearer: str, method: str = "GET") -> Any:
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "quantamind",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as reply:
            return json.loads(reply.read() or b"null")
    except urllib.error.HTTPError as exc:
        body = (exc.read() or b"").decode("utf-8", "replace")[:160]
        raise AuthFailed(f"{method} {path}", f"HTTP {exc.code}: {body}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AuthFailed(f"{method} {path}", str(exc)[:160]) from None


def installation_id(repo: str, jwt: str) -> int:
    """The installation covering `repo`.

    **A 404 HERE MEANS THE APP IS NOT INSTALLED, NOT THAT THE REPOSITORY IS MISSING**, and the two
    read identically to a caller. Creating an App and installing it are separate actions, and an
    App installed nowhere authenticates perfectly and can reach nothing -- which is exactly what
    this returned before `QuantaMinds/QuantaMind` was ticked.
    """
    got = _call(f"/repos/{repo}/installation", jwt)
    if not isinstance(got, dict) or not got.get("id"):
        raise AuthFailed("installation", f"no installation id for {repo}: {str(got)[:120]}")
    return int(got["id"])


def token(repo: str, app_id: str, key_path: Path) -> str:
    """An installation access token for `repo`, cached until shortly before it expires."""
    hit = _cache.get(repo)
    if hit and hit[1] - REFRESH_MARGIN_S > time.time():
        return hit[0]

    jwt = app_jwt(app_id, key_path)
    got = _call(f"/app/installations/{installation_id(repo, jwt)}/access_tokens", jwt, "POST")
    if not isinstance(got, dict) or not got.get("token"):
        raise AuthFailed("mint token", f"no token in reply: {str(got)[:120]}")
    # **`calendar.timegm`, NOT `time.mktime` MINUS `time.timezone`.** GitHub's `expires_at` is UTC;
    # `mktime` reads a struct as LOCAL time and the `timezone` fudge ignores daylight saving. The
    # first version was **exactly one hour out** and put every expiry two minutes in the PAST, so
    # the cache never once hit -- valid tokens every time, an API round trip every time, and
    # nothing that looks like a fault. Caught because the live test asserted the second call
    # returned the SAME token rather than merely a working one.
    expiry = got.get("expires_at", "")
    try:
        seconds = float(calendar.timegm(time.strptime(str(expiry), "%Y-%m-%dT%H:%M:%SZ")))
    except ValueError:
        # An unparsable expiry is not a reason to cache forever. Treat it as already old.
        seconds = time.time()
    _cache[repo] = (str(got["token"]), seconds)
    return str(got["token"])
