"""One standard a repository holds itself to, and whether a parser or a model decides it.

WHAT: `Rule`, `Severity` and `CheckKind`. A rule is data — it is declared in the customer's
      repository, not compiled into this product — and it carries the provenance of its own
      verdict so an auditor can tell a reproducible check from a judgement.
WHY:  **DOCUMENTATION IS WHAT THIS REPLACES.** A standard written in a wiki is remembered by
      whoever happens to review, applied differently by each of them, and unenforceable at any
      size. A rule declared in the repository is versioned with the code it governs, reviewed the
      way that code is reviewed, and diffable when it changes.

      **PROVENANCE IS DERIVED FROM THE CHECK, NEVER SET BY A CALLER.** `CheckKind.MODEL_JUDGED`
      yields `Provenance.MODEL` and everything else yields `Provenance.PARSER`, because the
      distinction is the whole value of the audit trail: a parser's verdict can be re-run on the
      same commit and shown to produce the same answer, and a model's cannot. A rule that could
      declare itself parser-verified while a model decided it would make the trail worthless, so
      the field does not exist to be set.

      **A RULE WITHOUT A DESCRIPTION IS REFUSED.** The description is what a developer reads next
      to a violation on their pull request. `no-console-log-in-prod` is a slug, not a reason, and
      a check nobody can act on is noise wearing a standard's clothes.

      **`CheckKind` IS CLOSED.** Adding a member forces every match over it to be revisited, which
      is the point: a new kind of check arriving as a free-text string is how "we support any
      rule" becomes "we silently ignore the ones we do not understand".
IMPORTS: stdlib plus `types.verdict` for `Provenance`. Nothing to its right.
CONSUMED BY: `ingest/rules_file.py`, and the checks that will read these (D1b).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from quantamind.types.verdict import Provenance

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class Severity(Enum):
    """How much a violation matters. Three values, chosen by the customer, never by us."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CheckKind(Enum):
    """What decides whether the rule is met. Closed on purpose -- see the module docstring."""

    FORBID_CALL = "forbid_call"
    FORBID_IMPORT = "forbid_import"
    NAMING_PATTERN = "naming_pattern"
    HARDCODED_SECRET = "hardcoded_secret"
    """**THE FIRST KIND THAT NEEDS NO TARGET AND NO PARSER.** The other three ask "is this
    identifier here"; this one asks "does any line look like an issued credential", which is a
    question about text rather than syntax. It is also the first that is not Python-only —
    a credential is a string in a `.env`, a `.tf` or a notebook exactly as much as in a module."""

    MODEL_JUDGED = "model_judged"


class RuleRefused(ValueError):
    """A declaration that cannot become a rule. Carries the id, so the customer can find it."""

    def __init__(self, rule_id: str, reason: str) -> None:
        super().__init__(f"rule {rule_id!r}: {reason}")
        self.rule_id, self.reason = rule_id, reason


@dataclass(frozen=True, slots=True)
class Rule:
    """One declared standard. Constructed only when every field it needs is present."""

    id: str
    description: str
    severity: Severity
    check: CheckKind
    target: str = ""
    """What the check looks for -- a call, an import, a pattern. Empty only for MODEL_JUDGED."""

    paths: tuple[str, ...] = ()
    """Path prefixes this rule governs. Empty means every file.

    **A RULE WITHOUT A SCOPE IS A RULE IN THE WRONG PLACE.** "No pandas in the product" is true of
    `src/` and false of `research/`, which is a separate uv project that MAY use it — and a rule
    that cannot say so fires on the code it was never meant to govern. That was found by running
    these rules over this repository before declaring them: the pandas rule flagged a research
    test, correctly by its own terms and wrongly by the standard it came from.
    """

    def __post_init__(self) -> None:
        if not SLUG.match(self.id):
            raise RuleRefused(self.id, "id must be a lowercase slug, so it can key an audit row")
        if not self.description.strip():
            raise RuleRefused(
                self.id,
                "a rule with no description cannot be acted on by the developer who sees it",
            )
        if self.check in (CheckKind.MODEL_JUDGED, CheckKind.HARDCODED_SECRET):
            return
        if not self.target.strip():
            raise RuleRefused(
                self.id, f"{self.check.value} needs a target; there is nothing to look for"
            )

    def applies_to(self, path: str) -> bool:
        """Whether this rule governs `path`. An unscoped rule governs everything.

        **A FILE OUTSIDE THE SCOPE PRODUCES NO ROW AT ALL**, which is not the same as a skip: there
        is no question to answer, the way a deleted file has no code to check. What must never
        happen is a PASSED row for a rule that was never meant to apply, because that inflates the
        denominator of a compliance rate with pairs nobody agreed to.
        """
        return not self.paths or any(path.startswith(prefix) for prefix in self.paths)

    @property
    def provenance(self) -> Provenance:
        """**DERIVED, NEVER DECLARED.** A model-judged rule cannot claim a parser verified it."""
        return Provenance.MODEL if self.check is CheckKind.MODEL_JUDGED else Provenance.PARSER

    @property
    def reproducible(self) -> bool:
        """Whether re-running this check on the same commit must give the same answer.

        The audit trail is worth what this is worth. It is a property of the CHECK, not of how
        carefully the run was done, which is why it reads off `provenance` rather than a flag.
        """
        return self.provenance is Provenance.PARSER
