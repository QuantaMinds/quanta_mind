"""A GitHub check run carrying the violations at the exact line they occurred.

WHAT: `inline(checks, rules)` turns `Checked` rows into GitHub annotation objects, and
      `publish(repo, head_sha, checks, rules, enabled)` posts the check run. Returns what it did.
WHY:  **C2, AND IT IS NOT THE COMMIT STATUS D1f ALREADY BUILT.** `ingest/publish/commit_status.py`
      posts one line with one state and no location; this posts a check run whose annotations
      appear ON THE DIFF, at the file and line, in GitHub's own review interface. The row had no
      body for weeks precisely because nobody had said which of the two it meant, and ticking it on
      D1f's work would have counted one build twice.

      **ONLY A PARSER'S VERDICT IS ANNOTATED, NEVER A MODEL'S.** An annotation is rendered by GitHub
      as a fact against a line — there is no room for "we think" — and our raw model findings
      measure 66.7-82.1% wrong across four blind pools. A `Judged` record has no path here at all,
      and `Outcome.DEFERRED` produces nothing. **The one surface where being wrong is loudest gets
      the half of the product that is reproducible.**

      **AND ONLY VIOLATIONS.** `PASSED` is the common case; annotating it would put a marker on
      every checked line and train a reviewer to dismiss the column. `UNCHECKABLE` is a statement
      about our coverage, not about their code, and belongs in the comment's own honest count
      rather than on somebody's diff.

      **SEVERITY IS THE CUSTOMER'S, NOT OURS.** `Severity.HIGH` becomes `failure` and fails the
      check; `MEDIUM` and `LOW` become `warning` and `notice` and do not. A product that decided
      for itself which of a team's standards should block a merge would be overriding the judgement
      the standards file exists to record.

      **THE 50-ANNOTATION CAP IS ANNOUNCED, NEVER SILENT.** GitHub accepts fifty per request. A
      run with more says how many were not shown, in the summary, because a truncated list that
      does not say it truncated reads as a complete one — the failure `render/blocks/file_table.py`
      was built to prevent, arriving on a different surface.
IMPORTS: ingest.github_api, types.deployment, types.standards.{checked,rule}. Leftward only.
CONSUMED BY: `serve/review/standards_step.py`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from quantamind.ingest.github_api import ApiFailed, call
from quantamind.types.deployment import Destination, permit
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.rule import Rule, Severity

MAX_ANNOTATIONS = 50
"""GitHub's limit per request. Copied from their documentation, not chosen."""

LEVEL = {Severity.HIGH: "failure", Severity.MEDIUM: "warning", Severity.LOW: "notice"}
"""**THE CUSTOMER'S SEVERITY DECIDES, NOT US.** Only `failure` fails the check run."""

NAME = "QuantaMind standards"
"""What appears in the Checks tab. Names the half being reported — not the whole review."""


def inline(checks: Sequence[Checked], rules: Sequence[Rule]) -> tuple[list[dict[str, object]], int]:
    """(annotations, how many were dropped by the cap). **Violations only, parser only.**

    **NAMED `inline`, NOT `annotations`.** Every module here opens with
    `from __future__ import annotations`, so a function of that name shadows the import and mypy
    reports a redefinition — a collision with a line that appears in all 177 source files.

    A rule whose id is not in `rules` is skipped rather than annotated at a default severity:
    inventing a severity for a rule we cannot find would put a level on somebody's diff that
    nobody chose.
    """
    severities = {rule.id: rule.severity for rule in rules}
    found: list[dict[str, object]] = []
    for row in checks:
        if row.outcome is not Outcome.VIOLATED or row.rule_id not in severities:
            continue
        line = row.site.line or 1
        found.append(
            {
                "path": row.site.path,
                "start_line": line,
                "end_line": line,
                "annotation_level": LEVEL[severities[row.rule_id]],
                "title": row.rule_id,
                "message": row.evidence,
            }
        )
    return found[:MAX_ANNOTATIONS], max(0, len(found) - MAX_ANNOTATIONS)


def summary(shown: int, dropped: int, decided: int) -> str:
    """The check run's summary. **States the denominator and any truncation.**"""
    if not shown and not dropped:
        return (
            f"{decided} check(s) decided against the rules this repository declares. "
            f"No violations.\n\nOnly rules a parser decided appear here; nothing a model "
            f"judged is annotated on your diff."
        )
    tail = (
        f" **{dropped} more are not shown** — GitHub accepts {MAX_ANNOTATIONS} per run."
        if dropped
        else ""
    )
    return (
        f"{shown + dropped} violation(s) of the rules this repository declares, over "
        f"{decided} decided check(s).{tail}\n\nOnly rules a parser decided appear here; "
        f"nothing a model judged is annotated on your diff."
    )


def publish(
    repo: str,
    head_sha: str,
    checks: Sequence[Checked],
    rules: Sequence[Rule],
    *,
    enabled: bool,
) -> str:
    """Post the check run. Returns what happened, as a sentence the caller prints.

    **`enabled=False` REHEARSES AND SAYS SO**, the same contract `POSTING_ENABLED` has everywhere
    else in this product: nothing is written to somebody's repository by a run that was only meant
    to be looked at.
    """
    shown, dropped = inline(checks, rules)
    decided = sum(1 for row in checks if row.counts_toward_compliance)
    failing = any(a["annotation_level"] == "failure" for a in shown)

    if not enabled:
        return (
            f"check run rehearsed: {len(shown)} annotation(s), {dropped} over the cap, "
            f"conclusion would be {'failure' if failing else 'success'}"
        )

    permit(Destination.GITHUB_API)
    payload = {
        "name": NAME,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": "failure" if failing else "success",
        "output": {
            "title": f"{len(shown) + dropped} violation(s)"
            if shown or dropped
            else "No violations",
            "summary": summary(len(shown), dropped, decided),
            "annotations": shown,
        },
    }
    try:
        call(repo, f"repos/{repo}/check-runs", method="POST", body=json.dumps(payload))
    except ApiFailed as exc:
        # **A FAILED CHECK RUN DOES NOT TAKE THE REVIEW WITH IT.** The comment is already worth
        # posting, and a check run needs the `checks:write` permission that an older installation
        # may not have granted — which is a fact about their consent, not a fault in the review.
        return f"check run not posted: {exc}"
    return f"check run posted: {len(shown)} annotation(s), {dropped} over the cap"
