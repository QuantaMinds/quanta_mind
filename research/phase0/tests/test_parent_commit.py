"""Verification of A2's parent-commit rule across all three merge strategies.

WHAT: Builds real repositories merged three ways and asserts each resolves to the
      trunk commit the PR landed on, not to a commit inside the PR.
WHY:  The exposure variable is defined at the parent commit, so this decides what
      every measurement is taken against, and getting it wrong is silent — the
      pipeline would happily classify against the wrong tree.

      The rebase case is the one that needs the test. GitHub replays each commit
      onto the base individually with new SHAs and no merge commit, so
      `merge_commit_sha^1` is the PR's own second-to-last commit rather than
      trunk. A rule that used it unconditionally would look correct on every merge
      and squash in the corpus and be wrong on every rebase.

      Detection is by diff coverage, not by commit message: a squash commit's
      message matches no individual PR commit, so message matching would reject
      every squashed multi-commit PR — the most common case on GitHub.
IMPORTS: GitPython, phase0.parent_commit, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from git import Actor, Repo

from phase0.parent_commit import GIT_LOOKUP_ERRORS, MergeShape, resolve
from phase0.pipeline.merge_shape import ResolutionRule

AUTHOR = Actor("Tester", "tester@example.com")
PR_FILES = frozenset({"acme/one.py", "acme/two.py"})


def _write(repo: Repo, path: str, body: str) -> None:
    target = Path(repo.working_tree_dir or "") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    repo.index.add([path])


def _commit(repo: Repo, path: str, body: str, message: str) -> str:
    _write(repo, path, body)
    return repo.index.commit(message, author=AUTHOR, committer=AUTHOR).hexsha


def _trunk(tmp_path: Path) -> tuple[Repo, str]:
    repo = Repo.init(tmp_path, initial_branch="main")
    _commit(repo, "acme/one.py", "# base\n", "chore: seed")
    trunk = _commit(repo, "README.md", "# base\n", "docs: readme")
    return repo, trunk


def test_merge_commit_resolves_to_first_parent(tmp_path: Path) -> None:
    """Two parents is unambiguous: the first is trunk before the merge."""
    repo, trunk = _trunk(tmp_path)
    repo.git.checkout("-b", "feature")
    _commit(repo, "acme/one.py", "# changed\n", "feat: one")
    _commit(repo, "acme/two.py", "# changed\n", "feat: two")
    repo.git.checkout("main")
    repo.git.merge("--no-ff", "feature", "-m", "Merge pull request #1")

    result = resolve(tmp_path, repo.head.commit.hexsha, PR_FILES, 2)
    assert (result.shape, result.parent_sha) == (MergeShape.MERGE_COMMIT, trunk)


def test_squash_resolves_to_first_parent(tmp_path: Path) -> None:
    """One commit covering the PR's whole file set is a squash; ^1 is trunk."""
    repo, trunk = _trunk(tmp_path)
    _write(repo, "acme/one.py", "# changed\n")
    _write(repo, "acme/two.py", "# changed\n")
    squashed = repo.index.commit("feat: add one and two (#1)", author=AUTHOR, committer=AUTHOR)

    result = resolve(tmp_path, squashed.hexsha, PR_FILES, 2)
    assert (result.shape, result.parent_sha) == (MergeShape.SQUASH, trunk)


def test_rebase_walks_back_past_the_prs_own_commits(tmp_path: Path) -> None:
    """The case `merge_commit_sha^1` gets wrong.

    Three replayed commits, each touching a subset of the PR's files. The parent
    is trunk, three steps back — not the second-to-last replayed commit.
    """
    repo, trunk = _trunk(tmp_path)
    _commit(repo, "acme/one.py", "# a\n", "feat: step one")
    _commit(repo, "acme/two.py", "# b\n", "feat: step two")
    last = _commit(repo, "acme/one.py", "# c\n", "feat: step three")

    result = resolve(tmp_path, last, PR_FILES, 3)
    assert (result.shape, result.parent_sha, result.steps_walked) == (MergeShape.REBASE, trunk, 3)


def test_rebase_stops_at_a_commit_outside_the_prs_files(tmp_path: Path) -> None:
    """The walk must stop at trunk even when the PR's commit count would allow more."""
    repo, _ = _trunk(tmp_path)
    interloper = _commit(repo, "other/thing.py", "# x\n", "chore: unrelated")
    _commit(repo, "acme/one.py", "# a\n", "feat: step one")
    last = _commit(repo, "acme/two.py", "# b\n", "feat: step two")

    result = resolve(tmp_path, last, PR_FILES, 5)
    assert result.parent_sha == interloper


