"""The commit walk must be bounded by date, never by a count.

WHAT: Builds a real repository whose in-window fix sits behind 2,500 later commits,
      and asserts the scan still reaches it. Also asserts that an unreadable walk
      raises rather than returning an empty list.
WHY:  `window.py` walked `iter_commits(ref, max_count=2000)` from the tip. Commits
      landing after the window end hit `continue` but still consumed that budget, so a
      repository that had since landed more than 2,000 commits exhausted the walk
      before it reached the window. `candidates` returned `[]`, the PR scored CLEAN,
      and `commits_examined` was 0 -- a verdict about the repository produced by a
      limit of ours. Measured on the human arm: 60 of 191 scanned PRs, breaking at
      0.00% against 33.59% for the rest.

      The fixture is sized to the defect. 2,500 > 2,000, so `test_fix_behind_many_later
      _commits_is_found` FAILS against the old implementation rather than passing for
      an unrelated reason -- and `test_a_count_capped_walk_would_miss_it` proves that
      on the same repository, so the fixture cannot silently stop exercising the bug.

      Real repositories, not mocks: the thing under test is which commits a git walk
      yields, and a stub would only prove the stub was told what to return.
IMPORTS: GitPython, phase0.outcome.window, phase0.outcome.scan, phase0.extract_prs,
         pytest, stdlib subprocess/datetime.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from git import Repo

from phase0.extract_prs import PRRecord
from phase0.outcome.scan import WINDOW_DAYS, scan
from phase0.outcome.window import Exclusion, WindowUnreadable, candidates

MERGED_AT = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
EPOCH = int(MERGED_AT.timestamp())
GIT_TIMEOUT_S = 60

# Above the 2,000 the walk used to cap at. The margin is deliberate: a fixture sized
# at exactly the old cap would pass or fail on an off-by-one rather than on the defect.
NOISE_COMMITS = 2500


def _stream(noise: int) -> str:
    """A fast-import stream: the merge, an in-window fix, then `noise` later commits.

    fast-import rather than a commit loop because 2,500 GitPython commits take tens of
    seconds and this has to run in `just check`.
    """
    lines: list[str] = []
    mark = 1

    def commit(message: str, stamp: int, path: str, body: str) -> None:
        nonlocal mark
        lines.append("commit refs/heads/main")
        lines.append(f"mark :{mark}")
        lines.append(f"committer Tester <tester@example.com> {stamp} +0000")
        lines.append(f"data {len(message.encode())}")
        lines.append(message)
        if mark > 1:
            lines.append(f"from :{mark - 1}")
        lines.append(f"M 644 inline {path}")
        lines.append(f"data {len(body.encode())}")
        lines.append(body)
        mark += 1

    commit("feat: add handler", EPOCH, "acme/handlers.py", "original")
    # +2 days, same file, "fix:" subject -- BROKE by the FIX_TOUCHING_SAME_FILE rule.
    commit("fix: correct handler pagination", EPOCH + 2 * 86400, "acme/handlers.py", "fixed")
    # Far outside the window, and newest -- these are what the count cap spent itself on.
    for i in range(noise):
        commit(f"chore: unrelated {i}", EPOCH + 30 * 86400 + i * 60, f"other/f{i}.txt", str(i))
    return "\n".join(lines)


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=True
    )
    return done.stdout.strip()


@pytest.fixture(scope="module")
def buried(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    """A repo whose in-window fix sits behind NOISE_COMMITS later commits."""
    path = tmp_path_factory.mktemp("buried")
    _git(path, "init", "-q", ".")
    subprocess.run(
        ["git", "fast-import", "--quiet"],
        cwd=path,
        input=_stream(NOISE_COMMITS),
        text=True,
        timeout=GIT_TIMEOUT_S,
        check=True,
    )
    # fast-import writes refs/heads/main; HEAD may still point at an unborn default.
    _git(path, "symbolic-ref", "HEAD", "refs/heads/main")
    root = _git(path, "rev-list", "--max-parents=0", "main")
    return path, root


def _pr(merged_sha: str) -> PRRecord:
    return PRRecord(
        pr_id="1",
        repo="o/r",
        language="python",
        parent_sha="0" * 40,
        merged_sha=merged_sha,
        merged_at=MERGED_AT.isoformat().replace("+00:00", "Z"),
        changed_files=("acme/handlers.py",),
        changed_symbols=("handle",),
    )


def test_the_fixture_actually_buries_the_fix(buried: tuple[Path, str]) -> None:
    """Guards the guard: the noise must really sit between the tip and the window."""
    path, _ = buried
    assert int(_git(path, "rev-list", "--count", "main")) == NOISE_COMMITS + 2
    assert NOISE_COMMITS > 2000, "fixture no longer exceeds the cap it exists to defeat"


def test_a_count_capped_walk_would_miss_it(buried: tuple[Path, str]) -> None:
    """The old implementation, run on this repo, finds nothing.

    Without this, a passing `test_fix_behind_many_later_commits_is_found` would not
    distinguish "the fix works" from "the fixture stopped reproducing the bug".
    """
    path, merged = buried
    repo = Repo(path)
    start, end = MERGED_AT, MERGED_AT + timedelta(days=WINDOW_DAYS)
    capped = [
        c
        for c in repo.iter_commits("HEAD", max_count=2000)
        if start < c.committed_datetime <= end and not c.hexsha.startswith(merged[:7])
    ]
    assert capped == [], "the count cap no longer truncates; this fixture is now toothless"


def test_fix_behind_many_later_commits_is_found(buried: tuple[Path, str]) -> None:
    """The date-bounded walk reaches the window regardless of what landed after it."""
    path, merged = buried
    repo = Repo(path)
    found = candidates(repo, MERGED_AT, MERGED_AT + timedelta(days=WINDOW_DAYS), merged, "HEAD")
    assert len(found) == 1
    assert str(found[0].message).startswith("fix: correct handler")


def test_scan_scores_it_broke(buried: tuple[Path, str]) -> None:
    """End to end: the verdict the truncated walk was reporting as CLEAN."""
    path, merged = buried
    record = scan(path, _pr(merged))
    assert record.outcome.value == "broke"
    assert record.commits_examined == 1


def test_unreadable_walk_raises_rather_than_reading_as_empty(tmp_path: Path) -> None:
    """`[]` must mean "the window is empty", never "the walk could not run"."""
    _git(tmp_path, "init", "-q", ".")
    repo = Repo(tmp_path)
    with pytest.raises(WindowUnreadable):
        candidates(repo, MERGED_AT, MERGED_AT + timedelta(days=WINDOW_DAYS), "", "no/such/ref")


def test_a_repo_that_cannot_be_walked_is_never_clean(tmp_path: Path) -> None:
    """Whichever gate catches it, the answer is UNSCANNABLE and the reason is typed.

    This repo is caught earlier than the window walk -- an unresolvable merge SHA is
    MERGE_UNREACHABLE -- so it does not pin the WINDOW_UNREADABLE mapping; that
    contract is held one level down, where `candidates` raises rather than returning
    `[]`. What it does pin is the property those gates exist for: an unwalkable
    repository must not arrive as a claim that the PR broke nothing.
    """
    _git(tmp_path, "init", "-q", ".")
    record = scan(tmp_path, _pr("0" * 40))
    assert record.outcome.value == "unscannable"
    assert record.exclusion is not Exclusion.NONE
    assert record.commits_examined == 0
