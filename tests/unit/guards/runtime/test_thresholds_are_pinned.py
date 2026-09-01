"""Verification that no guard threshold can be weakened without a test failing.

WHAT: Reads every integer threshold in `scripts/guard/` straight out of the source with `ast`
      and checks it twice — that it still MEANS what it has to mean, and that it still equals
      the value recorded here.
WHY:  **FIFTEEN OF SEVENTEEN WEAKENINGS SURVIVED THE ENTIRE UNIT SUITE.** Setting every
      coverage floor to 0, `check_agents_md.MAX_LINES` to 9999, and `hook_pre_edit.DENY` to 0
      each left `pytest tests/unit` fully green. The mechanisms were well tested — twelve tests
      cover `assert_examined` alone — but nothing tested the NUMBERS WIRED INTO THEM, so every
      call site could be disabled while the mechanism's own tests kept passing.

      **`DENY = 0` IS THE WORST OF THEM.** `hook_pre_edit.decide` returns `DENY` to block an
      edit, and the hook's exit code is what the tool obeys. At 0 it returns ALLOW, so the hook
      enforcing "no direct commits to main" permits every edit it exists to stop, silently, with
      no test failing and no output changing.

      **THE FLOORS WERE THE SHARPEST IRONY.** They exist because a guard examining nothing prints
      the same word as a guard finding nothing wrong. A floor of 0 never fires, which is the
      exact condition they were built to detect, and it passed.

      Two layers, because they fail differently. `test_thresholds_still_mean_something` encodes
      what a value must never become and keeps holding when a number is legitimately changed.
      `test_thresholds_match_their_recorded_values` pins the exact numbers, so a deliberate
      change is a visible edit to this file rather than a line nobody sees.
IMPORTS: pytest, ast, pathlib. Reads `scripts/guard/` as text; imports nothing from it.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import ast
from pathlib import Path

GUARDS = Path(__file__).resolve().parents[4] / "scripts" / "guard"

# Every integer threshold in the guard layer, as of 2026-08-29. A guard added with a new
# threshold fails here until its number is recorded, which is the point: an unrecorded
# threshold is one nobody decided.
RECORDED: dict[str, int] = {
    "check_agents_md.py::MAX_LINES": 210,
    "check_assert_quality.py::floor(test modules)": 20,
    "check_branch_name.py::GIT_TIMEOUT_S": 30,
    "check_conventions.py::floor(python files)": 40,
    "check_module_identity.py::floor(python modules)": 40,
    # D7f. **40 IS THE SAME FLOOR `check_module_identity` USES** for "did the walk find the
    # source tree at all", copied rather than chosen: this guard examines every python module in
    # `src/`, and a run that examined none must report a broken walk instead of "ok".
    # **30s, COPIED FROM `check_branch_name.py`, NOT CHOSEN.** Both guards shell out to git for a
    # branch name or a status, and AGENTS.md requires an explicit timeout on every subprocess call.
    "check_work_on_main.py::GIT_TIMEOUT_S": 30,
    "runtime/check_network_chokepoint.py::floor(python modules)": 40,
    "runtime/check_no_partial_clone.py::CLONE_FILE_FLOOR": 10,
    "check_no_research_imports.py::floor(python files)": 40,
    "check_structure.py::MAX_DIR_FILES": 15,
    "check_structure.py::MAX_FILE_LINES": 200,
    "check_structure.py::floor(source files)": 40,
    "runtime/check_subprocess_timeouts.py::SUBPROCESS_FLOOR": 10,
    # Set below the count `docs/` actually holds, to catch discovery collapsing rather than
    # to police the number drifting. Same floor and same reason as the resolver beside it.
    "citations/identity.py::floor(documents)": 20,
    "citations/resolve.py::floor(markdown documents)": 20,
    "hooks/hook_post_edit.py::FEEDBACK": 2,
    "hooks/hook_post_edit.py::QUIET": 0,
    "hooks/hook_post_edit.py::TOOL_TIMEOUT_S": 60,
    "hooks/hook_pre_edit.py::ALLOW": 0,
    "hooks/hook_pre_edit.py::DENY": 2,
    "hooks/hook_pre_edit.py::GIT_TIMEOUT_S": 30,
    "hooks/hook_session_end.py::GIT_TIMEOUT_S": 30,
    "records/check_decided_vocabulary.py::floor(decisions)": 3,
    "records/check_decided_vocabulary.py::floor(documents)": 3,
    "records/check_decided_vocabulary.py::floor(paragraphs)": 100,
    "records/check_docs_sync.py::GIT_TIMEOUT_S": 30,
    "records/check_documented_commands.py::FLOOR": 2,
    "records/check_documented_recipes.py::RECIPE_FLOOR": 20,
    "records/check_no_vague_refs.py::MARKDOWN_FLOOR": 40,
    "records/check_schema_shape.py::RECORDED_VERSION": 7,
    "records/check_withdrawn_amendments.py::AMENDMENT_FLOOR": 20,
}


def _thresholds() -> dict[str, int]:
    """Every integer threshold in the guard layer, keyed by file and name.

    A coverage floor is keyed by the population it names rather than by line number, so
    moving a call does not look like a changed threshold.
    """
    found: dict[str, int] = {}
    for path in sorted(p for p in GUARDS.rglob("*.py") if p.name != "__init__.py"):
        rel = path.relative_to(GUARDS).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign | ast.AnnAssign):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id.isupper()
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, int)
                    and not isinstance(node.value.value, bool)
                ):
                    found[f"{rel}::{target.id}"] = node.value.value
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call) and getattr(node.func, "id", "") == "assert_examined"
            ):
                continue
            if len(node.args) >= 3 and all(isinstance(node.args[i], ast.Constant) for i in (0, 2)):
                found[f"{rel}::floor({node.args[0].value})"] = node.args[2].value
    return found


def test_the_extractor_finds_thresholds_at_all() -> None:
    """A scan that collapses to nothing would make every other test here vacuous."""
    found = _thresholds()

    assert len(found) >= 20, f"threshold scan collapsed to {len(found)}; the guards were not read"
    assert "check_structure.py::MAX_DIR_FILES" in found, "a known threshold was not found"


def test_thresholds_still_mean_something() -> None:
    """What each value may never become, independent of what it currently is.

    This layer survives a legitimate renumbering. A floor of 0 admits everything, and a
    blocking code equal to the allowing code blocks nothing.
    """
    found = _thresholds()

    for key, value in found.items():
        if "floor" in key.lower() or key.endswith("FLOOR"):
            assert value > 0, f"{key} is {value}; a floor of zero can never fire"
        if key.endswith(("MAX_LINES", "MAX_FILE_LINES", "MAX_DIR_FILES")):
            assert 0 < value < 1000, f"{key} is {value}, which caps nothing"

    assert found["hooks/hook_pre_edit.py::DENY"] != found["hooks/hook_pre_edit.py::ALLOW"], (
        "the pre-edit hook cannot distinguish a refusal from a permission"
    )
    assert found["hooks/hook_pre_edit.py::DENY"] != 0, "a DENY of 0 is an exit code meaning success"
    assert found["hooks/hook_post_edit.py::FEEDBACK"] != found["hooks/hook_post_edit.py::QUIET"], (
        "the post-edit hook cannot distinguish a complaint from silence"
    )


def test_thresholds_match_their_recorded_values() -> None:
    """Every threshold equals the number recorded above, and there are no unrecorded ones."""
    found = _thresholds()

    assert found == RECORDED, (
        "a guard threshold changed. If that was deliberate, edit RECORDED in this file and say "
        "in the PR why the new number is right; a threshold nobody recorded is one nobody decided."
    )
