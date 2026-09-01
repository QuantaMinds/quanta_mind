"""The audit trail as a file somebody can hand to an auditor.

WHAT: `document(rows, window, repo)` returns the export as JSON text: what the trail covers, what
      it does NOT cover, and one object per recorded check.
WHY:  **D4b CLAIMED "EXPORTABLE" FOR A FORTNIGHT WITH NO EXPORT.** `quantamind compliance` printed
      a summary; nothing could produce the trail itself. `docs/product/unit-economics.md` had
      already written the gap down — *"A compliance buyer asks for the artefact, not the query"* —
      and the row stayed ticked anyway. Same shape as D1g's title this morning: a tick that is
      right about the work and wrong in the word somebody reads.

      **JSON, NOT CSV, AND THE REASON IS THE CAVEATS.** A CSV is easier to open and cannot carry
      the three sentences that make this document honest: nothing is backfilled, an absent row
      means the check did not run, and `DEFERRED` is not a pass. Those belong IN the artefact, not
      in an email beside it — an export that outlives its covering note is exactly how a partial
      record becomes a claim of full coverage.

      **`limits` COMES FIRST IN THE DOCUMENT.** A reader who stops after the first object has read
      the part that stops them over-reading the rest. Same choice `render/blocks/compliance_table`
      made when it put the caveat above the table rather than under it.

      **THE WINDOW IS THE DATA'S, NOT THE REPOSITORY'S.** The trail begins when the rule engine was
      installed. An export implying it covers the repository's whole life would be the most
      dangerous document this product can produce.
IMPORTS: store.audit.export. Leftward, value objects only.
CONSUMED BY: `serve/commands/run_report.py`, behind `quantamind compliance --export`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from quantamind.store.audit.export import Recorded, Window

NOT_BACKFILLED = (
    "Nothing here is backfilled. The trail begins when rule checking was installed on this "
    "repository, not when the repository did, and a commit from before that has no rows."
)
ABSENT = (
    "An absent row means the check did not run — never that it passed. A file, a rule or a "
    "commit missing from this document was not evaluated."
)
UNDECIDED = (
    "`uncheckable` and `deferred` are not passes. A rate computed over these rows must use "
    "`passed + violated` as its denominator, which is what `quantamind compliance` does."
)
REPRODUCIBLE = (
    "A row whose provenance is `parser` can be re-run against its `head_sha` and must give the "
    "same answer. A row whose provenance is `model` cannot, and is not evidence of the same kind."
)


def _stamp(seconds: int | None) -> str | None:
    return datetime.fromtimestamp(seconds, UTC).isoformat() if seconds is not None else None


def document(rows: Sequence[Recorded], window: Window, repo: str) -> str:
    """The whole export, as JSON text. **Empty is a document, not an error.**

    A repository with no recorded checks still produces a file, and that file says it covers
    nothing. Returning an error instead would leave the caller with nothing to hand over and no
    statement of why — and "we have checked nothing here" is a true, useful and auditable answer.
    """
    payload = {
        "repository": repo,
        "limits": {
            "covers": {
                "from": _stamp(window.first),
                "to": _stamp(window.last),
                "reviews": window.reviews,
                "checks": len(rows),
            },
            "not_backfilled": NOT_BACKFILLED,
            "absent_means_unchecked": ABSENT,
            "undecided_is_not_a_pass": UNDECIDED,
            "reproducibility": REPRODUCIBLE,
        },
        "checks": [
            {
                "pull_request": row.pr_number,
                "commit": row.head_sha,
                "decided_at": _stamp(row.decided_at),
                "rule": row.rule_id,
                "path": row.path,
                "line": row.line or None,
                "outcome": row.outcome,
                "provenance": row.provenance,
                "evidence": row.evidence or None,
                "undecided_because": row.reason or None,
            }
            for row in rows
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"
