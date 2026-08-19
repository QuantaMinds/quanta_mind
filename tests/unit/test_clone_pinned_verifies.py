"""Known-answer and sabotage tests for the pinned-corpus materialiser.

WHAT: Builds a throwaway repository with two commits, materialises it pinned to the FIRST, and
      asserts HEAD landed there rather than on the tip. Then breaks the pinning outright and
      asserts the same check fails.
WHY:  The materialiser's whole job is that `HEAD` ends up on a commit that is not the default
      branch's tip. A test that only cloned and checked "it is a repository" would pass against a
      version that never pinned anything, because a clone of a real repository looks healthy from
      every angle except which history it is about to hand you.

      THE SABOTAGE REMOVES `_pin_head` ENTIRELY, not its verification step. Stubbing only the
      final `rev-parse` comparison would leave the update-ref still running and the test would
      stay green against a mechanism that still worked -- which is the dud sabotage this project
      has already shipped once. With the pin gone the clone sits on the tip, and the assertion
      that catches that is the same one the real run depends on.
IMPORTS: stdlib (json, subprocess, sys, pathlib); the script under test, loaded by path.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fixtures"))

from clone_pinned import FixtureCloneFailed, materialise  # noqa: E402


def _run(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, timeout=60)
    assert done.returncode == 0, f"git {args[0]} failed: {done.stderr.decode()[:200]}"
    return done.stdout.decode().strip()


@pytest.fixture
def origin(tmp_path: Path) -> tuple[Path, str, str]:
    """(repo, first commit, tip). Two commits, so 'pinned' and 'latest' are distinguishable."""
    repo = tmp_path / "origin"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "t@example.com")
    _run(repo, "config", "user.name", "t")
    shas = []
    for n in (1, 2):
        (repo / f"f{n}.py").write_text(f"x = {n}\n")
        _run(repo, "add", "-A")
        _run(repo, "commit", "-q", "-m", f"commit {n}")
        shas.append(_run(repo, "rev-parse", "HEAD"))
    return repo, shas[0], shas[1]


def _manifest(tmp_path: Path, url: Path, sha: str) -> Path:
    path = tmp_path / "pinned.json"
    path.write_text(json.dumps({"repos": [{"name": "sample", "sha": sha, "url": str(url)}]}))
    return path


def test_head_lands_on_the_pinned_commit_not_the_tip(
    tmp_path: Path, origin: tuple[Path, str, str]
) -> None:
    repo, first, tip = origin
    assert first != tip, "the fixture must have two distinct commits or it proves nothing"
    dest = tmp_path / "repos"

    rows = materialise(_manifest(tmp_path, repo, first), dest)

    assert rows == [("sample", first, True)]
    assert _run(dest / "sample", "rev-parse", "HEAD") == first


def test_a_second_run_is_idempotent(tmp_path: Path, origin: tuple[Path, str, str]) -> None:
    repo, first, _tip = origin
    dest = tmp_path / "repos"
    manifest = _manifest(tmp_path, repo, first)

    materialise(manifest, dest)
    again = materialise(manifest, dest)

    assert again == [("sample", first, False)], "a pinned clone was re-cloned or re-pinned"


def test_a_commit_the_clone_does_not_have_is_a_failure(
    tmp_path: Path, origin: tuple[Path, str, str]
) -> None:
    repo, _first, _tip = origin
    absent = "0" * 40

    with pytest.raises(FixtureCloneFailed) as caught:
        materialise(_manifest(tmp_path, repo, absent), tmp_path / "repos")

    assert "not in the clone" in caught.value.reason


def test_sabotaging_the_pin_leaves_the_clone_on_the_tip(
    tmp_path: Path, origin: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the WHOLE pinning step removed, HEAD is the tip and the known answer above fails."""
    import clone_pinned

    repo, first, tip = origin
    monkeypatch.setattr(clone_pinned, "_pin_head", lambda path, name, sha: None)

    clone_pinned.materialise(_manifest(tmp_path, repo, first), tmp_path / "repos")

    landed = _run(tmp_path / "repos" / "sample", "rev-parse", "HEAD")
    assert landed == tip, "sabotage did not take effect — the clone was already pinned somehow"
    assert landed != first, "the pin is not what puts HEAD on the pinned commit"
