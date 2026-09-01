"""What a repository's declared rules actually did, counted with the denominator intact.

WHAT: `standing(conn, repo_id)` reads every `rule_check` row for one repository and returns a
      `Standing`: per-rule counts of all four outcomes, the files violations concentrate in, and
      `thin()` when there is not yet enough to read a proportion.
WHY:  **A COMPLIANCE VIEW THAT REPORTS ONLY PASS AND FAIL IS THE ARTEFACT THIS PRODUCT EXISTS TO
      REPLACE.** `UNCHECKABLE` and `DEFERRED` are counted and rendered beside the other two,
      because a rule nobody could evaluate is not a rule that passed. Folding them into the
      denominator would make "we checked and it was fine" and "we could not check" the same
      number on a buyer's screen, which is the collapse `AGENTS.md` rule 3 exists to prevent.

      **PER REPOSITORY, NEVER PER DEVELOPER.** The competitor screenshot ranks named engineers.
      That is a cultural decision wearing a feature's clothes, and `docs/plans/roadmap/
      product-build.md` declines it until somebody asks for it on purpose.

      **`MIN_FOR_A_RATE` IS IMPORTED, NOT REDECLARED.** "How many observations before a
      proportion means anything" is one decision, and the same number written in two modules is
      two numbers that must agree — the defect found in `rank/order`, `types/settings` and
      `types/ranking` all separately holding 0.9.
IMPORTS: stdlib, `store.lifecycle` for the shared rate floor, `types.checked` for the outcomes.
CONSUMED BY: `render/compliance_table.py`, via `serve/`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from quantamind.store.lifecycle import MIN_FOR_A_RATE
from quantamind.types.standards.checked import Outcome

HOTSPOTS = 5
"""Files named in the hotspot list. The remainder is stated as a count, never dropped."""


@dataclass(frozen=True, slots=True)
class RuleStanding:
    """One rule's record. All four outcomes, because the denominator is the product."""

    rule_id: str
    passed: int
    violated: int
    uncheckable: int
    deferred: int

    @property
    def seen(self) -> int:
        """Every time this rule was considered, whatever came of it."""
        return self.passed + self.violated + self.uncheckable + self.deferred

    @property
    def decided(self) -> int:
        """Times the rule could actually be evaluated. The honest denominator for a rate."""
        return self.passed + self.violated

    @property
    def violation_rate(self) -> float | None:
        """Violations over what was DECIDED, or None when nothing was. Never a silent zero."""
        return self.violated / self.decided if self.decided else None


@dataclass(frozen=True, slots=True)
class Standing:
    """A repository's compliance record, with its own limits attached."""

    rules: tuple[RuleStanding, ...]
    hotspots: tuple[tuple[str, int], ...]
    other_hotspots: int
    reviews: int

    def thin(self) -> str | None:
        """Why this cannot be read as a rate yet, or None when it can. Returned, not printed."""
        if self.reviews < MIN_FOR_A_RATE:
            return (
                f"{self.reviews} reviewed change(s) recorded; a rate needs at least "
                f"{MIN_FOR_A_RATE}. Counts below are real, proportions are not yet meaningful."
            )
        return None


def standing(conn: sqlite3.Connection, repo_id: int) -> Standing:
    """Every rule this repository declared, and what happened to it.

    **A REPOSITORY WITH NO CHECKS RETURNS AN EMPTY STANDING, NOT AN ERROR.** Nothing checked yet
    is a real state for a new installation, and it must stay distinguishable from a failed read.
    """
    rows = conn.execute(
        "SELECT rc.rule_id, rc.outcome, COUNT(*) FROM rule_check rc "
        "JOIN review r ON r.id = rc.review_id WHERE r.repo_id = ? "
        "GROUP BY rc.rule_id, rc.outcome",
        (repo_id,),
    ).fetchall()

    tally: dict[str, dict[str, int]] = {}
    for rule_id, outcome, count in rows:
        tally.setdefault(str(rule_id), {})[str(outcome)] = int(count)

    rules = tuple(
        RuleStanding(
            rule_id=rule_id,
            passed=counts.get(Outcome.PASSED.value, 0),
            violated=counts.get(Outcome.VIOLATED.value, 0),
            uncheckable=counts.get(Outcome.UNCHECKABLE.value, 0),
            deferred=counts.get(Outcome.DEFERRED.value, 0),
        )
        for rule_id, counts in sorted(tally.items())
    )

    hot = conn.execute(
        "SELECT rc.path, COUNT(*) AS n FROM rule_check rc "
        "JOIN review r ON r.id = rc.review_id "
        "WHERE r.repo_id = ? AND rc.outcome = ? GROUP BY rc.path ORDER BY n DESC, rc.path",
        (repo_id, Outcome.VIOLATED.value),
    ).fetchall()
    hotspots = tuple((str(path), int(n)) for path, n in hot[:HOTSPOTS])

    reviews = int(
        conn.execute("SELECT COUNT(*) FROM review WHERE repo_id = ?", (repo_id,)).fetchone()[0]
    )
    return Standing(rules, hotspots, max(0, len(hot) - HOTSPOTS), reviews)
