"""Which declared repository imports what this change broke, and what happens when we cannot look.

WHAT: Drives `verify.consumers.affected()` with the clone lookup injected, over trees this test
      writes.
WHY:  **A LINK WE COULD NOT READ IS THE COMMON CASE, NOT THE EDGE ONE.** The App is installed on
      the repository under review and very often not on the one consuming it. "Nothing imports
      this" and "we could not open the consumer" are the two answers this product exists to keep
      apart, and here the second will be the frequent one for a long time.

      **THE MATCH IS AN IMPORT, NOT A MENTION.** Grepping for the symbol would hit a comment, a
      docstring, a same-named local and a string in a fixture. A false *"your change breaks
      billing"* is the most expensive sentence this product can print — it is about somebody
      else's repository, and the reader cannot check it without leaving their pull request.

      **AND NOTHING IS OPENED WHEN NOTHING BROKE.** An additive change asks no question, so no
      linked repository is fetched. `test_an_additive_change_opens_nothing` passes a lookup that
      raises, which is the only way to prove a call did not happen.
IMPORTS: quantamind.ingest.standards.links_file, quantamind.parse.public_api,
      quantamind.verify.consumers.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.ingest.standards.links_file import Link
from quantamind.parse.public_api import Break
from quantamind.verify.consumers import affected

BILLING = Link("acme/billing", "consumes our Invoice schema")
MOBILE = Link("acme/mobile")
BREAK = Break("total", "no longer takes `currency`")


def _repo(root: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


def test_a_consumer_that_imports_the_symbol_is_named(tmp_path: Path) -> None:
    clone = _repo(tmp_path, {"src/invoice.py": "from shared.money import total\n"})
    got = affected((BILLING,), (BREAK,), lambda repo: clone)

    (consumer,) = got.consumers
    assert (consumer.repo, consumer.symbol) == ("acme/billing", "total")
    assert consumer.where == ("src/invoice.py",)


def test_a_consumer_that_only_mentions_the_name_is_not_named(tmp_path: Path) -> None:
    """**THE FALSE POSITIVE THAT WOULD COST THE MOST.** A docstring, a comment and a local of the
    same name are not imports, and a grep cannot tell the difference."""
    clone = _repo(
        tmp_path,
        {
            "src/a.py": '"""Computes the total."""\ntotal = 1\n',
            "src/b.py": (
                "# total is computed elsewhere\ndef f():\n    total = 2\n    return total\n"
            ),
        },
    )

    assert affected((BILLING,), (BREAK,), lambda repo: clone).consumers == ()


def test_a_link_we_cannot_open_is_reported_as_unread(tmp_path: Path) -> None:
    """ "Nothing imports this" and "we could not look" must never be the same answer."""
    got = affected((MOBILE,), (BREAK,), lambda repo: None)

    assert got.consumers == ()
    assert [item.repo for item in got.unread] == ["acme/mobile"]
    assert "could not be opened" in got.unread[0].render()


def test_both_answers_appear_together(tmp_path: Path) -> None:
    """One readable consumer and one unreadable one is the expected real-world shape."""
    clone = _repo(tmp_path, {"src/invoice.py": "from shared.money import total\n"})
    got = affected(
        (BILLING, MOBILE), (BREAK,), lambda repo: clone if repo == "acme/billing" else None
    )

    assert [c.repo for c in got.consumers] == ["acme/billing"]
    assert [u.repo for u in got.unread] == ["acme/mobile"]
    assert got.asked() is True


def test_an_additive_change_opens_nothing() -> None:
    """**PROVEN BY A LOOKUP THAT RAISES**, which is the only way to show a call did not happen.
    A review of an additive change must cost nothing here."""

    def _explode(repo: str) -> Path:
        raise AssertionError(f"opened {repo} with nothing to ask about")

    got = affected((BILLING, MOBILE), (), _explode)

    assert got.asked() is False


def test_no_declared_links_opens_nothing(tmp_path: Path) -> None:
    """The common case: a repository that declared none. There is nobody to ask."""

    def _explode(repo: str) -> Path:
        raise AssertionError(f"opened {repo} with no links declared")

    assert affected((), (BREAK,), _explode).asked() is False


def test_a_test_file_in_the_consumer_does_not_count(tmp_path: Path) -> None:
    """A consumer's own tests importing the symbol is not a downstream dependency breaking; it is
    their suite, and naming it would send the reader to a file that is theirs to fix anyway."""
    clone = _repo(tmp_path, {"tests/test_invoice.py": "from shared.money import total\n"})

    assert affected((BILLING,), (BREAK,), lambda repo: clone).consumers == ()
