"""Verification of the call-site census against the pre-registered table.

WHAT: Runs census.count_call_sites over RUNBOOK section 1.1's specification table
      and asserts the exact counts, plus the hand-counted fixture gate.
WHY:  The denominator is the number everything else divides by. An off-by-N here
      is invisible in every downstream figure -- coverage, exposure rate, and the
      relative risk itself all shift by a constant nobody can see. RUNBOOK section
      1.1 therefore gates on an *exact* match, not an approximate one.

      EXPECTED_COUNTS was written before the implementation existed, so the
      implementation is fitted to the specification rather than the reverse.
IMPORTS: phase0.census, pytest.
CONSUMED BY: `just test-phase0`; scripts/guard/check_assert_quality.py inspects it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.census import count_call_sites, non_builtin

# RUNBOOK section 1.1, verbatim. Values are NON-BUILTIN call sites.
EXPECTED_COUNTS: dict[str, tuple[str, int]] = {
    "direct_calls": ("foo(); bar()", 2),
    "method_calls": ("obj.method()", 1),
    "chained": ("a().b().c()", 3),
    "comprehension": ("[f(x) for x in y]", 1),
    "decorators": ("@dec\ndef f(): ...", 1),
    "excludes_builtins": ('"a".strip(); len(x)', 0),
    "super_is_counted": ("super().validate(r)", 1),
}


def _count(source: str) -> int:
    return len(non_builtin(count_call_sites(source)))


@pytest.mark.parametrize("case", sorted(EXPECTED_COUNTS))
def test_census_matches_the_specification(case: str) -> None:
    """Every pre-registered case counts exactly, not approximately."""
    source, expected = EXPECTED_COUNTS[case]
    assert _count(source) == expected


def test_builtin_exclusion_is_specified_as_zero() -> None:
    """The DyPyBench correction, pinned as data: builtins are 0, not 2.

    ~59% of the apparent static-vs-dynamic gap is builtin calls. Counting them
    deflates coverage into meaninglessness, so the spec says zero here and this
    assertion is what stops it being quietly relaxed later.
    """
    assert EXPECTED_COUNTS["excludes_builtins"][1] == 0


def test_super_is_counted_even_though_pycg_misses_it() -> None:
    """The denominator counts what the numerator cannot resolve. That is the point.

    `super().validate(r)` is two syntactic calls. `super()` is a builtin and drops
    out; `validate` remains and is exactly the edge PyCG never emits.
    """
    assert EXPECTED_COUNTS["super_is_counted"][1] == 1


def test_computed_callee_has_no_static_name_but_is_still_counted() -> None:
    """`getattr(m, n)()` has no resolvable name and must still reach the denominator.

    This is the switchboard from README.md. A census that skipped it would hide
    exactly the sites the product exists to surface.
    """
    sites = non_builtin(count_call_sites("getattr(mod, cfg['h'])()"))
    assert [s.callee_name for s in sites] == [""]


def test_enclosing_name_is_pycg_shaped() -> None:
    """The join in classify_exposure.py can only match through the enclosing FQN."""
    source = "class A:\n    def m(self):\n        target()\n"
    sites = non_builtin(count_call_sites(source, module="mod"))
    assert [(s.callee_name, s.enclosing) for s in sites] == [("target", "mod.A.m")]


def test_line_numbers_are_one_based() -> None:
    """Off-by-one here would misattribute every site to the wrong function."""
    sites = non_builtin(count_call_sites("x = 1\nfoo()\n"))
    assert [s.line for s in sites] == [2]


def test_hand_counted_fixture_matches_exactly() -> None:
    """RUNBOOK section 1.1's gate: an independently counted file, exact match.

    The count in HAND_COUNT was established by reading the fixture, not by running
    the census over it. Approximate agreement is a failure, not a pass.
    """
    fixture = Path(__file__).parent / "fixtures" / "hand_counted.py"
    expected = int((fixture.parent / "hand_counted.expected").read_text().strip())
    assert _count(fixture.read_text(encoding="utf-8")) == expected
