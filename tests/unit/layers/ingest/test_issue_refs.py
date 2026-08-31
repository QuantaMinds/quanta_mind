"""The issue references in a pull request's own text, and which of them leave the repository.

WHAT: Drives `ingest.context.issue_refs.references()` over the shapes an author actually writes.
WHY:  **NOTHING IN THIS CODEBASE HAD EVER READ `Closes #412`,** so every case here is a first. The
      ones that matter are not the happy path: a reference that names another repository must come
      back marked, because `tickets.behind()` refuses those without making a request and a `foreign`
      flag that defaulted False would quietly quote somebody's private issue title into a comment.

      **THE FALSE-POSITIVE CASES ARE TESTED AS DELIBERATELY AS THE TRUE ONES.** This reads text and
      not markdown structure, so `#4` inside a code fence is a reference to it. That is a known
      cost — a spurious line in a block, never a wrong verdict — and it is pinned here so the next
      reader can tell a limitation that was seen from one that was missed.
IMPORTS: quantamind.ingest.context.issue_refs. No other project imports.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.ingest.context.issue_refs import Ref, references

HERE = "acme/app"


def _one(body: str, title: str = "") -> Ref:
    found = references(title, body, HERE)
    assert len(found) == 1, f"expected exactly one reference, got {found}"
    return found[0]


@pytest.mark.parametrize(
    ("body", "keyword"),
    [
        ("Closes #412", "closes"),
        ("closed #412", "closed"),
        ("Fixes #412", "fixes"),
        ("Fix: #412", "fix"),
        ("resolves #412", "resolves"),
        ("Related to #412", ""),
        ("#412", ""),
    ],
)
def test_the_closing_keyword_is_kept_because_it_is_a_different_claim(
    body: str, keyword: str
) -> None:
    """ "Closes #412" says this change finishes that work; "#412" says only that it relates.

    Folding them together would print a stronger claim than the author made, inside a block whose
    only job is to state the author's claim faithfully.
    """
    ref = _one(body)

    assert (ref.number, ref.keyword, ref.foreign) == (412, keyword, False)


def test_a_reference_in_the_title_counts_and_comes_first() -> None:
    """Authors put the ticket in the title as often as the body, and it is read first."""
    found = references("Closes #7 — retire the shim", "See also #9.", HERE)

    assert [(r.number, r.keyword) for r in found] == [(7, "closes"), (9, "")]


@pytest.mark.parametrize(
    "body",
    [
        "See other/lib#7",
        "See https://github.com/other/lib/issues/7",
        "See https://github.com/other/lib/pull/7",
        "Fixes other/lib#7",
    ],
)
def test_a_reference_naming_another_repository_is_marked_foreign(body: str) -> None:
    """**THE FLAG THE EGRESS RULE RESTS ON.** `tickets.behind()` never requests a foreign ref, so
    a default of False here would turn a refusal into a fetch and a private title into a comment.
    """
    ref = _one(body)

    assert (ref.repo, ref.number, ref.foreign) == ("other/lib", 7, True)


def test_our_own_repository_written_out_in_full_is_not_foreign() -> None:
    """`acme/app#3` and `#3` are the same ticket. Treating the explicit spelling as foreign would
    decline to read an issue in the repository we are already reviewing."""
    assert _one("Closes acme/app#3").foreign is False
    assert _one("Closes ACME/App#3").foreign is False, "GitHub owner names are case-insensitive"


def test_one_ticket_named_twice_is_one_reference_and_keeps_the_stronger_claim() -> None:
    """Fetching it twice would print it twice, and taking the LAST occurrence would silently
    downgrade `closes #5` to a bare mention three paragraphs later."""
    found = references("", "Closes #5.\n\nMore prose.\n\nSee #5 again.", HERE)

    assert len(found) == 1
    assert found[0].keyword == "closes"


def test_an_unqualified_reference_takes_the_reviewed_repository() -> None:
    """A `Ref` with an empty repo would be unprintable and unfetchable. It is resolved here."""
    assert _one("Closes #1").repo == HERE


def test_text_with_no_reference_returns_empty_and_not_a_placeholder() -> None:
    """Empty is a real answer: this author named no ticket. The block says so."""
    assert references("A title", "Prose with a # and a number 412, but no reference.", HERE) == ()


def test_a_bare_number_or_a_hash_alone_is_not_a_reference() -> None:
    """`#` is a markdown heading and `412` is a number. Neither names an issue."""
    assert references("", "# Heading\n\n412 files changed.", HERE) == ()


def test_a_reference_inside_a_code_fence_is_still_read_and_that_is_known() -> None:
    """**A LIMITATION THAT WAS SEEN, NOT MISSED.** This reads text, not markdown structure.

    The cost is one spurious line in a block a human is reading anyway, against the complexity of
    a markdown parser with `dependencies = []`. Recorded as an assertion so the trade is visible
    rather than discovered later as a surprise.
    """
    assert _one("```\ngit log --grep '#412'\n```").number == 412


def test_the_rendered_form_shows_the_repository_only_when_it_is_another_one() -> None:
    """`closes #412` for ours, `other/lib#7` for theirs — a reader needs the qualifier exactly
    when the reference points somewhere they cannot assume."""
    assert _one("Closes #412").render() == "closes #412"
    assert _one("See other/lib#7").render() == "other/lib#7"
    assert _one("Fixes other/lib#7").render() == "fixes other/lib#7"
