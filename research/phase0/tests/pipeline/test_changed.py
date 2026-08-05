"""Verification that changed files and symbols come from the tree, not the corpus.

WHAT: Pins file extraction, line-range extraction and symbol attribution against a real
      git diff on a real repository.
WHY:  A24 measured the corpus attributing 92 distinct `.py` files to a pull request that
      changed two. Everything downstream keys off the file set, so it has to be derived
      from `git diff parent..merged` and that derivation has to be pinned.

      Symbol attribution is parsed at the PARENT on purpose: the exposure variable asks
      what a caller could have known before the change landed, so a symbol the PR
      introduces has no pre-existing callers and must not appear.
IMPORTS: phase0.pipeline.changed.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0.pipeline.changed import (
    changed_python_files,
    file_agreement,
    module_name,
    source_at,
    symbols_touched,
    touched_line_ranges,
)


def test_changed_files_come_from_the_tree(repo: tuple[Path, str, str]) -> None:
    root, parent, child = repo
    assert changed_python_files(root, parent, child) == ("pkg/added.py", "pkg/mod.py")


def test_only_the_symbol_whose_body_changed_is_reported(
    repo: tuple[Path, str, str], parent_source: str
) -> None:
    """One line inside `Handler.validate` changed; the other two functions did not."""
    root, parent, child = repo
    ranges = touched_line_ranges(root, parent, child, "pkg/mod.py")
    assert symbols_touched(parent_source, ranges, module_name("pkg/mod.py")) == {
        "pkg.mod.Handler.validate"
    }


def test_a_symbol_the_pr_added_is_not_reported(repo: tuple[Path, str, str]) -> None:
    """It has no pre-existing callers, so it is not what the exposure variable measures."""
    root, parent, child = repo
    ranges = touched_line_ranges(root, parent, child, "pkg/added.py")
    assert source_at(root, parent, "pkg/added.py") == ""
    assert symbols_touched("", ranges, "pkg.added") == set()


def test_source_at_returns_the_parent_revision(repo: tuple[Path, str, str]) -> None:
    root, parent, child = repo
    assert "request.strip().lower()" not in source_at(root, parent, "pkg/mod.py")
    assert "request.strip().lower()" in source_at(root, child, "pkg/mod.py")


def test_module_name_drops_the_package_initialiser() -> None:
    assert module_name("src/pkg/mod.py") == "src.pkg.mod"
    assert module_name("pkg/__init__.py") == "pkg"


def test_agreement_is_jaccard_not_coverage() -> None:
    """Coverage would score the zenml case 1.0: two files, both inside ninety-two."""
    two = frozenset({"a.py", "b.py"})
    inflated = two | frozenset(f"f{i}.py" for i in range(92))
    assert file_agreement(two, inflated) < 0.03
    assert file_agreement(two, two) == 1.0
    assert file_agreement(frozenset(), frozenset()) == 1.0
