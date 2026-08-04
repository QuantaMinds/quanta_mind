"""Contract test for the call-site census.

WHAT: Asserts census.count_call_sites is unimplemented, and carries the Day 1
      specification table from RUNBOOK section 1.1 as executable data.
WHY:  A stub with no test is an intention; a stub with a contract test is a spec.
      EXPECTED_COUNTS below is the gate Day 1 has to satisfy -- it is written now,
      before any implementation exists, so the implementation cannot be fitted to
      whatever the counter happens to produce.
IMPORTS: phase0.census, pytest.
CONSUMED BY: `just test-phase0`; scripts/guard/check_assert_quality.py inspects it.
"""

from __future__ import annotations

import pytest

from phase0.census import count_call_sites

# RUNBOOK section 1.1. Day 1 flips these from "raises" to "equals".
EXPECTED_COUNTS: dict[str, tuple[str, int]] = {
    "direct_calls": ("foo(); bar()", 2),
    "method_calls": ("obj.method()", 1),
    "chained": ("a().b().c()", 3),
    "comprehension": ("[f(x) for x in y]", 1),
    "decorators": ("@dec\ndef f(): ...", 1),
    "excludes_builtins": ('"a".strip(); len(x)', 0),
    "super_is_counted": ("super().validate(r)", 1),
}


@pytest.mark.parametrize("case", sorted(EXPECTED_COUNTS))
def test_census_is_unimplemented(case: str) -> None:
    """Every specified case must fail loudly until Day 1 implements it."""
    source, _expected = EXPECTED_COUNTS[case]
    with pytest.raises(NotImplementedError):
        count_call_sites(source)


def test_builtin_exclusion_is_specified_as_zero() -> None:
    """The DyPyBench correction, pinned as data: builtins are 0, not 2.

    ~59% of the apparent static-vs-dynamic gap is builtin calls. Counting them
    deflates coverage into meaninglessness, so the spec says zero here and this
    assertion is what stops that being quietly relaxed later.
    """
    assert EXPECTED_COUNTS["excludes_builtins"][1] == 0


def test_super_is_counted_even_though_pycg_misses_it() -> None:
    """The denominator counts what the numerator cannot resolve. That is the point."""
    assert EXPECTED_COUNTS["super_is_counted"][1] == 1