def test_unresolvable_refs_are_ambiguous_not_exceptions(tmp_path: Path) -> None:
    """Every shape of bad ref is attrition, counted, and never fatal.

    Two distinct GitPython failure modes are covered here, and they raise across
    UNRELATED hierarchies. A 40-hex SHA that is simply absent raises ValueError; a
    ref that is not a SHA at all raises BadName, which derives from gitdb's
    ODBError and is neither a GitError nor a ValueError. A handler catching only
    the obvious two lets the second escape and end the run -- and merge_commit_sha
    arrives from an API payload, so a malformed value is a realistic input.
    """
    _trunk(tmp_path)
    shapes = {
        "absent 40-hex": resolve(tmp_path, "0" * 40, PR_FILES, 1).shape,
        "not a sha": resolve(tmp_path, "not-a-sha", PR_FILES, 1).shape,
        "empty": resolve(tmp_path, "", PR_FILES, 1).shape,
    }
    assert set(shapes.values()) == {MergeShape.AMBIGUOUS}


def test_git_lookup_errors_span_both_hierarchies() -> None:
    """Pinned so a future narrowing of the handler fails loudly here."""
    from git.exc import GitError, ODBError

    assert (GitError, ODBError, ValueError) == GIT_LOOKUP_ERRORS


def test_merge_touching_unrelated_files_is_ambiguous(tmp_path: Path) -> None:
    """Neither squash nor rebase: refuse rather than classify against a guess."""
    repo, _ = _trunk(tmp_path)
    odd = _commit(repo, "other/thing.py", "# x\n", "chore: unrelated single commit")
    result = resolve(tmp_path, odd, PR_FILES, 2)
    assert result.shape is MergeShape.AMBIGUOUS


def test_no_file_list_and_covered_file_list_are_different_rules(tmp_path: Path) -> None:
    """A46. Both return SQUASH, and only one of them tested anything.

    `covered >= pr_files` passing on a list we have, and returning SQUASH because there
    is no list at all, are different claims. They shared one verdict, so the share of
    parents resting on nothing could not be counted -- "no edge here" and "we failed
    here" as the same value on the wire, which non-negotiable 3 forbids.
    """
    repo, _trunk_sha = _trunk(tmp_path)
    merged = _commit(repo, "acme/one.py", "# changed\n", "feat: change one")

    with_list = resolve(tmp_path, merged, frozenset({"acme/one.py"}), 1)
    without_list = resolve(tmp_path, merged, frozenset(), 1)

    assert with_list.shape is MergeShape.SQUASH
    assert without_list.shape is MergeShape.SQUASH
    assert with_list.parent_sha == without_list.parent_sha
    # Same shape, same parent, same reason-to-a-skim. The rule is the only field that
    # tells them apart, which is why it exists.
    assert with_list.rule is ResolutionRule.FILE_COVERAGE
    assert without_list.rule is ResolutionRule.NO_FILE_LIST


def test_a_merge_commit_records_that_git_alone_decided_it(tmp_path: Path) -> None:
    """Two parents needs no file list, and the rule must say so."""
    repo, _trunk_sha = _trunk(tmp_path)
    repo.git.checkout("-b", "feature")
    _commit(repo, "acme/one.py", "# changed\n", "feat: one")
    repo.git.checkout("main")
    repo.git.merge("--no-ff", "feature", "-m", "Merge pull request #9")
    merged = repo.head.commit.hexsha

    resolved = resolve(tmp_path, merged, frozenset({"acme/one.py"}), 1)

    assert resolved.shape is MergeShape.MERGE_COMMIT
    assert resolved.rule is ResolutionRule.MERGE_PARENTS


def test_subjects_decide_without_the_corpus_file_list(tmp_path: Path) -> None:
    """A28's rule runs first, and a resolution it produced must not read as corpus-based.

    The file list passed here is DELIBERATELY wrong -- a file the PR never touched. If
    the subject rule did not decide, the file rules would, and the recorded rule would
    say `file_coverage` instead.
    """
    repo, _trunk_sha = _trunk(tmp_path)
    first = _commit(repo, "acme/one.py", "# a\n", "feat: first of two")
    _commit(repo, "acme/one.py", "# b\n", "feat: second of two")
    merged = repo.head.commit.hexsha
    subjects = ("feat: first of two", "feat: second of two")

    resolved = resolve(tmp_path, merged, frozenset({"nowhere/absent.py"}), 2, subjects)

    assert resolved.rule is ResolutionRule.SUBJECT_SEQUENCE
    assert resolved.shape is MergeShape.REBASE
    assert resolved.parent_sha == repo.commit(first).parents[0].hexsha
