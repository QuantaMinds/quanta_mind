"""What the review found, with a parser's verdicts kept apart from a model's.

WHAT: `found(checks, findings)` renders the defects section: rule violations first, model findings
      second, each labelled by what produced it. Empty string when there is nothing to report.
WHY:  **A REVIEWER MUST BE ABLE TO TELL WHICH HALF THEY ARE TRUSTING.** A rule violation is a fact
      about the syntax tree: the call is there or it is not, and anyone can re-run the check on the
      same commit and get the same answer. A model finding is a reading, and four blind pools put
      raw ones 66.7-82.1% wrong. Printing them in one undifferentiated list would average the
      credibility of both down to the weaker, and it is the parser half that makes an audit trail
      worth keeping.

      **"NOTHING FOUND" IS PRINTED ONLY FOR THE HALF THAT LOOKED.** A repository declaring no rules
      gets no rule section at all, because "no violations" would imply rules existed to violate.
      Silence about a check that never ran is the failure this product exists to refuse, and it is
      cheapest to make impossible here, in the renderer.
IMPORTS: types.{checked,finding}. Nothing to its right.
CONSUMED BY: `render/comment.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.checked import Checked, Outcome
from quantamind.types.finding import Finding

PARSER = "**Found by a parser** — re-runnable on this commit, so these are facts"
MODEL = "**Found by the model** — a reading, not a fact; check before acting"


def _where(path: str, line: int) -> str:
    return f"`{path}:{line}`" if line else f"`{path}`"


def found(checks: Sequence[Checked] = (), findings: Sequence[Finding] = ()) -> str:
    """The defects section, or empty when neither half has anything to say."""
    violations = [c for c in checks if c.outcome is Outcome.VIOLATED]
    if not violations and not findings:
        return ""

    lines: list[str] = []
    if violations:
        lines += ["", PARSER, ""]
        lines += [
            f"- {_where(v.site.path, v.site.line)} — `{v.rule_id}`: {v.evidence}"
            for v in violations
        ]
    if findings:
        lines += ["", MODEL, ""]
        lines += [f"- {_where(f.path, f.line)} — {f.claim}" for f in findings]
    return "\n".join(lines)
