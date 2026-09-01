"""One standard defined once for an organisation, and what a repository may do to it.

WHAT: `combine(org, own)` merges an organisation's rules with a repository's own and returns
      `Inheritance` — the effective rules plus a typed record of every rule TIGHTENED, DROPPED or
      REFUSED. `ORG_REPO` names where the organisation's file lives.
WHY:  **D1e. "DEFINE A STANDARD ONCE AND IT IS CHECKED ON EVERY PULL REQUEST ACROSS ALL
      REPOSITORIES" IS THE ENTERPRISE CLAIM, AND A PER-REPOSITORY `rules.toml` DOES NOT MAKE IT.**
      Fifty repositories each holding their own copy is fifty copies to drift, and the drift is
      invisible until an auditor diffs them by hand.

      **A REPOSITORY MAY TIGHTEN AN INHERITED RULE AND MAY NOT SILENTLY DROP ONE.** Tightening is
      a team holding itself to more than the organisation asks, which needs no permission.
      Dropping is a team quietly exempting itself, and **a standard that can be disabled invisibly
      is not a standard** — so a drop is allowed, declared explicitly with `inherit = false`, and
      **recorded**. `Dropped` records reach the audit trail; a rule that vanished without one would
      be the failure this whole row exists to prevent.

      **LOOSENING WITHOUT SAYING SO IS REFUSED, NOT SILENTLY APPLIED.** A local rule that lowers an
      inherited severity while still claiming to inherit it is a contradiction, and the safe
      reading is the strict one: the organisation's severity stands and a `Refused` record says
      why. Taking the looser value would let a rename-and-lower quietly weaken every repository.

      **NOTHING IS INHERITED WHEN THE ORGANISATION FILE COULD NOT BE READ.** `Inheritance.org_read`
      is False then, and it is a different answer from an organisation that declares nothing —
      the same distinction `rules_file.py` draws for a single repository, one level up. A merge
      that treated an unreachable org file as an empty one would report a repository as fully
      compliant at the moment its inherited standards stopped arriving.
IMPORTS: types.standards.rule, types.verdict. Nothing to its right.
CONSUMED BY: `serve/standards_step.py`, which fetches both files and enforces the result.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from quantamind.types.standards.rule import Rule, Severity

ORG_REPO = ".quantamind"
"""The repository an organisation's rules live in: `<owner>/.quantamind`, holding `rules.toml`.

**THE SAME NAME GITHUB ALREADY USES FOR ORGANISATION DEFAULTS** (`.github`), so the convention is
one a team has met before, and it is a real repository with real permissions — an organisation's
standards are readable by whoever can read that repository, and changed through a pull request
against it like anything else."""

STRICTNESS = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}
"""Order on `Severity`. **Declared here rather than on the enum**: `types/` must not learn about
inheritance, and this is the only place the ordering means anything."""


@dataclass(frozen=True, slots=True)
class Tightened:
    """A repository holding itself to more than its organisation asks. **Allowed, and recorded.**"""

    rule_id: str
    organisation: Severity
    repository: Severity

    def render(self) -> str:
        return (
            f"`{self.rule_id}` — raised from {self.organisation.value} to "
            f"{self.repository.value} by this repository"
        )


@dataclass(frozen=True, slots=True)
class Dropped:
    """An inherited rule this repository declared it does not follow. **Never silent.**"""

    rule_id: str
    organisation: Severity

    def render(self) -> str:
        return (
            f"`{self.rule_id}` — inherited at {self.organisation.value}, "
            f"switched off by this repository with `inherit = false`"
        )


@dataclass(frozen=True, slots=True)
class Refused:
    """A local declaration that would have weakened an inherited rule. The strict value stands."""

    rule_id: str
    reason: str

    def render(self) -> str:
        return f"`{self.rule_id}` — {self.reason}"


@dataclass(frozen=True, slots=True)
class Inheritance:
    """What a repository is actually held to, and everything it changed on the way."""

    rules: tuple[Rule, ...] = ()
    tightened: tuple[Tightened, ...] = ()
    dropped: tuple[Dropped, ...] = ()
    refused: tuple[Refused, ...] = ()
    org_read: bool = True
    """False when the organisation's file could not be read. **Not the same as declaring none.**"""

    inherited_ids: frozenset[str] = field(default=frozenset())
    """Which effective rules came from the organisation. The audit trail names their origin."""

    def changed(self) -> bool:
        """Whether this repository altered its inheritance in any way worth reporting."""
        return bool(self.tightened or self.dropped or self.refused)


def _dropped_ids(own_raw: Sequence[dict[str, object]]) -> frozenset[str]:
    """Rule ids this repository declared it does not inherit.

    A `[[rule]]` entry carrying `inherit = false` is an opt-out, not a rule: it names an inherited
    id and switches it off. It is read from the raw entries because a `Rule` cannot represent
    "absent" — and should not learn how, since the concept exists only in a merge.
    """
    return frozenset(
        str(entry.get("id", ""))
        for entry in own_raw
        if entry.get("inherit") is False and entry.get("id")
    )


def combine(
    org: Sequence[Rule],
    own: Sequence[Rule],
    *,
    org_read: bool = True,
    own_raw: Sequence[dict[str, object]] = (),
) -> Inheritance:
    """The rules this repository is held to, and every change it made to what it inherited.

    **A LOCAL RULE OF THE SAME ID REPLACES THE INHERITED ONE ONLY WHEN IT IS AT LEAST AS STRICT.**
    Equal severity replaces silently — the repository may want a different target or scope. Higher
    severity replaces and is recorded as `Tightened`. Lower severity is refused, the organisation's
    rule stands, and a `Refused` says so.
    """
    if not org_read:
        # **NOTHING IS INHERITED FROM A FILE WE COULD NOT READ.** Reporting the repository's own
        # rules as the whole story would hide that its inherited standards did not arrive.
        return Inheritance(tuple(own), org_read=False)

    opted_out = _dropped_ids(own_raw)
    by_id = {rule.id: rule for rule in org}
    local = {rule.id: rule for rule in own}

    effective: list[Rule] = []
    inherited: set[str] = set()
    tightened: list[Tightened] = []
    dropped: list[Dropped] = []
    refused: list[Refused] = []

    for rule_id, org_rule in by_id.items():
        if rule_id in opted_out:
            dropped.append(Dropped(rule_id, org_rule.severity))
            continue
        mine = local.get(rule_id)
        if mine is None:
            effective.append(org_rule)
            inherited.add(rule_id)
            continue
        if STRICTNESS[mine.severity] > STRICTNESS[org_rule.severity]:
            tightened.append(Tightened(rule_id, org_rule.severity, mine.severity))
            effective.append(mine)
        elif STRICTNESS[mine.severity] < STRICTNESS[org_rule.severity]:
            refused.append(
                Refused(
                    rule_id,
                    f"this repository declares it {mine.severity.value} while the organisation "
                    f"declares it {org_rule.severity.value}; the stricter one applies. To stop "
                    f"following it, declare `inherit = false`, which is recorded.",
                )
            )
            effective.append(org_rule)
            inherited.add(rule_id)
        else:
            effective.append(mine)

    effective.extend(rule for rule_id, rule in local.items() if rule_id not in by_id)
    return Inheritance(
        tuple(effective),
        tuple(tightened),
        tuple(dropped),
        tuple(refused),
        org_read=True,
        inherited_ids=frozenset(inherited),
    )
