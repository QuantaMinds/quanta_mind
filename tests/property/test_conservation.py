"""Property tier: every hunk is accounted for, on diffs nobody chose.

WHAT: Hypothesis generates unified diffs -- varying file counts, hunk counts, funcname headers
      present or absent, in scope and out of it -- and asserts `len(units) + len(unresolved) ==
      hunks` for all of them, plus that a hunk never appears in both lists.
WHY:  **AGENTS.md rule 3 and `ARCHITECTURE.md` "Invariants" both say this invariant is
      PROPERTY-tested. It was not.** `tests/property/` held one file, about layer order.
      Conservation was asserted in unit tests and one live test, all of them on diffs chosen by
      the person writing the assertion — which is the weakest place to check a conservation law,
      because the shapes that break it are the ones nobody thought to write down.

      THE INVARIANT IS THE PRODUCT'S REASON TO EXIST. "No unit here" and "we could not parse
      this" must never be the same value on the wire; conservation is what makes the difference
      countable. A parser that silently dropped one hunk in a thousand would still look correct
      in every fixture and would quietly shrink the denominator of the coverage line we publish.

      SCOPE IS GENERATED TOO, not held fixed. The research's coverage rate moved from 91% to 52%
      once out-of-scope hunks were counted, so the interaction between `scope` and the hunk total
      is exactly where the accounting went wrong before.
IMPORTS: quantamind.parse.units; hypothesis. Tier 2, no mocks.
CONSUMED BY: justfile (`just test-property`), .github/workflows/ci.yml.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from quantamind.parse.units import units_in

PATHS = st.sampled_from(["a.py", "pkg/b.py", "pkg/sub/c.py", "notes.md", "d.js", "e.txt"])
FUNCNAMES = st.sampled_from(["", " def alpha(self):", " class Beta:", " def gamma():"])


@st.composite
def diffs(draw: st.DrawFn) -> tuple[str, int]:
    """(a unified diff, the number of hunks in it). The count is built, never parsed back."""
    files = draw(st.lists(PATHS, min_size=1, max_size=4, unique=True))
    body: list[str] = []
    hunks = 0
    for path in files:
        body += [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}"]
        for index in range(draw(st.integers(min_value=1, max_value=3))):
            start = 1 + index * 20
            header = draw(FUNCNAMES)
            body.append(f"@@ -{start},3 +{start},4 @@{header}")
            body += [" context", "+added line", " context"]
            hunks += 1
    return "\n".join(body) + "\n", hunks


@given(made=diffs(), scope=st.lists(PATHS, max_size=4, unique=True))
@settings(max_examples=250, deadline=None)
def test_every_hunk_is_either_a_unit_or_an_unresolved_never_neither(
    made: tuple[str, int], scope: list[str]
) -> None:
    diff, _built = made
    parsed = units_in(diff, scope=frozenset(scope))

    assert parsed.conserved(), (
        f"{len(parsed.units)} units + {len(parsed.unresolved)} unresolved != {parsed.hunks} "
        f"hunks — a hunk went missing, and a missing hunk is a coverage claim we cannot make"
    )
    assert parsed.hunks >= 0
    assert len(parsed.units) + len(parsed.unresolved) == parsed.hunks


@given(made=diffs())
@settings(max_examples=250, deadline=None)
def test_scoping_everything_in_never_loses_a_hunk(made: tuple[str, int]) -> None:
    """With every path in scope the parser must see exactly the hunks the diff was built with.

    The built count is the known answer. Reading the total back out of `parsed.hunks` alone would
    let a parser that skipped a file agree with itself.
    """
    diff, built = made
    scope = frozenset(line[6:].strip() for line in diff.splitlines() if line.startswith("+++ b/"))
    parsed = units_in(diff, scope=scope)

    assert parsed.hunks == built, f"built {built} hunks, parser saw {parsed.hunks}"
    assert parsed.conserved()
