"""Call-site census: the coverage denominator.

WHAT: A tree-sitter pass counting every call site in a source file, including the
      ones no resolver can handle. Builtins are excluded.
WHY:  This is the number everything else divides by, and no upstream graph tool
      emits it -- they emit edges. Get it wrong and every downstream result is
      wrong by a constant nobody can see, which is why RUNBOOK section 1.1 gates
      on an *exact* match against a hand-counted 200-line file rather than an
      approximate one.

      Builtins are excluded because DyPyBench found `"abc".strip()`-class calls
      are ~59% of the apparent static-vs-dynamic gap. Counting them makes coverage
      look catastrophic and tells a developer nothing.

      Counting must never mix with resolving. If it does, the denominator quietly
      shrinks and coverage inflates -- the one bug that would make this look solved
      while being exactly wrong.
IMPORTS: tree_sitter, tree_sitter_python, tree_sitter_typescript. No graph tool.
CONSUMED BY: run_pipeline.py, classify_exposure.py; tests/test_census.py.
"""

from __future__ import annotations

from dataclasses import dataclass

# RUNBOOK section 7: the exclusion list differs per arm.
PYTHON_BUILTINS: frozenset[str] = frozenset({"len", "super", "print", "isinstance", "range"})
TS_BUILTIN_PREFIXES: tuple[str, ...] = ("Array.prototype.", "Object.", "console.")


@dataclass(frozen=True, slots=True)
class CallSite:
    """One syntactic call, resolved or not."""

    path: str
    line: int
    column: int
    callee_text: str  # verbatim source, e.g. 'getattr(mod, cfg["handler"])'
    is_builtin: bool


def count_call_sites(source: str, language: str = "python") -> list[CallSite]:
    """Enumerate every call site in one file.

    Counts, and only counts. Resolution is run_graph.py's job.

    Raises:
        NotImplementedError: Day 1 of the run. See RUNBOOK section 1.1.
    """
    raise NotImplementedError("Phase 0 Day 1 — see docs/findings/PHASE0_RUNBOOK.md")
