"""Gate 2c, live half: what the customer is shown, computed from real pull requests.

WHAT: Renders the coverage line and the comment for every real ranking, and requires the cases that
      occur to render DIFFERENTLY from one another.
WHY:  The golden fixture proves the three cases render differently in principle. This proves the
      line is computed from THIS change — it must name this pull request's own files — and that the
      cases actually arise in repositories nobody chose for the purpose.

      **Cases that do not occur are named, not passed over.** "We never saw it" and "it works" are
      different facts, and only the golden fixture covers the second.
IMPORTS: tests.live.pipeline; quantamind.render.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import collections
from pathlib import Path

import pytest
from pipeline import Skips, clone_all, ranked_pulls

from quantamind.render.comment import comment
from quantamind.render.coverage_line import coverage_line
from quantamind.types.ranking import Discrimination


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return clone_all(tmp_path_factory.mktemp("render"))


def test_the_coverage_line_is_computed_from_each_change_and_differs_by_case(
    clones: dict[str, Path],
) -> None:
    skips = Skips()
    seen: collections.Counter[str] = collections.Counter()
    line_per_case: dict[str, str] = {}

    for case in ranked_pulls(clones, skips):
        where = f"{case.repo}#{case.number}"
        line = coverage_line(case.ranking)
        seen[case.ranking.discrimination.value] += 1
        line_per_case.setdefault(case.ranking.discrimination.value, line)

        named = [u.unit.qualified_name for u in case.ranking.units]
        assert any(f"`{path}`" in line for path in named), (
            f"{where}: the coverage line names none of this change's files, so it is a fixed "
            f"string rather than a report. files={named} line={line!r}"
        )

        body = comment(case.ranking, ())
        if case.ranking.fired:
            assert body is not None, f"{where}: fired but rendered no comment"
            assert body.index(line) < body.index("| # | file |"), (
                f"{where}: the coverage line is not above the table. A reader who sees the list "
                "first weighs it against nothing"
            )
            for claim in ("bug", "vulnerabilit", "incorrect", "you should fix"):
                assert claim not in body.lower(), (
                    f"{where}: the comment claimed something about correctness ({claim!r}). "
                    "infer/ is closed on evidence and we publish no findings"
                )
        else:
            assert body is None, (
                f"{where}: a change below the threshold produced a comment. A cheerful "
                "'nothing to report' is a claim we did not earn"
            )

    print(f"\n  discriminations seen live: {dict(seen)}")
    unseen = {d.value for d in Discrimination} - set(seen)
    print(f"  NOT seen live, covered only by tests/unit/golden/: {sorted(unseen) or 'none'}")

    assert len(set(line_per_case.values())) == len(line_per_case), (
        "two different cases rendered the SAME coverage line on real data, so the line is not "
        f"computed from what happened: {line_per_case}"
    )
    assert {"ordered", "no_history"} <= set(seen), (
        f"the two cases that dominate real repositories did not both occur: {dict(seen)} — the "
        "corpus has stopped exercising the pipeline"
    )


def test_parsing_conserves_every_hunk_and_reaches_the_coverage_line(
    clones: dict[str, Path],
) -> None:
    """Conservation on real diffs, plus the resolution rate conservation alone cannot see."""
    skips = Skips()
    checked = hunks = units = unresolved = 0

    for case in ranked_pulls(clones, skips):
        where = f"{case.repo}#{case.number}"
        assert case.parsed.conserved(), (
            f"{where}: {case.parsed.hunks} hunks produced {len(case.parsed.units)} units and "
            f"{len(case.parsed.unresolved)} unresolved — a hunk vanished, so the coverage line "
            "would be computed over a list something fell out of"
        )
        checked += 1
        hunks += case.parsed.hunks
        units += len(case.parsed.units)
        unresolved += len(case.parsed.unresolved)

        # The unresolved records must reach what the customer reads.
        if case.parsed.unresolved:
            line = coverage_line(case.ranking, case.parsed.unresolved)
            assert "could not be parsed" in line, (
                f"{where}: {len(case.parsed.unresolved)} unresolved records never reached the "
                f"coverage line. line={line!r}"
            )

    print(
        f"\n  parsed {hunks} hunks across {checked} pull requests: "
        f"{units} resolved, {unresolved} unresolved ({units / max(hunks, 1):.0%} resolved)"
    )
    assert checked >= 8, f"only {checked} pull requests parsed"
    assert hunks > 0, "no hunks were parsed at all; the patch read is returning nothing"
    # A parser that resolved nothing would conserve perfectly and report that we read none of it.
    assert units > 0, (
        f"{hunks} hunks and not one resolved to a declaration — conservation holds and the parser "
        "is doing nothing, which is the failure conservation alone cannot see"
    )
