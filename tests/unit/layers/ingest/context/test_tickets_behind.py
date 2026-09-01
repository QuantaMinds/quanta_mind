"""What `behind()` fetches, what it refuses, and the four things it must never confuse.

WHAT: Drives `ingest.context.tickets.behind()` with the pull-request read and the issues API both
      stubbed, and asserts on the `Context` it returns.
WHY:  **FOUR STATES LEAVE `Context.stated` EMPTY AND THEY ARE NOT THE SAME ANSWER.** The author
      wrote no description; a reference named another repository; GitHub would not return the
      issue; there were more references than we fetch. Collapsing any pair produces the failure
      `AGENTS.md` non-negotiable 3 exists to refuse — most sharply the first and third, where an
      outage of ours would be printed as a statement about somebody's work.

      **THE FOREIGN CASE ASSERTS THAT NO REQUEST WAS MADE, NOT THAT NONE SUCCEEDED.** A test that
      only checked the ticket was absent would pass against an implementation that asked GitHub for
      a private issue, was refused, and recorded the refusal — which is the egress leak, still
      leaking, wearing the right outcome. The stub records every call and the assertion is on that
      list.

      **AND THE STUB RETURNS A REAL PAYLOAD SHAPE.** `is_pull` is read from the presence of a
      `pull_request` key, which is how GitHub distinguishes them; a stub that returned a bare title
      would let that field default silently.
IMPORTS: pytest, quantamind.ingest.context.tickets, quantamind.ingest.diff.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.ingest import github_api
from quantamind.ingest.context import tickets as under_test
from quantamind.ingest.context.tickets import FETCH_CAP, Declined, behind
from quantamind.ingest.diff import DiffReadFailed, Stated

REPO = "acme/app"


@pytest.fixture
def asked(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every path the issues API was asked for, in order. Empty is an assertable answer."""
    seen: list[str] = []

    def _call(repo: str, path: str, **_: object) -> bytes:
        seen.append(path)
        number = path.rsplit("/", 1)[-1]
        if number == "404":
            raise github_api.ApiFailed("GET", path, "404 Not Found")
        body = {"title": f"Ticket {number}", "state": "open"}
        if number == "77":
            body["pull_request"] = {"url": "..."}
        return json.dumps(body).encode()

    monkeypatch.setattr(under_test.github_api, "call", _call)
    return seen


def _says(monkeypatch: pytest.MonkeyPatch, title: str, body: str) -> None:
    monkeypatch.setattr(under_test, "stated_goal", lambda *_: Stated(title, body))


def test_a_same_repository_ticket_is_fetched_and_carries_what_github_said(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    _says(monkeypatch, "Retire the shim", "Closes #412")

    context = behind(REPO, 9)

    assert asked == [f"repos/{REPO}/issues/412"]
    assert context.skipped == ()
    (ticket,) = context.tickets
    assert (ticket.title, ticket.state, ticket.is_pull) == ("Ticket 412", "open", False)
    # **THE TITLE IS GITHUB'S JOB.** A bare `#412` in a comment body is expanded by GitHub into
    # *title* `#412`, so printing ours as well rendered the title twice — seen on
    # `QuantaMinds/quanta_mind#92`. The title is still FETCHED, because `behind()` reading it is
    # how we know the reference resolves at all.
    assert ticket.render() == "closes #412 (issue, open)"
    assert ticket.title == "Ticket 412", "the title is still read; it is only not printed"


def test_a_reference_that_is_really_a_pull_request_says_so(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """GitHub numbers issues and pull requests in one sequence, so `#77` is often a pull request.
    Asserting "issue" would be a claim the payload contradicts."""
    _says(monkeypatch, "", "Builds on #77")

    (ticket,) = behind(REPO, 9).tickets

    assert ticket.is_pull is True
    assert "pull request" in ticket.render()


def test_a_foreign_reference_is_declined_without_a_single_request(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """**THE EGRESS RULE, ASSERTED ON THE CALL LIST AND NOT ON THE OUTCOME.** An implementation
    that asked, was refused, and recorded the refusal would produce the same `Context` and would
    still have sent somebody's private issue number to an endpoint we hold no token for.
    """
    _says(monkeypatch, "", "Fixes other/lib#7")

    context = behind(REPO, 9)

    assert asked == [], "a cross-repository reference must not be requested at all"
    assert context.tickets == ()
    (skipped,) = context.skipped
    assert skipped.why is Declined.ANOTHER_REPOSITORY
    assert "other/lib#7" in skipped.render()


def test_an_issue_github_refuses_is_a_typed_skip_and_not_a_missing_ticket(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """ "There was no ticket" and "we could not read the ticket" must not be one value."""
    _says(monkeypatch, "", "Closes #404 and #412")

    context = behind(REPO, 9)

    assert len(asked) == 2
    assert [t.ref.number for t in context.tickets] == [412]
    (skipped,) = context.skipped
    assert (skipped.ref.number, skipped.why) == (404, Declined.NOT_READABLE)


def test_references_past_the_cap_are_counted_rather_than_dropped(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """One reference is one API call. The remainder is named, so the block can say how many it
    did not fetch instead of ending early and reading as though that were all of them."""
    _says(monkeypatch, "", " ".join(f"#{n}" for n in range(1, FETCH_CAP + 4)))

    context = behind(REPO, 9)

    assert len(asked) == FETCH_CAP, asked
    assert len(context.tickets) == FETCH_CAP
    assert [s.why for s in context.skipped] == [Declined.OVER_THE_CAP] * 3


def test_an_author_who_wrote_nothing_gives_an_empty_context_that_knows_it_is_empty(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """A real result. `empty()` is what lets the renderer print nothing here and only here."""
    _says(monkeypatch, "", "")

    context = behind(REPO, 9)

    assert context.empty() is True
    assert context.unreadable == ""


def test_a_pull_request_we_could_not_read_is_not_an_author_who_wrote_nothing(
    monkeypatch: pytest.MonkeyPatch, asked: list[str]
) -> None:
    """**THE ONE THAT WOULD LIBEL SOMEBODY.** Both leave `stated` empty; only one of them is a
    fact about the author. `empty()` must stay False so the block prints our failure as ours.
    """

    def _boom(*_: object) -> Stated:
        raise DiffReadFailed(REPO, 9, "the pull request payload was not an object")

    monkeypatch.setattr(under_test, "stated_goal", _boom)

    context = behind(REPO, 9)

    assert context.empty() is False
    assert "not an object" in context.unreadable
    assert (context.tickets, context.skipped) == ((), ())
    assert asked == [], "a failed pull-request read must not go on to fetch tickets"
