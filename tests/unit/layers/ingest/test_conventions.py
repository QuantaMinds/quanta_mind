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


def test_the_last_rule_survives_a_long_document(tmp_path: Path) -> None:
    """**A CHARACTER CAP DROPS RULES 9 THROUGH 15, AND NOBODY SEES WHICH HALF WAS APPLIED.**

    Truncating at 6,000 characters cut this repository's own AGENTS.md mid-list. Keeping the
    rule-shaped lines and discarding the argument between them fits several times as many actual
    rules in the same budget: 12,583 characters of prose became 4,436 of rules, and the last rule
    survived where truncation had removed it.
    """
    padding = "This paragraph explains why the rule exists and is not itself a rule. " * 30
    doc = "\n\n".join(f"{n}. rule number {n}\n\n{padding}" for n in range(1, 16))
    clone = _repo(tmp_path / "d", {"AGENTS.md": doc})

    ((_, text),) = written(clone, "HEAD")

    assert "rule number 15" in text, (
        "the LAST rule was dropped. A review that enforces the first half of a standard and "
        "reports it as the standard is worse than one that read none of it"
    )
    assert "This paragraph explains" not in text, "the argument was kept instead of the rules"


def test_prose_with_no_rule_lines_is_still_bounded_and_says_so(tmp_path: Path) -> None:
    """Nothing rule-shaped to keep, so it falls back to the cap — with the marker."""
    clone = _repo(tmp_path / "e", {"AGENTS.md": "word " * (MAX_CHARS // 2)})

    ((_, text),) = written(clone, "HEAD")

    assert text.endswith(TRUNCATED), "the document was cut without saying it had been"
    assert len(text) <= MAX_CHARS + len(TRUNCATED)


def test_an_uncommitted_local_document_is_read_and_labelled(tmp_path: Path) -> None:
    """**A RULE ON ONE LAPTOP BINDS NOBODY ELSE.**

    A developer running this on their own checkout may keep a gitignored CLAUDE.md, and on that
    machine it is a real standard. It is read, and its name says it is uncommitted, because a
    review presenting it as the team's standard would be inventing consensus. The endpoint never
    sees one: its clones have no working tree.
    """
    clone = _repo(tmp_path / "f", {"AGENTS.md": "- one\n- two\n- three\n"})
    (clone / "CLAUDE.md").write_text("- local one\n- local two\n- local three\n", encoding="utf-8")

    names = [name for name, _ in written(clone, "HEAD")]

    assert names == ["AGENTS.md", "CLAUDE.md (uncommitted)"], (
        f"an uncommitted local convention was lost or unlabelled: {names}"
    )


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
