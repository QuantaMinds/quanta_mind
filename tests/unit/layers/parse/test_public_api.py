"""What counts as narrowing a module's public surface, and — harder — what does not.

WHAT: Drives `parse.public_api.surface()` and `broke()` over pairs of module sources.
WHY:  **THIS IS THE ONLY CLAIM IN THE COMMENT THAT IS ABOUT SOMEBODY ELSE'S REPOSITORY**, so a
      false positive costs more here than anywhere: the reader cannot check it without leaving
      their pull request. Every "must not fire" case below is worth more than the ones that fire.

      **ADDITIONS ARE NEVER BREAKS.** A new export, a new optional argument, a new module — all
      leave every existing caller working. A section firing on those fires on most pull requests
      and is read on none.

      **A REORDER IS A BREAK EVEN WHEN THE NAMES SURVIVE**, because positional callers exist and
      are invisible from here. `AGENTS.md` rule 3's reasoning: we cannot see the call sites, so we
      report the change rather than guessing nobody relied on it.
IMPORTS: quantamind.parse.public_api, quantamind.parse.python_names.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.parse.public_api import broke, surface
from quantamind.parse.python_names import UnparseableSource


def _breaks(before: str, after: str) -> list[str]:
    return [item.name for item in broke(surface(before), surface(after))]


def test_a_removed_export_is_a_break() -> None:
    assert _breaks("def send(a):\n    pass\n", "") == ["send"]


def test_a_private_name_is_not_part_of_the_surface() -> None:
    """A leading underscore is the only privacy Python has, and it is honoured."""
    assert _breaks("def _helper(a):\n    pass\n", "") == []


def test_dunder_all_overrides_the_underscore_convention() -> None:
    """A module that declares `__all__` has said what it offers, including an underscored name."""
    before = (
        '__all__ = ["_deliberate"]\n\n\ndef _deliberate():\n    pass\n\n\ndef public():\n    pass\n'
    )

    assert _breaks(before, "def public():\n    pass\n") == ["_deliberate"]


def test_a_dropped_parameter_is_a_break() -> None:
    assert _breaks("def send(to, subject):\n    pass\n", "def send(to):\n    pass\n") == ["send"]


def test_a_reordered_parameter_list_is_a_break() -> None:
    """Positional callers exist and cannot be seen from here."""
    assert _breaks("def send(a, b):\n    pass\n", "def send(b, a):\n    pass\n") == ["send"]


def test_a_new_required_argument_is_a_break() -> None:
    assert _breaks("def send(a):\n    pass\n", "def send(a, b):\n    pass\n") == ["send"]


def test_a_new_optional_argument_is_not_a_break() -> None:
    """**THE FALSE POSITIVE THAT WOULD END THIS SECTION.** Adding a default breaks nobody."""
    assert _breaks("def send(a):\n    pass\n", "def send(a, b=1):\n    pass\n") == []


def test_a_new_export_is_not_a_break() -> None:
    assert (
        _breaks("def send(a):\n    pass\n", "def send(a):\n    pass\n\n\ndef also():\n    pass\n")
        == []
    )


def test_a_renamed_parameter_is_a_break_because_keyword_callers_exist() -> None:
    assert _breaks("def send(to):\n    pass\n", "def send(recipient):\n    pass\n") == ["send"]


def test_a_function_that_becomes_a_class_is_a_break() -> None:
    assert _breaks("def Job():\n    pass\n", "class Job:\n    pass\n") == ["Job"]


def test_self_is_not_part_of_the_contract() -> None:
    """A method's `self` is supplied by the caller's instance, not passed. Counting it would make
    every method-to-function refactor look like a parameter change."""
    before = "class A:\n    def go(self, x):\n        pass\n"

    assert surface(before)["A"].positional == ()


def test_a_keyword_only_argument_without_a_default_is_required() -> None:
    """`def f(a, *, b)` breaks every caller just as `def f(a, b)` does."""
    assert _breaks("def f(a):\n    pass\n", "def f(a, *, b):\n    pass\n") == ["f"]


def test_a_module_that_will_not_parse_raises_rather_than_reading_as_empty() -> None:
    """An empty surface would report every export as removed — the worst possible false positive."""
    with pytest.raises(UnparseableSource):
        surface("def broken(:\n")


def test_nested_definitions_are_not_part_of_the_surface() -> None:
    """A closure is unreachable from outside, and a method is reached through its class."""
    source = "def outer():\n    def inner():\n        pass\n    return inner\n"

    assert sorted(surface(source)) == ["outer"]
