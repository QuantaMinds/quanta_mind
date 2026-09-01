"""The guard that catches work on `main` however it was made.

WHAT: `check_work_on_main` against real git repositories in every state that matters.
WHY:  **`hook_pre_edit.py` IS SCOPED TO `"matcher": "Write|Edit"` AND NEVER SEES `Bash`.** A
      heredoc, `sed -i` or `python -c` writes `main` with the hook none the wiser — which is not
      hypothetical: `CORRECTIONS.md` entry 14 was itself written onto `main` that way. A hook
      cannot enumerate every shell construction that writes a file; a guard looks at the result.

      **AND IT MUST BE SILENT ON A CLEAN `main`.** CI checks out the default branch after every
      merge. A guard that failed there would be switched off within a day, so that case is tested
      as hard as the failing one.
IMPORTS: scripts/guard/check_work_on_main.py (via sys.path); stdlib subprocess.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from check_work_on_main import check_work_on_main  # noqa: E402


def _repo(root: Path, branch: str) -> Path:
    """A real repository with a real `origin/main`, because the guard asks git, not a mock."""
    origin, work = root / "origin", root / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, timeout=30)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, timeout=30)
    for setting in (("user.email", "t@e.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(work), "config", *setting], check=True, timeout=30)
    (work / "a.txt").write_text("one\n", encoding="utf-8")
    for command in (
        ["git", "-C", str(work), "add", "-A"],
        ["git", "-C", str(work), "commit", "-qm", "one"],
        ["git", "-C", str(work), "branch", "-M", "main"],
        ["git", "-C", str(work), "push", "-q", "-u", "origin", "main"],
    ):
        subprocess.run(command, check=True, timeout=30)
    if branch != "main":
        subprocess.run(["git", "-C", str(work), "checkout", "-qb", branch], check=True, timeout=30)
    return work


def test_a_clean_main_matching_its_remote_is_silent(tmp_path: Path) -> None:
    """**CI CHECKS OUT `main` AFTER EVERY MERGE.** Firing here would get the guard turned off."""
    assert check_work_on_main(_repo(tmp_path, "main")) == []


def test_a_feature_branch_is_silent_however_dirty(tmp_path: Path) -> None:
    """The guard is about `main`, not about tidiness."""
    work = _repo(tmp_path, "feat/thing")
    (work / "a.txt").write_text("changed\n", encoding="utf-8")

    assert check_work_on_main(work) == []


def test_a_tracked_file_modified_on_main_is_reported_by_name(tmp_path: Path) -> None:
    """**NAMES THE ARTEFACT.** Not "work on main" — which file, spelled correctly.

    The first version sliced past `git status --porcelain`'s fixed-width prefix while the helper
    that ran it stripped whitespace, so ` M a.txt` arrived as `M a.txt` and the message said
    `.txt`. A truncated filename in a guard's own output is the guard telling you something false.
    """
    work = _repo(tmp_path, "main")
    (work / "a.txt").write_text("changed\n", encoding="utf-8")

    found = check_work_on_main(work)
    assert len(found) == 1
    assert found[0].rule == "uncommitted-on-main"
    assert "a.txt" in found[0].detail
    assert ".txt," not in found[0].detail, "the filename was truncated"


def test_an_untracked_scratch_file_on_main_is_not_reported(tmp_path: Path) -> None:
    """A scratch file is not a change to main, and refusing it would be noise."""
    work = _repo(tmp_path, "main")
    (work / "scratch.txt").write_text("notes\n", encoding="utf-8")

    assert check_work_on_main(work) == []


def test_a_commit_on_main_the_remote_lacks_is_reported_separately(tmp_path: Path) -> None:
    """**A DIFFERENT MISTAKE NEEDS A DIFFERENT REMEDY**, so it is not folded into the first."""
    work = _repo(tmp_path, "main")
    (work / "a.txt").write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "commit", "-qam", "direct"], check=True, timeout=30)

    found = check_work_on_main(work)
    assert [v.rule for v in found] == ["committed-to-main"]
    assert "1 commit(s)" in found[0].detail
    assert "git branch" in found[0].detail, "must say how to move it off main"


def test_both_are_reported_when_both_are_true(tmp_path: Path) -> None:
    """Committed once and still editing: two findings, because they are two problems."""
    work = _repo(tmp_path, "main")
    (work / "a.txt").write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "commit", "-qam", "direct"], check=True, timeout=30)
    (work / "a.txt").write_text("again\n", encoding="utf-8")

    assert {v.rule for v in check_work_on_main(work)} == {
        "uncommitted-on-main",
        "committed-to-main",
    }


def test_the_real_repository_is_not_reported_from_a_feature_branch() -> None:
    """**THE GUARD RUNS ON THE PRODUCT, NOT ONLY ON FIXTURES.**

    Silent here means silent because this branch is not `main`, which is the state the suite runs
    in; the failing states above are covered by real repositories built for them.
    """
    assert check_work_on_main(ROOT) == []
