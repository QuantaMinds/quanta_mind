"""An installation ended, or stopped covering some repositories. Record it.

WHAT: `withdraw(decision, settings)` marks the affected `installation` rows removed and returns
      the repository names it marked, so a no-op is visible rather than inferred.
WHY:  **`store/installations.withdraw()` HAD NO CALLER AT ALL.** It was written, tested and never
      wired, so an uninstall left every row `ACTIVE` and `State.REMOVED` was unreachable in
      production. `Entitlement.may_review` reads `state is not REMOVED` first, which meant the one
      branch that refuses outright could not be taken by a customer who had actually left. A rule
      that cannot fire and a rule that never needed to fire produce the same output, which is the
      defect AGENTS.md rule 14 names.

      **IT RETURNS WHAT IT MARKED, NOT WHETHER IT SUCCEEDED.** A whole-account withdrawal that
      matched nothing and one that removed nine repositories both "worked". The names are the only
      thing that tells an operator which happened, and `withdraw()` already returns a rowcount for
      the same reason.

      **A WHOLE-ACCOUNT REMOVAL IS READ FROM OUR STORE, NOT FROM THE PAYLOAD.** GitHub omits the
      repository list on `installation.deleted`, so the only record of what that installation
      covered is the one we wrote at install time. Trusting the payload here would mark nothing and
      report success.

      **IT DOES NOT DELETE THE TENANT STORE, AND THAT IS DELIBERATE.** `removed_at` means "they
      left", and the audit trail is the thing a compliance team asked us to keep. Destroying it on
      an uninstall would make leaving and never having been a customer the same answer, and a
      reinstall a month later would silently lose the history. `store/tenancy.py` has no delete
      path for the same reason.
IMPORTS: store.{installations,schema,tenancy}, types.forge.delivery, types.settings. Leftward only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import time
from pathlib import Path

from quantamind.store import installations, schema, tenancy
from quantamind.types.forge.delivery import Installed, Withdrawn
from quantamind.types.settings import Settings


def withdraw(decision: Withdrawn | Installed, settings: Settings) -> tuple[str, ...]:
    """Mark what this delivery says we no longer cover. Returns the repositories marked."""
    root = Path(settings.database_path)
    conn = schema.open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        if isinstance(decision, Withdrawn):
            targets = installations.covered(conn, decision.account)
        else:
            targets = decision.no_longer_covered
        if not targets:
            return ()
        now = int(time.time())
        marked = [repo for repo in targets if installations.withdraw(conn, repo, at=now) > 0]
    finally:
        conn.close()
    kind = decision.action if isinstance(decision, Withdrawn) else "removed"
    print(
        f"[serve] {kind} {decision.account}: withdrew {len(marked)}/{len(targets)} repository(ies)",
        flush=True,
    )
    return tuple(marked)
