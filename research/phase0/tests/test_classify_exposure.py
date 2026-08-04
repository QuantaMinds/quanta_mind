"""Verification of the exposure variable and amendment A6's restriction.

WHAT: Asserts the arms are distinct, that single-site pairs are measured exactly,
      that multi-site pairs are held out of the primary table and bounded instead,
      and that a syntax failure never reaches an arm.
WHY:  The join is the most failure-prone code in the study, and its failures are
      silent. Two of these tests exist because the drafted algorithm was wrong:

      test_multi_site_pair_is_held_out_of_the_primary_table would have caught it.
      PyCG emits a SET of callees per caller, so a function calling S directly and
      through getattr yields one edge and the drafted `S in edges[F]` marked BOTH
      sites resolved. The bias ran toward UNEXPOSED, toward RR ~ 1, and therefore
      toward the stop rule -- an artefact that could have killed a live thesis.

      test_package_prefix_drift_still_matches exists because PyCG names the same
      function two ways: `sub.deep.helper_fn` at its definition and
      `acme.sub.deep.helper_fn` where an import resolved it. Verified by running
      it. Strict equality would mark nested-package callers unresolved wholesale.
IMPORTS: phase0.classify_exposure, phase0.census, phase0.pycg_failure, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import pytest

from phase0.census import CallSite
from phase0.classify_exposure import Cardinality, Exposure, classify
from phase0.pycg_failure import GraphStatus


def _site(caller: str, name: str, line: int = 1) -> CallSite:
    return CallSite(
        path="m.py",
        line=line,
        column=0,
        callee_text=name,
        callee_name=name,
        enclosing=caller,
        is_builtin=False,
    )


def test_three_arms_not_two() -> None:
    """UNANALYZED_RESOURCE is a real arm. Merging it changes the conclusion."""
    assert {e.value for e in Exposure} == {"exposed", "unexposed", "unanalyzed_resource"}


def test_resolved_single_site_is_unexposed() -> None:
    """One site, and PyCG emitted the edge: measurable exactly, and resolved."""
    result = classify(
        "m.target",
        "target",
        [_site("m.caller", "target")],
        {"m.caller": {"m.target"}},
        GraphStatus.OK,
    )
    assert result.primary is Exposure.UNEXPOSED


def test_unresolved_single_site_is_exposed() -> None:
    """One site and no edge. This is the whole thesis, in one assertion."""
    result = classify(
        "m.target",
        "target",
        [_site("m.caller", "target")],
        {"m.caller": {"<builtin>.super"}},
        GraphStatus.OK,
    )
    assert result.primary is Exposure.EXPOSED


def test_multi_site_pair_is_held_out_of_the_primary_table() -> None:
    """A6. The test that would have caught the drafted algorithm.

    One caller, two sites, one edge. PyCG cannot say which site the edge came
    from, so the pair is not measurable and must not enter the primary table.
    """
    sites = [_site("m.caller", "target", 1), _site("m.caller", "target", 2)]
    result = classify("m.target", "target", sites, {"m.caller": {"m.target"}}, GraphStatus.OK)
    assert (result.primary, result.multi_site_pairs, result.single_site_pairs) == (None, 1, 0)


def test_multi_site_pair_is_bounded_both_ways() -> None:
    """A6's sensitivity analysis: coded UNEXPOSED and EXPOSED, reported as bounds."""
    sites = [_site("m.caller", "target", 1), _site("m.caller", "target", 2)]
    result = classify("m.target", "target", sites, {"m.caller": {"m.target"}}, GraphStatus.OK)
    assert (result.sensitivity_low, result.sensitivity_high) == (
        Exposure.UNEXPOSED,
        Exposure.EXPOSED,
    )


def test_bounds_agree_when_a_single_site_already_settles_it() -> None:
    """When both bounds match, the collapse provably changed no conclusion."""
    sites = [_site("m.a", "target"), _site("m.b", "target", 2), _site("m.b", "target", 3)]
    result = classify("m.target", "target", sites, {}, GraphStatus.OK)
    assert result.bounds_agree is True


def test_package_prefix_drift_still_matches() -> None:
    """PyCG's two names for one function must not read as two functions.

    Definition site says `sub.deep.helper_fn`; the edge says
    `acme.sub.deep.helper_fn`. Strict equality would call this unresolved.
    """
    result = classify(
        "sub.deep.helper_fn",
        "helper_fn",
        [_site("handlers.Base.validate", "helper_fn")],
        {"handlers.Base.validate": {"acme.sub.deep.helper_fn"}},
        GraphStatus.OK,
    )
    assert result.primary is Exposure.UNEXPOSED


def test_similar_names_do_not_match_across_a_dot_boundary() -> None:
    """Leniency stops at the dot: `revalidate` is not `validate`."""
    result = classify(
        "m.validate",
        "validate",
        [_site("m.caller", "validate")],
        {"m.caller": {"m.revalidate"}},
        GraphStatus.OK,
    )
    assert result.primary is Exposure.EXPOSED


def test_builtin_sites_never_reach_an_arm() -> None:
    """Builtins are out of both numerator and denominator."""
    builtin = CallSite("m.py", 1, 0, "len", "len", "m.caller", is_builtin=True)
    result = classify("m.len", "len", [builtin], {}, GraphStatus.OK)
    assert (result.primary, result.single_site_pairs) == (None, 0)


def test_resource_exhaustion_is_its_own_arm() -> None:
    """A timeout is not evidence of dynamism, and not evidence of resolution."""
    result = classify("m.target", "target", [], {}, GraphStatus.TIMEOUT)
    assert result.primary is Exposure.UNANALYZED_RESOURCE


def test_syntax_failure_is_refused_rather_than_classified() -> None:
    """A7. Attrition has no arm, so classifying it must fail loudly, not silently."""
    with pytest.raises(ValueError, match="attrition"):
        classify("m.target", "target", [], {}, GraphStatus.SYNTAX_UNSUPPORTED)


def test_cardinality_reports_measurability() -> None:
    """The tag that drives the primary/sensitivity split is derived, not passed in."""
    assert {c.value for c in Cardinality} == {"single", "multi"}
