"""The two GET routes a browser needs to sign in, and what each answers.

WHAT: `get(path, cookies, settings)` returns a `Reply` — status, headers, body — for `/login` and
      `/callback`, and a 404 for anything else.
WHY:  **IT RETURNS A REPLY RATHER THAN WRITING TO A SOCKET.** A route that owns the handler cannot
      be tested without one, and the first thing worth testing here is what a forged callback gets
      back. The listener does the writing.

      **THE `state` LIVES IN A SHORT-LIVED COOKIE AND IS COMPARED TO THE ONE IN THE URL.** Two
      copies, one the attacker cannot set, which is what makes a forged callback fail — the
      double-submit pattern. It needs no server-side table, and a table would be a second thing to
      expire correctly.

      **ACCOUNTS LIVE IN ONE STORE BESIDE THE TENANTS, NEVER INSIDE ONE.** A person is not a
      repository. `tenancy.tenants()` globs `<root>/<owner>/*.db`, so a file at the root is not
      mistaken for a customer — the same reasoning the delivery ledger already follows.
IMPORTS: stdlib, serve.web.signin, store.schema, types.settings. Rightmost layer.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

from quantamind.render import page
from quantamind.serve.web import pages, signin
from quantamind.store import accounts
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings

LOGIN = "/login"
CALLBACK = "/callback"
STATE_COOKIE = "qm_state"
STATE_SECONDS = 600
"""How long a sign-in may take. Ten minutes: long enough for a slow consent screen, short enough
that a stolen state value is worthless by the time anybody could use it."""

ACCOUNTS_DB = "accounts.db"
REPO_PREFIX = "/r/"
HTML = "text/html; charset=utf-8"
SIGN_IN_PAGE = (
    "<h1>QuantaMind</h1><p>A code reviewer that reports what it did not check.</p>"
    '<p><a href="/login">Sign in with GitHub</a></p>'
)


@dataclass(frozen=True, slots=True)
class Reply:
    """What to send back. Built, then written by the caller, so a route is testable alone."""

    status: int
    body: str
    headers: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    kind: str = "text/plain; charset=utf-8"
    """**PLAIN TEXT IS THE DEFAULT AND HTML IS THE EXCEPTION.** A refusal that carried caller text
    would be inert as text and live as markup, so the pages that mean to be HTML say so and
    everything else stays a document a browser will not execute."""


def _state_cookie(state: str) -> str:
    return (
        f"{STATE_COOKIE}={state}; Max-Age={STATE_SECONDS}; Path=/; HttpOnly; Secure; SameSite=Lax"
    )


def _cookie_value(header: str, name: str) -> str:
    for part in header.split(";"):
        key, _, value = part.strip().partition("=")
        if key == name:
            return value
    return ""


def get(path: str, cookies: str, settings: Settings, *, at: int | None = None) -> Reply:
    """Answer one GET. Never raises: a browser gets a page, not a stack trace."""
    moment = int(time.time()) if at is None else at
    where, _, query = path.partition("?")

    if where == LOGIN:
        try:
            state = signin.new_state()
            url = signin.authorize_url(settings, state)
        except signin.SignInFailed as refused:
            return Reply(503, f"sign-in is not configured: {refused.reason}")
        return Reply(302, "", (("Location", url), ("Set-Cookie", _state_cookie(state))))

    if where == CALLBACK:
        fields = urllib.parse.parse_qs(query)
        conn = open_store(Path(settings.database_path) / ACCOUNTS_DB)
        try:
            token = signin.sign_in(
                conn,
                settings,
                code=(fields.get("code") or [""])[0],
                state=(fields.get("state") or [""])[0],
                expected=_cookie_value(cookies, STATE_COOKIE),
                at=moment,
            )
        except signin.SignInFailed as refused:
            # The stage is named and the reason is not echoed back: a callback error page that
            # repeats attacker-supplied text is a reflection, and this one is reached by a browser.
            return Reply(400, f"sign-in failed at the {refused.stage} step")
        finally:
            conn.close()
        # The state cookie is spent here. Leaving it would let one consent screen sign in twice.
        return Reply(
            302,
            "",
            (
                ("Location", "/"),
                ("Set-Cookie", signin.cookie(token)),
                ("Set-Cookie", f"{STATE_COOKIE}=; Max-Age=0; Path=/"),
            ),
        )

    if where == "/" or where.startswith(REPO_PREFIX):
        conn = open_store(Path(settings.database_path) / ACCOUNTS_DB)
        try:
            session = accounts.whose(conn, signin.token_in(cookies), at=moment)
        finally:
            conn.close()
        if not session.signed_in:
            # **THE REASON IS NOT SHOWN.** "Expired" and "no such session" differ to us and not to
            # a visitor, who gets the same page and the same link either way.
            return Reply(200, page.page("QuantaMind", SIGN_IN_PAGE), kind=HTML)
        root = Path(settings.database_path)
        if where == "/":
            return Reply(200, pages.home(root, session.login), kind=HTML)
        body = pages.repository(root, session.login, where[len(REPO_PREFIX) :])
        if body is None:
            # A repository that is not this account's answers exactly as one that does not exist.
            return Reply(404, page.page("Not found", "<h1>Not found</h1>"), kind=HTML)
        return Reply(200, body, kind=HTML)

    return Reply(404, "no such path")
