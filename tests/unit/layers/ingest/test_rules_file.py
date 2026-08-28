"""No rules and unreadable rules must never produce the same answer.

WHAT: Runs `ingest/rules_file.read()` over REAL files on disk — a missing one, a broken one, a
      good one, and one with declarations that cannot become rules.
WHY:  **THE FAILURE THIS GUARDS WOULD REPORT A CUSTOMER AS COMPLIANT AT THE MOMENT ENFORCEMENT
      STOPPED.** A repository with no rules has declared none. A repository whose file will not
      parse has declared some and we cannot read them. Both end with zero enforceable rules, and
      if they return the same value the compliance dashboard shows a clean sheet for a customer
      whose standards are silently off. The refusal list is what separates them.

      **AND A REJECTED DECLARATION IS RETURNED, NOT DROPPED.** Skipping the entries we do not
      understand narrows what a customer believes is enforced, invisibly, in exactly the artefact
      built to make it visible.
IMPORTS: ingest.rules_file, types.{rule,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.ingest.rules_file import RULES_PATH, read
from quantamind.types.rule import CheckKind, Rule, RuleRefused, Severity
from quantamind.types.verdict import Provenance, Reason

GOOD = """
[[rule]]
id = "no-console-log-in-prod"
description = "Logging to the console in production hides output from the log pipeline."
severity = "high"
check = "forbid_call"
target = "console.log"

[[rule]]
id = "async-error-handling"
description = "An awaited call without a handler fails silently."
severity = "high"
check = "model_judged"
"""


def _write(root: Path, text: str) -> Path:
    (root / RULES_PATH.parent).mkdir(parents=True, exist_ok=True)
    (root / RULES_PATH).write_text(text, encoding="utf-8")
    return root


def test_no_rules_file_is_not_the_same_answer_as_an_unreadable_one(tmp_path: Path) -> None:
    """**THE ONE THAT MATTERS.** Both give zero rules; only one is a customer in trouble."""
    absent_rules, absent_refusals = read(tmp_path)

    broken = _write(tmp_path / "broken", "[[rule]]\nid = 'unclosed")
    broken_rules, broken_refusals = read(broken)

    assert (absent_rules, absent_refusals) == ((), ()), "a repository with no rules declared none"
    assert broken_rules == (), "a file that will not parse must yield no enforceable rules"
    assert len(broken_refusals) == 1, (
        "an unreadable rules file produced no refusal, so it is indistinguishable from a "
        "repository that declared nothing — and the dashboard would call it compliant"
    )
    assert broken_refusals[0].reason is Reason.UNPARSEABLE_SYNTAX
    assert str(RULES_PATH) in broken_refusals[0].site.path


def test_a_declared_rule_is_read_with_the_severity_and_check_it_declared(tmp_path: Path) -> None:
    rules, refused = read(_write(tmp_path, GOOD))

    assert refused == (), f"a well-formed file produced refusals: {refused}"
    assert [r.id for r in rules] == ["no-console-log-in-prod", "async-error-handling"]
    assert rules[0].severity is Severity.HIGH
    assert rules[0].check is CheckKind.FORBID_CALL
    assert rules[0].target == "console.log"


def test_a_model_judged_rule_cannot_claim_a_parser_verified_it(tmp_path: Path) -> None:
    """The audit trail is worth exactly what this distinction is worth."""
    rules, _ = read(_write(tmp_path, GOOD))
    by_id = {r.id: r for r in rules}

    assert by_id["no-console-log-in-prod"].provenance is Provenance.PARSER
    assert by_id["no-console-log-in-prod"].reproducible is True
    assert by_id["async-error-handling"].provenance is Provenance.MODEL
    assert by_id["async-error-handling"].reproducible is False, (
        "a model-judged rule reported itself reproducible. Re-running it on the same commit "
        "need not give the same answer, and an audit row that claims otherwise is worthless"
    )


BAD = {
    "no description": 'id = "x"\nseverity = "high"\ncheck = "forbid_call"\ntarget = "y"',
    "unknown severity": 'id = "x"\ndescription = "d"\nseverity = "urgent"\n'
    'check = "forbid_call"\ntarget = "y"',
    "unknown check": 'id = "x"\ndescription = "d"\nseverity = "high"\n'
    'check = "vibes"\ntarget = "y"',
    "no target": 'id = "x"\ndescription = "d"\nseverity = "high"\ncheck = "forbid_call"',
}


@pytest.mark.parametrize("why", sorted(BAD))
def test_a_declaration_that_cannot_become_a_rule_comes_back_named(tmp_path: Path, why: str) -> None:
    rules, refused = read(_write(tmp_path / why.replace(" ", "-"), "[[rule]]\n" + BAD[why]))

    assert rules == (), f"{why}: enforced a rule we could not read"
    assert len(refused) == 1, f"{why}: the declaration was dropped silently instead of returned"
    assert refused[0].reason is Reason.MALFORMED_DECLARATION


def test_one_bad_declaration_does_not_take_the_good_ones_with_it(tmp_path: Path) -> None:
    rules, refused = read(_write(tmp_path, GOOD + '\n[[rule]]\nid = "broken"\n'))

    assert [r.id for r in rules] == ["no-console-log-in-prod", "async-error-handling"]
    assert len(refused) == 1 and refused[0].site.path == "broken"


def test_a_duplicate_id_is_refused_rather_than_last_one_winning(tmp_path: Path) -> None:
    """Audit rows key on the id; two rules sharing one makes the trail ambiguous."""
    rules, refused = read(_write(tmp_path, GOOD + GOOD))

    assert len(rules) == 2, f"a duplicate id was enforced twice: {[r.id for r in rules]}"
    assert len(refused) == 2


def test_a_rule_with_no_description_is_refused_at_construction() -> None:
    """The description is what the developer reads beside the violation. A slug is not a reason."""
    with pytest.raises(RuleRefused, match="cannot be acted on"):
        Rule(id="x", description="  ", severity=Severity.LOW, check=CheckKind.MODEL_JUDGED)
