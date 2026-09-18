"""An installation delivery: provision what it added, withdraw what it lost, then warm.

WHAT: `settle(decision, settings, answer)` handles both installation outcomes end to end. It calls
      `answer(status, payload)` once, in the middle, and does the slow half afterwards.
WHY:  **IT TAKES THE ANSWERING FUNCTION BECAUSE THE REPLY HAS TO HAPPEN BETWEEN TWO PIECES OF
      WORK.** GitHub needs a 2XX inside ten seconds; provisioning store files is fast, and
      `onboarding.admit()` clones and indexes each repository at roughly 31 seconds apiece. A
      function that returned its reply could not warm afterwards, and one that warmed first would
      time the delivery out and earn a retry — turning one slow install into several. The listener
      passes `_say` for the same reason it passes `work` for a review: the socket owns writing, this
      owns deciding.

      **ONE ENTRY POINT FOR BOTH OUTCOMES, BECAUSE ONE DELIVERY CAN BE BOTH.** An
      `installation_repositories` payload carries `repositories_added` and `repositories_removed`
      together. Handling them in two branches of the listener would mean whichever branch matched
      first silently dropped the other half.

      **IT IS NOT IN `serve/listener.py` BECAUSE IT IS INSTALLATION WORK, NOT SOCKET WORK** — the
      argument `serve/installed_repos.py` already makes about itself, and the 200-line cap is again
      what said so out loud when a fourth outcome needed room.
IMPORTS: serve.{installed_repos,onboarding,withdrawal}, types.forge.delivery,
      types.settings.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quantamind.serve.installed_repos import claim, provisioned
from quantamind.serve.onboarding import admit
from quantamind.serve.withdrawal import withdraw
from quantamind.types.forge.delivery import Installed, Withdrawn
from quantamind.types.settings import Settings

Answer = Callable[[int, dict[str, Any]], None]


def settle(decision: Installed | Withdrawn, settings: Settings, answer: Answer) -> None:
    """Provision, withdraw, answer, then warm. `answer` is called exactly once."""
    if isinstance(decision, Withdrawn):
        # Nothing to provision and nothing to warm: the installation is over. The reply names what
        # was marked so a delivery that matched no rows is visible in GitHub's own delivery log.
        gone = withdraw(decision, settings)
        answer(200, {"withdrawn": list(gone), "account": decision.account})
        return

    made = provisioned(decision, settings)
    # **THE ROWS ARE WRITTEN BEFORE THE ANSWER, AND THAT ORDERING IS A BUG FIX.** They used to be
    # written by `admit()` — after the reply, after four GitHub calls per repository and a ~31s
    # clone-and-index each. A removal arriving inside that window found no rows and withdrew
    # nothing, reporting success. Seen against a live endpoint: install two, remove one, and the
    # removal reported `withdrawn: []` while the row was still being created behind it.
    claim(made, settings, decision.account)
    # **WITHDRAWN BEFORE THE ANSWER TOO.** Marking a row removed is one UPDATE; the reply should
    # carry it, because a caller told two different things about one delivery in two places has no
    # way to know which to believe.
    gone = withdraw(decision, settings) if decision.no_longer_covered else ()
    answer(200, {"provisioned": made, "withdrawn": list(gone)})
    admit(made, settings, decision.account)
