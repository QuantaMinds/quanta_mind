"""Run the real pipeline over real repositories and require it to match the research ranker.

WHAT: Clones open-source repositories, reads their history with `ingest.history`, indexes it with
      `store.touches`, ranks with `rank.score`, and compares every score and every ordering against
      `defect_return.py`'s `bisect_left(ts) - bisect_left(ts - YEAR)` computed on the same data.
WHY:  **This is the ranker stage's ordering-identity gate in miniature.** The research ranker is the
      one with the p-value; a reimplementation that reorders anything has changed the policy. Only
      a run against real history exercises the shapes that matter — thousands of ties, files with
      one commit, files whose history predates the window entirely.

      **Paths are fed SHUFFLED.** Python's sort is stable, so an alphabetically-ordered input lets a
      missing `(-score, path)` tie-break produce the right answer by accident. The first version of
      this check passed against a deliberately broken tie-break for exactly that reason.

      Two sabotages were run against it by hand and both are caught: making the window inclusive of
      the change itself produced 900 score mismatches of 900 and erased the no-history case
      entirely; dropping the tie-break produced 105 ordering mismatches.
IMPORTS: quantamind.ingest.history, quantamind.store.{schema,touches}, quantamind.rank.score.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import bisect
import collections
import random
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.history import read_touches
from quantamind.rank.score import discriminate, order
from quantamind.store import schema
from quantamind.store import touches as touch_store

YEAR = 365 * 86400
# Small, real, and cloned in full: `ingest.history` refuses a blob-filtered clone, which is the
# point of that refusal -- the read is not deterministic until the object store is warm.
REPOS = ("pytest-dev/pluggy", "jazzband/pip-tools")
SAMPLE_PER_REPO = 200
SEED = 20260818


def _research_prior(index: dict[str, list[int]], path: str, as_of: int) -> int:
    """`defect_return.py`'s prior(), verbatim."""
    stamps = index.get(path, [])
    return bisect.bisect_left(stamps, as_of) - bisect.bisect_left(stamps, as_of - YEAR)


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    out: dict[str, Path] = {}
    base = tmp_path_factory.mktemp("clones")
    for repo in REPOS:
        dest = base / repo.replace("/", "_")
        done = subprocess.run(
            ["git", "clone", "-q", f"https://github.com/{repo}.git", str(dest)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert done.returncode == 0, f"clone of {repo} failed: {done.stderr[:200]}"
        out[repo] = dest
    return out


def test_the_productionised_ranker_reproduces_the_research_ranker(clones: dict[str, Path]) -> None:
    rng = random.Random(SEED)
    cases = score_bad = order_bad = 0
    seen: collections.Counter[str] = collections.Counter()

    for repo, clone in clones.items():
        touches = read_touches(clone, pathspec="*.py")
        assert len(touches) > 100, f"{repo}: only {len(touches)} touches — the read looks truncated"

        conn = schema.open_store(clone / "index.db")
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        assert touch_store.index(conn, repo_id, touches) == len(touches)

        index: dict[str, list[int]] = collections.defaultdict(list)
        by_time: dict[int, set[str]] = collections.defaultdict(set)
        for t in touches:
            index[t.path].append(t.committed_at)
            by_time[t.committed_at].add(t.path)
        for stamps in index.values():
            stamps.sort()

        for as_of in rng.sample(sorted(by_time), min(SAMPLE_PER_REPO, len(by_time))):
            paths = list(by_time[as_of])
            rng.shuffle(paths)  # a stable sort would hide a missing tie-break
            cases += 1
            produced = touch_store.counts(conn, repo_id, paths, as_of=as_of)
            expected = {p: _research_prior(index, p, as_of) for p in paths}
            if dict(produced) != expected:
                score_bad += 1
            if order(produced) != sorted(sorted(paths), key=lambda f: (-expected[f], f)):
                order_bad += 1
            seen[discriminate(produced).value] += 1
        conn.close()

    assert cases > 200, f"only {cases} cases sampled — too few to have exercised the shapes"
    assert score_bad == 0, f"{score_bad} of {cases} scores differ from the research ranker"
    assert order_bad == 0, f"{order_bad} of {cases} ORDERINGS differ — this is a policy change"
    # A case absent from the corpus is a case nothing tested.
    assert seen["ordered"] > 0 and seen["flat_nonzero"] > 0, f"cases not exercised: {dict(seen)}"
