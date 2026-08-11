"""A partial checkout must be a typed failure, never a smaller exposure denominator.

WHAT: Known-answer tests over a real git repository and a real worktree, with a `.py`
      file deleted from the tree to simulate a checkout that stopped partway.
WHY:  The failure this guards is silent by construction: an LFS smudge error ends the
      checkout at the first LFS object and everything after it is absent, so `measure`
      reads fewer files and reports a smaller denominator that looks like a repository
      holding less Python. Nothing errors.

      The decisive test is `test_a_complete_worktree_reports_nothing_missing`. A check
      that fired on every tree would also "catch" the partial one, and every exposure
      record would become a `checkout` failure -- caught, and useless. Both halves are
      asserted so the check is known to discriminate rather than merely to fire.
IMPORTS: GitPython, phase0.pipeline.{checkout,worktree}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Actor, Repo

from phase0.pipeline.checkout import CheckoutUnverifiable, missing_python
from phase0.pipeline.worktree import at_commit

AUTHOR = Actor("Fixture", "fixture@example.com")


def _repo(tmp_path: Path) -> tuple[Path, str]:
    """A clone holding three `.py` files and one that is not Python."""
    clone = tmp_path / "repo"
    clone.mkdir()
    repo = Repo.init(clone, initial_branch="main")
    for name, body in (
        ("assets/blob.bin", "not python\n"),
        ("acme/a.py", "def one() -> int:\n    return 1\n"),
        ("acme/b.py", "def two() -> int:\n    return 2\n"),
        ("zsrc/late.py", "def three() -> int:\n    return 3\n"),
    ):
        target = clone / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        repo.index.add([name])
    sha = repo.index.commit("chore: seed", author=AUTHOR, committer=AUTHOR).hexsha
    repo.close()
    return clone, sha


def test_a_complete_worktree_reports_nothing_missing(tmp_path: Path) -> None:
    """The half that makes the other half mean something.

    Without this, a check that flagged every tree would look like it worked and would
    turn every exposure record into a `checkout` failure.
    """
    clone, sha = _repo(tmp_path)
    with at_commit(clone, sha, "0") as tree:
        assert tree is not None
        assert missing_python(tree, clone, sha) == ()


def test_a_file_absent_from_the_tree_is_detected(tmp_path: Path) -> None:
    """Delete one `.py` from the worktree: exactly that path comes back."""
    clone, sha = _repo(tmp_path)
    with at_commit(clone, sha, "1") as tree:
        assert tree is not None
        (tree / "zsrc/late.py").unlink()
        assert missing_python(tree, clone, sha) == ("zsrc/late.py",)


def test_the_lfs_shape_is_caught_every_file_after_the_first_asset(tmp_path: Path) -> None:
    """The real failure: the checkout stops, so a whole tail is absent at once.

    `assets/` sorts before `acme/` and `zsrc/`, which is why an LFS asset early in the
    path order takes the Python with it. Simulated by removing everything after it.
    """
    clone, sha = _repo(tmp_path)
    with at_commit(clone, sha, "2") as tree:
        assert tree is not None
        for path in ("acme/a.py", "acme/b.py", "zsrc/late.py"):
            (tree / path).unlink()
        assert missing_python(tree, clone, sha) == ("acme/a.py", "acme/b.py", "zsrc/late.py")


def test_a_git_failure_raises_rather_than_reporting_completeness(tmp_path: Path) -> None:
    """ "We could not look" must not return the same value as "nothing is absent".

    `changed._git` returns `""` on failure, so reusing it here would have made an
    unreadable tree report an empty expected set and therefore nothing missing --
    identical to a complete checkout. This is why `checkout.py` calls git itself.
    """
    clone, sha = _repo(tmp_path)
    with at_commit(clone, sha, "3") as tree:
        assert tree is not None
        with pytest.raises(CheckoutUnverifiable) as raised:
            missing_python(tree, clone, "0" * 40)

    # The sha it could not read, so the message names the failure rather than implying
    # the tree was fine. Asserted on content because `pytest.raises` alone passes on any
    # CheckoutUnverifiable, including one raised for an unrelated reason.
    assert "0000000000" in str(raised.value)
    assert "failed" in str(raised.value)
