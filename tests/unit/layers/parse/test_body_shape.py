"""What counts as the same body, and — harder — what must not.

WHAT: Drives `parse.body_shape.shapes_in()` over pairs that should collide and pairs that must
      not, plus the parse failure it now raises instead of swallowing.
WHY:  **THE FALSE POSITIVES ARE THE WHOLE RISK.** "This code already exists somewhere else" is
      printed on somebody's pull request as a fact, and the first one that is wrong is the last
      time that section gets read. So the pairs that must NOT match outnumber the pairs that must:
      a different literal, a different operator, a different reuse of the same name.

      **ALPHA-EQUIVALENCE IS THE POINT, AND IT CUTS BOTH WAYS.** `x + x` and `y + y` are the same
      body; `y + y` and `y + z` are not, and a normaliser that simply deleted names would call
      them equal. `test_two_names_used_once_each_is_not_one_name_used_twice` is that case.

      **API NAMES ARE KEPT DELIBERATELY.** A copied block gets its variables renamed; it does not
      get `.commit()` renamed to `.rollback()`. `test_a_different_method_is_a_different_body`
      fails if somebody "improves" the normaliser by aliasing attributes too.
IMPORTS: quantamind.parse.body_shape, quantamind.parse.python_names.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.parse.body_shape import shapes_in
from quantamind.parse.python_names import UnparseableSource


def _digest(source: str) -> str:
    found = shapes_in(source)
    assert len(found) == 1, f"expected one function, got {[s.name for s in found]}"
    return found[0].digest


RENAMED = (
    "def a(x, y):\n    total = x + y\n    return total\n",
    "def b(first, second):\n    out = first + second\n    return out\n",
)


def test_a_renamed_copy_is_the_same_body() -> None:
    """The finding this exists for: copy, rename the locals, change nothing else."""
    assert _digest(RENAMED[0]) == _digest(RENAMED[1])


def test_the_function_name_is_not_part_of_the_shape() -> None:
    """A copied function is usually renamed. Requiring the name to match would find only the
    duplicates that are easiest to spot by eye."""
    body = "    x += 1\n    return x\n"

    assert _digest(f"def a(x):\n{body}") == _digest(f"def totally_other(x):\n{body}")


def test_a_docstring_does_not_change_the_shape() -> None:
    """Two functions written identically and documented differently are the duplicate."""
    documented = 'def a(x):\n    """One."""\n    x += 1\n    return x\n'
    otherwise = 'def b(x):\n    """Something else entirely."""\n    x += 1\n    return x\n'

    assert _digest(documented) == _digest(otherwise)


def test_comments_and_spacing_do_not_change_the_shape() -> None:
    """Free, because comments are not in the AST — which is half the reason this is not a text
    digest."""
    commented = "def a(x):\n    # explain\n    x += 1\n\n    return x\n"

    assert _digest(commented) == _digest("def b(x):\n    x += 1\n    return x\n")


def test_two_names_used_once_each_is_not_one_name_used_twice() -> None:
    """**THE CASE A NAME-DELETING NORMALISER GETS WRONG.** `x + x` and `y + z` are different
    functions, and reporting them as copies is the false positive that ends the section."""
    assert _digest("def a(x):\n    return x + x\n") != _digest("def b(y, z):\n    return y + z\n")


def test_a_different_literal_is_a_different_body() -> None:
    """`timeout=30` and `timeout=60` are not the same logic."""
    thirty = "def a():\n    return connect(timeout=30)\n"

    assert _digest(thirty) != _digest("def b():\n    return connect(timeout=60)\n")


def test_a_different_operator_is_a_different_body() -> None:
    """Structure, not a bag of nodes. `a - b` and `a + b` reach `ast.walk` identically."""
    assert _digest("def a(x, y):\n    return x - y\n") != _digest(
        "def b(x, y):\n    return x + y\n"
    )


def test_reordered_statements_are_a_different_body() -> None:
    """Field order IS the structure, which is why the traversal is `iter_fields`."""
    first = "def a(x):\n    p = x + 1\n    q = x * 2\n    return p, q\n"
    second = "def b(x):\n    q = x * 2\n    p = x + 1\n    return p, q\n"

    assert _digest(first) != _digest(second)


def test_a_different_method_is_a_different_body() -> None:
    """API names are kept. A copy renames its variables, not the methods it calls."""
    commit = "def a(s):\n    s.commit()\n    return s\n"

    assert _digest(commit) != _digest("def b(s):\n    s.rollback()\n    return s\n")


def test_two_identical_functions_in_one_module_both_match() -> None:
    """**THE ALIAS TABLE IS PER FUNCTION.** Sharing it would make the second body's `x` alias to
    a later slot, so the commonest duplicate of all — twice in one file — would stop matching."""
    found = shapes_in(
        "def a(x):\n    x += 1\n    return x\n\n\ndef b(y):\n    y += 1\n    return y\n"
    )

    assert [s.name for s in found] == ["a", "b"]
    assert found[0].digest == found[1].digest


def test_nested_functions_are_found_too() -> None:
    """A closure is where copied logic hides from a top-level-only scan."""
    source = "def outer():\n    def inner(x):\n        return x\n    return inner\n"

    assert {s.name for s in shapes_in(source)} == {"outer", "inner"}


def test_the_statement_count_excludes_the_docstring() -> None:
    """The floor is applied to this number, so a docstring must not lift a body over it."""
    (shape,) = shapes_in('def a(x):\n    """Doc."""\n    return x\n')

    assert shape.statements == 1


def test_a_file_that_is_not_python_raises_rather_than_reading_as_empty() -> None:
    """**"NO FUNCTIONS" AND "NOT PYTHON" ARE DIFFERENT ANSWERS.** Returning `()` for both made
    `twins()` report 51 of this repository's 390 library files as a coverage gap when every one
    had been read perfectly."""
    with pytest.raises(UnparseableSource):
        shapes_in("def broken(:\n")


def test_a_module_with_no_functions_is_empty_and_does_not_raise() -> None:
    """The other side of that pair, and the one that was being miscounted."""
    assert shapes_in("X = 1\n\n\nclass C:\n    pass\n") == ()
