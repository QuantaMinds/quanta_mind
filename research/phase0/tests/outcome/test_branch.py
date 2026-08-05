"""Verification that the outcome scan walks the PR's own base branch, or says it cannot.

WHAT: Builds real git repositories with a non-default base branch, a deleted base branch,
      and a merge commit that is not an ancestor of the branch it merged into, then
      asserts the verdict and the exclusion category for each.
WHY:  The scan walked from the clone's HEAD. 15.5% of the corpus merges into `dev`,
      `develop` or a feature branch, so for those PRs the merge commit and every commit
      after it sat outside the walk, and each one returned CLEAN. Nothing errored, no
      exclusion count moved, and the verdict was well-formed -- the failure was invisible
      by construction, and it biased toward the null in exactly the repositories with a
      release process.

      `test_fix_on_dev_is_found` is the regression: before the fix it returned CLEAN, and
      it is the only test here that would have failed. The other two assert that the
      cases which CANNOT be answered are counted by category rather than defaulted, since
      a fallback to HEAD would restore the identical bug inside a narrower band.

      Real repositories, not mocks. A mocked `is_ancestor` would prove that our stub
      returns what we told it to, and the defect was precisely that the real walk and our
      belief about it disagreed.
IMPORTS: GitPython, phase0.outcome.{scan,record,window}, phase0.extract_prs, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Actor, Repo

from phase0.extract_prs import PRRecord
from phase0.outcome.conclusion import Outcome
from phase0.outcome.scan import scan
from phase0.outcome.window import Exclusion, merge_on_base

MERGED_AT = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
AUTHOR = Actor("Tester", "tester@example.com")
TOUCHED = "acme/handlers.py"


def _commit(repo: Repo, path: str, message: str, when: datetime) -> str:
    target = Path(repo.working_tree_dir or "") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {message}\n", encoding="utf-8")
    repo.index.add([path])
    # GitPython's date parser rejects an offset written "+00:00"; it wants "+0000".
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S%z")
    made = repo.index.commit(
        message, author=AUTHOR, committer=AUTHOR, author_date=stamp, commit_date=stamp
    )
    return made.hexsha


def _pr(merged_sha: str, base_ref: str) -> PRRecord:
    return PRRecord(
        pr_id="1",
        repo="o/r",
        language="python",
        parent_sha="0" * 40,
        merged_sha=merged_sha,
        merged_at=MERGED_AT.isoformat().replace("+00:00", "Z"),
        changed_files=(TOUCHED,),
        changed_symbols=("handle",),
        base_ref=base_ref,
    )


def _repo_with_dev(tmp_path: Path) -> tuple[Repo, str]:
    """A repo on `main`, with `dev` branched off and the PR merged into `dev`."""
    repo = Repo.init(tmp_path, initial_branch="main")
    _commit(repo, "README.md", "chore: init", MERGED_AT - timedelta(days=10))
    repo.create_head("dev")
    repo.heads.dev.checkout()
    merged = _commit(repo, TOUCHED, "feat: add handler", MERGED_AT)
    return repo, merged


def test_fix_on_dev_is_found(tmp_path: Path) -> None:
    """The regression. A fix on `dev` for a PR merged into `dev` must read BROKE.

    HEAD is left on `main`, which is where the old walk started and found nothing.
    """
    repo, merged = _repo_with_dev(tmp_path)
    _commit(repo, TOUCHED, "fix: crash on empty payload", MERGED_AT + timedelta(days=2))
    repo.heads.main.checkout()

    result = scan(tmp_path, _pr(merged, "dev"))

    assert result.outcome is Outcome.BROKE
    assert result.exclusion is Exclusion.NONE
    assert result.is_consistent


def test_fix_on_main_does_not_count_for_a_dev_pr(tmp_path: Path) -> None:
    """The mirror image: a fix on a branch the PR did not merge into is not evidence.

    Without this, "walk some branch that has a fix" would pass the test above while
    still measuring the wrong history.
    """
    repo, merged = _repo_with_dev(tmp_path)
    repo.heads.main.checkout()
    _commit(repo, TOUCHED, "fix: crash on empty payload", MERGED_AT + timedelta(days=2))

    result = scan(tmp_path, _pr(merged, "dev"))

    assert result.outcome is Outcome.CLEAN
    assert result.exclusion is Exclusion.NONE


def test_deleted_base_branch_is_counted_not_defaulted(tmp_path: Path) -> None:
    """A base branch deleted after merge is an exclusion with a name, never a CLEAN."""
    repo, merged = _repo_with_dev(tmp_path)
    _commit(repo, TOUCHED, "fix: crash on empty payload", MERGED_AT + timedelta(days=2))
    repo.heads.main.checkout()

    result = scan(tmp_path, _pr(merged, "feature/gone"))

    assert result.outcome is Outcome.UNSCANNABLE
    assert result.exclusion is Exclusion.BASE_REF_MISSING
    assert result.is_consistent


def test_merge_unreachable_from_base_is_its_own_category(tmp_path: Path) -> None:
    """A merge commit that is not an ancestor of its base branch is a DIFFERENT fact
    from a missing branch, and agentops#811/#817/#818/#819 are all of this kind.

    Built with `checkout --orphan`, giving a commit with NO common ancestor with `dev` --
    which is how agentops presented. A branch merely forked from `dev` would not do: with
    the same tree, parent, message and timestamps git deduplicates it to the very SHA the
    branch already points at, and the commit is then trivially reachable.
    """
    repo, _ = _repo_with_dev(tmp_path)
    repo.git.checkout("--orphan", "rewritten")
    stranded = _commit(repo, TOUCHED, "feat: add handler on a rewritten history", MERGED_AT)
    repo.heads.main.checkout()

    # Confirms the FIXTURE, independently of the code under test: `git merge-base` exits
    # non-zero with no output when two commits share no ancestor at all.
    assert repo.git.merge_base(stranded, "dev", with_exceptions=False) == ""

    result = scan(tmp_path, _pr(stranded, "dev"))

    assert result.outcome is Outcome.UNSCANNABLE
    assert result.exclusion is Exclusion.MERGE_UNREACHABLE
    assert result.exclusion is not Exclusion.BASE_REF_MISSING
    assert result.is_consistent


def test_merge_on_base_separates_no_from_unknown(tmp_path: Path) -> None:
    """Three answers, because "not on the branch" and "we could not check" differ.

    `reachable` returns one False for both, which is right for the scan -- either way the
    window cannot be walked -- and wrong for a prevalence count, where "no" describes the
    repository and "unknown" describes us. Recorded at admission, so it covers PRs the
    gate later rejects: every agentops case that exposed this was dropped at `no_python`
    before any scan ran.
    """
    repo, merged = _repo_with_dev(tmp_path)
    repo.heads.main.checkout()

    assert merge_on_base(tmp_path, merged, "dev") == "yes"
    assert merge_on_base(tmp_path, merged, "feature/gone") == "unknown"
    assert merge_on_base(tmp_path, "", "dev") == "unknown"

    repo.git.checkout("--orphan", "rewritten")
    stranded = _commit(repo, TOUCHED, "feat: handler on a rewritten history", MERGED_AT)
    repo.heads.main.checkout()

    assert merge_on_base(tmp_path, stranded, "dev") == "no"
