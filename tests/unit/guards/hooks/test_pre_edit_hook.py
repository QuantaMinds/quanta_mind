"""Verification that the pre-edit hook actually refuses the edits it exists to refuse.

WHAT: Drives `hook_pre_edit.decide` against a real git repository on a protected branch, on a
      feature branch, against vendored source, and against a reviewed golden file.
WHY:  **THE HOOK ENFORCING RULE 9 HAD NO TEST OF ANY KIND.** It is the mechanism behind "branch
      per change" and the vendored-source freeze, and nothing exercised it. Rewriting `DENY = 2`
      to `DENY = 0` left `pytest tests/unit` completely green while turning every refusal into a
      permission — the hook would print its refusal to stderr and then return success, so the
      edit it just objected to would proceed.

      **THE EXPECTED CODES ARE WRITTEN AS LITERALS ON PURPOSE.** Asserting `decide(...) == DENY`
      would import the value under test and pass at any value, which is how the threshold got
      away unpinned in the first place. 2 and 0 are written out, and
      `tests/unit/guards/test_thresholds_are_pinned.py` holds the same numbers from the other
      direction.
IMPORTS: pytest, subprocess, scripts/guard/hooks/hook_pre_edit.py.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# **`parents[4]`, NOT `[3]`.** This file moved down a level when `tests/unit/guards/` hit its
# fifteen-file cap. A depth index is exactly the kind of reference AGENTS.md rule 12 is about:
# it stays syntactically valid after a move and silently resolves somewhere else.
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts" / "guard" / "hooks"))

import hook_pre_edit

BLOCK = 2  # what the tool obeys as a refusal. Not imported; see the module docstring.
PERMIT = 0


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A real git repository with one commit, sitting on `main`."""

    def run(*args: str) -> None:
        subprocess.run(args, cwd=tmp_path, capture_output=True, check=True, timeout=30)

    run("git", "init", "-q", "-b", "main")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t")
    (tmp_path / "seed.txt").write_text("seed\n")
    run("git", "add", "-A")
    run("git", "commit", "-qm", "seed")
    return tmp_path


def _switch(repo: Path, branch: str) -> None:
    subprocess.run(
        ["git", "switch", "-qc", branch], cwd=repo, capture_output=True, check=True, timeout=30
    )


def test_an_edit_on_the_protected_branch_is_refused(repo: Path, capsys) -> None:
    """The rule-9 case. This is the one that silently inverted when DENY was 0."""
    assert hook_pre_edit.decide("src/quantamind/rank/history.py", repo) == BLOCK

    assert "main" in capsys.readouterr().err


def test_the_same_edit_on_a_feature_branch_is_permitted(repo: Path) -> None:
    """The false-positive direction: a hook that refused everything would be removed."""
    _switch(repo, "fix/1-something")

    assert hook_pre_edit.decide("src/quantamind/rank/history.py", repo) == PERMIT


def test_vendored_source_is_refused_even_on_a_feature_branch(repo: Path, capsys) -> None:
    """The vendor freeze does not depend on which branch you are on."""
    _switch(repo, "fix/1-something")

    assert hook_pre_edit.decide("vendor/tree_sitter/parser.c", repo) == BLOCK

    assert "vendored" in capsys.readouterr().err


def test_a_golden_file_escalates_to_a_human_rather_than_passing(repo: Path, capsys) -> None:
    """Golden edits return control to a person; the permission is 'ask', not a silent yes."""
    _switch(repo, "fix/1-something")

    result = hook_pre_edit.decide("tests/fixtures/golden/review.json", repo)
    printed = capsys.readouterr().out

    assert result == PERMIT, "the hook must hand the decision over, not refuse outright"
    assert '"permissionDecision": "ask"' in printed, "the golden edit was allowed without asking"


def test_the_golden_sentinel_is_consumed_so_it_cannot_be_left_set(repo: Path, capsys) -> None:
    """One approval, one edit. A sentinel that survived would approve every later edit."""
    _switch(repo, "fix/1-something")
    sentinel = repo / hook_pre_edit.SENTINEL
    sentinel.write_text("")

    first = hook_pre_edit.decide("tests/fixtures/golden/review.json", repo)
    first_output = capsys.readouterr().out
    second = hook_pre_edit.decide("tests/fixtures/golden/review.json", repo)
    second_output = capsys.readouterr().out

    assert first == PERMIT
    assert "ask" not in first_output, "the sentinel was set and the hook asked anyway"
    assert not sentinel.exists(), "the sentinel survived and now approves every golden edit"
    assert second == PERMIT
    assert '"permissionDecision": "ask"' in second_output, (
        "the second golden edit was approved without asking, so the sentinel was not consumed"
    )
