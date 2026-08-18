"""Gate 2c: the three cases must render DIFFERENTLY, and the line must name real files.

WHAT: Renders a discriminating change, a flat-history change and a no-history change against a
      checked-in golden file, and asserts the three lines are materially different.
WHY:  **A coverage line that reads the same whatever happened is decoration.** It would be equally
      convincing if the ranker had never run, which makes it worse than nothing: it is reassurance
      the product did not earn.

      **A case that never appears in a fixture is a case nothing tests**, which is why all three are
      here rather than only the interesting one.

      **The golden file is compared, not just eyeballed.** A rendering change that alters what the
      customer is told must show up as a diff a human approves, not as a passing test.
IMPORTS: quantamind.rank.order, quantamind.render.{comment,coverage_line}, quantamind.types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.rank.order import rank
from quantamind.render.comment import comment
from quantamind.render.coverage_line import NothingToReport, coverage_line
from quantamind.types.ranking import Discrimination, Ranking
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

GOLDEN = Path(__file__).parent / "golden" / "coverage_lines.md"

CASES = {
    "ordered": {
        "src/pay/app.py": 9,
        "tests/test_pay.py": 4,
        "src/pay/ledger.py": 2,
        "src/pay/settle.py": 0,
    },
    "flat_nonzero": {"src/a.py": 3, "src/b.py": 3, "src/c.py": 3, "src/d.py": 3},
    "no_history": {"src/new/mod.py": 0, "src/new/__init__.py": 0, "tests/test_new.py": 0},
}


def _rendered() -> dict[str, str]:
    return {name: coverage_line(rank(scores)) for name, scores in CASES.items()}


def test_every_case_is_reachable_and_lands_in_the_expected_discrimination() -> None:
    got = {name: rank(scores).discrimination for name, scores in CASES.items()}
    assert got == {
        "ordered": Discrimination.ORDERED,
        "flat_nonzero": Discrimination.FLAT_NONZERO,
        "no_history": Discrimination.NO_HISTORY,
    }, f"a fixture stopped exercising its case: {got}"


def test_the_three_cases_render_materially_different_lines() -> None:
    lines = _rendered()
    assert len(set(lines.values())) == 3, (
        "two cases rendered the same coverage line, so the line is not computed from what "
        f"happened: {lines}"
    )
    assert "No file in this change has prior history" in lines["no_history"]
    assert "could not separate them" in lines["flat_nonzero"]
    assert "Ranked 4 file(s) by prior-fix history" in lines["ordered"]


def test_the_line_names_the_files_rather_than_only_counting_them() -> None:
    """A count is unfalsifiable; a path can be checked against the diff by the person reading it."""
    line = _rendered()["ordered"]
    assert "`src/pay/app.py`" in line, "the funded files must be named"
    assert "`src/pay/settle.py`" in line, "the UNREAD file must be named — that is the residual"


def test_different_unresolved_sets_produce_different_lines() -> None:
    ranking = rank(CASES["ordered"])
    one = coverage_line(
        ranking,
        [Unresolved(Site("src/pay/app.py", 12), Reason.DYNAMIC_DISPATCH, Construct.CALL_SITE)],
    )
    two = coverage_line(
        ranking,
        [Unresolved(Site("src/pay/ledger.py", 40), Reason.UNPARSEABLE_SYNTAX, Construct.DECORATOR)],
    )
    assert one != two, "the unresolved records are not reaching the line; it is a fixed string"


def test_an_empty_ranking_raises_rather_than_reassuring(tmp_path: Path) -> None:
    with pytest.raises(NothingToReport):
        coverage_line(Ranking(units=(), fired=True))


def test_a_change_below_the_threshold_is_not_commented_on() -> None:
    """None is a decision the caller records; a reassuring sentence would be a claim unearned."""
    ranking = rank(CASES["no_history"])
    body = comment(ranking)
    assert body is None, (
        f"a change below the threshold rendered a comment: {body!r}. A cheerful 'nothing to "
        "report' is a claim we did not earn, and it trains readers to ignore the ones that matter"
    )
    # And the same ranking DOES produce a coverage line, so the silence is the comment's choice
    # rather than the renderer having nothing to say.
    assert "No file in this change has prior history" in coverage_line(ranking)


def test_the_coverage_line_comes_first_in_the_comment() -> None:
    body = comment(rank(CASES["ordered"]))
    assert body is not None
    head, coverage = body.split("\n\n")[0], body.split("\n\n")[1]
    assert head.startswith("###"), "the header is first"
    assert "Ranked 4 file(s)" in coverage, (
        "coverage must precede the table; a reader seeing the list first weighs it against nothing"
    )
    assert body.index(coverage) < body.index("| # | file |"), "coverage line is above the table"


def test_the_comment_makes_no_claim_about_correctness() -> None:
    body = comment(rank(CASES["ordered"]))
    assert body is not None
    for forbidden in ("bug", "vulnerabilit", "you should fix", "incorrect", "error in"):
        assert forbidden not in body.lower(), (
            f"the comment claimed something about correctness ({forbidden!r}); infer/ is closed "
            "and we publish no findings"
        )


def test_the_rendering_matches_the_reviewed_golden_file() -> None:
    lines = _rendered()
    rendered = "\n\n".join(f"## {name}\n\n{lines[name]}" for name in sorted(lines))
    if not GOLDEN.exists():  # pragma: no cover - only on first run
        GOLDEN.write_text(rendered + "\n")
        pytest.fail(f"golden file created at {GOLDEN}; review it by hand and re-run")
    assert rendered + "\n" == GOLDEN.read_text(), (
        f"the rendered coverage lines changed. This is what the customer reads — diff {GOLDEN}, "
        "confirm the new wording is what you meant, then update it deliberately"
    )


def test_a_single_file_change_is_not_described_as_a_failed_ranking() -> None:
    """Real output: "All 1 file(s) have the same prior-fix history ... could not separate"."""
    line = coverage_line(rank({"src/only.py": 11}))
    assert "could not separate" not in line, f"there is nothing to separate: {line}"
    assert "one file" in line and "`src/only.py`" in line
    assert "nothing to rank" in line


def test_a_single_file_comment_omits_the_equally_worth_reading_note() -> None:
    body = comment(rank({"src/only.py": 11}))
    assert body is not None
    assert "equally worth reading" not in body, (
        "that note reads as a malfunction when there is only one file"
    )
