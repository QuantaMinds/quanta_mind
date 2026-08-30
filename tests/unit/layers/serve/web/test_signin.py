"""Verification that a callback with the wrong state is refused before the code is spent.

WHAT: Drives `serve/web/signin` — the authorize URL, the state check, the cookie flags, and the
      cookie parser — with GitHub's two endpoints stubbed and a real store underneath.
WHY:  **WITHOUT A CHECKED `state`, ANYONE CAN LOG A VICTIM INTO THE ATTACKER'S ACCOUNT.** They
      hand the victim's browser a callback carrying THEIR code; the victim's session then belongs
      to the attacker, and everything the victim does afterwards happens in the attacker's
      account. That is login-CSRF, and the parameter exists for it. A test that only checked the
      happy path would pass with the comparison deleted.

      **THE STATE IS COMPARED BEFORE THE CODE IS EXCHANGED.** Spending a real authorisation code
      on a request about to be rejected is a wasted credential and a needless call.

      **THE COOKIE CARRIES THREE FLAGS AND EACH CLOSES A DIFFERENT DOOR.** `HttpOnly` stops script
      reading it, `Secure` stops it travelling in the clear, `SameSite=Lax` stops it riding a
      cross-site POST. Asserting one would let the other two be dropped silently.
IMPORTS: pytest, quantamind.serve.web.signin, quantamind.store.{accounts,schema}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from quantamind.serve.web import signin
from quantamind.store.accounts import whose
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings

NOW = 1_700_000_000
CONFIGURED = Settings(oauth_client_id="abc123", oauth_client_secret="s3cret")


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    return open_store(tmp_path / "s.db")


@pytest.fixture
def github(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """GitHub's two endpoints, recording what was asked of them."""
    asked: dict[str, object] = {"exchanged": 0}

    def post(url: str, body: dict[str, str]) -> dict[str, object]:
        asked["exchanged"] = int(asked["exchanged"]) + 1
        asked["body"] = body
        return {"access_token": "gho_token"}

    monkeypatch.setattr(signin, "_post", post)
    monkeypatch.setattr(signin, "_get", lambda url, token: {"login": "dhanush", "id": 4242})
    return asked


def test_the_authorize_url_carries_the_state_and_the_narrow_scope() -> None:
    url = signin.authorize_url(CONFIGURED, "abc")

    assert "state=abc" in url
    assert "scope=read%3Auser" in url, "sign-in asked for more than a name"
    assert "client_id=abc123" in url


def test_an_authorize_url_without_state_is_refused() -> None:
    """A URL with no state produces a callback nobody can validate."""
    with pytest.raises(signin.SignInFailed, match="state value is required"):
        signin.authorize_url(CONFIGURED, "")


def test_an_unconfigured_app_refuses_rather_than_building_a_broken_url() -> None:
    with pytest.raises(signin.SignInFailed, match="no oauth_client_id"):
        signin.authorize_url(Settings(), "abc")


def test_a_matching_state_signs_the_user_in(conn: sqlite3.Connection, github) -> None:
    token = signin.sign_in(conn, CONFIGURED, code="c", state="s", expected="s", at=NOW)

    assert whose(conn, token, at=NOW).login == "dhanush"


def test_a_mismatched_state_is_refused_and_the_code_is_never_spent(
    conn: sqlite3.Connection, github
) -> None:
    """The login-CSRF case, and the exchange must not happen at all."""
    with pytest.raises(signin.SignInFailed, match="state did not match"):
        signin.sign_in(conn, CONFIGURED, code="c", state="attacker", expected="victim", at=NOW)

    assert github["exchanged"] == 0, "a real authorisation code was spent on a rejected callback"


def test_an_empty_expected_state_is_refused(conn: sqlite3.Connection, github) -> None:
    """No stored state means nothing to compare, which must not compare equal."""
    with pytest.raises(signin.SignInFailed, match="state did not match"):
        signin.sign_in(conn, CONFIGURED, code="c", state="", expected="", at=NOW)


def test_a_callback_with_no_code_is_refused(conn: sqlite3.Connection, github) -> None:
    with pytest.raises(signin.SignInFailed, match="no code"):
        signin.sign_in(conn, CONFIGURED, code="", state="s", expected="s", at=NOW)


def test_github_returning_no_login_is_a_failure_not_an_anonymous_session(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch, github
) -> None:
    """An unnamed session is a session belonging to nobody."""
    monkeypatch.setattr(signin, "_get", lambda url, token: {})

    with pytest.raises(signin.SignInFailed, match="no login or id"):
        signin.sign_in(conn, CONFIGURED, code="c", state="s", expected="s", at=NOW)

    assert conn.execute("SELECT COUNT(*) FROM session").fetchone()[0] == 0


def test_the_secret_goes_in_the_body_and_nowhere_else(conn: sqlite3.Connection, github) -> None:
    signin.sign_in(conn, CONFIGURED, code="c", state="s", expected="s", at=NOW)

    assert github["body"]["client_secret"] == "s3cret"


@pytest.mark.parametrize("flag", ["HttpOnly", "Secure", "SameSite=Lax"])
def test_the_cookie_carries_every_flag(flag: str) -> None:
    """Each closes a different door; asserting one would let the others be dropped."""
    assert flag in signin.cookie("t0ken")


def test_the_cookie_is_read_back_out_of_a_header_with_others_beside_it() -> None:
    header = f"other=1; {signin.COOKIE}=t0ken; another=2"

    assert signin.token_in(header) == "t0ken"


def test_a_header_without_the_cookie_yields_empty_rather_than_raising() -> None:
    assert signin.token_in("other=1; another=2") == ""
    assert signin.token_in("") == ""


def test_two_states_are_never_the_same() -> None:
    assert signin.new_state() != signin.new_state()
