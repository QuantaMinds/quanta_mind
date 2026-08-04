"""Property tier: the declared layer order is well-formed and recoverable.

WHAT: Hypothesis properties over discovery.LAYER_ORDER and discovery.layer_of --
      the declaration that scripts/guard/check_conventions.py enforces imports
      against.
WHY:  This is the seed of invariant 4 in ARCHITECTURE.md section 6 ("the layer
      import graph is a DAG with the declared topological order"). The full
      invariant needs a Pack, which does not exist before the call-site census layer; what is
      checkable today is that the declaration itself is coherent and that
      layer_of round-trips against it. A layering guard built on a declaration
      with a duplicate or an unrecoverable path would pass while enforcing the
      wrong order -- silent failure, which is the thing this repository exists to
      eliminate.
IMPORTS: discovery (via tests/conftest.py), hypothesis. Tier 2, no mocks.
CONSUMED BY: justfile (`just test-property`), .github/workflows/ci.yml.
"""

from __future__ import annotations

from pathlib import Path

from discovery import LAYER_ORDER, layer_of
from hypothesis import given
from hypothesis import strategies as st

PACKAGE_ROOT = Path("src") / "qmctx"

# Path components only -- no separators, no dots, nothing empty.
_NAMES = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    min_size=1,
    max_size=12,
)


def test_layer_order_has_no_duplicates() -> None:
    """A repeated layer makes the '<' comparison in check_conventions ambiguous."""
    assert len(set(LAYER_ORDER)) == len(LAYER_ORDER)


@given(layer=st.sampled_from(LAYER_ORDER), module=_NAMES, depth=st.integers(0, 3))
def test_layer_of_recovers_the_declared_layer(layer: str, module: str, depth: int) -> None:
    """Any file at any depth under a layer resolves back to that layer."""
    path = PACKAGE_ROOT.joinpath(layer, *["sub"] * depth, f"{module}.py")
    assert layer_of(path, PACKAGE_ROOT) == layer


@given(names=st.lists(_NAMES, min_size=1, max_size=6))
def test_layer_of_rejects_names_outside_the_declaration(names: list[str]) -> None:
    """Anything not declared a layer resolves to None, never to a neighbouring layer."""
    outside = [n for n in names if n not in LAYER_ORDER]
    results = {layer_of(PACKAGE_ROOT / n / "m.py", PACKAGE_ROOT) for n in outside}
    assert results <= {None}


@given(names=st.lists(_NAMES, min_size=1, max_size=4), module=_NAMES)
def test_paths_outside_the_package_have_no_layer(names: list[str], module: str) -> None:
    """A path that is not under src/qmctx/ is not a layer, whatever it is called.

    Asserted as a set equality rather than `is None` so the assertion carries a
    value -- check_assert_quality.py treats a lone `x is None` as a weak assert,
    and it is right to.
    """
    results = {layer_of(Path("scripts") / n / f"{module}.py", PACKAGE_ROOT) for n in names}
    assert results == {None}
