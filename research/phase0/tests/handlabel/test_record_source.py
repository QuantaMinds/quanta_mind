"""The gate scans the pipeline's own record, never a rebuild of it.

WHAT: Pins `record_for` -- the draw reads the stored `PRRecord`, returns the SAME object,
      and yields None for a candidate the pipeline never admitted.
WHY:  `draw._as_record` rebuilt the classifier's input from a `Candidate` and got three
      fields wrong, each reproducing a defect the pipeline had already fixed and
      documented:

        base_ref    never set -> `base_ref_of("")` returns "HEAD", so the scan walked the
                    clone's DEFAULT branch instead of the branch the PR merged into. 15.5%
                    of the corpus merges into dev/develop/a feature branch, and every one
                    of those was scored against the wrong history.
        arm         hardcoded "human" on a draw invoked `--arm agent`.
        merged_sha  the PR's last branch commit, not the merge commit the scan needs for
                    reachability and to exclude the merge from its own window.

      So the gate certified a classifier the study does not run, on roughly one PR in six.
      Demonstrated on `camUrban/PteraSoftware#32`: its real base `release-3.1.0` is
      deleted, so the pipeline returns UNSCANNABLE, while the rebuilt input walked `main`
      and returned BROKE.

      Nothing exercised `draw` at all -- no test called it -- which is how three wrong
      fields survived. `draw` clones over the network and cannot run offline, so the
      invariant that mattered is factored out here where it can be asserted on real
      records with no mock: identity, not equality, because an object that merely compares
      equal today is exactly what a future rebuild would produce.
IMPORTS: phase0.extract_prs, phase0.handlabel.{draw,select}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from phase0.extract_prs import PRRecord
from phase0.handlabel.draw import record_for
from phase0.handlabel.select import Candidate

# The three fields the rebuild got wrong, set to values a rebuild could not invent.
STORED = PRRecord(
    pr_id="2607442037",
    repo="o/r",
    language="python",
    parent_sha="a" * 40,
    merged_sha="b" * 40,
    merged_at="2025-07-07T00:49:29Z",
    changed_files=("pkg/mod.py",),
    changed_symbols=("pkg.mod.f",),
    arm="agent",
    base_ref="release-3.1.0",
)


def _candidate(pr_id: int) -> Candidate:
    return Candidate(
        pr_id=pr_id,
        repo="o/r",
        number=32,
        merged_at="2025-07-07T00:49:29Z",
        title="t",
        commit_shas=("c" * 40,),
        changed_files=("pkg/mod.py",),
    )


def test_the_stored_record_is_returned_not_a_copy() -> None:
    """Identity. An equal-but-rebuilt object is precisely what regressed before."""
    got = record_for(_candidate(2607442037), {STORED.pr_id: STORED})
    assert got is STORED


def test_the_three_fields_the_rebuild_got_wrong_survive() -> None:
    """base_ref, arm and merged_sha reach the scan as the pipeline wrote them."""
    got = record_for(_candidate(2607442037), {STORED.pr_id: STORED})
    assert got is not None
    assert (got.base_ref, got.arm, got.merged_sha) == ("release-3.1.0", "agent", "b" * 40)
    assert got.base_ref != "", "an empty base_ref makes base_ref_of return HEAD"
    assert got.merged_sha != "c" * 40, "that is the branch commit, not the merge commit"


def test_an_unadmitted_candidate_yields_none() -> None:
    """The study never analyses it, so the gate must not certify the classifier on it."""
    records = {STORED.pr_id: STORED}
    assert (record_for(_candidate(999), records), record_for(_candidate(2607442037), records)) == (
        None,
        STORED,
    )


def test_lookup_is_by_string_id() -> None:
    """`Candidate.pr_id` is an int and the record's is a str; a type mismatch here would
    silently drop EVERY candidate and empty the draw rather than raising."""
    assert record_for(_candidate(2607442037), {"2607442037": STORED}) is STORED
