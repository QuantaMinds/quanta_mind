"""Ask each forge what it still covers, and withdraw what we hold that it does not list.

WHAT: `reconcile(settings, listing)` walks every live account, compares what we hold against what
      the forge lists, and withdraws the difference. `Reconciled` says what happened per account.
WHY:  **`installation_repositories` SENDS A DELTA, AND A DELTA IS NOT SELF-HEALING.** `Installed`
      carries the full list on an `installation` event, which is idempotent — re-provisioning six
      existing tenants does nothing. Removals have no such property: one dropped delivery and a
      repository stays entitled forever, reviewed and billed, with nothing anywhere recording that
      we are wrong. `serve/installation/installation_event.py` handles the delivery that arrives;
      this is the
      only thing that notices the one that did not.

      **AN OUTAGE MUST NEVER DEPROVISION A CUSTOMER, AND THAT IS THE WHOLE DESIGN.** A timeout, a
      rate limit, a 500 and a revoked key all mean "we could not ask", which is not the same fact
      as "the forge says this repository is gone". Only an answer withdraws. `onboarding.admit`
      already refuses to downgrade an installation on an unreadable repository for the same reason;
      the asymmetry here is stronger because the cost is a silently unreviewed customer.

      **THE LISTING IS AN ARGUMENT, NOT AN IMPORT.** It is the one piece that opens a socket, so
      passing it in is what lets every decision below be tested against a real store with no
      network — the same seam `serve/installation_event.settle` uses for its answering function.

      **A LISTING THAT COMES BACK EMPTY IS REFUSED, NOT OBEYED.** An installation covering nothing
      is not a state GitHub produces — it lists at least the repository we authenticated against —
      so an empty list is far more likely to be a shape we misread than a customer who removed
      every repository at once. Obeying it would withdraw the entire account on a parsing mistake,
      which is the single most expensive thing this module could get wrong. `NotInstalled` is how
      a caller says "gone", deliberately and by name.
IMPORTS: ingest.installation_scope (the two failure kinds), store.{installations,schema,
      tenancy}, types.settings, stdlib sqlite3. Leftward only.
CONSUMED BY: `serve/commands/run_reconcile.py`.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from quantamind.ingest.installation_scope import CouldNotAsk, NotInstalled
from quantamind.store import installations, schema, tenancy
from quantamind.types.settings import Settings

# **THE FAILURE KINDS COME FROM THE LAYER THAT PRODUCES THEM**, so there is one definition of
# what 'gone' means rather than two that can drift apart on opposite sides of an import.
__all__ = ["Account", "CouldNotAsk", "NotInstalled", "Reconciled", "reconcile", "stale"]

Listing = Callable[[str], tuple[str, ...]]
"""Given one repository we hold, every repository its installation still covers."""


@dataclass(frozen=True, slots=True)
class Account:
    """What reconciliation did about one account, and why."""

    account: str
    held: int
    withdrawn: tuple[str, ...] = field(default_factory=tuple)
    gone: bool = False
    unasked: str = ""
    """Empty when the forge answered. Otherwise why it did not, and nothing was withdrawn."""

    def render(self) -> str:
        if self.unasked:
            return f"{self.account}: NOT RECONCILED — {self.unasked}"
        if self.gone:
            return f"{self.account}: gone — withdrew {len(self.withdrawn)}/{self.held}"
        if not self.withdrawn:
            return f"{self.account}: {self.held} repository(ies), all still covered"
        names = ", ".join(self.withdrawn)
        return f"{self.account}: withdrew {len(self.withdrawn)}/{self.held} — {names}"


@dataclass(frozen=True, slots=True)
class Reconciled:
    """Every account looked at. `unasked` is a count, not a silence."""

    accounts: tuple[Account, ...]

    @property
    def withdrawn(self) -> int:
        return sum(len(one.withdrawn) for one in self.accounts)

    @property
    def unasked(self) -> int:
        return sum(1 for one in self.accounts if one.unasked)

    def render(self) -> str:
        lines = [one.render() for one in self.accounts] or ["no accounts to reconcile"]
        lines.append(
            f"{len(self.accounts)} account(s): withdrew {self.withdrawn}, "
            f"could not ask about {self.unasked}"
        )
        return "\n".join(lines)


def stale(held: tuple[str, ...], listed: tuple[str, ...]) -> tuple[str, ...]:
    """What we hold that the forge did not list. Pure, so the comparison is testable exhaustively.

    **BOTH SIDES ARE `owner/name` STRINGS AND THAT IS ASSERTED BY THE CALLER, NOT ASSUMED HERE.**
    AGENTS.md rule 14 names a comparison where `candidate in ours_caught` was false for all 194
    because the two sides held different populations. A set difference between a full name and a
    bare name would return everything and read as a catastrophic mass uninstall.
    """
    return tuple(sorted(set(held) - set(listed)))


def reconcile(settings: Settings, listing: Listing, *, account: str = "") -> Reconciled:
    """Compare every live account against the forge. Withdraws only on an answer."""
    root = Path(settings.database_path)
    conn = schema.open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        names = (account,) if account else installations.accounts(conn)
        looked = [_one(conn, name, listing) for name in names]
    finally:
        conn.close()
    return Reconciled(tuple(looked))


def _one(conn: sqlite3.Connection, account: str, listing: Listing) -> Account:
    """One account. Never raises: a failure on one must not stop the rest of the estate."""
    held = installations.covered(conn, account)
    if not held:
        return Account(account, 0)
    try:
        listed = listing(held[0])
    except NotInstalled:
        return _withdraw(conn, account, held, held, gone=True)
    except CouldNotAsk as exc:
        return Account(account, len(held), unasked=str(exc)[:160])
    if not listed:
        # See the module docstring: an installation covering nothing is not a state the forge
        # produces, so this is read as a shape we misunderstood rather than as an instruction.
        return Account(account, len(held), unasked="the forge listed no repositories at all")
    return _withdraw(conn, account, held, stale(held, listed))


def _withdraw(
    conn: sqlite3.Connection,
    account: str,
    held: tuple[str, ...],
    drop: tuple[str, ...],
    *,
    gone: bool = False,
) -> Account:
    """Mark `drop` removed and report what actually moved, never what was attempted."""
    now = int(time.time())
    marked = tuple(repo for repo in drop if installations.withdraw(conn, repo, at=now) > 0)
    return Account(account, len(held), marked, gone=gone)
