"""Who imports the changed file — and what an empty answer is allowed to mean.

WHAT: Builds a REAL git repository, commits real Python, and asks `parse/importers` who imports
      what. No fixtures of parsed output: the thing under test is whether it reads a tree correctly.
WHY:  **THE REVIEW'S "EFFECT ON CALLERS" SENTENCE RESTS ENTIRELY ON THIS.** If it over-matches, the
      comment tells a developer their change breaks a file it does not touch. If it under-matches,
      the comment says nothing depends on the code while something does — and that is the more
      expensive direction, because it reads as a clean bill of health.

      **A GREP WOULD PASS THE FIRST TEST HERE AND FAIL THE SECOND.** `gemini_helper` contains
      `gemini`, and a file mentioning the module in a comment or a string is not an importer. The
      shortlist is grep; the decision is a parse, and the second test is what holds that line.
IMPORTS: parse.importers, types.verdict.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.parse.importers import importers, module_of
from quantamind.types.verdict import Reason

GIT_TIMEOUT_S = 30


def _repo(root: Path, files: dict[str, str]) -> Path:
    """A real git repository with one commit. Real, because the subject reads git."""
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
        ["commit", "--quiet", "-m", "one"],
    ):
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, timeout=GIT_TIMEOUT_S, capture_output=True
        )
    return root


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/quantamind/infer/gemini.py", "quantamind.infer.gemini"),
        ("src/quantamind/infer/__init__.py", "quantamind.infer"),
        ("README.md", ""),
    ],
)
def test_a_path_maps_to_the_module_another_file_would_import(path: str, expected: str) -> None:
    assert module_of(path) == expected


def test_a_real_importer_is_found(tmp_path: Path) -> None:
    clone = _repo(
        tmp_path / "a",
        {
            "src/pkg/target.py": "def go() -> None:\n    pass\n",
            "src/pkg/user.py": "from pkg.target import go\n\n\ndef run() -> None:\n    go()\n",
            "src/pkg/other.py": "x = 1\n",
        },
    )

    found, unreadable = importers(clone, "HEAD", "src/pkg/target.py")

    assert found == ("src/pkg/user.py",), f"the importer was not found: {found}"
    assert unreadable == ()


def test_a_name_that_merely_contains_the_module_is_not_an_importer(tmp_path: Path) -> None:
    """**THE ONE A GREP FAILS.** `pkg.target_helper` contains `pkg.target`, and a mention in a
    comment or a string is not a dependency. Over-matching tells a developer their change breaks
    a file it never touches."""
    clone = _repo(
        tmp_path / "b",
        {
            "src/pkg/target.py": "def go() -> None:\n    pass\n",
            "src/pkg/target_helper.py": "def helper() -> None:\n    pass\n",
            "src/pkg/looks_close.py": (
                "# this file talks about pkg.target in a comment\n"
                'NOTE = "pkg.target is mentioned here as a string"\n'
                "from pkg.target_helper import helper\n"
            ),
        },
    )

    found, _ = importers(clone, "HEAD", "src/pkg/target.py")

    assert found == (), (
        f"a comment, a string and a longer module name were counted as imports: {found}. "
        "The grep is a shortlist; the parse is the decision"
    )


def test_a_file_that_will_not_parse_is_reported_not_skipped(tmp_path: Path) -> None:
    """A syntax error is not the absence of a dependency, and must not read as one."""
    clone = _repo(
        tmp_path / "c",
        {
            "src/pkg/target.py": "def go() -> None:\n    pass\n",
            "src/pkg/broken.py": "from pkg.target import go\ndef oops(:\n",
        },
    )

    found, unreadable = importers(clone, "HEAD", "src/pkg/target.py")

    assert found == (), "a file that will not parse cannot be confirmed as an importer"
    assert len(unreadable) == 1, (
        "the unparseable file vanished. An empty result would then mean both 'nothing imports "
        "this' and 'we could not tell', which is the silence this product refuses"
    )
    assert unreadable[0].reason is Reason.UNPARSEABLE_SYNTAX
    assert unreadable[0].site.path == "src/pkg/broken.py"


def test_the_changed_file_is_not_its_own_importer(tmp_path: Path) -> None:
    clone = _repo(tmp_path / "d", {"src/pkg/target.py": "import pkg.target\n"})

    found, _ = importers(clone, "HEAD", "src/pkg/target.py")

    assert found == ()


# **`MAX_CANDIDATES` BOUNDS A `git grep` THAT CAN MATCH THOUSANDS OF FILES**, and it was freely
# mutable with every tier green. At 0 no candidate is ever considered and every import resolves
# to nothing, which reads as "this file has no importers" rather than as a bounded search. Two
# hundred is written out; `MAX_CANDIDATES + 1` reads the value under test.

CANDIDATE_CAP = 200


def test_the_candidate_cap_is_two_hundred() -> None:
    from quantamind.parse.importers import MAX_CANDIDATES

    assert MAX_CANDIDATES == CANDIDATE_CAP


def test_a_grep_matching_more_files_than_the_cap_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five hundred matches come back as two hundred, not as five hundred and not as none."""
    from quantamind.parse import importers as module

    hits = "\n".join(f"abc123:src/f{n:04d}.py" for n in range(500))
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=hits, stderr=""),
    )

    assert (
        len(module._candidates(Path("/clone"), "abc123", "quantamind.rank.order")) == CANDIDATE_CAP
    )


def test_a_grep_matching_fewer_files_returns_them_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """The false-positive direction: a bound that truncated an ordinary result would hide files."""
    from quantamind.parse import importers as module

    hits = "abc123:src/a.py\nabc123:src/b.py\n"
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=hits, stderr=""),
    )

    assert module._candidates(Path("/clone"), "abc123", "quantamind.rank.order") == [
        "src/a.py",
        "src/b.py",
    ]
