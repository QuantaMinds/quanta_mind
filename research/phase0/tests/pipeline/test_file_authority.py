"""What verification does when it has no authority to verify against.

WHAT: Pins `no_file_authority` -- the exclusion raised when GitHub supplies no file list
      -- and pins that the corpus is not substituted in its place.
WHY:  `verify_files` read `authority = merge.api_files or corpus_files`, so an absent
      GitHub list silently promoted the corpus's list to authority and gated admission on
      it at a 0.6 agreement threshold. No amendment authorised that; it was inherited.

      The substitution had a DIRECTION. The corpus over-attributes -- measured against
      GitHub it claimed 104, 65 and 40 `.py` files for PRs whose real lists were 2, 9 and
      2, with no Python among them. A correct diff scored against an inflated expectation
      falls below the threshold and is rejected at `file_set`, an `integrity` verdict that
      blames the repository's account of itself for a gap that was ours -- and it lands
      hardest on the PRs the corpus mis-attributes most, which tracks size. That is A16's
      confounder entering through our own gate.

      `test_the_corpus_list_is_not_consulted` is the one that would have caught it: it
      supplies a corpus list that WOULD have passed the old fallback, so if the fallback
      ever returns this file fails rather than the suite passing quietly.
IMPORTS: pytest, phase0.github_pulls, phase0.pipeline.{assemble,rejection,verify_files}.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.github_pulls import MergeInfo
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection
from phase0.pipeline.verify_files import verify_files

HONEST = ("pkg/mod.py", "pkg/added.py")


def _merge(sha: str, api_files: tuple[str, ...] = ()) -> MergeInfo:
    return MergeInfo(
        pr_id="1",
        number=1,
        merged=True,
        merge_commit_sha=sha,
        merged_at="2025-06-24T22:46:29Z",
        base_ref="main",
        commit_count=1,
        api_files=api_files,
    )


def test_no_github_list_is_a_named_exclusion() -> None:
    """An absent authority is a typed absence, not a licence to substitute a worse one."""
    outcome = verify_files("1", _merge("deadbeef"), frozenset(HONEST))
    assert isinstance(outcome, Rejection)
    assert (outcome.stage, outcome.category) == ("no_file_authority", "resource")


def test_the_corpus_list_is_not_consulted(repo: tuple[Path, str, str]) -> None:
    """The corpus list here is CORRECT, so the old fallback admitted this PR.

    It is refused now, and that is the point: verification either has GitHub's account of
    the PR or it does not. A gate that passes on the corpus's say-so is not verifying.
    """
    root, _, child = repo
    outcome = build_record(
        root,
        _merge(child, api_files=()),
        pr_id="1",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        corpus_files=HONEST,
    )
    assert isinstance(outcome, Rejection)
    assert outcome.stage == "no_file_authority"


def test_a_matching_github_list_still_admits(repo: tuple[Path, str, str]) -> None:
    """The gate did not simply become "reject everything"."""
    root, _, child = repo
    outcome = build_record(
        root,
        _merge(child, api_files=HONEST),
        pr_id="2",
        repo="acme/widget",
        merged_at="2025-06-24T22:46:29Z",
        corpus_files=HONEST,
    )
    assert not isinstance(outcome, Rejection), getattr(outcome, "reason", "")
    assert set(outcome.changed_files) == set(HONEST)


def test_resource_not_integrity() -> None:
    """The category is a claim about WHOSE data was missing, and it must be ours.

    `integrity` says the corpus's account of the unit cannot be trusted, and A17's bounds
    treat the two differently -- `restricted` narrows the estimand, the other two bias it.
    """
    outcome = verify_files("1", _merge("deadbeef"), frozenset(HONEST))
    assert isinstance(outcome, Rejection)
    assert outcome.category == "resource"
    assert outcome.category != "integrity"
