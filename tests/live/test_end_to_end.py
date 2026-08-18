"""Every layer built so far, run over real merged pull requests from real repositories.

WHAT: Clones repositories, reads history through `ingest`, indexes it through `store`, ranks real
      merged pull requests through `rank`, and asserts the invariants that hold across the whole
      path — including that history from AFTER a pull request cannot reach its own ranking.
WHY:  The unit tests hold each layer to its own contract and the replay gate holds the ranker to
      the research. Neither runs the layers together against data nobody chose, which is where the
      seams between them fail.

      **The leakage assertion is the one that matters.** It indexes the full history — including
      commits made after the pull request — and requires the ranking to be identical to one built
      from history truncated before it. That proves the WINDOW does the bounding rather than the
      caller having happened to pass clean data, and a retrospective built on a leaking bound looks
      brilliant and means nothing.

      **Both outcomes must appear.** A corpus in which the ranker always fires would not exercise
      the no-history path, and a corpus in which it never fires would not exercise the ranking. A
      case absent from the fixture is a case nothing tests.
IMPORTS: quantamind.ingest.history, quantamind.store.{schema,touches}, quantamind.rank.order.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import collections
import json
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.history import read_touches
from quantamind.rank.order import BUDGET, rank
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.ranking import Allocation

# One repository in active development and one in a quiet period, on purpose: the quiet one is
# where the ranker must stay silent, and a corpus of only busy repositories never exercises that.
REPOS = ("pallets/flask", "encode/httpx")
MAX_PRS = 12


def _gh(args: list[str]) -> object:
    done = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=180)
    assert done.returncode == 0, f"gh api {args[0]} failed: {done.stderr[:200]}"
    return json.loads(done.stdout)


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base = tmp_path_factory.mktemp("e2e")
    out: dict[str, Path] = {}
    for repo in REPOS:
        dest = base / repo.replace("/", "_")
        done = subprocess.run(
            ["git", "clone", "-q", f"https://github.com/{repo}.git", str(dest)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert done.returncode == 0, f"clone of {repo} failed: {done.stderr[:200]}"
        out[repo] = dest
    return out


def test_the_whole_pipeline_ranks_real_pull_requests_without_leaking(
    clones: dict[str, Path],
) -> None:
    ranked_prs = fired = silent = 0
    # Every skip is counted and printed. A silent `continue` is how a test keeps passing
    # while covering nothing: if an API shape changed, all of these would skip and only
    # a bare total would notice.
    skipped: collections.Counter[str] = collections.Counter()

    for repo, clone in clones.items():
        touches = read_touches(clone, pathspec="*.py")
        assert len(touches) > 500, f"{repo}: {len(touches)} touches — the read looks truncated"

        conn = schema.open_store(clone / "e2e.db")
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        assert touch_store.index(conn, repo_id, touches) == len(touches)

        pulls = [
            p
            for p in _gh([f"repos/{repo}/pulls?state=closed&per_page=40"])  # type: ignore[union-attr]
            if p.get("merged_at")
        ][:MAX_PRS]
        assert pulls, f"{repo}: no merged pull requests returned"

        for pull in pulls:
            number, base_sha = pull["number"], pull["base"]["sha"]
            changed = [
                f["filename"]
                for f in _gh([f"repos/{repo}/pulls/{number}/files?per_page=100"])  # type: ignore[union-attr]
                if f["filename"].endswith(".py")
            ]
            if not changed:
                skipped["no python files changed"] += 1
                continue
            shown = subprocess.run(
                ["git", "-C", str(clone), "show", "-s", "--format=%ct", base_sha],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if shown.returncode != 0:
                # A base commit absent from the clone is not a pipeline failure -- a fork, or a
                # branch force-pushed since. It IS a coverage hole, so it is counted.
                skipped[f"{repo}: base commit not in clone"] += 1
                continue
            as_of = int(shown.stdout.strip().split("\n")[-1])

            scores = touch_store.counts(conn, repo_id, sorted(changed), as_of=as_of)
            ranking = rank(scores)
            ranked_prs += 1
            fired += ranking.fired
            silent += not ranking.fired

            # Conservation: every changed file appears exactly once, funded or cold.
            names = [u.unit.qualified_name for u in ranking.units]
            assert sorted(names) == sorted(set(changed)), (
                f"{repo}#{number}: ranking lost or invented files"
            )
            assert [u.rank for u in ranking.units] == list(range(1, len(names) + 1))
            assert len(ranking.funded()) == min(BUDGET, len(names))
            assert all(u.allocation is Allocation.COLD for u in ranking.units[BUDGET:])
            assert ranking.units[0].allocation is Allocation.DEEP

            # A change nothing has touched must not be presented as a judgement about risk.
            if all(u.score.value == 0 for u in ranking.units):
                assert not ranking.fired, f"{repo}#{number}: fired on an all-zero ranking"

            # LEAKAGE: rebuild the index from history strictly before this pull request and
            # require an identical ranking. If the window is what bounds us, nothing changes.
            bounded = [t for t in touches if t.committed_at < as_of]
            other = touch_store.ensure_repo(conn, "github.com", f"{repo}#bounded{number}")
            touch_store.index(conn, other, bounded)
            assert touch_store.counts(conn, other, sorted(changed), as_of=as_of) == scores, (
                f"{repo}#{number}: history after the change reached its own ranking"
            )
        conn.close()

    total_skipped = sum(skipped.values())
    print(f"\n  ranked {ranked_prs} pull requests: {fired} fired, {silent} silent")
    print(f"  skipped {total_skipped}: {dict(skipped)}")

    assert ranked_prs >= 8, (
        f"only {ranked_prs} pull requests ranked and {total_skipped} skipped ({dict(skipped)}) "
        "— too few to have exercised the pipeline"
    )
    # A test that skips most of its corpus is a test whose coverage nobody can see.
    assert total_skipped < ranked_prs * 3, (
        f"{total_skipped} skipped against {ranked_prs} ranked ({dict(skipped)}) — the corpus is "
        "mostly being discarded, so the pass says little about the pipeline"
    )
    assert fired > 0, "the ranker never fired; the ranking path was not exercised"
    assert silent > 0, "the ranker always fired; the no-history path was not exercised"
