"""Every helper that puts caller text into HTML, and the escaping each one owes.

WHAT: Drives `render/page`'s `escaped`, `pre`, `link` and `page` with text carrying markup and
      asserts the markup does not survive as markup.
WHY:  **`render/page.py` HAD NO TESTS AT ALL.** Deleting the escaping from `pre()` — the helper
      every report on the repository page passes through, compliance, outcomes and now cost — broke
      nothing in the suite. The escaping was correct; nothing held it there, so the next edit to
      that line would have been silent.

      **`link()` ESCAPES BOTH HALVES BECAUSE BOTH CARRY CALLER TEXT.** An href is an attribute
      context, which is why `escaped` uses `quote=True`: a value that terminates the quoted
      attribute escapes the attribute without ever needing a `<`.
IMPORTS: quantamind.render.page.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.render.page import escaped, link, page, pre

MARKUP = '<script>alert("x")</script>'


def test_escaped_neutralises_tags_and_quotes() -> None:
    got = escaped(MARKUP)

    assert "<script>" not in got
    assert "&lt;script&gt;" in got
    assert '"' not in got, "quote=True is what makes this safe inside an attribute"


def test_pre_escapes_the_report_it_wraps() -> None:
    """The regression: this is the path every table on the repository page takes."""
    got = pre(f"QuantaMind — cost, {MARKUP}")

    assert got.startswith("<pre>") and got.endswith("</pre>")
    assert "<script>" not in got, f"a report reached the page as live markup: {got}"
    assert "&lt;script&gt;" in got


def test_link_escapes_the_href_as_well_as_the_label() -> None:
    got = link('/r/x" onmouseover="steal()', MARKUP)

    assert 'onmouseover="steal()"' not in got, f"the href broke out of its attribute: {got}"
    assert "<script>" not in got


def test_page_escapes_the_title_and_leaves_the_body_alone() -> None:
    """The body is already-rendered HTML by contract; the title is caller text."""
    got = page(MARKUP, "<h1>ok</h1>")

    assert "<h1>ok</h1>" in got, "the body must be placed verbatim, or every caller double-escapes"
    assert f"<title>{MARKUP}" not in got
    assert "&lt;script&gt;" in got
