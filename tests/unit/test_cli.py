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

from quantamind.serve.cli import UNBUILT, main, render_config
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


def test_an_unbuilt_command_names_the_stage_that_delivers_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """ "Not implemented" sends a reader to the source. Naming the stage sends them to the plan."""
    main(["review"])
    out = capsys.readouterr().out
    assert UNBUILT["review"] in out
    assert "implementation.md" in out


def test_render_config_reports_whether_a_model_will_run() -> None:
    """The one line an operator actually needs: is this install going to spend money."""
    quiet = render_config(Settings(inference_enabled=False))
    loud = render_config(Settings(inference_enabled=True))
    assert "runs a model on a review:  False" in quiet
    assert "runs a model on a review:  True" in loud
