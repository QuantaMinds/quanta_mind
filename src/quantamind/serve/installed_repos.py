"""The store files an installation needs, made before anything is warmed.

WHAT: `provisioned(decision, settings)` creates one store file per repository in an installation
      and returns the ones it made, printing the refusals.
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
IMPORTS: store.tenancy, stdlib pathlib/typing. Leftward only.
CONSUMED BY: `serve/listener.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantamind.store import tenancy


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
