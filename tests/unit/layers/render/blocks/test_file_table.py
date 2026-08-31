"""The shape of the file table: what each row carries, and what the fold does with the rest.

WHAT: Drives `render.blocks.scope_block.coverage()` and asserts on the table it delegates to
      `render/blocks/file_table.py`.
WHY:  **SPLIT FROM `test_scope_block.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That file
      asks what the scope SENTENCE says; this asks what the TABLE shows. They failed for different
      reasons twice in one afternoon — one on the wording of a count, one on eighty-seven rows.

      **TWO PROPERTIES HERE ARE PUBLISHING RULES.** The table is ALPHABETICAL, because rank order
      lets a reader count to the cut and read the budget off it, and `publishing-rules.md`
      never-publishes how the budget is split. And no score the RANKING computed may appear:
      *what the ranking is built from* is first on that list.

      **THE FOLD IS NOT A CAP.** The first version repeated all four columns inside it, so a real
      ninety-file pull request produced eighty-seven near-identical rows — the wall the table was
      built to replace, one click further away. Grouping is not truncation and the test asserts
      every path survives.
IMPORTS: quantamind.parse.change_effort, quantamind.rank.order,
      quantamind.render.blocks.scope_block, quantamind.types.checked.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from quantamind.parse.change_effort import Effort
from quantamind.rank.order import rank
from quantamind.render.blocks.scope_block import coverage
from quantamind.types.checked import Checked

SCORES = {f"src/mod{n}.py": 20 - n for n in range(8)}
SIZES = {path: Effort(added=4, removed=1) for path in SCORES}


def _block(
    scores: dict[str, int],
    sizes: dict[str, Effort] | None = None,
    checks: tuple[Checked, ...] = (),
) -> str:
    return "\n".join(coverage(rank(scores), (), sizes, checks))


def test_the_size_and_the_place_to_look_ride_beside_the_path() -> None:
    """The whole point: a reviewer should not have to open a file to learn it changed two lines."""
    sizes = {"src/a.py": Effort(added=160, removed=6, functions=("def handle(request):",))}
    block = _block({"src/a.py": 9, "src/b.py": 7}, sizes=sizes)

    assert "| 166 lines |" in block
    assert "`def handle(request):`" in block


def test_a_file_we_have_no_size_for_says_nothing_rather_than_zero() -> None:
    """A pure rename or a binary reaches here with no parsed hunk. "0 lines" beside a file that
    certainly changed is a wrong statement where silence is merely a quiet one."""
    block = _block({"src/a.py": 9, "src/b.py": 7}, sizes={"src/a.py": Effort(added=1)})

    assert "`src/b.py`" in block
    assert "0 lines" not in block


def test_the_files_read_closely_are_marked_and_the_others_are_not() -> None:
    """A table where every row looks the same cannot answer "did you look at MY file"."""
    marked = [
        line
        for line in _block(SCORES, sizes=SIZES).splitlines()
        if line.startswith("|") and "read closely" in line
    ]

    assert len(marked) == 3, marked
    assert all("mod0" in m or "mod1" in m or "mod2" in m for m in marked)


def test_the_list_is_alphabetical_and_not_the_ranking() -> None:
    """**A PUBLISHING RULE, NOT A LAYOUT PREFERENCE.** Rank order lets a reader count to the cut
    and read the budget off the list, which `publishing-rules.md` never-publishes.

    The scores here make the two orders disagree: `zebra.py` is the busiest file and sorts last.
    """
    three = {"src/zebra.py": 99, "src/apple.py": 2, "src/mango.py": 1}
    block = _block(three, sizes={p: Effort(added=2) for p in three})
    rows = [line for line in block.splitlines() if line.startswith("| `src/")]

    assert rows == sorted(rows), f"the table is in rank order, which discloses the budget: {rows}"
    assert "apple" in rows[0], rows


def test_no_score_from_the_ranking_reaches_the_page() -> None:
    """*What the ranking is built from* is first on the never-publish list, and a per-file fix
    count was printed in this comment once before being removed for a different reason.

    **THE ASSERTION IS THE SCORE VALUE, NOT THE SHAPE OF THE LINE.** This used to require a line
    to be a bare path — which was right until the line legitimately gained a size and a rule
    count, both from sources a customer already has. What must never appear is the number the
    RANKING computed, so the fixture uses a distinctive one and looks for it.
    """
    block = _block({"src/zebra.py": 4242, "src/apple.py": 2, "src/mango.py": 1})

    assert "4242" not in block, f"the ranking's own score reached the page: {block}"
    assert "`src/zebra.py`" in block, "the file itself must still be listed"


def test_a_table_with_nothing_to_say_is_a_plain_list_instead() -> None:
    """**A TABLE OF DASHES IS FURNITURE.** The CLI renders a ranking with no diff parsed and no
    rules run, so every cell would be an em dash and four columns would carry nothing.

    A live run against `pallets/flask#6133` printed exactly that. Every path is still listed and
    the ones read closely are still marked — only the columns go.
    """
    block = _block({"src/a.py": 9, "src/b.py": 7})

    assert "| file | changed |" not in block
    assert "- `src/a.py`" in block and "- `src/b.py`" in block
    assert "read closely" in block


def test_the_quiet_files_are_grouped_by_directory_and_none_is_dropped() -> None:
    """**EIGHTY-SEVEN TABLE ROWS IS THE WALL THE TABLE WAS BUILT TO REPLACE.**

    The fold repeated all four columns, and on a real ninety-file pull request that was
    eighty-seven near-identical lines reading "4 rules passed". The columns carry nothing there by
    definition — a file is in that group because nothing was found in it. Grouping is not
    truncation: every path is still present and a reader can still find their own name.
    """
    # The three highest are read closely and stay in the open table; the rest fold. The quiet
    # files must therefore score BELOW them or this test asserts against the wrong half.
    scores = {
        "src/read/one.py": 99,
        "src/read/two.py": 98,
        "src/read/three.py": 97,
        "src/a/one.py": 9,
        "src/a/two.py": 8,
        "src/b/three.py": 7,
        "top.py": 6,
    }
    block = _block(scores, sizes={p: Effort(added=3) for p in scores})
    fold = block.split("nothing found")[1]

    assert "- `src/a` — `one.py`, `two.py`" in fold
    assert "- `src/b` — `three.py`" in fold
    assert "- `(root)` — `top.py`" in fold
    for path in scores:
        name = path.rpartition("/")[2]
        assert f"`{name}`" in block, f"{path} vanished from the comment"
    assert "| file | changed |" not in fold, "the fold repeats the columns it has nothing to put in"
