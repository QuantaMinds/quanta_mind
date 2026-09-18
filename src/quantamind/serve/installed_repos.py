"""Everything an installation needs written BEFORE the delivery is answered.

WHAT: `provisioned(decision, settings)` creates one store file per repository and returns the
      ones it made; `claim(repos, settings, account)` writes their `installation` rows.
WHY:  **IT ANSWERS BEFORE IT WARMS, SO THIS DELIBERATELY STOPS SHORT.** GitHub needs a 2XX inside
      ten seconds and a clone does not finish in ten. Folding `onboarding.admit()` in here would put
      the slow half in front of the reply and reintroduce the timeout the acknowledge-then-work
      shape exists to avoid. The caller does both, in that order.

      **IT IS NOT IN `serve/listener.py` BECAUSE IT IS INSTALLATION WORK, NOT SOCKET WORK.** That
      module was provisioning store files and formatting two log lines about it, and its 200-line
      cap is what said so out loud when a POST route needed room.

      **AND IT IS NOT IN `serve/onboarding.py`, WHICH IS WHERE IT BELONGS.** That module is also at
      the cap. This is a seam the file-length rule chose rather than a reader would have, and saying
      so is cheaper than leaving the next person to wonder.

      **A REFUSED REPOSITORY IS PRINTED, NOT COUNTED.** `tenancy.provision` refuses a name it cannot
      turn into a safe path, and "provisioned 3/5" without the two names is not something an
      operator can act on.
      **THE TWO ARE ONE CONCERN: THE FAST HALF.** Both are one write and neither touches the
      network, which is what makes them safe in front of GitHub's ten-second reply window —
      `onboarding.admit()` is the slow half and stays there. They sit together because the reason
      they run here is the same reason, and splitting them would invite the next person to move
      one of them back.

      **`claim()` EXISTS BECAUSE THE ROWS USED TO BE WRITTEN TOO LATE.** `admit()` recorded them
      after four GitHub calls and a ~31s clone-and-index per repository. A removal arriving inside
      that window found no rows, withdrew nothing, and reported success — seen against a live
      endpoint, not reasoned about. It is also the ONLY caller that may `reinstate`, because an
      installation event is the one thing that states a repository is covered.
IMPORTS: store.{installations,schema,tenancy}, types.settings, stdlib pathlib/time/typing.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings


def provisioned(decision: Any, settings: Any) -> list[str]:
    """Create the store files for an installation and report what was made. **Does not warm.**

    **THE CALLER ANSWERS BEFORE IT WARMS, SO THIS DELIBERATELY STOPS SHORT.** GitHub needs a 2XX
    inside ten seconds and a clone does not finish in ten; folding `admit()` in here would put the
    slow half in front of the reply and reintroduce the timeout this shape exists to avoid.

    **IT LIVES HERE RATHER THAN IN `serve/listener.py` BECAUSE IT IS INSTALLATION WORK.** The socket
    layer was provisioning store files and formatting two log lines about it, and the 200-line cap
    on that module is what said so out loud.
    """
    made, refused = tenancy.provision(Path(settings.database_path), decision.repos)
    for full in refused:
        print(f"[serve] {full}: NOT provisioned", flush=True)
    print(
        f"[serve] install {decision.action!r} {decision.account}: "
        f"provisioned {len(made)}/{len(decision.repos)}",
        flush=True,
    )
    return made


def claim(repos: list[str], settings: Settings, account: str) -> None:
    """Write the installation rows NOW, before the delivery is answered.

    **THIS IS THE FAST HALF, AND SPLITTING IT OUT IS THE POINT.** `admit()` records too, but only
    after four GitHub calls and a clone per repository — so until this existed, a removal arriving
    during a warm-up found no rows to remove and said it had removed nothing. Writing the row is
    one INSERT; nothing here touches the network.

    **IT IS THE ONE CALLER THAT MAY REINSTATE.** An installation event states that a repository is
    covered, which is exactly the claim that clears `removed_at`. `admit()`'s later write does not
    get to make that claim — see `store/installations.record`.
    """
    if not repos:
        return
    conn = open_store(tenancy.shared(Path(settings.database_path), tenancy.ACCOUNTS))
    try:
        now = int(time.time())
        for repo in repos:
            owner = repo.split("/", 1)[0]
            installations.record(conn, account or owner, repo, at=now, reinstate=True)
    finally:
        conn.close()
