"""Only a parser's verdict may hold a merge, and this is where that is asserted rather than assumed.

WHAT: Drives `verify/blocking.decide` over real `Checked` rows and, for the invariant that matters
      most, over rows produced by `verify/rule_check.check` from real source rather than
      hand-built -- so the claim "a model-judged rule cannot violate" is tested against the code
      that would have to break it, not against a fixture restating it.
WHY:  **THIS GATE CAN STOP SOMEBODY'S MERGE.** Raw model findings measure 66.7 to 82.1% wrong, so
      a model verdict reaching `state="failure"` is the worst outcome this product has available.
      The protection is structural -- `check()` returns `DEFERRED` for `MODEL_JUDGED` before any
      path that can build a violation -- and a structural protection nobody tests is a comment.
IMPORTS: pytest, quantamind.types.{checked,rule,verdict}, quantamind.verify.{blocking,rule_check}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.checked import Checked, Outcome
from quantamind.types.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Reason, Site
from quantamind.verify import rule_check
from quantamind.verify.blocking import Gate, Standing, blocking, decide

SOURCE = "import pickle\n\n\ndef go():\n    return pickle.loads(b'')\n"


def _row(outcome: Outcome, rule_id: str = "no-pickle") -> Checked:
    if outcome is Outcome.VIOLATED:
        return Checked(rule_id, Site("a.py", 1), outcome, evidence="pickle.loads at line 5")
    if outcome is Outcome.UNCHECKABLE:
        return Checked(rule_id, Site("a.py"), outcome, why=Reason.UNPARSEABLE_SYNTAX)
    return Checked(rule_id, Site("a.py"), outcome)


def test_a_model_judged_rule_cannot_produce_a_row_that_blocks() -> None:
    """The invariant the whole gate rests on, driven through the real checker.

    The rule targets `pickle` and the source calls it, so a FORBID_IMPORT rule with this target
    violates. Declared as MODEL_JUDGED, the identical target against the identical source must
    reach `DEFERRED` and contribute nothing to `blocking()`.
    """
    parser_rule = Rule("no-pickle", "no pickle", Severity.HIGH, CheckKind.FORBID_IMPORT, "pickle")
    model_rule = Rule("no-pickle", "no pickle", Severity.HIGH, CheckKind.MODEL_JUDGED, "pickle")

    by_parser = rule_check.check(parser_rule, "a.py", SOURCE)
    by_model = rule_check.check(model_rule, "a.py", SOURCE)

    assert by_parser.outcome is Outcome.VIOLATED, (
        "the fixture must actually violate, or this test proves nothing about the model half"
    )
    assert by_model.outcome is Outcome.DEFERRED, f"a model rule reached {by_model.outcome}"
    assert blocking([by_model]) == (), "a model verdict reached the set that can block a merge"
    assert decide([by_model]).standing is Standing.CLEAR


def test_a_parser_violation_blocks_and_the_gate_names_it() -> None:
    gate = decide([_row(Outcome.VIOLATED), _row(Outcome.PASSED, "no-eval")])

    assert gate.standing is Standing.BLOCKED
    assert [row.rule_id for row in gate.violations] == ["no-pickle"]
    assert gate.passed == 1


def test_a_change_no_rule_governed_is_not_a_pass() -> None:
    """`NOT_DECLARED` exists so a green tick is never posted against a standard nobody wrote."""
    assert decide([]).standing is Standing.NOT_DECLARED


def test_what_could_not_be_checked_never_blocks_and_is_never_dropped() -> None:
    gate = decide([_row(Outcome.UNCHECKABLE), _row(Outcome.PASSED)])

    assert gate.standing is Standing.CLEAR, "a failure to decide is not a violation"
    assert gate.unchecked == 1, "the count a reader needs to judge the pass was dropped"
    assert gate.checked == 2, "the denominator must count every row a rule produced"


def test_a_deferred_row_is_counted_and_does_not_block() -> None:
    gate = decide([_row(Outcome.DEFERRED)])

    assert gate.standing is Standing.CLEAR
    assert gate.deferred == 1


def test_a_gate_cannot_claim_to_block_without_naming_what_blocked_it() -> None:
    with pytest.raises(ValueError, match="must name what blocked it"):
        Gate(Standing.BLOCKED, (), deferred=0, unchecked=0, passed=0)


def test_a_gate_cannot_hold_violations_and_report_itself_clear() -> None:
    with pytest.raises(ValueError, match="did not block"):
        Gate(Standing.CLEAR, (_row(Outcome.VIOLATED),), deferred=0, unchecked=0, passed=0)
