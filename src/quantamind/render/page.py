"""One HTML page, escaped, with no dependency and no template engine.

WHAT: `page(title, body)` wraps content in a document. `escaped(text)` is the only way text
      reaches it. `pre(text)` shows an existing text report without re-rendering it.
WHY:  **EVERY NAME ON THIS PAGE COMES FROM SOMEBODY ELSE.** A repository name, an account, a rule
      id — all of them arrive from GitHub or a customer's `.quantamind/rules.toml`, and a page
      that interpolates them raw is an injection with extra steps. `escaped()` exists so the
      escaping is a function call somebody can grep for rather than a habit.

      **THE TEXT REPORTS ARE SHOWN, NOT REBUILT.** `render/dashboard.py` and
      `render/compliance_table.py` already decide what those tables say, and re-rendering them in
      HTML would be a second implementation of the same judgement — the one that drifts. They go
      inside `<pre>`, escaped, so the web page and the CLI cannot disagree about a number.

      **NO CSS FRAMEWORK, NO SCRIPT.** `pyproject.toml` declares `dependencies = []` and a
      dashboard is not the place to break it. A page with no script is also a page where a missed
      escape cannot execute anything.
IMPORTS: stdlib only.
CONSUMED BY: `serve/web/routes.py`.
"""

from __future__ import annotations

import html

STYLE = (
    "body{font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;max-width:60rem;"
    "margin:2rem auto;padding:0 1rem;color:#111;background:#fff}"
    "a{color:#0645ad}pre{background:#f6f6f6;padding:1rem;overflow-x:auto;white-space:pre-wrap}"
    "h1,h2{font-weight:600}"
)


def escaped(text: str) -> str:
    """The only way caller text reaches a page. `quote=True` covers attribute contexts too."""
    return html.escape(text, quote=True)


def pre(text: str) -> str:
    """An existing text report, shown verbatim and escaped. Never re-rendered."""
    return f"<pre>{escaped(text)}</pre>"


def link(href: str, label: str) -> str:
    """An anchor whose href and label are both escaped, because both carry caller text."""
    return f'<a href="{escaped(href)}">{escaped(label)}</a>'


def page(title: str, body: str) -> str:
    """A whole document. `body` is HTML the caller has already escaped; `title` is text.

    **`body` IS TRUSTED AND `title` IS NOT**, which is the one asymmetry here worth stating: a
    caller assembles `body` from `escaped()`, `pre()` and `link()`, and passing raw text to it is
    the mistake this docstring exists to make visible.
    """
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{escaped(title)}</title><style>{STYLE}</style></head>"
        f"<body>{body}</body></html>"
    )
