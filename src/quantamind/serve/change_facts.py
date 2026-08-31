"""Everything about a change that is true whether or not the model ran.

WHAT: `gather(clone, repo, number, changed, head_sha)` returns a `Facts`: the author's stated goal
      and its tickets, the bodies repeated elsewhere in the tree, how much of each file changed,
      and the repositories this one declares a link to.
WHY:  **THESE FOUR ARRIVED ONE AT A TIME AND EACH ADDED A LINE TO `deliver()` UNTIL IT CROSSED THE
      CAP THREE TIMES.** They are one concern and they belong together: every one is read from the
      clone or the pull request, every one is reproducible on the same commit by anybody, and none
      of them costs a model call. That is what makes them assertable where a model finding is only
      a claim to check.

      **THE POINT IS THAT A DELIVERY WITH `infer/` OFF STILL SAYS SOMETHING.** The model is
      unreachable, refused, or out of tokens often enough that a comment built only on it degrades
      to a file list — which is what happened before D6a. Gathering the deterministic half in one
      place makes it obvious that it does not depend on the other half, and hard to accidentally
      couple them later.

      **NOTHING HERE RAISES.** `behind()` reports a failed read as a value, `twins()` counts the
      files it could not parse, `effort()` returns nothing for a path it saw no hunk for, and
      `links_file.read()` distinguishes an absent declaration from an unreadable one. A delivery is
      not worth losing over any of them, and each already says so in its own module.
IMPORTS: ingest.{context.tickets,diff,standards.links_file}, parse.{change_effort,duplicate_bodies}.
      Rightmost layer, leftward only.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from quantamind.ingest.context.tickets import Context, behind
from quantamind.ingest.diff import unified_diff
from quantamind.ingest.standards import links_file
from quantamind.ingest.standards.links_file import Link
from quantamind.parse.change_effort import Effort, effort
from quantamind.parse.duplicate_bodies import Duplicates, twins


@dataclass(frozen=True, slots=True)
class Facts:
    """The deterministic half of a review. Every field is re-derivable from the same commit."""

    intent: Context
    repeated: Duplicates
    sizes: Mapping[str, Effort] = field(default_factory=dict)
    links: tuple[Link, ...] = ()
    links_unreadable: bool = False
    """**Distinct from an empty `links`.** No declaration means this business declared none, which
    is the common case; an unreadable one means we could not tell, and printing the first for the
    second would be a claim about somebody's architecture made out of our own failed read."""


def gather(clone: Path, repo: str, number: int, changed: Sequence[str], head_sha: str) -> Facts:
    """Read all four. **One API call for the diff, one for the pull request, the rest is local.**"""
    links, refused = links_file.read(clone, head_sha)
    return Facts(
        intent=behind(repo, number),
        repeated=twins(clone, list(changed)),
        sizes=effort(unified_diff(repo, number), changed),
        links=links,
        links_unreadable=bool(refused),
    )
