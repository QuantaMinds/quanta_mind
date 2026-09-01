"""Sign in with GitHub: the redirect, the callback, and the cookie that carries the session.

WHAT: `authorize_url(settings, state)` is where a browser is sent. `sign_in(settings, code, ...)`
      exchanges the code, identifies the user, records the account and returns a session token.
      `cookie(token)` and `token_in(header)` carry it.
WHY:  **B2 — nothing could be attributed to a person, so no dashboard could be shown to one.**
      `store/installations.py` keys on a GitHub account; this is how a human proves they hold it.

      **`state` IS REQUIRED AND CHECKED, NOT DECORATIVE.** Without it, anyone can hand a victim's
      browser a callback URL carrying THEIR code and log the victim into the attacker's account —
      a login-CSRF, and the reason the parameter exists. `sign_in` refuses when it does not match.

      **THE CLIENT SECRET IS NEVER LOGGED AND NEVER RETURNED.** It goes into one POST body and
      nowhere else. `render_config` reports it as set or unset, the same rule
      `public_read_token` follows, because `config` output lands in terminal scrollback.

      **THE COOKIE IS `HttpOnly`, `Secure` AND `SameSite=Lax`.** Script cannot read it, it does
      not travel in the clear, and it is not sent on a cross-site POST. Each of the three closes
      a different door and none substitutes for another.
IMPORTS: stdlib, store.{accounts,schema}, types.settings. Rightmost layer.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
import urllib.parse
import urllib.request

from quantamind.store import accounts
from quantamind.types.deployment import Destination, permit
from quantamind.types.settings import Settings

AUTHORIZE = "https://github.com/login/oauth/authorize"
EXCHANGE = "https://github.com/login/oauth/access_token"
IDENTIFY = "https://api.github.com/user"
HTTP_TIMEOUT_S = 30
COOKIE = "qm_session"
SCOPE = "read:user"
"""The narrowest scope that answers "who is this". Sign-in needs a name, not a repository."""


class SignInFailed(RuntimeError):
    """The flow did not complete. Carries what went wrong, never a bare failure."""

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(f"{stage}: {reason}")
        self.stage, self.reason = stage, reason


def new_state() -> str:
    """A one-time value tying a callback to the browser that started the flow."""
    return secrets.token_urlsafe(24)


def authorize_url(settings: Settings, state: str) -> str:
    """Where to send the browser. Refuses rather than building a URL that cannot work."""
    if not settings.oauth_client_id:
        raise SignInFailed("authorize", "no oauth_client_id is configured")
    if not state:
        raise SignInFailed(
            "authorize", "a state value is required; without it the callback is forgeable"
        )
    query = urllib.parse.urlencode(
        {"client_id": settings.oauth_client_id, "scope": SCOPE, "state": state}
    )
    return f"{AUTHORIZE}?{query}"


def _post(url: str, body: dict[str, str]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(body).encode(),
        headers={"Accept": "application/json"},
    )
    # **ASK BEFORE THE SOCKET OPENS.** D7f: an air-gapped deployment REFUSES
    # this, rather than attempting it and failing somewhere the customer sees
    # in their egress log and we do not.
    permit(Destination.GITHUB_API)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        parsed = json.loads(response.read())
    return parsed if isinstance(parsed, dict) else {}


def _get(url: str, token: str) -> dict[str, object]:
    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        parsed = json.loads(response.read())
    return parsed if isinstance(parsed, dict) else {}


def sign_in(
    conn: sqlite3.Connection, settings: Settings, *, code: str, state: str, expected: str, at: int
) -> str:
    """Complete the callback and return a session token. Raises rather than half-signing anybody in.

    **THE STATE IS COMPARED FIRST, BEFORE THE CODE IS SPENT.** Exchanging first would burn a real
    authorisation code on a request we were about to reject anyway.
    """
    if not expected or not secrets.compare_digest(state, expected):
        raise SignInFailed("callback", "state did not match the one this browser was given")
    if not code:
        raise SignInFailed("callback", "no code in the callback")
    if not (settings.oauth_client_id and settings.oauth_client_secret):
        raise SignInFailed("exchange", "oauth_client_id and oauth_client_secret are both required")

    granted = _post(
        EXCHANGE,
        {
            "client_id": settings.oauth_client_id,
            "client_secret": settings.oauth_client_secret,
            "code": code,
        },
    )
    token = str(granted.get("access_token") or "")
    if not token:
        raise SignInFailed("exchange", str(granted.get("error_description") or "no access_token"))

    who = _get(IDENTIFY, token)
    login = str(who.get("login") or "")
    raw_id = who.get("id")
    github_id = int(raw_id) if isinstance(raw_id, int | str) else 0
    if not login or github_id <= 0:
        raise SignInFailed("identify", "GitHub returned no login or id for this token")

    accounts.remember(conn, login, github_id, at=at)
    return accounts.issue(conn, login, at=at)


def cookie(token: str) -> str:
    """The `Set-Cookie` value. Three flags, each closing a different door."""
    age = accounts.SESSION_HOURS * 3600
    return f"{COOKIE}={token}; Max-Age={age}; Path=/; HttpOnly; Secure; SameSite=Lax"


def token_in(header: str) -> str:
    """The session token from a `Cookie` header, or empty. Never raises on a malformed one."""
    for part in header.split(";"):
        name, _, value = part.strip().partition("=")
        if name == COOKIE:
            return value
    return ""
