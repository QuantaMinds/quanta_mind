"""Which account an installation belongs to, and whether we may review for it.

WHAT: `record()` writes one repository's installation row; `entitled(conn, repo)` returns an
      `Entitlement` saying whether we may review and how we know; `withdraw()` marks an uninstall.
WHY:  **THE INSTALL FLOW PROVISIONED A STORE AND DID NOT KNOW WHOSE IT WAS.** `product-build.md`
      B4. Without this row there is nobody to attribute a review to, and B5 — "today any
      installation is reviewed, paid or not" — has nothing to check.

      **`UNKNOWN` IS A STATE, NOT A DEFAULT FOR `NO`.** A repository installed before this table
      existed was never assessed, and `eligible` stays NULL for it. Reading NULL as refused would
      turn every existing customer off at the next delivery; reading it as allowed would grant an
      entitlement nobody checked. It is returned as `UNKNOWN` and the caller decides, which is the
      only reading that does not invent a fact.

      **AN UNINSTALL IS RECORDED, NEVER DELETED.** `removed_at` is set and the row stays. A
      compliance trail that forgets is not one, and "they were never a customer" and "they left"
      are different answers to an auditor.

      **IT TAKES PRIMITIVES, NOT A `Verdict`.** `verify/` sits to the RIGHT of `store/`, so this
      layer cannot import the type that produced the decision. The caller flattens it.
IMPORTS: stdlib only. The store layer.
CONSUMED BY: `serve/onboarding.py` on installation, `serve/review_delivery.py` at delivery.
"""

from __future__ import annotations

import enum
import sqlite3
from dataclasses import dataclass


class State(enum.Enum):
    """How this repository stands with us. Three values, none of them a default for another."""

    UNKNOWN = "unknown"
    """No row. Installed before this table existed, or never installed at all."""

    ACTIVE = "active"
    REMOVED = "removed"
    """Uninstalled. Distinct from UNKNOWN: we knew them and they left."""


@dataclass(frozen=True, slots=True)
class Entitlement:
    """Whether a review may run, and the evidence for it. Never a bare boolean."""

    state: State
    tier: str
    eligible: bool | None
    reasons: tuple[str, ...]

    @property
    def may_review(self) -> bool:
        """**UNKNOWN REVIEWS.** Refusing it would silence every installation predating the table."""
        return self.state is not State.REMOVED

    def why(self) -> str:
        if self.state is State.UNKNOWN:
            return "no installation row; predates the mapping or was never installed"
        if self.state is State.REMOVED:
            return "the installation was removed"
        if self.eligible is None:
            return f"installed on the {self.tier} tier; eligibility was never assessed"
        if self.eligible:
            return f"installed on the {self.tier} tier and eligible"
        return f"installed on the {self.tier} tier, NOT eligible: {'; '.join(self.reasons)}"


def record(
    conn: sqlite3.Connection,
    account: str,
    repo: str,
    *,
    at: int,
    tier: str = "free",
    eligible: bool | None = None,
    reasons: tuple[str, ...] = (),
) -> None:
    """Write or refresh one repository's installation. Idempotent — GitHub redelivers.

    **`first_seen` IS NOT MOVED BY A REDELIVERY.** It is when we first saw them, and an
    installation event replayed a month later must not rewrite that.
    """
    if not account.strip() or "/" not in repo:
        raise ValueError(
            f"an installation needs an account and an owner/name repo, got {account!r} {repo!r}"
        )
    conn.execute(
        "INSERT INTO installation (account, repo, tier, eligible, reasons, first_seen, removed_at)"
        " VALUES (?, ?, ?, ?, ?, ?, NULL) ON CONFLICT(account, repo) DO UPDATE SET"
        " tier = excluded.tier, eligible = excluded.eligible, reasons = excluded.reasons,"
        " removed_at = NULL",
        (account, repo, tier, eligible, "\n".join(reasons), at),
    )
    conn.commit()


def withdraw(conn: sqlite3.Connection, repo: str, *, at: int) -> int:
    """Mark every row for `repo` removed. Returns how many, so a no-op is visible."""
    cursor = conn.execute(
        "UPDATE installation SET removed_at = ? WHERE repo = ? AND removed_at IS NULL", (at, repo)
    )
    conn.commit()
    return int(cursor.rowcount)


def entitled(conn: sqlite3.Connection, repo: str) -> Entitlement:
    """Whether a review may run for `repo`, and how we know. Never raises on a missing row."""
    row = conn.execute(
        "SELECT tier, eligible, reasons, removed_at FROM installation WHERE repo = ?", (repo,)
    ).fetchone()
    if row is None:
        return Entitlement(State.UNKNOWN, "", None, ())
    tier, eligible, reasons, removed_at = row
    return Entitlement(
        state=State.REMOVED if removed_at is not None else State.ACTIVE,
        tier=str(tier),
        eligible=None if eligible is None else bool(eligible),
        reasons=tuple(r for r in str(reasons or "").split("\n") if r),
    )
