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

from phase0.parent_commit import MergeShape, resolve

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


def test_unknown_commit_is_ambiguous_not_an_exception(tmp_path: Path) -> None:
    """A deleted or rewritten commit is corpus attrition, counted, not fatal."""
    _trunk(tmp_path)
    result = resolve(tmp_path, "0" * 40, PR_FILES, 1)
    assert (result.shape, result.is_resolved) == (MergeShape.AMBIGUOUS, False)


def test_merge_touching_unrelated_files_is_ambiguous(tmp_path: Path) -> None:
    """Neither squash nor rebase: refuse rather than classify against a guess."""
    repo, _ = _trunk(tmp_path)
    odd = _commit(repo, "other/thing.py", "# x\n", "chore: unrelated single commit")
    result = resolve(tmp_path, odd, PR_FILES, 2)
    assert result.shape is MergeShape.AMBIGUOUS
