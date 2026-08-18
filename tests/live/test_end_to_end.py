"""Every layer together, over real merged pull requests: conservation, labelling, and no leakage.

WHAT: Runs the whole product over real pull requests and asserts the invariants that hold across
      the seams — every changed file accounted for, funding consistent with whether anything was
      ranked, and history from AFTER a change unable to reach its own ranking.
WHY:  Unit tests hold each layer to its own contract; the replay gate holds the ranker to the
      research. Neither runs the layers together against data nobody chose, which is where seams
      fail.

      **The leakage assertion is the one that matters.** It rebuilds the index from history
      strictly before each pull request and requires an identical ranking, proving the WINDOW does
      the bounding rather than the caller having happened to pass clean data. A retrospective built
      on a leaking bound looks brilliant and means nothing.
IMPORTS: tests.live.pipeline; quantamind.rank, quantamind.store, quantamind.types.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipeline import Skips, clone_all, ranked_pulls

from quantamind.rank.order import BUDGET
from quantamind.store import touches as touch_store
from quantamind.types.ranking import Allocation


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return clone_all(tmp_path_factory.mktemp("e2e"))


def test_the_whole_pipeline_ranks_real_pull_requests_without_leaking(
    clones: dict[str, Path],
) -> None:
    skips = Skips()
    ranked = fired = silent = 0

    for case in ranked_pulls(clones, skips):
        ranked += 1
        fired += case.ranking.fired
        silent += not case.ranking.fired
        where = f"{case.repo}#{case.number}"

        names = [u.unit.qualified_name for u in case.ranking.units]
        assert sorted(names) == sorted(set(case.changed)), (
            f"{where}: the ranking lost or invented files. Every changed file must appear exactly "
            f"once, funded or cold. changed={sorted(set(case.changed))} ranked={sorted(names)}"
        )
        assert [u.rank for u in case.ranking.units] == list(range(1, len(names) + 1)), (
            f"{where}: ranks are not 1..n contiguous, so a position was skipped or reused"
        )

        # Funding depends on whether anything was RANKED. This previously read
        # `len(funded()) == min(BUDGET, n)` unconditionally, which asserted the behaviour the
        # no-history fix corrected: it published an alphabetical top-three.
        if case.ranking.ranked():
            assert len(case.ranking.funded()) == min(BUDGET, len(names)), (
                f"{where}: a ranked change must fund min(budget, files)"
            )
            assert case.ranking.units[0].allocation is Allocation.DEEP
        else:
            assert case.ranking.funded() == (), (
                f"{where}: nothing was ranked, so funding anything would publish sort(filenames) "
                "as a judgement about risk"
            )
            assert all(u.allocation is Allocation.COLD for u in case.ranking.units)
            assert not case.ranking.fired, f"{where}: fired on a change where every score was zero"

        # LEAKAGE: rebuild the index from history strictly before this pull request. If the window
        # is what bounds us, the scores are identical.
        bounded = [t for t in case.touches if t.committed_at < case.as_of]
        other = touch_store.ensure_repo(
            case.conn, "github.com", f"{case.repo}#bounded{case.number}"
        )
        touch_store.index(case.conn, other, bounded)
        rebuilt = touch_store.counts(case.conn, other, case.changed, as_of=case.as_of)
        assert dict(rebuilt) == case.scores, (
            f"{where}: history from AFTER the change reached its own ranking. The window is not "
            f"bounding: with-future={case.scores} without-future={dict(rebuilt)}"
        )

    print(f"\n  ranked {ranked} pull requests: {fired} fired, {silent} silent")
    print(f"  skipped {skips.total}: {dict(skips.counts)}")
    assert ranked >= 8, (
        f"only {ranked} pull requests ranked and {skips.total} skipped ({dict(skips.counts)}) — "
        "too few to have exercised the pipeline"
    )
    assert skips.total < ranked * 3, (
        f"{skips.total} skipped against {ranked} ranked ({dict(skips.counts)}) — the corpus is "
        "mostly being discarded, so the pass says little"
    )
    assert fired > 0, "the ranker never fired; the ranking path was not exercised"
    assert silent > 0, "the ranker always fired; the no-history path was not exercised"
