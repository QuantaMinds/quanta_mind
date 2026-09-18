"""Everything that happens to an installation rather than to a pull request.

WHAT: `installation_event.settle` answers a delivery and then does the slow half;
      `installed_repos` writes what an account covers; `onboarding.admit` clones and indexes;
      `withdrawal.withdraw` takes coverage away; `reconcile` asks the forge what is still true.
WHY:  **`serve/` REACHED THE FIFTEEN-FILE FANOUT CAP WHEN THE UNINSTALL PATH MET THE STRIPE WORK
      ON MAIN.** AGENTS.md rule 4: introduce a sub-package, do not raise the cap. The concern that
      split out is the one with its own lifetime — an installation is created, changed and removed
      on the forge's schedule, while everything left in `serve/` happens because a pull request
      moved.

      **THEY ARE READ TOGETHER AND ALMOST NOWHERE ELSE.** `settle` calls `provisioned`, `admit`
      and `withdraw` in one ordering that exists because the 2XX has to land between the fast half
      and the slow one; reading any of them alone hides that ordering.

      **THIS IS WHERE A SECOND FORGE LANDS.** Bitbucket installs, changes and uninstalls through a
      different set of events carrying the same four outcomes, and `types/forge/delivery.py`
      already names them. Putting the GitHub-shaped versions here first is what keeps that from
      becoming a second copy of `serve/`.
IMPORTS: nothing itself. The modules import store, ingest and types, never rightward.
CONSUMED BY: `serve/listener.py`, `serve/commands/`, `serve/web/scan_route.py`.
"""
