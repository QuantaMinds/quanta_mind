"""Which systems a customer has agreed we may quote INTO a pull request comment.

WHAT: `Source` names where context came from; `allowed(clone, sha)` reads
      `.quantamind/context.toml` and returns the sources whose text may be quoted. `quotable`
      answers for one source.
WHY:  **D6c. "EGRESS IS A DECISION, NOT A DETAIL."** Reading a Jira ticket to understand a change
      is one thing; printing its text into a GitHub comment is another, and the second moves the
      customer's data from a system with one access list into a system with a different one. A
      private Slack thread quoted into a public repository's pull request is a data incident that
      no amount of review quality makes acceptable.

      **DENY BY DEFAULT, AND PER SOURCE.** No file means nothing outside GitHub is quoted. A
      customer who wants Jira text in their comments says so about Jira, and that says nothing
      about Slack. One switch for "external context" would let agreeing to a ticket title agree to
      a private channel.

      **GITHUB IS ALWAYS QUOTABLE AND THAT IS NOT AN EXCEPTION.** The comment is posted to GitHub,
      by an app the customer installed on GitHub, quoting text already in the same repository and
      visible to everyone who can see the pull request. Nothing crosses a boundary, so there is no
      decision to ask for. Every OTHER source crosses one.

      **A FILE WE CANNOT READ GRANTS NOTHING.** Not an error, not a default-open: an unreadable
      consent file is the absence of consent, which is the only reading that cannot leak. This is
      the one place in the product where "we could not tell" and "no" are deliberately the same
      answer, and the reason is that the cost of the two mistakes is not symmetric.
IMPORTS: stdlib tomllib, ingest.blob. Leftward only.
CONSUMED BY: `serve/review/change_facts.py`, and the renderers that quote external text.
"""

from __future__ import annotations

import tomllib
from enum import Enum
from pathlib import Path

from quantamind.ingest.blob import BlobUnreadable, at

CONSENT_PATH = Path(".quantamind") / "context.toml"
TABLE = "context"


class Source(Enum):
    """Where a piece of context came from. **The value is the key in the consent file.**"""

    GITHUB = "github"
    """The repository's own issues and pull requests. Always quotable — see the module docstring."""

    JIRA = "jira"
    SLACK = "slack"


ALWAYS = frozenset({Source.GITHUB})
"""Sources needing no consent, because quoting them crosses no boundary."""


def allowed(clone: Path, sha: str = "HEAD") -> frozenset[Source]:
    """The sources this repository has agreed may be quoted into its comments.

    **AN UNREADABLE OR ABSENT FILE RETURNS `ALWAYS` AND NOTHING MORE.** There is no path through
    this function that grants a source without the customer having written its name down.
    """
    try:
        raw = at(clone, sha, CONSENT_PATH.as_posix())
    except BlobUnreadable:
        return ALWAYS
    if raw is None:
        return ALWAYS
    try:
        document = tomllib.loads(raw)
    except (tomllib.TOMLDecodeError, ValueError):
        return ALWAYS

    declared = document.get(TABLE)
    if not isinstance(declared, dict):
        return ALWAYS

    granted = set(ALWAYS)
    for source in Source:
        # **ONLY `True` GRANTS.** A string, a number or a missing key is not consent, and reading
        # "yes" or 1 as agreement would let a typo open an egress path.
        if declared.get(f"quote_{source.value}") is True:
            granted.add(source)
    return frozenset(granted)


def quotable(source: Source, granted: frozenset[Source]) -> bool:
    """Whether text from `source` may appear in the comment."""
    return source in granted
