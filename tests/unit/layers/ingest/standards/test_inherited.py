"""D1e: what a repository may do to a standard its organisation defined once.

WHAT: `ingest/standards/inherited.combine` over organisation rules and a repository's own.
WHY:  **"A STANDARD THAT CAN BE DISABLED INVISIBLY IS NOT A STANDARD"** — the row's own sentence,
      and the reason every test here checks what was RECORDED and not only what was enforced. A
      merge that produced the right effective rules while losing the record of a drop would pass a
      naive test and defeat the row.

      **THE ASYMMETRY IS THE DESIGN.** Tightening needs no permission and is recorded. Loosening
      while still claiming to inherit is refused and the strict value stands. Dropping outright is
      allowed, must be explicit, and is recorded. Each is a separate test because each is a
      separate decision somebody could reverse.
IMPORTS: quantamind.ingest.standards.inherited, quantamind.types.standards.rule.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

from quantamind.ingest.standards.inherited import STRICTNESS, Inheritance, combine
from quantamind.types.standards.rule import CheckKind, Rule, Severity


def _rule(rule_id: str, severity: Severity, target: str = "print") -> Rule:
    return Rule(rule_id, f"Standard {rule_id}.", severity, CheckKind.FORBID_CALL, target)


ORG = [_rule("no-print", Severity.MEDIUM), _rule("no-eval", Severity.HIGH, "eval")]


def test_a_repository_declaring_nothing_inherits_everything() -> None:
    """The enterprise claim: define once, checked everywhere, with no local file at all."""
    merged = combine(ORG, [])

    assert {r.id for r in merged.rules} == {"no-print", "no-eval"}
    assert merged.inherited_ids == frozenset({"no-print", "no-eval"})
    assert merged.changed() is False


def test_a_repository_may_add_its_own_without_touching_what_it_inherits() -> None:
    """Extending is the common case and must not read as a change to the inheritance."""
    merged = combine(ORG, [_rule("no-shell", Severity.LOW, "os.system")])

    assert {r.id for r in merged.rules} == {"no-print", "no-eval", "no-shell"}
    assert "no-shell" not in merged.inherited_ids
    assert merged.changed() is False


def test_tightening_is_allowed_and_recorded() -> None:
    """A team holding itself to more than the organisation asks needs no permission."""
    merged = combine(ORG, [_rule("no-print", Severity.HIGH)])

    effective = {r.id: r.severity for r in merged.rules}
    assert effective["no-print"] is Severity.HIGH
    assert len(merged.tightened) == 1
    assert merged.tightened[0].organisation is Severity.MEDIUM
    assert merged.tightened[0].repository is Severity.HIGH
    assert merged.dropped == ()


def test_loosening_is_refused_and_the_organisations_severity_stands() -> None:
    """**A RENAME-AND-LOWER MUST NOT QUIETLY WEAKEN EVERY REPOSITORY.**

    The repository still gets the rule, at the organisation's severity, and is told why.
    """
    merged = combine(ORG, [_rule("no-eval", Severity.LOW, "eval")])

    effective = {r.id: r.severity for r in merged.rules}
    assert effective["no-eval"] is Severity.HIGH, "the looser local severity was applied"
    assert len(merged.refused) == 1
    assert "stricter one applies" in merged.refused[0].reason
    assert "inherit = false" in merged.refused[0].reason, "must say how to opt out properly"


def test_an_explicit_drop_removes_the_rule_AND_leaves_a_record() -> None:
    """**THE ROW'S CENTRAL REQUIREMENT.** Allowed, explicit, and never silent."""
    merged = combine(ORG, [], own_raw=[{"id": "no-eval", "inherit": False}])

    assert {r.id for r in merged.rules} == {"no-print"}, "the dropped rule is not enforced"
    assert len(merged.dropped) == 1, "a rule vanished with no record of it"
    assert merged.dropped[0].rule_id == "no-eval"
    assert merged.dropped[0].organisation is Severity.HIGH, "the record keeps what was given up"
    assert merged.changed() is True


def test_a_drop_renders_a_sentence_naming_the_rule_and_the_mechanism() -> None:
    """The audit trail carries text a person reads, not an enum they have to look up."""
    merged = combine(ORG, [], own_raw=[{"id": "no-eval", "inherit": False}])
    rendered = merged.dropped[0].render()

    assert "no-eval" in rendered
    assert "high" in rendered
    assert "inherit = false" in rendered


def test_an_unreadable_organisation_file_inherits_nothing_and_says_so() -> None:
    """**NOT THE SAME AS AN ORGANISATION THAT DECLARES NOTHING.**

    A merge treating an unreachable file as an empty one would report a repository as fully
    compliant at the moment its inherited standards stopped arriving.
    """
    merged = combine(ORG, [_rule("no-shell", Severity.LOW, "os.system")], org_read=False)

    assert {r.id for r in merged.rules} == {"no-shell"}
    assert merged.org_read is False
    assert merged.inherited_ids == frozenset()


def test_an_organisation_declaring_nothing_is_a_readable_empty_inheritance() -> None:
    """The other half of the pair above: zero rules, read successfully."""
    merged = combine([], [_rule("no-shell", Severity.LOW, "os.system")])

    assert {r.id for r in merged.rules} == {"no-shell"}
    assert merged.org_read is True


def test_equal_severity_replaces_without_being_reported_as_a_change() -> None:
    """A repository may want its own target at the same severity. That is not a weakening."""
    local = Rule("no-print", "Ours.", Severity.MEDIUM, CheckKind.FORBID_CALL, "pprint")
    merged = combine(ORG, [local])

    effective = {r.id: r for r in merged.rules}
    assert effective["no-print"].target == "pprint"
    assert merged.changed() is False


def test_the_severity_order_is_the_one_the_merge_depends_on() -> None:
    """**A REVERSED ORDER WOULD TURN EVERY TIGHTENING INTO A REFUSAL AND VICE VERSA.**

    Nothing else in the codebase orders `Severity`, so nothing else would catch it.
    """
    assert STRICTNESS[Severity.HIGH] > STRICTNESS[Severity.MEDIUM] > STRICTNESS[Severity.LOW]


def test_an_empty_inheritance_reports_no_change() -> None:
    """The default must not claim anything happened."""
    assert Inheritance().changed() is False
