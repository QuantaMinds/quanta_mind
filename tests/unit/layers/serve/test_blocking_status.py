"""The join: that a model verdict cannot reach the wire, and that rehearsal writes nothing.

WHAT: Drives `serve/blocking_status.announce` with the GitHub writer replaced by a spy, and asserts
      what was posted -- including the two cases where the right answer is NOTHING.
WHY:  **THE TWO SILENCES ARE THE POINT AND THEY ARE DIFFERENT SILENCES.** A change no rule governed
      must post nothing, because a green tick against a standard nobody wrote is a claim we cannot
      support. A rehearsal must post nothing while still deciding, because what the status WOULD
      have said is the thing an operator runs a rehearsal to find out. A test asserting only "no
      exception" would pass against a function that posted in both cases.
IMPORTS: pytest, quantamind.serve.blocking_status, quantamind.types.{checked,rule,verdict},
      quantamind.verify.{blocking,rule_check}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.serve import blocking_status
from quantamind.types.checked import Checked, Outcome
from quantamind.types.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Site
from quantamind.verify import rule_check
from quantamind.verify.blocking import Standing

HEAD = "c" * 40
SOURCE = "import pickle\n\n\ndef go():\n    return pickle.loads(b'')\n"


class _Spy:
    def __init__(self) -> None:
        self.posted: list[tuple[str, str, str, str]] = []

    def __call__(self, repo: str, head_sha: str, state: str, description: str) -> bool:
        self.posted.append((repo, head_sha, state, description))
        return True


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> _Spy:
    made = _Spy()
    monkeypatch.setattr(blocking_status.commit_status, "post", made)
    return made


def _violation() -> Checked:
    return Checked("no-pickle", Site("app/loader.py", 5), Outcome.VIOLATED, evidence="pickle.loads")


def test_a_parser_violation_posts_a_failing_status(spy: _Spy) -> None:
    standing = blocking_status.announce("acme/widgets", HEAD, [_violation()], enabled=True)

    assert standing is Standing.BLOCKED
    repo, head, state, _description = spy.posted[0]
    assert (repo, head, state) == ("acme/widgets", HEAD, "failure")


def test_a_model_judged_rule_never_reaches_the_wire_as_a_failure(spy: _Spy) -> None:
    """Driven through the real checker: the same target that violates as a parser rule."""
    model_rule = Rule("no-pickle", "no pickle", Severity.HIGH, CheckKind.MODEL_JUDGED, "pickle")
    row = rule_check.check(model_rule, "app/loader.py", SOURCE)
    assert row.outcome is Outcome.DEFERRED, "the fixture stopped exercising the model path"

    standing = blocking_status.announce("acme/widgets", HEAD, [row], enabled=True)

    assert standing is Standing.CLEAR
    assert [state for _r, _h, state, _d in spy.posted] == ["success"], (
        "a model verdict changed what a commit status said about a merge"
    )


def test_a_change_no_rule_governed_posts_nothing_at_all(spy: _Spy) -> None:
    standing = blocking_status.announce("acme/widgets", HEAD, [], enabled=True)

    assert standing is Standing.NOT_DECLARED
    assert spy.posted == [], "a green tick was posted against a standard nobody wrote"


def test_a_rehearsal_decides_the_gate_and_writes_nothing(
    spy: _Spy, capsys: pytest.CaptureFixture[str]
) -> None:
    standing = blocking_status.announce("acme/widgets", HEAD, [_violation()], enabled=False)

    assert standing is Standing.BLOCKED, "rehearsal must still decide, or it rehearses nothing"
    assert spy.posted == [], "POSTING_ENABLED=0 wrote to a customer's repository"
    assert "rehearsed failure" in capsys.readouterr().out
