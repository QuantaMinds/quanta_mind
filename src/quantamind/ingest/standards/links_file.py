"""The repositories a business says are connected to this one, declared rather than discovered.

WHAT: `read(clone, sha)` returns `(links, refused)` from `.quantamind/links.toml` at the reviewed
      commit — every well-formed link, and an `Unresolved` for every declaration that is not.
WHY:  **DECLARED BEATS DISCOVERED, AND THAT IS A PRODUCT DECISION BEFORE IT IS A TECHNICAL ONE.**
      Finding the links ourselves needs an org-wide crawl and permissions across every repository a
      customer owns — a large ask, a large blast radius, and an answer that is *our guess about
      their architecture*. **A link they wrote down is provenance an auditor can be shown.**
      → `docs/plans/roadmap/product-build.md` "D3a The business declares its links"

      **THIS SHIPS BEFORE ANYTHING READS THE OTHER REPOSITORY, AND IT IS STILL WORTH SHIPPING.**
      D3b — a changed exported symbol checked against the repositories that import it — is gated on
      a design partner with more than one repository that matters. What the declaration buys today
      is TYPED SILENCE: the comment can name the repositories it did NOT look at instead of
      printing one static sentence saying cross-repository impact is unchecked. `AGENTS.md`
      non-negotiable 3 — "no edge here" and "we failed here" must never be the same value — applied
      to a boundary rather than a call site.

      **AN UNREADABLE DECLARATION IS NOT AN ABSENT ONE.** A malformed file comes back as a refusal
      naming where it was, never as "this business declared no links": the second would report a
      customer as having no cross-repository surface at the moment their declaration stopped
      parsing, which is the failure this product exists to refuse. Same contract as
      `ingest/standards/rules_file.py`, deliberately — one shape for one kind of file.
IMPORTS: stdlib tomllib, pathlib; `ingest.blob` for the read at a commit, `types.verdict` for the
      refusal. Nothing to its right.
CONSUMED BY: `render/blocks/scope_block.py`, via `serve/review_delivery.py`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from quantamind.ingest.blob import BlobUnreadable, at
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

LINKS_PATH = Path(".quantamind") / "links.toml"
TABLE = "link"


@dataclass(frozen=True, slots=True)
class Link:
    """One repository this one is declared to be connected to."""

    repo: str
    """`owner/name`. The identity GitHub uses, so a reader can go and look."""

    why: str = ""
    """What the customer says the connection is. Shown verbatim; never inferred."""

    def render(self) -> str:
        return f"`{self.repo}`" + (f" — {self.why}" if self.why else "")


class LinkRefused(ValueError):
    """A declaration that cannot become a link. Carries what was wrong with it."""


def _refusal(where: str, reason: Reason) -> Unresolved:
    return Unresolved(site=Site(where), reason=reason, construct=Construct.FILE)


def _one(entry: object, index: int) -> tuple[Link | None, Unresolved | None]:
    """One declaration into a link, or a refusal naming where it was. Never both, never neither."""
    where = f"{LINKS_PATH.as_posix()}[{index}]"
    if not isinstance(entry, dict):
        return None, _refusal(where, Reason.MALFORMED_DECLARATION)
    repo = str(entry.get("repo", "")).strip()
    # **`owner/name` OR NOTHING.** A bare name is not a repository anybody can open, and guessing
    # the owner from the repository under review would invent a link the customer did not declare.
    if repo.count("/") != 1 or not all(part.strip() for part in repo.split("/")):
        return None, _refusal(where, Reason.MALFORMED_DECLARATION)
    return Link(repo=repo, why=str(entry.get("why", "")).strip()), None


def read(clone: Path, sha: str) -> tuple[tuple[Link, ...], tuple[Unresolved, ...]]:
    """Every link declared at `sha`, and a refusal for every declaration that is not one.

    **NO FILE AND AN UNREADABLE FILE ARE DIFFERENT ANSWERS.** Absent means this business declared
    no links, which is the common case and a real one. Unparseable means they declared something we
    could not read, and reporting that as "no links" would quietly narrow their cross-repository
    surface to nothing on the day their file broke.

    **DUPLICATES ARE KEPT ONCE, NOT REFUSED.** A repository named twice is a typo in a declaration,
    not a contradiction; dropping the whole file over it would cost the customer every other link.
    """
    try:
        source = at(clone, sha, LINKS_PATH.as_posix())
    except BlobUnreadable:
        return (), (_refusal(LINKS_PATH.as_posix(), Reason.UNPARSEABLE_SYNTAX),)
    if source is None:
        return (), ()

    try:
        parsed = tomllib.loads(source)
    except tomllib.TOMLDecodeError:
        return (), (_refusal(LINKS_PATH.as_posix(), Reason.MALFORMED_DECLARATION),)

    entries = parsed.get(TABLE, [])
    if not isinstance(entries, list):
        return (), (_refusal(LINKS_PATH.as_posix(), Reason.MALFORMED_DECLARATION),)

    links: list[Link] = []
    refused: list[Unresolved] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        link, refusal = _one(entry, index)
        if refusal is not None:
            refused.append(refusal)
        elif link is not None and link.repo.lower() not in seen:
            seen.add(link.repo.lower())
            links.append(link)
    return tuple(links), tuple(refused)
