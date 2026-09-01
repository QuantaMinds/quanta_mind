"""D1c: reading a model's reply, where every shape we did not ask for is `UNDECIDED`.

WHAT: `serve/rule_judge.py:parse_reply` against the replies a model actually produces, and
      `judge_with` against settings with inference off.
WHY:  **THIS FILE EXISTS BECAUSE A SABOTAGE DISABLED THE MECHANISM WITH NOTHING FAILING.** Changing
      "a reply we did not understand" from `UNDECIDED` to `MET` left the whole suite green: the
      parser had no tests at all, so the strictness the module docstring claims was unenforced. A
      model asked for one of three words will sometimes write a paragraph, and reading a paragraph
      as `MET` is how a declared standard silently stops being checked.
IMPORTS: serve.rule_judge, types.settings, types.standards.{judged,rule}, verify.judged_rule.
"""

from __future__ import annotations

from unittest import mock

import pytest

from quantamind.serve import rule_judge
from quantamind.serve.rule_judge import judge_with, parse_reply
from quantamind.types.settings import Settings
from quantamind.types.standards.judged import Verdict
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.verify.judged_rule import judge_all


@pytest.mark.parametrize(
    "reply",
    [
        "",
        "   \n  \n",
        "I think this file is fine, honestly.",
        "The standard appears to be met here.",  # says "met" but does not BEGIN with the token
        '```json\n{"verdict": "met"}\n```',
        "Sure! Here is my assessment:\nMET",  # the token is present, just not first
    ],
    ids=["empty", "blank", "prose", "prose-containing-met", "json", "token-not-first"],
)
def test_any_reply_we_did_not_ask_for_is_undecided(reply: str) -> None:
    """**NOT ONE OF THESE MAY READ AS COMPLIANCE.**"""
    verdict, quote, _ = parse_reply(reply)
    assert verdict is Verdict.UNDECIDED
    assert quote == ""


def test_a_clean_met_is_read_as_met() -> None:
    """The check has to admit the true positive too, or it is not a check."""
    verdict, quote, why = parse_reply("MET\nEvery public function says why it exists.")
    assert verdict is Verdict.MET
    assert quote == ""
    assert "why it exists" in why


def test_broken_carries_the_quote_from_the_second_line() -> None:
    """The quote is the second line exactly; the explanation is whatever follows."""
    verdict, quote, why = parse_reply("BROKEN\ndef deceptive(rows):\nIt says what, not why.")
    assert verdict is Verdict.BROKEN
    assert quote == "def deceptive(rows):"
    assert why == "It says what, not why."


def test_broken_with_no_second_line_yields_an_empty_quote() -> None:
    """**An unusable BROKEN is caught downstream, not smuggled through as a violation.**

    `verify/judged_rule.judge` turns an unanchorable quote into `UNDECIDED`; this only has to
    report honestly that there was no quote rather than invent one.
    """
    verdict, quote, _ = parse_reply("BROKEN")
    assert verdict is Verdict.BROKEN
    assert quote == ""


def test_decoration_around_the_token_is_tolerated() -> None:
    """A model that bolds its answer has still answered. Formatting is not a refusal."""
    assert parse_reply("**BROKEN**\ndef deceptive(rows):")[0] is Verdict.BROKEN
    assert parse_reply("`met`\nfine")[0] is Verdict.MET


PROSE = Rule(
    "explain-why",
    "Every public function explains why it exists.",
    Severity.MEDIUM,
    CheckKind.MODEL_JUDGED,
)


def test_no_judge_when_inference_is_off_and_nothing_is_judged() -> None:
    """**The model is opt-in and its absence is not an error.**

    Asserted through the consequence rather than through `is None`: with inference off, a
    model-judged rule against a real file must produce no records at all.
    """
    off = judge_with(Settings(inference_enabled=False, inference_project="p"))
    no_project = judge_with(Settings(inference_enabled=True, inference_project=""))

    assert judge_all([PROSE], "a.py", "def f():\n    return 1\n", off) == ()
    assert judge_all([PROSE], "a.py", "def f():\n    return 1\n", no_project) == ()


def test_a_configured_judge_is_actually_called() -> None:
    """The negative above means nothing unless the positive path reaches the transport.

    The transport itself is replaced — this asserts that `judge_with` returns something
    `judge_all` will call, and that its parsed answer arrives as the record's verdict.
    """
    settings = Settings(inference_enabled=True, inference_project="p")
    asked: list[str] = []

    def transport(prompt: str, **kwargs: object) -> str:
        asked.append(prompt)
        return "MET\nIt explains why."

    with mock.patch.object(rule_judge, "_ask", transport):
        records = judge_all([PROSE], "a.py", "def f():\n    return 1\n", judge_with(settings))

    assert len(asked) == 1
    assert "Every public function explains why it exists." in asked[0], "the rule's own words"
    assert [record.verdict for record in records] == [Verdict.MET]
