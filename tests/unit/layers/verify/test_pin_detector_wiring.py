"""Verification that the pin detector is handed a list it can actually act on.

WHAT: Pins the wiring between the changed-file list and `verify/pin_check`, and the `None`
      sentinel that makes an unfiltered fetch possible.
WHY:  **EVERY EXISTING ORACLE TEST PASSES WITH THE WIRING BROKEN.** They call `detect()` with a
      synthetic diff string, so they prove the detector works and say nothing about whether it is
      ever given anything. It was not: `changed_files()` filtered to `REVIEWABLE_SUFFIXES`, which
      holds no `.yml`, and that filtered list was passed to `check()`, so `workflows()` returned
      `[]` and the detector exited before touching git on every pull request ever delivered.
      → `docs/findings/oracles/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`

      So these tests start from a changed-file LIST, the thing the delivery path actually holds,
      and assert on what reaches the detector. A test that starts from a diff cannot fail the way
      this system failed.
IMPORTS: pytest, quantamind.verify.pin_check, quantamind.ingest.diff, quantamind.types.change.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.types.change import REVIEWABLE_SUFFIXES
from quantamind.verify.pin_check import workflows

WORKFLOW = ".github/workflows/tests.yaml"
MIXED = [WORKFLOW, ".github/workflows/lock.yml", "src/flask/app.py", "README.md"]


def test_the_ranking_filter_removes_every_workflow() -> None:
    """The premise of the defect, pinned so it cannot be argued about later."""
    kept = [name for name in MIXED if name.endswith(REVIEWABLE_SUFFIXES)]
    assert kept == ["src/flask/app.py"], kept
    assert ".yml" not in REVIEWABLE_SUFFIXES and ".yaml" not in REVIEWABLE_SUFFIXES


def test_the_detector_sees_workflows_in_an_unfiltered_list() -> None:
    assert workflows(MIXED) == [WORKFLOW, ".github/workflows/lock.yml"], workflows(MIXED)


def test_the_detector_sees_nothing_in_the_ranking_filtered_list() -> None:
    """**THE DEFECT, AS AN ASSERTION.** This is what the delivery path used to pass."""
    filtered = [name for name in MIXED if name.endswith(REVIEWABLE_SUFFIXES)]
    assert workflows(filtered) == [], "the ranker's list can never carry a workflow"


def test_delivery_passes_the_unfiltered_list_to_the_detector() -> None:
    """Reads the call site, because the defect was invisible in every behavioural test.

    A source-level assertion is weak and is used here on purpose: the alternative is a live
    pull request with a pinned workflow, and this is the property that actually broke.
    """
    source = __import__("inspect").getsource(
        __import__("quantamind.serve.review_delivery", fromlist=["review_delivery"])
    )
    assert "pin_check.check(clone, head_sha, every_file)" in source, (
        "the detector must be handed the unfiltered list; passing `changed` is the defect"
    )
    assert "changed_files(delivery_repo, number, suffixes=None)" in source, (
        "the unfiltered fetch must ask for no filter explicitly"
    )


def test_an_empty_suffix_tuple_would_filter_everything_out() -> None:
    """Why the sentinel is `None`. `()` reads like "no filter" and silently means "nothing".

    A caller reaching for `suffixes=()` to get the whole list would receive an empty one and
    read it as a change that touched no files -- the same shape as the defect being fixed.
    """
    assert not "a.py".endswith(()), "endswith(()) is False, so () is not 'no filter'"


def test_workflows_accepts_both_yaml_spellings() -> None:
    """A repository using `.yml` and one using `.yaml` must not get different coverage."""
    assert workflows([".github/workflows/a.yml"]) == [".github/workflows/a.yml"]
    assert workflows([".github/workflows/b.yaml"]) == [".github/workflows/b.yaml"]
    assert workflows(["docs/not_a_workflow.yaml"]) == [], "only workflow paths count"


def test_the_detector_runs_before_the_no_source_files_return() -> None:
    """**A WORKFLOW-ONLY PULL REQUEST IS THE COMMON SHAPE CARRYING A PIN CHANGE.**

    `deliver()` returned `NO_FILES` as soon as no source file changed, which is before the
    detector ran — so giving it the unfiltered list fixed nothing for exactly the pull requests
    it exists to catch. Found by firing at a real one, not by any test, which is why the order
    is asserted here rather than trusted.
    """
    source = __import__("inspect").getsource(
        __import__("quantamind.serve.review_delivery", fromlist=["review_delivery"])
    )
    check_at = source.index("pin_check.check(clone, head_sha, every_file)")
    return_at = source.index("return Delivered(Outcome.NO_FILES")
    assert check_at < return_at, (
        "pin_check must run BEFORE the no-source-files return, or a workflow-only "
        "pull request exits with the detector never having looked"
    )


def test_a_workflow_only_change_can_still_produce_a_comment() -> None:
    """The other half: having run, a mismatch must survive to a body rather than be discarded."""
    source = __import__("inspect").getsource(
        __import__("quantamind.serve.review_delivery", fromlist=["review_delivery"])
    )
    guard = source.index("if not changed:")
    assert "if not pins:" in source[guard : guard + 400], (
        "with no source files, NO_FILES must be conditional on there being no pins either"
    )
