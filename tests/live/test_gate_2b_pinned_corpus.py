"""Gate 2b — reproduce the research's result on the six repositories that produced it.

WHAT: Replays the event definition through the PRODUCT path — `read_commits` → `Touch` →
      `touches.counts` → `rank.order` — over the pinned corpus in `tests/fixtures/pinned.json`,
      and asserts the per-repository (hit, alpha_hit) vectors are IDENTICAL, event for event, to
      `research/phase0/external/defect_return_external.json`.
WHY:  Gate 2a asserts the product ORDERS a set of files the way the research does. That is
      necessary and not sufficient, and the gap is the event set: a reimplementation can order
      every event correctly while admitting different EVENTS, and then report a different miss
      rate from a corpus that is no longer the one with the p-value. Gate 2a never caught this,
      because it built both the product's ranking and its own `expected` oracle from the SAME
      `read_commits` output — so the commit stream itself had never been checked against the
      research's.

      **EQUALITY, NOT AN INTERVAL.** The plan asked for "top-3 miss inside 0.82-1.81%". That
      interval is Wilson on 24/1969 — the ORIGINAL EIGHT repositories the ranker was developed
      against. The pinned six are a different corpus with a different interval, [0.84%, 1.73%] on
      29/2400, and holding one population to the other's interval is the category error
      `test_event_replay_gate.py` already warns about, one level up. It is also far too weak:
      once the events match, the miss rate is 1.21% by construction, not by luck, so an interval
      that admits anything from 0.84% to 1.73% would pass a product that had drifted. Equality
      against the artefact is the check the interval was standing in for.

      **THE FIX-WORD MATCH IS CASE-INSENSITIVE**, because `commit_stream.py` lowercases the
      subject before `defect_return.py` sees it. `test_event_replay_gate.py` claimed in a comment
      to match the research by testing the raw subject; it did the opposite, admitting fewer.
IMPORTS: quantamind.ingest.commits, quantamind.store.{schema,touches}, quantamind.rank.score,
         quantamind.types.touch.
CONSUMED BY: `just gate-2b`.
"""

from __future__ import annotations

import bisect
import collections
import json
import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.commits import read_commits
from quantamind.rank.score import order
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.touch import Touch

# Copied from defect_return.py. Not chosen here.
YEAR = 365 * 86400
WINDOW = 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/pinned.json"
REPOS_DIR = ROOT / "tests/fixtures/repos"
ARTEFACT = ROOT / "research/phase0/external/defect_return_external.json"
SECOND_COPY = ROOT / "research/phase0/results/defect_return_external.json"

pytestmark = pytest.mark.pinned_corpus


def _baseline() -> dict[str, list[tuple[bool, bool]]]:
    """The research's (hit, alpha_hit) per repository, from whichever shape it was written in.

    The checked-in artefact stores two bare booleans per event; the current `run_repo` writes a
    richer record. Both are read, so regenerating the artefact does not silently void this gate.
    """
    # Two copies are checked in and `research/phase0/claims/verify.py` reads the OTHER one. Nothing
    # keeps them equal: `defect_return.py` writes to its working directory, so a re-run updates
    # whichever copy the runner stood in. If they disagree, this gate has no oracle.
    if SECOND_COPY.exists():
        assert json.loads(SECOND_COPY.read_text()) == json.loads(ARTEFACT.read_text()), (
            f"{ARTEFACT.name} differs between {ARTEFACT.parent} and {SECOND_COPY.parent} — "
            f"which one is the research result?"
        )
    raw = json.loads(ARTEFACT.read_text())
    out: dict[str, list[tuple[bool, bool]]] = {}
    for name, events in raw.items():
        rows: list[tuple[bool, bool]] = []
        for event in events:
            if isinstance(event, dict):
                rows.append((bool(event["hit"]), bool(event["alpha_hit"])))
            else:
                rows.append((bool(event[0]), bool(event[1])))
        out[name] = rows
    return out


def _research_prior(index: dict[str, list[int]], path: str, as_of: int) -> int:
    stamps = index.get(path, [])
    return bisect.bisect_left(stamps, as_of) - bisect.bisect_left(stamps, as_of - YEAR)


