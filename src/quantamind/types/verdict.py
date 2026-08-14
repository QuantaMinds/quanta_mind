"""Typed silence: the record we emit when we could not answer.

WHAT: `Confidence`, `Provenance`, `Reason`, `Construct` and the `Unresolved` record that
      carries them. The vocabulary for saying "we did not resolve this, and here is why".
WHY:  "There is nothing here" and "we failed here" must never be the same value on the wire.
      Every layer that can fail to resolve something emits an `Unresolved` instead of
      returning nothing, so the coverage line has something to report and a reader can tell
      an empty result from an unexamined one. This is the product's reason to exist reduced
      to a dataclass.
IMPORTS: stdlib only (dataclasses, enum). Nothing -- this is the floor of the floor.
CONSUMED BY: parse, rank, verify, render, and the store that persists them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Confidence(Enum):
    """How much weight a claim carries. There is no default, deliberately.

    RESOLVED is the only value that may be published as fact, and it requires two
    independent resolvers agreeing. A single resolver's answer is INFERRED at best.
    """

    RESOLVED = "resolved"
    INFERRED = "inferred"
    UNRESOLVED = "unresolved"


class Provenance(Enum):
    """Which mechanism produced a claim. Never inferred from context, always recorded.

    The distinction that matters is PARSER versus MODEL: a claim a parser produced can be
    re-checked deterministically, and a claim a model produced cannot.
    """

    PARSER = "parser"
    GIT_HISTORY = "git_history"
    MODEL = "model"
    HUMAN = "human"


class Reason(Enum):
    """Why a resolution failed. Closed set, because an open one becomes a free-text field.

    Adding a member is a deliberate act and forces every match statement to be revisited,
    which is the point -- a new failure mode should not arrive silently as a string.
    """

    DYNAMIC_DISPATCH = "dynamic_dispatch"
    RUNTIME_REGISTRATION = "runtime_registration"
    UNPARSEABLE_SYNTAX = "unparseable_syntax"
    LANGUAGE_UNSUPPORTED = "language_unsupported"
    GENERATED_FILE = "generated_file"
    EXTERNAL_SYMBOL = "external_symbol"
    TIMEOUT = "timeout"


class Construct(Enum):
    """The syntactic thing we were looking at when resolution failed.

    Kept separate from `Reason` because the pair is what makes a coverage line useful: a
    reader wants "a call site, because of dynamic dispatch", not one or the other.
    """

    CALL_SITE = "call_site"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    DECORATOR = "decorator"
    FILE = "file"


@dataclass(frozen=True, slots=True)
class Site:
    """Where in the tree something is. Line is 1-indexed; 0 means the whole file."""

    path: str
    line: int = 0

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("Site.path is empty; a site with no path cannot be reported")
        if self.line < 0:
            raise ValueError(f"Site.line is negative at {self.path}: {self.line}")

    def render(self) -> str:
        return self.path if self.line == 0 else f"{self.path}:{self.line}"


@dataclass(frozen=True, slots=True)
class Unresolved:
    """One thing we could not resolve, and enough context to report it to a human.

    Constructed only with all three fields. There is no `Unresolved(site)` shorthand,
    because an unresolved record without a reason is the same as silence and defeats the
    purpose of having the type at all.
    """

    site: Site
    reason: Reason
    construct: Construct

    def render(self) -> str:
        """One line for the coverage line: what it was, where, and why it stayed unknown."""
        what = self.construct.value.replace("_", " ")
        why = self.reason.value.replace("_", " ")
        return f"{what} at {self.site.render()} — {why}"


class ResolveError(Exception):
    """Raised when a resolver cannot proceed, as distinct from resolving to nothing.

    An `Unresolved` is a RESULT: we looked and could not tell. This exception is a
    FAILURE: we could not look. Collapsing the two is how a broken reader comes to report
    a clean coverage line, so they are different types and always have been.
    """

    def __init__(self, site: Site, reason: str) -> None:
        super().__init__(f"{site.render()}: {reason}")
        self.site = site
        self.reason = reason
