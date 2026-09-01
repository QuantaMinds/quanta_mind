"""D1c: what a model is allowed to say about a prose rule, and what it may never say.

WHAT: `verify/judged_rule.py` in isolation — one rule, one file, an injected judge.
WHY:  **EVERY FAILURE PATH MUST LAND ON `UNDECIDED`.** A judge that raises, replies nothing, or
      quotes a line it invented must never read as "the standard is met". Each test names the
      guarantee it holds; `docs/plans/feat-d1c-model-checked-rules.md` lists what must break each
      one, and the sabotage run is recorded in the PR.
IMPORTS: types.standards.{checked,judged,rule}, types.verdict, verify.{judged_rule,rule_check}.
"""

from __future__ import annotations

import pytest

from quantamind.types.standards.checked import Outcome
from quantamind.types.standards.judged import MIN_QUOTE_CHARS, Judged, Verdict
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Provenance, Site
from quantamind.verify.judged_rule import anchored, judge, judge_all
from quantamind.verify.rule_check import check

PROSE = Rule(
    "explain-why",
    "Every public function explains WHY it exists, not only what it does.",
    Severity.MEDIUM,
    CheckKind.MODEL_JUDGED,
)

SOURCE = '''"""A module."""


def total(rows):
    return sum(rows)


def deceptive(rows):
    return len(rows)
'''


def _saying(verdict: Verdict, quote: str = "", why: str = "said so"):
    """A judge that always answers the same thing."""

    def ask(rule: Rule, path: str, source: str) -> tuple[Verdict, str, str]:
        return verdict, quote, why

    return ask


# --- the guarantee the whole row rests on -------------------------------------------------


def test_model_judged_rule_never_leaves_deferred() -> None:
    """**A model-judged rule produces `DEFERRED` and nothing else, forever.**

    This is what keeps a Gemini opinion out of `counts_toward_compliance`. If this ever returns
    PASSED or VIOLATED, the compliance rate silently starts including unreproducible verdicts.
    """
    row = check(PROSE, "src/app.py", SOURCE)
    assert row.outcome is Outcome.DEFERRED
    assert not row.counts_toward_compliance


def test_judged_is_not_a_checked_and_carries_model_provenance() -> None:
    """The two verdict types cannot be confused: different class, provenance fixed at MODEL."""
    record = judge(PROSE, "src/app.py", SOURCE, _saying(Verdict.MET))
    assert isinstance(record, Judged)
    assert record.provenance is Provenance.MODEL
    assert record.reproducible is False


# --- every failure path lands on UNDECIDED ------------------------------------------------


def test_transport_failure_is_undecided_not_met() -> None:
    """**A judge that raises must not read as compliance.**"""

    def ask(rule: Rule, path: str, source: str) -> tuple[Verdict, str, str]:
        raise RuntimeError("vertex refused")

    record = judge(PROSE, "src/app.py", SOURCE, ask)
    assert record.verdict is Verdict.UNDECIDED
    assert "vertex refused" in record.why


def test_broken_without_a_real_quote_is_undecided() -> None:
    """**A violation quoting text that is not in the file is not a violation.**

    This is the failure most likely to survive review: the sentence reads correctly either way.
    """
    record = judge(PROSE, "src/app.py", SOURCE, _saying(Verdict.BROKEN, "def invented(self):"))
    assert record.verdict is Verdict.UNDECIDED
    assert "not in the file" in record.why


def test_broken_with_a_real_quote_survives_and_carries_the_line() -> None:
    """A quote actually in the file anchors, and the record names where to look."""
    record = judge(PROSE, "src/app.py", SOURCE, _saying(Verdict.BROKEN, "def deceptive(rows):"))
    assert record.verdict is Verdict.BROKEN
    assert record.quote == "def deceptive(rows):"
    assert record.site.line == 8


def test_a_quote_too_short_to_locate_does_not_anchor() -> None:
    """Anchoring on three characters would match almost any file and prove nothing."""
    assert not anchored("def", SOURCE)
    assert anchored("def deceptive(rows):", SOURCE)


def test_broken_without_a_quote_is_refused_at_construction() -> None:
    """`Judged` refuses the unusable state itself, the way `Checked` refuses evidence-free."""
    with pytest.raises(ValueError, match=str(MIN_QUOTE_CHARS)):
        Judged("r", Site("a.py"), Verdict.BROKEN, quote="def")


# --- the model is opt-in -------------------------------------------------------------------


def test_no_judge_means_no_records_and_no_error() -> None:
    """**`ask=None` is the configured-off answer, not a failure.**"""
    assert judge_all([PROSE], "src/app.py", SOURCE, None) == ()


def test_only_model_judged_rules_are_put_to_the_model() -> None:
    """A parser rule must never reach the judge — deterministic beats clever."""
    parser_rule = Rule("no-print", "Use the logger.", Severity.LOW, CheckKind.FORBID_CALL, "print")
    asked: list[str] = []

    def ask(rule: Rule, path: str, source: str) -> tuple[Verdict, str, str]:
        asked.append(rule.id)
        return Verdict.MET, "", ""

    judge_all([parser_rule, PROSE], "src/app.py", SOURCE, ask)
    assert asked == ["explain-why"]