def _replay(clone: Path, name: str, repo: str) -> tuple[list[tuple[bool, bool]], int]:
    """([(hit, alpha_hit)] through the product path, order mismatches) for one repository."""
    commits = read_commits(clone, pathspec="*.py")
    assert len(commits) > 100, f"{name}: {len(commits)} commits — the read looks truncated"

    index: dict[str, list[int]] = collections.defaultdict(list)
    for commit in commits:
        for path in commit.paths:
            index[path].append(commit.committed_at)
    for stamps in index.values():
        stamps.sort()

    conn = schema.open_store(clone / "gate2b-index.db")
    repo_id = touch_store.ensure_repo(conn, "github.com", repo)
    touch_store.index(
        conn,
        repo_id,
        [Touch(path=p, committed_at=c.committed_at) for c in commits for p in c.paths],
    )

    rows: list[tuple[bool, bool]] = []
    mismatches = 0
    for i, commit in enumerate(commits):
        files = set(commit.paths)
        if not (2 <= len(files) <= MAX_FILES):
            continue
        target: set[str] = set()
        for later in commits[i + 1 :]:
            if later.committed_at - commit.committed_at > WINDOW:
                break
            # Lowercased, because `commit_stream.py` lowercases before the research matches.
            if any(w in later.subject.lower() for w in FIXWORDS):
                target |= later.paths & files
        if not target:
            continue

        produced = touch_store.counts(conn, repo_id, sorted(files), as_of=commit.committed_at)
        expected = {f: _research_prior(index, f, commit.committed_at) for f in files}
        assert dict(produced) == expected, f"{name}: scores diverged at {commit.committed_at}"
        if len(set(expected.values())) == 1:
            continue  # nothing for a ranking to distinguish; the research drops these too

        ranked = order(produced)
        if ranked != sorted(sorted(files), key=lambda f: (-expected[f], f)):
            mismatches += 1
        rows.append(
            (bool(set(ranked[:BUDGET]) & target), bool(set(sorted(files)[:BUDGET]) & target))
        )
        if len(rows) >= MAX_EVENTS:
            break  # the research caps per repository; without it the largest one dominates
    conn.close()
    return rows, mismatches


def test_the_product_reproduces_the_research_on_its_own_pinned_corpus() -> None:
    spec = json.loads(MANIFEST.read_text())
    baseline = _baseline()
    names = [r["name"] for r in spec["repos"]]
    assert sorted(names) == sorted(baseline), (
        f"manifest names {sorted(names)} but the artefact holds {sorted(baseline)}"
    )

    missing = [n for n in names if not (REPOS_DIR / n).exists()]
    assert not missing, f"pinned corpus not materialised: {missing}. Run `just fixtures` first."

    divergences: list[str] = []
    total_mismatches = hits = alpha_hits = events = 0
    for repo in spec["repos"]:
        name, sha = repo["name"], repo["sha"]
        clone = REPOS_DIR / name
        # The corpus is the commits, not the repository. A clone sitting at today's branch tip
        # would produce a plausible number from a history the research never measured.
        landed = subprocess.run(
            ["git", "-C", str(clone), "rev-parse", "HEAD"],
            capture_output=True,
            timeout=60,
        )
        assert landed.returncode == 0, f"{name}: rev-parse exited {landed.returncode}"
        assert landed.stdout.decode().strip() == sha, (
            f"{name} is at {landed.stdout.decode().strip()[:12]}, pinned at {sha[:12]} — "
            f"re-run `just fixtures`"
        )
        rows, mismatches = _replay(clone, name, repo["repo"])
        want = baseline[name]
        total_mismatches += mismatches
        if rows != want:
            first = next(
                (i for i, (a, b) in enumerate(zip(rows, want, strict=False)) if a != b), None
            )
            divergences.append(
                f"{name} (pinned {sha[:12]}): produced {len(rows)} events, research had "
                f"{len(want)}; first differing index {first}"
            )
        events += len(rows)
        hits += sum(1 for h, _ in rows if h)
        alpha_hits += sum(1 for _, a in rows if a)

    print(f"\n  events {events}  hits {hits}  alpha hits {alpha_hits}")
    if events:
        print(f"  miss {1 - hits / events:.4f}  alphabetical {1 - alpha_hits / events:.4f}")

    assert total_mismatches == 0, f"{total_mismatches} orderings differ from the research ranker"
    assert not divergences, "the product does not reproduce the research corpus:\n  " + "\n  ".join(
        divergences
    )
