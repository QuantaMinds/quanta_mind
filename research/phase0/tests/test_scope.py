"""Verification of the shared file set — amendment A3.

WHAT: Asserts that scope.resolve produces one file set, that it is deterministic,
      and that it returns None rather than an empty scope when a PR touches no
      analysable Python.
WHY:  A3 exists because the census and PyCG must see identical files. If the
      census walks wider, every out-of-scope call site has no possible edge, reads
      as unresolved, and exposure inflates toward 100% — which RUNBOOK section 6
      Q4 lists as a stop condition without naming this as the cause. The guarantee
      is only real if one function owns it, so these tests assert that it does.
IMPORTS: phase0.scope, pytest, tmp_path.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

from phase0 import scope


def _make_package(root: Path) -> Path:
    pkg = root / "acme"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "handlers.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (pkg / "sub" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sub" / "deep.py").write_text("def b():\n    pass\n", encoding="utf-8")
    return pkg


def test_scope_covers_the_whole_package_not_just_changed_files(tmp_path: Path) -> None:
    """Callers live anywhere in the package, so the scope cannot be the diff."""
    _make_package(tmp_path)
    resolved = scope.resolve(tmp_path, ["acme/handlers.py"])
    assert resolved is not None
    names = sorted(p.name for p in resolved.files)
    assert names == ["__init__.py", "__init__.py", "deep.py", "handlers.py"]


def test_file_order_is_deterministic(tmp_path: Path) -> None:
    """The file list is passed to PyCG on the command line; unstable order would
    make re-runs differ for no reason, and RUNBOOK section 5 requires reproducibility."""
    _make_package(tmp_path)
    first = scope.resolve(tmp_path, ["acme/handlers.py"])
    second = scope.resolve(tmp_path, ["acme/handlers.py"])
    assert first is not None and second is not None
    assert first.files == second.files


def test_non_source_directories_are_excluded(tmp_path: Path) -> None:
    """A vendored copy would be counted in the denominator and never resolved."""
    pkg = _make_package(tmp_path)
    vendored = pkg / "vendor"
    vendored.mkdir()
    (vendored / "third.py").write_text("def c():\n    pass\n", encoding="utf-8")
    resolved = scope.resolve(tmp_path, ["acme/handlers.py"])
    assert resolved is not None
    assert [p for p in resolved.files if "vendor" in p.parts] == []


def test_unanalysable_changes_yield_no_scope(tmp_path: Path) -> None:
    """Every way a PR can have nothing to analyse returns None, not an empty scope.

    Each of these is corpus attrition and is counted as such. An empty Scope would
    flow downstream and be indistinguishable from a package with no call sites,
    which would quietly enter the denominator as a zero.
    """
    _make_package(tmp_path)
    results = {
        "docs only": scope.resolve(tmp_path, ["README.md", "docs/guide.rst"]),
        "deleted before parent": scope.resolve(tmp_path, ["acme/never_existed.py"]),
        "no files at all": scope.resolve(tmp_path, []),
    }
    assert results == {
        "docs only": None,
        "deleted before parent": None,
        "no files at all": None,
    }


def test_package_root_is_the_outermost_package(tmp_path: Path) -> None:
    """PyCG's --package sets how module names are resolved, so it decides every FQN.

    Choosing an inner directory does not fail loudly — it silently renames every
    symbol in the graph, and the join in classify_exposure.py then matches nothing.
    """
    _make_package(tmp_path)
    resolved = scope.resolve(tmp_path, ["acme/sub/deep.py"])
    assert resolved is not None
    assert resolved.package_root.name == "acme"
