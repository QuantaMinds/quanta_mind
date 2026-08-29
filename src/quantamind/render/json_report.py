"""The review as data, for a coding agent that will act on it rather than read it.

WHAT: `report(...)` returns the review as a JSON string: the ranking, what was read and what was
      not, every finding with its line, every rule check with its outcome and provenance, and the
      verdicts if a model was consulted.
WHY:  **A HUMAN RE-TYPING PROSE IS NOT AN INTEGRATION.** `/qm-review` inside Cursor or Claude Code
      is worth something only if the agent can read the result and fix it. Markdown made for a
      person is a parsing problem for a tool, and a tool that half-parses it will act on half a
      review.

      **PROVENANCE STAYS HERE, THOUGH IT LEFT THE COMMENT.** A developer does not act on which of
      our components produced a line, so the posted comment dropped those headings. An agent
      SHOULD: a parser's verdict is reproducible and a model's is a reading with a measured error
      rate, and an agent deciding whether to apply a fix unattended needs to weigh them
      differently. Same facts, different reader.

      **`schema` IS A NUMBER SO A CONSUMER BREAKS LOUDLY.** A tool built against these keys will
      outlive this file. Without a version it would silently mis-read a renamed field and act on
      the wrong thing; with one it can refuse and say why.

      **`unread` IS ALWAYS PRESENT, EVEN WHEN EMPTY.** The residual is the product: an agent that
      cannot see which files went unreviewed will report a change as fully reviewed. An absent key
      and an empty list must not be the same answer, so the key is never omitted.

      **NULL MEANS UNDECIDED AND IS NEVER COLLAPSED TO FALSE.** `breaks: null` is "we could not
      tell"; `breaks: false` is "we checked the callers and it does not". An agent that read the
      first as the second would merge on a check that never ran.
IMPORTS: types.{checked,finding,ranking}. Nothing to its right, and nothing from `infer/`.
CONSUMED BY: `serve/run_commit.py`, behind `--json`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Protocol

from quantamind.types.checked import Checked
from quantamind.types.finding import Finding
from quantamind.types.ranking import Ranking
from quantamind.types.review import NotReviewed

SCHEMA = 1


class Verdicts(Protocol):
    """What `infer.change_summary.Summary` provides, without importing rightward into `infer/`."""

    @property
    def what_changed(self) -> str: ...
    @property
    def achieves_goal(self) -> bool | None: ...
    @property
    def reasoning(self) -> str: ...
    @property
    def impact(self) -> str: ...
    @property
    def breaks(self) -> bool | None: ...
    @property
    def breaks_why(self) -> str: ...
    @property
    def convention(self) -> str: ...
    @property
    def dependents(self) -> tuple[str, ...]: ...


def report(
    ranking: Ranking,
    *,
    summary: Verdicts | None = None,
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
    origin: str = "",
) -> str:
    """The whole review as one JSON object. Keys are stable within a `schema` number."""
    read = [unit.unit.site.path for unit in ranking.funded()]
    every = [unit.unit.site.path for unit in ranking.units]
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "origin": origin,
        # **ALWAYS PRESENT, `null` WHEN A RANKING RAN.** Same rule as `unread`: a key that is
        # sometimes absent makes "we ranked nothing" indistinguishable from an older writer.
        "not_reviewed_because": None,
        "files": {
            "changed": every,
            "reviewed": read,
            # **NEVER OMITTED.** An agent that cannot see this reports a partial review as whole.
            "unread": [path for path in every if path not in set(read)],
        },
        "history": {unit.unit.site.path: int(unit.score.value) for unit in ranking.units},
        "findings": [
            {"path": f.path, "line": f.line, "claim": f.claim, "provenance": f.provenance.value}
            for f in findings
        ],
        "rule_checks": [
            {
                "rule": c.rule_id,
                "path": c.site.path,
                "line": c.site.line,
                "outcome": c.outcome.value,
                "evidence": c.evidence,
                "undecided_because": c.why.value if c.why is not None else None,
                "counts_toward_compliance": c.counts_toward_compliance,
            }
            for c in checks
        ],
        # `null` throughout means "not consulted", which is not the same as a negative answer.
        "verdicts": None
        if summary is None
        else {
            "what_changed": summary.what_changed,
            "achieves_goal": summary.achieves_goal,
            "reasoning": summary.reasoning,
            "impact": summary.impact,
            "breaks": summary.breaks,
            "breaks_why": summary.breaks_why,
            "convention_broken": summary.convention or None,
            "dependents": list(summary.dependents),
        },
    }
    return json.dumps(body, indent=2, sort_keys=True)


def unreviewed(reason: NotReviewed, *, changed: Sequence[str] = (), origin: str = "") -> str:
    """The same object when there was no ranking to report, carrying WHY as a value.

    **THIS EXISTS BECAUSE THE ALTERNATIVE WAS A HUMAN SENTENCE AND EXIT 0.** Under `--json` the
    two early exits in `serve/run_commit.py` printed prose to stdout, so a tool got a decode
    error and a success code -- a change touching only Markdown looked exactly like a broken
    install. The keys are those of `report`, so one consumer parses both without branching.

    `files.changed` is passed in rather than derived: there is no ranking here, and reporting an
    empty changed-list when files did change would be a second lie in place of the first.
    """
    every = list(changed)
    return json.dumps(
        {
            "schema": SCHEMA,
            "origin": origin,
            "not_reviewed_because": reason.value,
            # Everything that changed went unread, by definition. `reviewed` is empty and
            # `unread` is the whole list -- the residual is still the product here.
            "files": {"changed": every, "reviewed": [], "unread": every},
            "history": {},
            "findings": [],
            "rule_checks": [],
            "verdicts": None,
        },
        indent=2,
        sort_keys=False,
    )
