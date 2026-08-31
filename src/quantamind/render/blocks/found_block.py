"""What the review found, with a parser's verdicts kept apart from a model's.

WHAT: `found(checks, findings)` renders the defects section: rule violations first, model findings
      second, each labelled by what produced it. Empty string when there is nothing to report.
WHY:  **THE PROVENANCE SPLIT MOVED TO THE AUDIT TRAIL, IT WAS NOT DROPPED.** This printed two
      headed sections — "found by a parser, these are facts" and "found by the model, a reading" —
      because a rule violation is re-runnable and a model finding is not. That distinction is real
      and still lives where it is used: `Rule.provenance`, `Checked`, and the rows a compliance
      reader queries. It left the COMMENT because a developer deciding whether to look at line 84
      does not act on which of our components produced the line, and a heading explaining our
      internals is the thing they scroll past.

      **RULE VIOLATIONS STILL COME FIRST**, without saying why: they are exact, so they are the
      ones worth reading first, and ordering carries that without a paragraph about it.

      **A REPOSITORY THAT DECLARED NO RULES STILL GETS NO RULE LINES.** "No violations" would imply
      rules existed to violate, and silence about a check that never ran is the failure this
      product refuses. The renderer is the cheapest place to make that impossible.
IMPORTS: types.{checked,finding}. Nothing to its right.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.checked import Checked, Outcome
from quantamind.types.finding import Finding

WORTH_CHECKING = "**Worth checking**"


def _where(path: str, line: int) -> str:
    return f"`{path}:{line}`" if line else f"`{path}`"


def found(checks: Sequence[Checked] = (), findings: Sequence[Finding] = ()) -> str:
    """The defects section, or empty when neither half has anything to say."""
    violations = [c for c in checks if c.outcome is Outcome.VIOLATED]
    if not violations and not findings:
        return ""

    lines: list[str] = ["", WORTH_CHECKING, ""]
    # Exact checks first: they are the ones that cannot be wrong, and the ordering says so
    # without a heading that explains our machinery to somebody who did not ask.
    lines += [
        f"- {_where(v.site.path, v.site.line)} — {v.rule_id.replace('-', ' ')}: {v.evidence}"
        for v in violations
    ]
    lines += [f"- {_where(f.path, f.line)} — {f.claim}" for f in findings]
    return "\n".join(lines)
