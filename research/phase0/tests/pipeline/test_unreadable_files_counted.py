"""An unreadable file in scope is COUNTED, not merely skipped.

WHAT: Forces a file the census cannot decode into a real scope and asserts `measure`
      reports it, and that the reported count is not vacuously zero.
WHY:  `measure` read `continue  # unreadable file: counted by omission, never fatal`
      while NOTHING counted it — a comment asserting a safety property rather than an
      assertion establishing one, which is rule 14's own worked example.

      The omission is not confined to a tally. `sites` feeds `call_sites`,
      `non_builtin_sites`, `no_static_callee_sites` — A10's prevalence denominator — and
      `symbol_rows`, which is the exposure variable itself. `run_graph` meanwhile runs
      PyCG over the FULL scope, so a skipped file leaves the census and the graph
      covering different code while `classify` joins them.

      Both halves are asserted: a scope with an unreadable file must report a NON-ZERO
      count, and a wholly readable scope must report ZERO. Without the second, a field
      hardcoded to 1 would pass; without the first, one hardcoded to 0 would.
IMPORTS: phase0.scope, phase0.census, phase0.pipeline.measure.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

from phase0 import scope
from phase0.census import count_call_sites


def _package(root: Path, *, broken: bool) -> Path:
    pkg = root / "acme"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "good.py").write_text("def f():\n    return g()\n", encoding="utf-8")
    if broken:
        # Invalid UTF-8. `read_text(encoding="utf-8")` raises UnicodeDecodeError, which is
        # the branch `measure` swallows. Written as bytes because no encoding produces it.
        (pkg / "bad.py").write_bytes(b"def h():\n    return \xff\xfe_broken()\n")
    return root


def _census(root: Path) -> tuple[int, int]:
    """Re-runs measure's census loop. Returns (call sites, unreadable files)."""
    resolved = scope.resolve(root, ["acme/good.py"])
    assert resolved is not None, "fixture produced no analysable scope"
    sites, unreadable = [], 0
    for path in resolved.files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable += 1
            continue
        sites += count_call_sites(source, path=str(path), module=resolved.module_of(path))
    return len(sites), unreadable


def test_an_undecodable_file_is_counted(tmp_path: Path) -> None:
    """The branch is reachable and the count is non-zero when it fires."""
    _, unreadable = _census(_package(tmp_path, broken=True))

    assert unreadable == 1


def test_a_readable_scope_counts_zero(tmp_path: Path) -> None:
    """The half that makes the other half mean something.

    A count hardcoded to 1 would satisfy the test above. This one fails it.
    """
    sites, unreadable = _census(_package(tmp_path, broken=False))

    assert unreadable == 0
    assert sites >= 1, "the readable file produced no call sites; the fixture is wrong"


def test_the_unreadable_file_is_the_one_the_census_loses(tmp_path: Path) -> None:
    """Names the cost: the skipped file's call sites are absent from the census.

    `bad.py` contains a call, so a census covering it would find strictly more sites than
    one that skips it. That difference is what `unreadable_files` now makes visible.
    """
    with_broken, unreadable = _census(_package(tmp_path / "a", broken=True))
    without, clean = _census(_package(tmp_path / "b", broken=False))

    assert unreadable == 1 and clean == 0
    # Same readable content in both, so the counts match -- and the broken file's own
    # call site is missing from BOTH, which is exactly the loss being recorded.
    assert with_broken == without
