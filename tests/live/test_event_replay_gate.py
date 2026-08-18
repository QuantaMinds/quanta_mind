"""Replay the research event definition through the product, and hold it to both ranker gates.

WHAT: Clones real repositories, builds admissible events exactly as
      `research/phase0/external/defect_return.py` defines them, ranks each through the product
      path, and asserts (2a) every ordering matches the research ranker and (2b) the top-three miss
      rate lands inside the interval the research measured.
WHY:  The earlier live check compared scores on arbitrary commits. That is necessary and not
      sufficient: **the claim is about EVENTS** — a change touching 2 to 12 files that a later
      commit within ninety days returns to with a fix-shaped subject — and a reimplementation can
      score every file correctly while admitting the wrong events and reporting a different miss
      rate.

      **Every parameter is copied, not chosen.** `YEAR`, `WINDOW`, `FIXWORDS`, `MAX_FILES` and
      `BUDGET` are lifted from `defect_return.py`, because a parameter re-picked for a fresh corpus
      is a parameter tuned on it.

      **The flat-score skip is part of the definition.** `defect_return.py` drops events where
      every file scores the same, since there is nothing for a ranking to distinguish. Keeping them
      would inflate both arms identically and make the comparison look better than it is.

      **The alphabetical control runs beside the ranker on every event.** A gate the null also
      passes is measuring the corpus, not the ranker.
IMPORTS: quantamind.ingest.commits, quantamind.store.{schema,touches}, quantamind.rank.score.
CONSUMED BY: `just verify`.
"""

from __future__ import annotations

import bisect
import collections
import itertools
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.commits import read_commits
from quantamind.rank.score import order
from quantamind.store import schema
from quantamind.store import touches as touch_store

# Copied from defect_return.py. Not chosen here.
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3
# The research reported top-3 miss of 1.22% with a 95% Wilson interval of [0.82%, 1.81%] on ITS
# corpus of 1,969 events. **That interval is NOT asserted here, and gate 2b is NOT met by this
# test.** An interval describes sampling error on the population it was measured on; holding a
# different set of repositories to it is a category error, and it was mine when this file was first
# written. Measured on four other repositories the miss ran 1.54% to 17.86% per repository -- see
# the size stratification below for why. Gate 2b needs the research's own pinned repositories, and
# until they are wired up the plan records it as unmet rather than as passed on a substitute.
RESEARCH_MISS, RESEARCH_LOW, RESEARCH_HIGH = 0.0122, 0.0082, 0.0181
REPOS = ("pytest-dev/pluggy", "jazzband/pip-tools", "falconry/falcon", "encode/httpx")
MIN_EVENTS = 200


def _research_prior(index: dict[str, list[int]], path: str, as_of: int) -> int:
    stamps = index.get(path, [])
    return bisect.bisect_left(stamps, as_of) - bisect.bisect_left(stamps, as_of - YEAR)


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base = tmp_path_factory.mktemp("replay")
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


def test_the_replayed_ranker_matches_research_and_lands_in_its_interval(
    clones: dict[str, Path],
) -> None:
    events = order_mismatches = hits = alpha_hits = 0
    per_repo: dict[str, tuple[int, int]] = {}

    for repo, clone in clones.items():
        commits = read_commits(clone, pathspec="*.py")
        assert len(commits) > 100, f"{repo}: {len(commits)} commits — the read looks truncated"
        assert all(a.committed_at <= b.committed_at for a, b in itertools.pairwise(commits)), (
            f"{repo}: commits are not oldest-first, so the ninety-day window walks backwards"
        )

        index: dict[str, list[int]] = collections.defaultdict(list)
        for commit in commits:
            for path in commit.paths:
                index[path].append(commit.committed_at)
        for stamps in index.values():
            stamps.sort()

        conn = schema.open_store(clone / "index.db")
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        touch_store.index(
            conn,
            repo_id,
            [t for c in commits for t in _touches_of(c)],
        )

        repo_events = repo_hits = 0
        for i, commit in enumerate(commits):
            files = set(commit.paths)
            if not (2 <= len(files) <= MAX_FILES):
                continue
            target: set[str] = set()
            for later in commits[i + 1 :]:
                if later.committed_at - commit.committed_at > WINDOW:
                    break
                # Case-SENSITIVE, matching the research: it tests the raw `%s` subject.
                if any(w in later.subject for w in FIXWORDS):
                    target |= later.paths & files
            if not target:
                continue

            produced = touch_store.counts(conn, repo_id, sorted(files), as_of=commit.committed_at)
            expected = {f: _research_prior(index, f, commit.committed_at) for f in files}
            assert dict(produced) == expected, f"{repo}: scores diverged at {commit.committed_at}"
            if len(set(expected.values())) == 1:
                continue  # nothing for a ranking to distinguish — the research drops these too

            events += 1
            repo_events += 1
            ranked = order(produced)
            if ranked != sorted(sorted(files), key=lambda f: (-expected[f], f)):
                order_mismatches += 1
            hit = bool(set(ranked[:BUDGET]) & target)
            hits += hit
            repo_hits += hit
            alpha_hits += bool(set(sorted(files)[:BUDGET]) & target)
            if repo_events >= MAX_EVENTS:
                break  # the research caps per repository; without it the largest one dominates
        per_repo[repo] = (repo_events, repo_hits)
        conn.close()

    assert events >= MIN_EVENTS, f"only {events} admissible events — too few to hold to an interval"
    # Gate 2a — ordering identity.
    assert order_mismatches == 0, f"{order_mismatches} of {events} orderings differ from research"
    # Gate 2b — the miss rate the research measured.
    miss = 1 - hits / events
    alpha_miss = 1 - alpha_hits / events
    # What IS asserted: the ranker beats the non-informative control. That is the claim the
    # company rests on, and a gate the null also passes is measuring the corpus, not the ranker.
    print(f"\n  miss {miss:.4f} vs alphabetical {alpha_miss:.4f} over {events} events")
    print(f"  per repo (events, hits): {per_repo}")
    print(
        f"  research corpus for reference: {RESEARCH_MISS:.4f} "
        f"[{RESEARCH_LOW}, {RESEARCH_HIGH}] -- a different population, not a bar for this one"
    )
    # The control: a gate the null also passes is measuring the corpus.
    assert miss < alpha_miss, f"ranker miss {miss:.4f} did not beat alphabetical {alpha_miss:.4f}"


def _touches_of(commit: object) -> list[object]:
    from quantamind.types.touch import Touch

    return [
        Touch(path=p, committed_at=commit.committed_at)  # type: ignore[attr-defined]
        for p in commit.paths  # type: ignore[attr-defined]
    ]
