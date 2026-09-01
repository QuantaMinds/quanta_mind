"""Context living outside GitHub: a Jira issue, a Slack message. Read over stdlib HTTP.

WHAT: `jira(base, key, token)` and `slack(channel, timestamp, token)` return `Elsewhere` — the
      title and body of one item — or a typed `Unreachable` naming why not.
WHY:  **D6c, CHEAPEST FIRST.** Both are REST and JSON over HTTPS, so `urllib` reaches them and
      `pyproject.toml`'s `dependencies = []` holds. What they need is not a library but the
      customer's credential, which is why both take a token rather than reading one from anywhere.

      **NOTHING HERE DECIDES WHETHER THE TEXT MAY BE QUOTED.** `ingest/context/egress.py` does, and
      it is a separate module on purpose: reading a ticket to rank a change and printing its text
      into a GitHub comment are different acts with different consequences, and a reader that also
      granted permission would make the second invisible.

      **A FAILURE IS A VALUE, NOT AN EXCEPTION AND NOT AN EMPTY STRING.** `Unreachable` carries the
      reason, so the comment can say "your Jira was not reachable" rather than printing a change
      with no stated goal and letting the reader assume the author gave none. That distinction is
      this product's whole argument, applied to one more source.

      **AND `Unreachable` IS THE EXPECTED ANSWER FOR MOST INSTALLATIONS.** No token is configured
      for either system today, so both functions decline immediately without opening a socket. A
      product that treated an unconfigured integration as a fault would report a fault to every
      customer who has not bought that integration.
IMPORTS: stdlib json, urllib. Nothing from this project.
CONSUMED BY: `serve/review/change_facts.py`, behind `ingest/context/egress.py`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum

from quantamind.types.deployment import Destination, permit

TIMEOUT_S = 10
"""Seconds before a context fetch is abandoned. **Context is a nicety; the review is not.**

A slow Jira must not hold up a review that is already worth posting without it."""

BODY_CAP = 2_000
"""Characters kept from a body. Enough to state a goal, far short of copying a document."""


class Unreachable(Enum):
    """Why nothing came back. **Every member is a different sentence to the reader.**"""

    NOT_CONFIGURED = "not_configured"
    """No credential for this system. The common case, and not a fault."""

    REFUSED = "refused"
    """The system answered and declined — wrong token, no permission, or no such item."""

    UNREADABLE = "unreadable"
    """It answered with something we could not parse. Ours to fix, not the customer's."""


@dataclass(frozen=True, slots=True)
class Elsewhere:
    """One item of context from a system that is not GitHub."""

    title: str
    body: str
    url: str = ""


def _fetch(request: urllib.request.Request) -> dict[str, object] | Unreachable:
    """One JSON GET. **Every failure becomes a typed value.**"""
    try:
        # **ASK BEFORE THE SOCKET OPENS.** D7f: an air-gapped deployment REFUSES
        # this, rather than attempting it and failing somewhere the customer sees
        # in their egress log and we do not.
        permit(Destination.EXTERNAL_CONTEXT)
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as answer:
            payload = json.loads(answer.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return Unreachable.REFUSED
    except (json.JSONDecodeError, UnicodeDecodeError):
        return Unreachable.UNREADABLE
    return payload if isinstance(payload, dict) else Unreachable.UNREADABLE


def _https(url: str, token: str, scheme: str) -> urllib.request.Request | None:
    """A request, or None when the URL is not HTTPS.

    **PLAIN HTTP IS REFUSED RATHER THAN DOWNGRADED.** The token is in the header; sending it over
    a URL the customer typed without a scheme would put a credential on the wire in clear.
    """
    if not url.startswith("https://"):
        return None
    return urllib.request.Request(url, headers={"Authorization": f"{scheme} {token}"})


def jira(base: str, key: str, token: str) -> Elsewhere | Unreachable:
    """One Jira issue by key, e.g. `PROJ-42`.

    `base` is the customer's site, `https://acme.atlassian.net`. The token is theirs and arrives
    from settings; this never reads a credential from the environment itself.
    """
    if not token or not base or not key:
        return Unreachable.NOT_CONFIGURED
    request = _https(f"{base.rstrip('/')}/rest/api/3/issue/{key}", token, "Bearer")
    if request is None:
        return Unreachable.REFUSED
    got = _fetch(request)
    if isinstance(got, Unreachable):
        return got
    fields = got.get("fields")
    if not isinstance(fields, dict):
        return Unreachable.UNREADABLE
    summary = str(fields.get("summary") or "")
    description = fields.get("description")
    # Jira's v3 description is a document tree, not a string. Rendering it fully is a parser we
    # have not written, so an unrenderable body is empty rather than a guess at its text.
    body = description if isinstance(description, str) else ""
    return Elsewhere(summary, body[:BODY_CAP], f"{base.rstrip('/')}/browse/{key}")


def slack(channel: str, timestamp: str, token: str) -> Elsewhere | Unreachable:
    """One Slack message by channel and timestamp.

    **THE MOST DANGEROUS SOURCE TO QUOTE**, which is why `egress.Source.SLACK` defaults to refused:
    a private channel's text printed into a pull request is visible to everyone who can read the
    repository, who are not the people who could read the channel.
    """
    if not token or not channel or not timestamp:
        return Unreachable.NOT_CONFIGURED
    url = (
        f"https://slack.com/api/conversations.history?channel={channel}"
        f"&latest={timestamp}&inclusive=true&limit=1"
    )
    request = _https(url, token, "Bearer")
    if request is None:
        return Unreachable.REFUSED
    got = _fetch(request)
    if isinstance(got, Unreachable):
        return got
    # **SLACK ANSWERS 200 WITH `ok: false`.** Reading only the status code would turn a refusal
    # into an empty message, which is the failure this module is shaped to prevent.
    if got.get("ok") is not True:
        return Unreachable.REFUSED
    messages = got.get("messages")
    if not isinstance(messages, list) or not messages:
        return Unreachable.UNREADABLE
    first = messages[0]
    if not isinstance(first, dict):
        return Unreachable.UNREADABLE
    return Elsewhere("", str(first.get("text") or "")[:BODY_CAP])
