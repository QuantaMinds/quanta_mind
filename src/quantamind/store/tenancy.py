"""Which database file a tenant's history lives in, and why it is not one file for everybody.

WHAT: `store_for(root, owner, name)` returns the path to one repository's store, creating the
      directory but never the file. `roots()` lists the stores that exist under a root.
WHY:  **THE SCHEMA ALREADY SEPARATES TENANTS LOGICALLY AND THAT IS NOT THE SAME AS ISOLATING
      THEM.** `repo` is `UNIQUE (host, name)` and five tables key on `repo_id`, so two customers'
      counts cannot mix inside one file. What one file gives them anyway is a shared blast radius:
      one corrupt page, one bad migration, one `rm` and every tenant is gone together. It also
      gives them a shared SQLite writer lock, so one long index build blocks every other
      installation's delivery.

      **AND OFFBOARDING A CUSTOMER SHOULD BE DELETING A FILE.** With one store it is a DELETE
      across five tables that has to get every foreign key right, on live data, with no second
      chance -- against `rm one/path.db`. A contract ending is the worst moment to be running
      hand-written cascades.

      **THE UNIT IS THE REPOSITORY, NOT THE INSTALLATION.** An installation can cover many
      repositories and its selection changes when somebody ticks a box in a settings page; a
      repository is the thing history belongs to and the thing `ensure_repo` already keys. Keying
      files by installation would move a tenant's data every time they changed their selection.

      **THE PATH IS DERIVED, NEVER TAKEN FROM THE PAYLOAD.** `owner` and `name` arrive from a
      webhook. They are HMAC-authenticated, which makes them not-arbitrary and not the same as
      well-formed: `..` or a separator in either would place a store outside the root or overwrite
      another tenant's. `serve/working_clone.path_for` refuses the same shapes for the same reason.
IMPORTS: stdlib, plus `store.schema` to create a tenant's file. Nothing to its right.
CONSUMED BY: `serve/review_delivery.py`, `serve/health.py`, `serve/listener.py`.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from quantamind.store import schema

SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class TenantRefused(ValueError):
    """A repository name that cannot be turned into a path. Carries what was rejected."""

    def __init__(self, part: str, reason: str) -> None:
        super().__init__(f"refusing to derive a store path from {part!r}: {reason}")
        self.part, self.reason = part, reason


def _segment(part: str) -> str:
    """One path segment, or a refusal. **A traversal here is a cross-tenant write.**"""
    cleaned = part.strip()
    if not cleaned or cleaned in {".", ".."} or not SAFE.match(cleaned):
        raise TenantRefused(part, "expected a plain owner or repository name")
    return cleaned


def store_for(root: Path, owner: str, name: str) -> Path:
    """`<root>/<owner>/<name>.db`. The directory is created; the file is not.

    **THE FILE IS LEFT ABSENT ON PURPOSE.** `store.schema.open_store` refuses a store whose version
    does not match, and `serve/health.py` distinguishes "no store yet" from "a store that will not
    open". Touching an empty file here would turn a first delivery into a version mismatch.
    """
    place = root / _segment(owner)
    place.mkdir(parents=True, exist_ok=True)
    return place / f"{_segment(name)}.db"


def tenants(root: Path) -> list[tuple[str, str]]:
    """Every `(owner, name)` with a store under `root`, sorted. Empty when there are none.

    Used by an operator asking who is installed, and by nothing that makes a decision -- a listing
    that drives behaviour would make a missing file mean "not a customer".
    """
    if not root.is_dir():
        return []
    return sorted(
        (owner.name, store.stem)
        for owner in root.iterdir()
        if owner.is_dir()
        for store in owner.glob("*.db")
    )


def provision(root: Path, repos: Iterable[str]) -> tuple[list[str], list[str]]:
    """Create a store for each `owner/name`. Returns `(made, refused)`, both named.

    **PROVISIONED ON INSTALL, NOT ON THE FIRST PULL REQUEST.** Without this a new tenant has no
    store until somebody opens one, and that first review pays a full clone and index build -- 37
    seconds on a 115,776-commit repository. Doing it at install moves the cost to the moment a
    human is watching an install page rather than waiting on a review.

    **IDEMPOTENT.** `store_for` creates the directory and `open_store` creates the file, so a
    redelivered installation event provisions the same tenants again with no effect. GitHub
    redelivers; a provisioning step that could not be repeated would be a bug waiting for a retry.

    **REFUSALS ARE RETURNED, NOT LOGGED AND DROPPED.** A repository that failed to provision is a
    customer whose first review will be slow or broken, and a caller that cannot see the list
    cannot say so.
    """
    made: list[str] = []
    refused: list[str] = []
    for full in repos:
        owner, _, name = str(full).partition("/")
        try:
            schema.open_store(store_for(root, owner, name)).close()
            made.append(str(full))
        except (sqlite3.Error, OSError, TenantRefused):
            refused.append(str(full))
    return made, refused
