"""`GET /scan?repo=owner/name` -- what the first history walk found for one repository.

WHAT: `answer(root, login, query)` returns the JSON body and status for the scan endpoint, as a
      `(status, body)` pair. `routes.get` wraps it in a `Reply`.
WHY:  **IT REPORTS A SCAN; IT DOES NOT PERFORM ONE.** `serve/onboarding.warm` already walks history
      at install time. A clone over HTTP would take far longer than any client will wait, and would
      hand anyone who can reach the port a way to make this process clone arbitrary repositories.

      **NOTHING HERE MAY WRITE, AND THE OBVIOUS SPELLING DOES.** `store.schema.open_store` CREATES a
      missing database and `store.touches.ensure_repo` INSERTS a missing row, so a GET written the
      short way would provision a store file and a repository row for any installed repository
      anybody asked about -- and `tenancy.tenants()`, which globs `<root>/<owner>/*.db`, would then
      count a tenant that had never been warmed. The file is checked before it is opened and
      `repo_id()` is the lookup that does not register. **`serve/web/routes.py` already refuses
      exactly this for the accounts store; this is the same refusal for a tenant's.**

      **A REPOSITORY THIS ACCOUNT DID NOT INSTALL ANSWERS AS ONE THAT DOES NOT EXIST**, the same way
      `pages.repository` does. A 404 and a 403 together enumerate other tenants.

      **AN INDEX THAT IS NOT BUILT YET IS A NAMED STATE, NOT AN EMPTY TABLE.** A repository
      installed a minute ago and one whose warm-up failed both hold zero touches; `scanned: false`
      is what stops the second reading as the first.

      **IT LIVES HERE RATHER THAN IN `routes.py` BECAUSE THAT MODULE DISPATCHES.** Inlined, it took
      `routes.py` past the 200-line cap, which was the structure guard saying what "one public
      concern per module" says in prose.
IMPORTS: render.scan_report, serve.web.pages, store.{schema,tenancy,touches}. Leftward and sideways
      into `pages`, which is this package's own account-scoped reader.
CONSUMED BY: `serve/web/routes.py`.
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

from quantamind.render.scan_report import as_of, report
from quantamind.serve.web import pages
from quantamind.store import tenancy
from quantamind.store.schema import open_store
from quantamind.store.touches import Hotspots, hotspots, repo_id

NOT_INDEXED = Hotspots(files=(), tracked=0, touches=0, first=0, last=0)

LIMITS = (
    "A count of commits, not a judgement about the code. No model ran. "
    "`scanned: false` means the index is not built yet, which is not the same "
    "as a repository with no history."
)


def answer(root: Path, login: str, query: str) -> tuple[int, str]:
    """The status and JSON body for one scan request. **Opens nothing it does not have to.**"""
    asked = (urllib.parse.parse_qs(query).get("repo") or [""])[0]
    if asked not in pages.mine(root, login):
        return 404, json.dumps({"error": "no such repository"})

    owner, _, short = asked.partition("/")
    store = tenancy.store_for(root, owner, short)
    spots = NOT_INDEXED
    if store.exists():
        conn = open_store(store)
        try:
            found = repo_id(conn, "github.com", asked)
            if found is not None:
                spots = hotspots(conn, found)
        finally:
            conn.close()

    return 200, json.dumps(
        {
            "repo": asked,
            "scanned": bool(spots.touches),
            "touches": spots.touches,
            "files_tracked": spots.tracked,
            "newest_commit_read": as_of(spots),
            "most_touched": [{"path": path, "touches": n} for path, n in spots.files],
            "report": report(asked, spots),
            "limits": LIMITS,
        }
    )
