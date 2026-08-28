"""The standards a team already wrote down, read from git at the commit under review.

WHAT: Builds real repositories and asks `ingest/conventions.written()` what they document.
WHY:  **A TEAM THAT WROTE ITS RULES DOWN SHOULD NOT HAVE TO WRITE THEM AGAIN FOR US.** Most
      repositories already carry `AGENTS.md`, `CLAUDE.md` or `CONTRIBUTING.md`, and those are the
      standards the team actually agreed to. Asking them to restate the same rules in
      `.quantamind/rules.toml` creates two documents that drift.

      **THE CLONE HAS NO WORKING TREE**, so this reads git — the same trap `rules_file` fell into,
      where a filesystem read returned "nothing declared" for every repository on earth. The
      fixture clones `--no-checkout` and asserts the tree is absent before reading, so it cannot
      quietly stop testing that.

      **AND THE CAP MUST BE VISIBLE.** A truncated document that did not say so would let a review
      claim it considered a convention it never read.
IMPORTS: ingest.conventions.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.ingest.standards.conventions import MAX_CHARS, TRUNCATED, written

GIT_TIMEOUT_S = 30


def _repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for args in (
        ["init", "--quiet", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "--quiet", "-m", "conventions"],
    ):
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )
    return root


def test_the_documents_a_team_keeps_are_found_in_order(tmp_path: Path) -> None:
    clone = _repo(
        tmp_path / "a",
        {
            "CONTRIBUTING.md": "Open an issue first.\n",
            "AGENTS.md": "Never use a bare except.\n",
            "README.md": "not a convention document\n",
        },
    )

    found = written(clone, "HEAD")

    assert [name for name, _ in found] == ["AGENTS.md", "CONTRIBUTING.md"], (
        f"wrong documents or wrong order: {[n for n, _ in found]}. An agent-instruction file is "
        "the most direct statement of how code is written here; a contributing guide is process"
    )
    assert "bare except" in dict(found)["AGENTS.md"]


def test_a_repository_with_no_conventions_yields_nothing(tmp_path: Path) -> None:
    clone = _repo(tmp_path / "b", {"README.md": "hello\n"})

    assert written(clone, "HEAD") == ()


def test_an_empty_convention_file_is_not_a_convention(tmp_path: Path) -> None:
    """A blank AGENTS.md would put an empty block in the prompt claiming to be standards."""
    clone = _repo(tmp_path / "c", {"AGENTS.md": "   \n\n"})

    assert written(clone, "HEAD") == ()


def test_a_long_document_is_truncated_and_says_so(tmp_path: Path) -> None:
    """**A SILENT TRUNCATION LETS A REVIEW CLAIM IT READ A CONVENTION IT NEVER SAW.**"""
    clone = _repo(tmp_path / "d", {"AGENTS.md": "rule\n" * (MAX_CHARS // 2)})

    ((_, text),) = written(clone, "HEAD")

    assert text.endswith(TRUNCATED), "the document was cut without saying it had been"
    assert len(text) <= MAX_CHARS + len(TRUNCATED)


def test_they_are_read_from_git_not_from_a_working_tree(tmp_path: Path) -> None:
    """The production clone is `--no-checkout`; a filesystem read finds nothing, forever."""
    origin = _repo(tmp_path / "origin", {"AGENTS.md": "One rule.\n"})
    clone = tmp_path / "no-tree"
    subprocess.run(
        ["git", "clone", "--no-checkout", "--quiet", str(origin), str(clone)],
        check=True,
        capture_output=True,
        timeout=60,
    )

    assert not (clone / "AGENTS.md").exists(), "the fixture must have no working tree"

    assert [name for name, _ in written(clone, "HEAD")] == ["AGENTS.md"]


def test_a_clone_git_cannot_read_yields_nothing_rather_than_raising(tmp_path: Path) -> None:
    """Conventions are context. A review without them is weaker; one that DIED for them is worse."""
    not_a_repo = tmp_path / "nope"
    not_a_repo.mkdir()

    assert written(not_a_repo, "HEAD") == ()
