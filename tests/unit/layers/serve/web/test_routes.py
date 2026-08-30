"""Verification that a forged callback is refused and that the state cookie is spent once.

WHAT: Drives `serve/web/routes.get` over both routes and the unknown path, asserting the status,
      the redirect and every cookie flag.
WHY:  **A ROUTE THAT OWNS THE SOCKET CANNOT BE TESTED WITHOUT ONE**, and the first thing worth
      testing here is what a forged callback gets back. `get()` returns a `Reply` and the listener
      writes it, which is why these cases exist at all.

      **THE STATE COOKIE IS SPENT ON USE.** Leaving it set would let one consent screen sign in
      twice, and a replayed callback is exactly what an attacker keeps.

      **THE ERROR PAGE DOES NOT ECHO THE CALLBACK.** It is reached by a browser with
      attacker-supplied query values; repeating them back is a reflection. The test asserts the
      code and state never appear in the body.
IMPORTS: pytest, quantamind.serve.web.routes, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.serve.web import routes, signin
from quantamind.types.settings import Settings

NOW = 1_700_000_000


@pytest.fixture
def configured(tmp_path: Path) -> Settings:
    return Settings(
        oauth_client_id="abc123", oauth_client_secret="s3cret", database_path=str(tmp_path)
    )


@pytest.fixture
def github(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(signin, "_post", lambda url, body: {"access_token": "gho"})
    monkeypatch.setattr(signin, "_get", lambda url, token: {"login": "dhanush", "id": 4242})


def _header(reply: routes.Reply, name: str) -> list[str]:
    return [v for k, v in reply.headers if k == name]


def test_login_redirects_and_plants_a_state_cookie(configured: Settings) -> None:
    reply = routes.get("/login", "", configured)

    assert reply.status == 302
    assert _header(reply, "Location")[0].startswith("https://github.com/login/oauth/authorize")
    assert "qm_state=" in _header(reply, "Set-Cookie")[0]


@pytest.mark.parametrize("flag", ["HttpOnly", "Secure", "SameSite=Lax"])
def test_the_state_cookie_carries_every_flag(configured: Settings, flag: str) -> None:
    assert flag in _header(routes.get("/login", "", configured), "Set-Cookie")[0]


def test_login_without_configuration_says_so_rather_than_redirecting_nowhere() -> None:
    reply = routes.get("/login", "", Settings())

    assert reply.status == 503
    assert "not configured" in reply.body


def test_a_callback_matching_its_cookie_signs_in(configured: Settings, github: None) -> None:
    reply = routes.get("/callback?code=c&state=s", "qm_state=s", configured, at=NOW)

    assert reply.status == 302
    assert _header(reply, "Location") == ["/"]
    assert any(signin.COOKIE in c for c in _header(reply, "Set-Cookie"))


def test_the_state_cookie_is_spent_on_use(configured: Settings, github: None) -> None:
    """Leaving it set lets one consent screen sign in twice."""
    reply = routes.get("/callback?code=c&state=s", "qm_state=s", configured, at=NOW)

    cleared = [c for c in _header(reply, "Set-Cookie") if c.startswith("qm_state=")]

    assert cleared and "Max-Age=0" in cleared[0]


def test_a_callback_whose_state_does_not_match_is_refused(
    configured: Settings, github: None
) -> None:
    reply = routes.get("/callback?code=c&state=attacker", "qm_state=victim", configured, at=NOW)

    assert reply.status == 400
    assert not any(signin.COOKIE in c for c in _header(reply, "Set-Cookie"))


def test_a_callback_with_no_cookie_at_all_is_refused(configured: Settings, github: None) -> None:
    """Nothing to compare must not compare equal."""
    assert routes.get("/callback?code=c&state=s", "", configured, at=NOW).status == 400


def test_the_error_page_does_not_echo_the_callback(configured: Settings, github: None) -> None:
    """Reached by a browser carrying attacker-supplied values; repeating them is a reflection."""
    reply = routes.get("/callback?code=EVILCODE&state=EVILSTATE", "qm_state=x", configured, at=NOW)

    assert "EVILCODE" not in reply.body
    assert "EVILSTATE" not in reply.body


def test_an_unknown_path_is_a_404_not_a_redirect(configured: Settings) -> None:
    reply = routes.get("/anything-else", "", configured)

    assert reply.status == 404
    assert _header(reply, "Location") == []
