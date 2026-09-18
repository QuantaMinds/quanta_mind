"""Verification that a secret written in `.env` is actually reachable by the code that needs it.

WHAT: Drives `types/dotenv.credential` — the two sources it reads, which one wins, and what an
      absent name returns.
WHY:  **THREE CREDENTIALS IN `.env` WERE READ BY NOTHING, AND EVERY TEST PASSED.**
      `serve/commands/run_endpoint.py` read `os.environ` directly while
      `types/dotenv.from_file` deliberately never writes there, so a `.env` holding
      `QUANTAMIND_WEBHOOK_SECRET` produced *"no webhook secret: refusing to bind"*. The file looked
      configured and was not. **Nothing in the suite could see it**, because every test that
      exercised the endpoint supplied the value some other way — which is exactly the shape
      `AGENTS.md` rule 14 describes: a check whose output is the same whether the thing works or
      not. It was found by running the command.

      **THE FILE-ONLY CASE IS THE REGRESSION AND IT IS TESTED FIRST.** A test that only ever passes
      a mapping, or only ever exports a variable, would pass against the broken version.

      **PRECEDENCE IS A SEPARATE TEST, BECAUSE GETTING IT BACKWARDS IS THE DANGEROUS FIX.** A
      working tree's `.env` overriding what a deployment exported would silently point production
      at a developer's sandbox key.
IMPORTS: pytest, quantamind.types.dotenv.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.types import dotenv
from quantamind.types.dotenv import credential

NAME = "QUANTAMIND_STRIPE_API_KEY"


def _dotenv_holding(tmp_path: Path, text: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the module's `.env` at a temporary file holding `text`."""
    written = tmp_path / ".env"
    written.write_text(text)
    monkeypatch.setattr(dotenv, "DOTENV", written)


def test_a_secret_only_in_the_dotenv_file_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**THE REGRESSION.** Against the old code this returns "" and the endpoint refuses to bind."""
    _dotenv_holding(tmp_path, f"{NAME}=sk_test_from_the_file\n", monkeypatch)
    monkeypatch.delenv(NAME, raising=False)

    assert credential(NAME) == "sk_test_from_the_file"


def test_an_exported_variable_beats_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A working tree must never override what a deployment exported for this process."""
    _dotenv_holding(tmp_path, f"{NAME}=sk_test_from_the_file\n", monkeypatch)
    monkeypatch.setenv(NAME, "sk_live_from_the_environment")

    assert credential(NAME) == "sk_live_from_the_environment"


def test_an_exported_empty_value_falls_through_to_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`QUANTAMIND_STRIPE_API_KEY=` — set but empty, which is what commenting a line out produces.

    `types/settings.py` already records this exact hazard for `QUANTAMIND_GCLOUD_PATH`: an empty
    string is not a configured value, and treating it as one produced a failure naming no cause.
    """
    _dotenv_holding(tmp_path, f"{NAME}=sk_test_from_the_file\n", monkeypatch)
    monkeypatch.setenv(NAME, "")

    assert credential(NAME) == "sk_test_from_the_file"


def test_an_absent_name_is_empty_and_never_a_placeholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every caller reads empty as a refusal — the endpoint will not bind, the routes answer 503."""
    _dotenv_holding(tmp_path, "SOMETHING_ELSE=x\n", monkeypatch)
    monkeypatch.delenv(NAME, raising=False)

    assert credential(NAME) == ""


def test_a_missing_dotenv_file_is_not_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A container has no `.env` at all and must behave exactly as it always has."""
    monkeypatch.setattr(dotenv, "DOTENV", tmp_path / "nothing-here")
    monkeypatch.delenv(NAME, raising=False)

    assert credential(NAME) == ""


def test_an_injected_mapping_reads_neither_the_file_nor_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A test that mutated the real environment would leak into whatever ran next."""
    _dotenv_holding(tmp_path, f"{NAME}=from_the_file\n", monkeypatch)
    monkeypatch.setenv(NAME, "from_the_environment")

    assert credential(NAME, {NAME: "injected"}) == "injected"
    assert credential("ABSENT", {NAME: "injected"}) == ""
