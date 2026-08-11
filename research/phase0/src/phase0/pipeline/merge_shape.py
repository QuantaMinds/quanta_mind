"""How a pull request reached trunk, decided from its own commit subjects.

WHAT: `by_subject` — squash versus rebase from the SEQUENCE of the PR's commit subjects,
      which GitHub's API reports authoritatively.
WHY:  Split from `parent_commit.py` because there are two independent ways to tell the
      shapes apart and only one of them depends on the corpus. The file-coverage rules
      there compare the merge against a file list the corpus supplies, and the corpus
      attributes 92 files to some three-file PRs — so those rules failed on exactly the
      PRs whose file lists were wrong, and `parent_commit` became the largest exclusion
      at 17-70% across commit-count bands.

      Keeping the corpus-free strategy in its own module makes that independence
      checkable rather than asserted: nothing here reads a file list.
IMPORTS: GitPython, stdlib dataclasses/enum. Nothing from phase0 -- the cycle
      matters: parent_commit imports this, never the other way.
CONSUMED BY: parent_commit.resolve; tests/pipeline/test_merge_shape.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from git import Commit


class MergeShape(Enum):
    """How the PR reached trunk. Decides which rule applies."""

    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"
    AMBIGUOUS = "ambiguous"  # excluded, and counted as corpus attrition


class ResolutionRule(Enum):
    """WHICH rule produced the shape. Recorded separately because the shape alone
    does not say what it rests on, and the rules do not rest on the same thing.

    `SUBJECT_SEQUENCE` and `MERGE_PARENTS` read only git and the API. `FILE_COVERAGE`
    reads the CORPUS's file list, which A46 measures as unreliable in both directions
    at a rate that is only a lower bound. `NO_FILE_LIST` is split out from it rather
    than folded in: `covered >= pr_files` passing on a list we have and returning
    SQUASH because there is no list at all are different claims, and only the second
    is a guess. Merging them is the collapse non-negotiable 3 forbids.
    """

    MERGE_PARENTS = "merge_parents"  # two parents; git alone decides
    SUBJECT_SEQUENCE = "subject_sequence"  # A28's rule; corpus-free
    FILE_COVERAGE = "file_coverage"  # the corpus file list decided
    NO_FILE_LIST = "no_file_list"  # SQUASH returned with nothing to test against
    UNRESOLVED = "unresolved"  # no rule reached; not about the rules at all


@dataclass(frozen=True, slots=True)
class ParentResolution:
    """The parent commit, how it was decided, and by WHICH rule."""

    shape: MergeShape
    parent_sha: str
    steps_walked: int = 0
    reason: str = ""
    # Keyword-only and WITHOUT a default, so every return site must name its rule and
    # mypy rejects one that does not. A default would let a new branch acquire a
    # plausible rule silently, which is the `_as_record` shape one field at a time.
    # Keyword-only because the existing call sites pass shape/sha/steps/reason
    # positionally, and appending a positional field is how a wrong value slides in.
    rule: ResolutionRule = field(kw_only=True)

    @property
    def is_resolved(self) -> bool:
        return self.shape is not MergeShape.AMBIGUOUS and bool(self.parent_sha)


def by_subject(merge: Commit, subjects: tuple[str, ...], limit: int) -> ParentResolution | None:
    """Shape from the SEQUENCE of the PR's commit subjects, not from any single one.

    A single match proves nothing. GitHub's default squash message reuses the commit
    title when a PR has one commit, so a squashed one-commit PR looks like a rebase --
    harmless (both give `merge^1`) but it means the single-subject test is untested
    exactly where it matters. And the message format is a per-repository setting;
    `squash_merge_commit_title` returns null from the API without push access, so it
    cannot be conditioned on.

    The sequence is decisive where one subject is not: a squash produces exactly ONE
    commit, so it can never yield two consecutive commits matching the PR's subjects in
    order, whatever the message setting. Rebase rewrites every SHA but preserves the
    messages, so the tail of the subject list appears walking back from the merge.

        k >= 2 matches in order  ->  rebase, parent is the earliest match's parent
        k <= 1                   ->  squash, parent is `merge^1`

    A merger who edits the message before confirming falls through to squash, which is
    the right answer for an edited squash. Returns None without subjects, so the
    file-based rules still apply.
    """
    if not subjects:
        return None

    walked: list[Commit] = []
    current = merge
    for _ in range(min(limit, len(subjects))):
        walked.append(current)
        if not current.parents:
            break
        current = current.parents[0]

    # Rebase replays in order, so walking back from the merge meets the PR's subjects
    # from the end. Count how many line up before the first mismatch.
    matched = 0
    for index, commit in enumerate(walked):
        expected = subjects[len(subjects) - 1 - index] if index < len(subjects) else None
        actual = str(commit.message).splitlines()[0].strip() if commit.message else ""
        if expected is None or actual != expected.strip():
            break
        matched += 1

    if matched >= 2:
        earliest = walked[matched - 1]
        if not earliest.parents:
            return ParentResolution(
                MergeShape.AMBIGUOUS,
                "",
                matched,
                "ran out of history",
                rule=ResolutionRule.SUBJECT_SEQUENCE,
            )
        return ParentResolution(
            MergeShape.REBASE,
            earliest.parents[0].hexsha,
            matched,
            f"{matched} of {len(subjects)} subjects matched in order: replayed",
            rule=ResolutionRule.SUBJECT_SEQUENCE,
        )
    return ParentResolution(
        MergeShape.SQUASH,
        merge.parents[0].hexsha,
        steps_walked=1,
        reason=f"{matched} consecutive subject match(es): one commit, so squashed",
        rule=ResolutionRule.SUBJECT_SEQUENCE,
    )
