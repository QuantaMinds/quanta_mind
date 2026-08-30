"""Verification that a repository with no tests reads as zero reach, and an empty clone raises.

WHAT: Drives `parse/suite_reach.reach` over real trees — a library with tests, one without, a
      tree of documentation examples, and a checkout that produced no Python at all.
WHY:  **A ZERO OVER A REAL SUITE AND A ZERO OVER NO SUITE ARE DIFFERENT ANSWERS.** The research
      twin learned this the expensive way: `django-rest-framework` reported 0% of 76 because
      `git-lfs` was absent and the checkout left an empty working tree while `git clone` exited 0
      and `git ls-tree HEAD` still listed 154 Python files. A share of zero described the read,
      not the repository. `NoSource` raises on that; a repository with code and genuinely no
      tests returns a real zero and says so in words.

      **IT COUNTS IMPORTS, NOT MENTIONS.** Measured across nineteen repositories, matching names
      as text over-reported by 12 to 43 points: `__init__` matches in any test mentioning a
      dunder, short stems collide — sphinx's `ru` and `it` are LOCALE files — and documentation
      examples were counted as source, which took `typer` to a 98% that was 91% tutorial snippets.
      Each of those three is a case below.
IMPORTS: pytest, quantamind.parse.suite_reach.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.parse.suite_reach import NoSource, reach

MENTION = "thing = 'a local named thing'\n\n\ndef test_it():\n    assert thing\n"
TEST = "from pkg.thing import x\n\n\ndef test_x():\n    assert x == 1\n"
"""One test that imports one module. Written once so the cases below stay readable."""


def _tree(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return root


def test_a_module_a_test_imports_is_reached(tmp_path: Path) -> None:
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/thing.py": "x = 1\n",
                "tests/test_thing.py": TEST,
            },
        )
    )

    assert (found.modules, found.reached) == (1, 1)
    assert found.share == 1.0
    assert "1 of 1" in found.sentence()


def test_a_module_only_MENTIONED_is_not_reached(tmp_path: Path) -> None:
    """The 12-to-43-point error. `thing` appears in the test and is never imported."""
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/thing.py": "x = 1\n",
                "tests/test_other.py": MENTION,
            },
        )
    )

    assert found.reached == 0
    assert found.modules == 1


def test_dunder_modules_are_not_counted(tmp_path: Path) -> None:
    """`__init__` is in every package; counting it marks every package as reached."""
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/__init__.py": "",
                "pkg/thing.py": "x = 1\n",
                "tests/test_thing.py": TEST,
            },
        )
    )

    assert found.modules == 1, "the package's __init__ was counted as a module"


def test_documentation_examples_are_not_source(tmp_path: Path) -> None:
    """typer read 98% and 91% of that source was `docs_src/tutorial/...` snippets."""
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/thing.py": "x = 1\n",
                "docs_src/tutorial/tutorial001.py": "print('hello')\n",
                "examples/demo.py": "print('demo')\n",
                "tests/test_thing.py": TEST,
            },
        )
    )

    assert found.modules == 1, "documentation was counted as library source"
    assert found.share == 1.0


def test_a_repository_with_no_tests_reads_zero_and_says_so(tmp_path: Path) -> None:
    """A real answer about a real repository, and a prospect deserves to be told it."""
    found = reach(_tree(tmp_path, {"pkg/thing.py": "x = 1\n", "pkg/other.py": "y = 2\n"}))

    assert found.has_suite is False
    assert found.share == 0.0
    assert "no test file found" in found.sentence()


def test_a_tree_with_no_python_raises_rather_than_reading_zero(tmp_path: Path) -> None:
    """The git-lfs case: `git clone` exits 0 and leaves an empty working tree."""
    _tree(tmp_path, {"README.md": "# nothing here\n"})

    with pytest.raises(NoSource, match="no Python file"):
        reach(tmp_path)


def test_vendored_directories_are_ignored(tmp_path: Path) -> None:
    """A vendored dependency is not this repository's source, and its tests are not its suite."""
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/thing.py": "x = 1\n",
                ".venv/lib/site-packages/other/mod.py": "z = 3\n",
                "node_modules/x/y.py": "w = 4\n",
                "tests/test_thing.py": TEST,
            },
        )
    )

    assert found.modules == 1


def test_the_sentence_always_carries_its_denominator(tmp_path: Path) -> None:
    """A bare percentage is a number nobody can check."""
    found = reach(
        _tree(
            tmp_path,
            {
                "pkg/a.py": "",
                "pkg/b.py": "",
                "pkg/c.py": "",
                "tests/test_a.py": "from pkg.a import thing\n\n\ndef test_a():\n    assert thing\n",
            },
        )
    )

    assert "1 of 3" in found.sentence()
