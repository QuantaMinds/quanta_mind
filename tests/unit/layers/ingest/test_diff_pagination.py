"""Verification that a change too large to read whole is refused, never silently truncated.

WHAT: Drives `ingest/diff.changed_files` over its pagination — a short page, an exhausted page
      budget, a malformed response — with the network read stubbed and nothing else faked.
WHY:  **THE REFUSAL WAS CORRECT AND NOTHING EXERCISED IT.** `changed_files` walks at most
      `MAX_PAGES` pages of `PER_PAGE` files and raises `DiffReadFailed` if the budget runs out
      with pages still coming, so a truncated file list can never be returned as a complete one.
      That is rule 3 — silence must be typed — implemented properly. But mutating `MAX_PAGES` to
      0 or 21 left every tier of the suite green: `ingest/diff` had no unit test, and the live
      tier cannot manufacture a thousand-file pull request to reach the branch.

      **A TRUNCATED LIST IS THE WORST FAILURE THIS MODULE COULD HAVE.** It would rank a change
      on the files it happened to see, publish a review of part of a diff, and read as a normal
      clean run. Nothing downstream could tell the difference.

      **THE BUDGET IS WRITTEN OUT AS 10 x 100.** Phrasing the boundary as `MAX_PAGES + 1` would
      read the values under test and pass at any of them, which is how they went unnoticed.
IMPORTS: pytest, quantamind.ingest.diff.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.ingest import diff

PAGES, PER_PAGE = 10, 100
"""The documented budget, written out. See the module docstring on why these are not imported."""


def _entry(name: str, status: str = "modified") -> dict[str, str]:
    return {"filename": name, "status": status}


def _stub(pages: dict[int, list[dict[str, str]]], monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Serve `pages` by page number, recording which pages were actually requested."""
    asked: list[int] = []

    def read(repo: str, number: int, path: str, accept: str = "") -> bytes:
        page = int(path.split("&page=")[1])
        asked.append(page)
        return json.dumps(pages.get(page, [])).encode()

    monkeypatch.setattr(diff, "_read", read)
    return asked


def test_the_budget_is_ten_pages_of_a_hundred() -> None:
    """The numbers the refusal below depends on. Both were freely mutable."""
    assert diff.MAX_PAGES == PAGES
    assert diff.PER_PAGE == PER_PAGE


def test_a_change_larger_than_the_budget_is_refused_not_truncated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every page full, forever. The list must never come back short and unlabelled."""
    full = [_entry(f"src/f{n}.py") for n in range(PER_PAGE)]
    asked = _stub(dict.fromkeys(range(1, PAGES + 3), full), monkeypatch)

    with pytest.raises(diff.DiffReadFailed, match="refusing to"):
        diff.changed_files("o/r", 1)

    assert asked == list(range(1, PAGES + 1)), "the page budget was not walked exactly once"


def test_a_short_page_ends_the_walk_and_returns_what_was_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ordinary case: fewer than a full page means the last page, and no further request."""
    asked = _stub({1: [_entry("src/a.py"), _entry("src/b.py")]}, monkeypatch)

    assert diff.changed_files("o/r", 1) == ["src/a.py", "src/b.py"]
    assert asked == [1], f"read {len(asked)} pages when one was enough"


def test_a_full_page_is_followed_by_another_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """The boundary: exactly PER_PAGE is indistinguishable from more, so it must keep going."""
    asked = _stub({1: [_entry(f"src/f{n}.py") for n in range(PER_PAGE)], 2: []}, monkeypatch)

    assert len(diff.changed_files("o/r", 1)) == PER_PAGE
    assert asked == [1, 2]


def test_a_change_touching_nothing_returns_empty_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty list is a legitimate answer, and must stay distinguishable from a failure."""
    _stub({1: []}, monkeypatch)

    assert diff.changed_files("o/r", 1) == []


def test_a_removed_file_is_dropped_and_a_modified_one_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`removed` has a history and no future; funding it spends budget on an unopenable file."""
    _stub({1: [_entry("src/gone.py", "removed"), _entry("src/here.py", "modified")]}, monkeypatch)

    assert diff.changed_files("o/r", 1) == ["src/here.py"]


def test_a_response_that_is_not_a_list_is_a_failure_not_an_empty_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GitHub returning an error object must not read as a change touching no files."""
    monkeypatch.setattr(diff, "_read", lambda *a, **k: b'{"message": "Not Found"}')

    with pytest.raises(diff.DiffReadFailed, match="files page 1 was dict"):
        diff.changed_files("o/r", 1)


def test_an_entry_missing_its_status_is_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A malformed entry cannot be skipped: skipping one silently shortens the file list."""
    monkeypatch.setattr(diff, "_read", lambda *a, **k: b'[{"filename": "src/a.py"}]')

    with pytest.raises(diff.DiffReadFailed, match="lacked filename/status"):
        diff.changed_files("o/r", 1)
