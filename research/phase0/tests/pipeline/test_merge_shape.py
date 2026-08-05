"""Verification of the subject-sequence rule — the one A28 replaced diff coverage with.

WHAT: Builds real repositories and asserts `by_subject` on each case that decides a shape:
      a rebase run, a multi-commit squash, the k = 1 boundary, and no subjects at all.
WHY:  This rule took `parent_commit` failure from 15.6% to about 1% and removed the corpus
      file list from detection entirely, which is the whole of A28. It had **no test**.
      Every `resolve()` call in `tests/test_parent_commit.py` passes four positional
      arguments and never `pr_commit_subjects`, so `by_subject` returned None on its first
      line and those tests exercise the diff-coverage fallback instead.

      Confirmed by sabotage rather than by reading: disabling the rule outright — making
      `by_subject` return None unconditionally — left **232 tests passing**. The rule the
      study's admission set now depends on could have been deleted without a single
      failure.

      The k = 1 case matters most and is the one live data cannot check. GitHub's default
      squash message for a ONE-commit PR is that commit's own title, so a squash can match
      exactly one subject; the threshold is 2 precisely so that cannot be read as a rebase.
      The corpus contains no k = 1 PRs, so this boundary is verified here or nowhere.
IMPORTS: GitPython, phase0.pipeline.merge_shape.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from git import Actor, Repo

from phase0.pipeline.merge_shape import MergeShape, by_subject

AUTHOR = Actor("Tester", "tester@example.com")


def _commit(repo: Repo, path: str, message: str) -> str:
    target = Path(repo.working_tree_dir or "") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {message}\n", encoding="utf-8")
    repo.index.add([path])
    return repo.index.commit(message, author=AUTHOR, committer=AUTHOR).hexsha


def _trunk(tmp_path: Path) -> tuple[Repo, str]:
    repo = Repo.init(tmp_path, initial_branch="main")
    _commit(repo, "acme/one.py", "chore: seed")
    return repo, _commit(repo, "README.md", "docs: readme")


def test_two_matching_subjects_are_a_rebase_and_the_parent_is_trunk(tmp_path: Path) -> None:
    """The case `merge^1` gets wrong: it would return the PR's own second-to-last commit."""
    repo, trunk = _trunk(tmp_path)
    _commit(repo, "acme/one.py", "feat: one")
    last = _commit(repo, "acme/two.py", "feat: two")

    result = by_subject(repo.commit(last), ("feat: one", "feat: two"), 2)

    assert result is not None
    assert (result.shape, result.parent_sha, result.steps_walked) == (MergeShape.REBASE, trunk, 2)
    assert result.parent_sha != repo.commit(last).parents[0].hexsha


def test_one_matching_subject_is_a_squash_not_a_rebase(tmp_path: Path) -> None:
    """The boundary the corpus cannot test, because it holds no k = 1 PRs.

    GitHub's default squash message for a one-commit PR is that commit's own title, so a
    squash matches exactly one subject. Reading that as a rebase would walk back past
    trunk. Both answers happen to be `merge^1` for a one-commit PR — which is why this
    must be asserted rather than trusted to show up as a wrong number.
    """
    repo, trunk = _trunk(tmp_path)
    squashed = _commit(repo, "acme/one.py", "feat: only commit")

    result = by_subject(repo.commit(squashed), ("feat: only commit",), 1)

    assert result is not None
    assert result.shape is MergeShape.SQUASH
    assert result.parent_sha == trunk


def test_a_multi_commit_squash_matches_nothing_and_resolves_to_merge_caret_1(
    tmp_path: Path,
) -> None:
    """GitHub's default for 2+ commits is the PR title, which matches no commit subject."""
    repo, trunk = _trunk(tmp_path)
    squashed = _commit(repo, "acme/one.py", "Add the widget (#4207)")

    result = by_subject(repo.commit(squashed), ("feat: one", "feat: two", "fix: three"), 3)

    assert result is not None
    assert (result.shape, result.parent_sha) == (MergeShape.SQUASH, trunk)


def test_the_walk_stops_at_the_first_mismatch(tmp_path: Path) -> None:
    """A run of two must not consume a third commit that trunk owns."""
    repo, _ = _trunk(tmp_path)
    interloper = _commit(repo, "acme/other.py", "chore: unrelated trunk commit")
    _commit(repo, "acme/one.py", "feat: one")
    last = _commit(repo, "acme/two.py", "feat: two")

    result = by_subject(repo.commit(last), ("feat: one", "feat: two"), 2)

    assert result is not None
    assert (result.shape, result.parent_sha) == (MergeShape.REBASE, interloper)


def test_no_subjects_declines_rather_than_guessing(tmp_path: Path) -> None:
    """Without the API's commit list the rule has no input, and says so.

    Returning None hands the decision to the file-coverage fallback. Returning a shape
    would be a verdict derived from nothing.
    """
    repo, _ = _trunk(tmp_path)
    head = _commit(repo, "acme/one.py", "feat: one")

    assert by_subject(repo.commit(head), (), 1) is None


def test_a_subject_matching_out_of_order_is_not_a_run(tmp_path: Path) -> None:
    """The rule is a SEQUENCE. A single coincidental match anywhere is not a rebase."""
    repo, trunk = _trunk(tmp_path)
    merged = _commit(repo, "acme/one.py", "feat: two")

    # "feat: two" is the PR's LAST subject, so it matches at k=1 and stops: one match is
    # a squash whose message happened to equal a commit title, not a replayed run.
    result = by_subject(repo.commit(merged), ("feat: one", "feat: two"), 2)

    assert result is not None
    assert (result.shape, result.parent_sha) == (MergeShape.SQUASH, trunk)
