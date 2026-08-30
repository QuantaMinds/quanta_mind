"""Unit tier: the command line reports honestly, including about itself.

WHAT: Asserts exit codes and output for the commands that exist and the ones that do not.
WHY:  A documented command with nothing behind it that exits 0 is the defect that made a
      runbook report five days of work it never did. So the unbuilt subcommands are asserted
      to exit NON-ZERO and to name the stage that will deliver them -- the failure has to be
      visible to a script, not just to a person reading the output.
IMPORTS: quantamind.serve.cli, quantamind.types.settings, pytest. Tier 1, no mocks.
CONSUMED BY: justfile (`just check`), .github/workflows/ci.yml.
"""

from __future__ import annotations

import pytest

from quantamind.render.config import render_config
from quantamind.serve.cli import UNBUILT, main
from quantamind.types.settings import Settings


def test_no_arguments_prints_help_and_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "quantamind" in capsys.readouterr().out


def test_config_prints_every_setting(capsys: pytest.CaptureFixture[str]) -> None:
    """A misconfiguration should be visible before a run, not diagnosed after one."""
    assert main(["config"]) == 0
    out = capsys.readouterr().out
    for field in Settings.__dataclass_fields__:
        assert field in out, f"`config` does not report {field}"


@pytest.mark.parametrize("command", sorted(UNBUILT))
def test_an_unbuilt_command_exits_non_zero(
    command: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exiting 0 having done nothing is how a runbook reports work it never performed.

    Asserted on the exit code rather than the message, because a script reads the code and a
    human reads the message, and only one of them is running in CI.
    """
    assert main([command]) == 2
    assert "not built yet" in capsys.readouterr().out


def test_the_unbuilt_message_names_a_stage_and_the_plan(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """ "Not implemented" sends a reader to the source. Naming the stage sends them to the plan.

    **This used to assert on `review`, which is now BUILT.** Rewriting it to pass by deleting the
    assertion would have removed the check along with the case; instead the mechanism is exercised
    against a synthetic entry, so it keeps working for the next unbuilt command. `UNBUILT` is empty
    today and a test that merely iterated it would be vacuous — passing because there is nothing
    to check, which reads identically to passing because everything is right.
    """
    monkeypatch.setitem(UNBUILT, "spike", "the stage that would deliver it")
    assert main(["spike"]) == 2
    out = capsys.readouterr().out
    assert "the stage that would deliver it" in out
    assert "implementation.md" in out


def test_review_is_built_and_no_longer_exits_two() -> None:
    """The other half of the change: `review` must not still be reachable as an unbuilt command."""
    assert "review" not in UNBUILT, (
        "review is built; leaving it in UNBUILT would exit 2 on a real run"
    )
    with pytest.raises(SystemExit):
        # It parses and REQUIRES its arguments, which is what a built command does. Exiting 2 with
        # "not built yet" and exiting 2 for a missing argument are different failures.
        main(["review"])


def test_render_config_reports_whether_a_model_will_run() -> None:
    """The one line an operator actually needs: is this install going to spend money."""
    quiet = render_config(Settings(inference_enabled=False))
    # **ENABLED IS NOT ENOUGH, AND THE LINE MUST NOT SAY IT IS.** Without a project to bill, the
    # webhook cannot call a model at all; a config that reported True here would be announcing
    # behaviour the process does not have, which this codebase has already shipped once.
    unbilled = render_config(Settings(inference_enabled=True))
    loud = render_config(Settings(inference_enabled=True, inference_project="a-gcp-project"))
    assert "runs a model on a review:  False" in quiet
    assert "runs a model on a review:  False" in unbilled
    assert "runs a model on a review:  True" in loud
