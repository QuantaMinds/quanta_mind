"""What an installation still covers, asked of the forge rather than remembered.

WHAT: `covers(probe, settings)` returns every repository the installation covering `probe` lists.
      `NotInstalled` when the forge says the App is gone; `CouldNotAsk` for everything else.
WHY:  **THE TWO FAILURES ARE DIFFERENT FACTS AND THE CALLER ACTS ON ONLY ONE.** "The App is not
      installed" is the forge telling us about the customer; a timeout, a rate limit and a 500 tell
      us about the network. `serve/reconcile.py` withdraws entitlement on the first and nothing at
      all on the second, so collapsing them into one exception would make an outage look like a
      mass uninstall — with no error anywhere, because the run would have succeeded.

      **THE TOKEN IS MINTED BEFORE THE LISTING, AND THAT IS THE PROBE.** `ingest/github_api.call`
      falls back to an UNAUTHENTICATED request when no installation token can be minted, which is
      the right read for a public repository and useless here: the listing would come back 401 and
      "we are not installed" would be indistinguishable from "our key is wrong". Minting first
      turns the question into one the forge answers with a status code. The token is cached inside
      `app_auth`, so the listing that follows pays nothing for it.

      **IT PAGES, AND A TRUNCATED PAGE IS A REFUSAL.** GitHub returns 30 per page by default. An
      account with 31 repositories would otherwise report the first 30 and the caller would
      withdraw the 31st — a correct-looking answer that deprovisions a customer for owning too
      many repositories. Past the page ceiling this raises rather than returning what it has.
IMPORTS: ingest.{app_auth,github_api}, types.settings. Leftward only.
CONSUMED BY: `serve/reconcile.py`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantamind.ingest import app_auth
from quantamind.ingest.github_api import ApiFailed, call
from quantamind.types.settings import Settings

PER_PAGE = 100
# Ten pages is 1,000 repositories for one installation. Past it we refuse rather than truncate,
# because the caller treats an unlisted repository as one to withdraw.
MAX_PAGES = 10


class NotInstalled(RuntimeError):
    """The forge says this installation is gone. The only failure that withdraws anything."""


class CouldNotAsk(RuntimeError):
    """We did not get an answer. Carries why, and must withdraw nothing."""


def covers(probe: str, settings: Settings) -> tuple[str, ...]:
    """Every repository the installation covering `probe` still lists, deduplicated and ordered."""
    if not (settings.app_id and settings.app_key_path):
        raise CouldNotAsk(
            "no GitHub App configured; set QUANTAMIND_APP_ID and QUANTAMIND_APP_KEY_PATH"
        )
    try:
        app_auth.token(probe, settings.app_id, Path(settings.app_key_path))
    except app_auth.AuthFailed as exc:
        if exc.status == 404:
            raise NotInstalled(f"{probe}: {exc.reason}") from None
        raise CouldNotAsk(f"{probe}: {exc.reason}") from None

    found: list[str] = []
    for page in range(1, MAX_PAGES + 1):
        batch = _page(probe, page)
        found.extend(batch)
        if len(batch) < PER_PAGE:
            return tuple(sorted(set(found)))
    raise CouldNotAsk(
        f"{probe}: more than {PER_PAGE * MAX_PAGES} repositories; refusing to answer from a "
        "truncated list, because the caller would withdraw everything past the last page"
    )


def _page(probe: str, page: int) -> list[str]:
    """One page of `GET /installation/repositories`, as full names."""
    try:
        raw = call(probe, f"installation/repositories?per_page={PER_PAGE}&page={page}")
    except ApiFailed as exc:
        raise CouldNotAsk(f"{probe}: {exc.reason}") from None
    try:
        body: Any = json.loads(raw or b"null")
    except json.JSONDecodeError as exc:
        raise CouldNotAsk(f"{probe}: reply was not JSON: {exc}") from None
    listed = body.get("repositories") if isinstance(body, dict) else None
    if not isinstance(listed, list):
        # **A SHAPE WE DID NOT EXPECT IS NOT AN EMPTY INSTALLATION.** Returning `[]` here would
        # read to the caller as "the forge listed nothing", and `reconcile` refuses that too —
        # but saying so here names the cause instead of leaving the next reader to infer it.
        raise CouldNotAsk(f"{probe}: reply carried no repositories list: {str(body)[:120]}")
    return [
        str(one["full_name"]) for one in listed if isinstance(one, dict) and one.get("full_name")
    ]
