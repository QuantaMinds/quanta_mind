"""The duplicate section: what it says, what it refuses to say, and when it says nothing.

WHAT: Drives `parse.duplicate_bodies.twins()` over trees this file writes, and
      `render.blocks.duplicate_block.duplicates()` over what comes back.
WHY:  **D2c IS THE FIRST CLAIM THIS PRODUCT ASSERTS THAT IS NEITHER A RULE THE CUSTOMER WROTE NOR
      A MODEL'S OPINION.** It is a parser's, so it may be stated flatly — and the cost of being
      wrong is correspondingly higher, because there is no hedge in the sentence.

      **THE SECTION IS SILENT ON A CLEAN CHANGE, AND THAT IS MEASURED RATHER THAN ASSUMED.** Over
      this repository: 139 library files, 443 functions, zero repeats at the floor. A block that
      announced "no duplicates found" would print on almost every review and be read on none.

      **IT REPORTS WHERE, NEVER WHAT TO DO.** `pallets/flask`'s `render_template` and
      `stream_template` are a real repeat and a deliberate one; "extract a helper" would be
      confident and wrong there. `test_the_block_gives_no_advice` fails if anybody adds it.

      **THE FLOOR AND THE LIBRARY FILTER ARE BOTH PINNED HERE.** Unfiltered, flask has 12 groups
      at three statements and seven are conventional test route handlers. Below three statements,
      `__init__` pairs. Both numbers came from a run over two real repositories.
IMPORTS: quantamind.parse.duplicate_bodies, quantamind.render.blocks.duplicate_block.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.parse.duplicate_bodies import MIN_STATEMENTS, twins
from quantamind.render.blocks.duplicate_block import duplicates

BODY = "    total = a + b\n    total *= 2\n    return total\n"
OTHER = "    out = x - y\n    out //= 3\n    return out\n"


def _tree(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_the_same_body_in_two_library_files_is_found(tmp_path: Path) -> None:
    """The finding, in its simplest real form."""
    _tree(
        tmp_path,
        {
            "src/one.py": f"def alpha(a, b):\n{BODY}",
            "src/two.py": f"def beta(first, second):\n{BODY}",
        },
    )
    found = twins(tmp_path, ["src/one.py"])

    assert len(found.repeats) == 1
    assert {site.path for site in found.repeats[0].sites} == {"src/one.py", "src/two.py"}


def test_a_repeat_the_change_does_not_touch_is_not_reported(tmp_path: Path) -> None:
    """The reviewer is answering a question about THIS pull request. The repository's other
    duplicates are true, not asked about, and would lengthen every review forever."""
    _tree(
        tmp_path,
        {
            "src/one.py": f"def alpha(a, b):\n{BODY}",
            "src/two.py": f"def beta(a, b):\n{BODY}",
            "src/changed.py": f"def gamma(x, y):\n{OTHER}",
        },
    )

    assert twins(tmp_path, ["src/changed.py"]).repeats == ()


def test_a_body_under_the_floor_is_not_reported(tmp_path: Path) -> None:
    """At two statements this reports `__init__` pairs. The floor was measured, not chosen."""
    short = "    self.x = x\n    return None\n"
    _tree(tmp_path, {"src/one.py": f"def a(x):\n{short}", "src/two.py": f"def b(y):\n{short}"})

    assert MIN_STATEMENTS == 3
    assert twins(tmp_path, ["src/one.py"]).repeats == ()


def test_test_files_are_not_searched(tmp_path: Path) -> None:
    """**THE FILTER DOES MORE WORK THAN THE FLOOR.** Unfiltered, flask showed 12 groups at this
    floor and seven were conventional test route handlers — real repeats, and not defects."""
    _tree(
        tmp_path,
        {
            "src/one.py": f"def alpha(a, b):\n{BODY}",
            "tests/test_one.py": f"def beta(a, b):\n{BODY}",
        },
    )

    assert twins(tmp_path, ["src/one.py"]).repeats == ()


def test_a_file_that_is_not_python_is_counted_and_named(tmp_path: Path) -> None:
    """ "No duplicates" and "no duplicates in what we could read" are different claims."""
    _tree(tmp_path, {"src/one.py": f"def alpha(a, b):\n{BODY}", "src/broken.py": "def x(:\n"})
    found = twins(tmp_path, ["src/one.py"])

    assert found.files_read == 2
    assert found.files_unparsed == 1
    assert "could not be parsed" in found.limits()


def test_a_clean_tree_reports_nothing_at_all(tmp_path: Path) -> None:
    """Measured over this repository: 443 functions, zero repeats. Silence is the normal answer."""
    _tree(
        tmp_path,
        {"src/one.py": f"def alpha(a, b):\n{BODY}", "src/two.py": f"def beta(x, y):\n{OTHER}"},
    )
    found = twins(tmp_path, ["src/one.py"])

    assert found.repeats == ()
    assert duplicates(found, ["src/one.py"]) == ""


def test_the_rendered_block_names_both_places_and_the_size(tmp_path: Path) -> None:
    """A reader acts on the file they touched; the other place is context, and both are needed."""
    _tree(
        tmp_path,
        {"src/one.py": f"def alpha(a, b):\n{BODY}", "src/two.py": f"def beta(p, q):\n{BODY}"},
    )
    block = duplicates(twins(tmp_path, ["src/one.py"]), ["src/one.py"])

    assert "`src/one.py:1` alpha()" in block
    assert "also at `src/two.py:1` beta()" in block
    assert "3 statements, identical" in block


def test_the_block_gives_no_advice(tmp_path: Path) -> None:
    """**IT REPORTS WHERE, NOT WHAT TO DO.** flask's `render_template`/`stream_template` pair is a
    real repeat and a deliberate one; advice would be confident and wrong there."""
    _tree(
        tmp_path,
        {"src/one.py": f"def alpha(a, b):\n{BODY}", "src/two.py": f"def beta(p, q):\n{BODY}"},
    )
    block = duplicates(twins(tmp_path, ["src/one.py"]), ["src/one.py"]).lower()

    for word in ("extract", "should", "refactor", "consider", "helper", "duplicate code"):
        assert word not in block, f"the block gave advice: {word!r}"
