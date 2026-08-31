"""What the writers need from GitHub, and the ways an empty answer could lie about it.

WHAT: Drives `ingest/publish/preflight.gaps` over permission sets shaped like GitHub's real reply,
      including the one this installation actually returned.
WHY:  **A PERMISSION THAT WAS NEVER GRANTED IS NOT A CODE PATH**, so no test of the writer could
      have caught D1f shipping against an App with no `statuses` permission — the spy returned True
      and every test passed. What is testable is the check that ASKS, and specifically that its
      empty answer means "asked and satisfied" rather than "did not ask".
IMPORTS: quantamind.ingest.publish.{preflight,commit_status}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import inspect

from quantamind.ingest.publish import commit_status, preflight

# What installation 157102851 actually returned on 2026-08-30, before the permission was granted.
REAL = {"contents": "read", "metadata": "read", "pull_requests": "write"}


def test_the_permission_set_this_installation_really_had_reports_the_status_gap() -> None:
    found = preflight.gaps(REAL)

    assert [gap.permission for gap in found] == ["statuses"]
    assert found[0].held == "none", "a permission GitHub never mentioned must read as none"
    assert found[0].required == "write"


def test_an_empty_permission_set_is_not_a_clean_bill_of_health() -> None:
    """The failure this check would otherwise become: silence read as approval."""
    found = preflight.gaps({})

    assert len(found) == len(preflight.NEEDED), (
        "an installation reporting nothing was told every surface works"
    )


def test_read_does_not_satisfy_write() -> None:
    found = preflight.gaps({**REAL, "statuses": "read"})

    assert [gap.permission for gap in found] == ["statuses"]
    assert found[0].held == "read"


def test_a_level_we_do_not_recognise_satisfies_nothing() -> None:
    """A permission model we do not understand is not one we may assume is sufficient."""
    found = preflight.gaps({**REAL, "statuses": "maintain"})

    assert [gap.permission for gap in found] == ["statuses"]


def test_admin_satisfies_write() -> None:
    assert preflight.gaps({**REAL, "statuses": "admin"}) == ()


def test_a_full_permission_set_reports_nothing_and_says_nothing() -> None:
    full = {name: level for name, (level, _why) in preflight.NEEDED.items()}

    assert preflight.gaps(full) == ()
    assert preflight.sentence(()) == "", "an operator must not be handed a line about no problem"


def test_the_sentence_names_the_permission_and_that_installations_must_accept_it() -> None:
    said = preflight.sentence(preflight.gaps(REAL))

    assert "statuses: write" in said
    assert "ACCEPT" in said, (
        "granting the permission is not enough and an operator who stops there is stuck"
    )


def test_the_status_writer_has_a_declared_permission() -> None:
    """Ties the declaration to the writer, so deleting the `NEEDED` entry cannot go unnoticed.

    `preflight` names this as the hole it cannot see about itself: a writer added without a line in
    `NEEDED` is invisible to the check. This closes it for the writer that prompted the module.
    """
    posts_to = inspect.getsource(commit_status.post)

    assert "statuses" in posts_to, "the writer stopped posting to the statuses endpoint"
    assert "statuses" in preflight.NEEDED, (
        "commit_status posts to /statuses/ and no permission is declared for it"
    )
