"""Materialise the pinned corpus named in `tests/fixtures/pinned.json`, at its exact commits.

WHAT: Clones each repository in the manifest with no working tree, moves `HEAD` onto the pinned
      commit, and verifies `rev-parse HEAD` returns that commit. Idempotent: a directory already
      sitting at the right commit is left alone. Prints one line per repository and exits non-zero
      if any of them is not at its pinned commit.
WHY:  `just fixtures` ran `git submodule update --init tests/fixtures/repos` against a repository
      with no `.gitmodules` and no submodules registered. It exited 1 every time it was run, and
      `CONTRIBUTING.md` told readers it was "not needed yet", so nobody ran it. Gate 2b -- the one
      gate standing between the ranker and the claim the company rests on -- was blocked on a
      fixture mechanism that did not exist.

      `--no-checkout`, AND WITHOUT `--filter`. The clone carries the whole commit and tree
      history and never writes a working tree, which is all `git log --name-only` reads.
      `--filter=blob:none` would be sound for the same reason and would halve the disk, and it is
      what the original research clones used -- but `check_no_partial_clone.py` bans the flag
      outright and was written precisely because an abandoned blobless strategy outlived its own
      withdrawal in the code. Taking the exception here would be the move that guard exists to
      stop, so this pays the disk instead. The tradeoff is stated in the pull request, not worked
      around in silence.

      NOT `--bare`, though a bare clone would be smaller still: `ingest/commits.py` refuses a
      directory with no `.git`, along with shallow and partial clones, because each of them reads
      wrong without ever failing. The fixture is shaped to the product rather than the product
      relaxed to the fixture.

      HEAD IS MOVED, NOT ASSUMED. A fresh clone's HEAD is the default branch's tip, which is not
      the commit the measurement ran at and drifts every time upstream merges. `git log` with no
      revision reads HEAD, so leaving it alone would silently measure a different history that
      still produces a plausible number.

      A MISSING COMMIT IS A FAILURE, NEVER A FALLBACK. If upstream has force-pushed the pinned
      commit out of reach, this stops. Ranking against whatever the branch points at today would
      reproduce the shape of the result and none of its provenance.
IMPORTS: stdlib only (argparse, json, pathlib, subprocess, sys). No project imports.
CONSUMED BY: `just fixtures`; `tests/live/test_gate_2b_pinned_corpus.py`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CLONE_TIMEOUT_S = 1800
GIT_TIMEOUT_S = 60
PINNED_REF = "refs/heads/pinned"


class FixtureCloneFailed(RuntimeError):
    """A repository is not at its pinned commit. Never silently a different history."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


def _git(args: list[str], timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], capture_output=True, timeout=timeout)


def _head_of(path: Path) -> str | None:
    """The commit `HEAD` resolves to, or None when this is not a readable repository."""
    if not path.exists():
        return None
    done = _git(["-C", str(path), "rev-parse", "HEAD"], GIT_TIMEOUT_S)
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", "replace").strip()


def _pin_head(path: Path, name: str, sha: str) -> None:
    """Point HEAD at `sha`, then verify it. Raises rather than leaving HEAD where it was."""
    if _git(["-C", str(path), "cat-file", "-e", f"{sha}^{{commit}}"], GIT_TIMEOUT_S).returncode:
        raise FixtureCloneFailed(
            name,
            f"pinned commit {sha[:12]} is not in the clone — upstream may have force-pushed it "
            f"out of reach. Refusing to rank against whatever the branch points at today.",
        )
    for args in (["update-ref", PINNED_REF, sha], ["symbolic-ref", "HEAD", PINNED_REF]):
        done = _git(["-C", str(path), *args], GIT_TIMEOUT_S)
        if done.returncode != 0:
            raise FixtureCloneFailed(
                name, f"git {args[0]} exited {done.returncode}: {done.stderr[:160]!r}"
            )
    landed = _head_of(path)
    if landed != sha:
        raise FixtureCloneFailed(name, f"HEAD is {landed} after pinning, expected {sha}")


def materialise(manifest: Path, dest_root: Path) -> list[tuple[str, str, bool]]:
    """[(name, sha, freshly_cloned)] for every repository, each verified to be at its commit.

    Raises `FixtureCloneFailed` for any repository that cannot be put at its pinned commit. The
    caller gets no partial success: a corpus missing one of its six is not the corpus the interval
    was measured on.
    """
    spec = json.loads(manifest.read_text())
    dest_root.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, str, bool]] = []

    for repo in spec["repos"]:
        out.append(pin(repo["name"], repo["sha"], repo["url"], dest_root / repo["name"]))
    return out


def pin(name: str, sha: str, url: str, dest: Path, checkout: bool = False) -> tuple[str, str, bool]:
    """(name, sha, freshly_cloned) for ONE repository, verified to be at its commit.

    Public because `scripts/verify/build_pack.py` needs the same thing for a different corpus, and
    two implementations of "clone at a commit and check it landed" is the drift pattern this
    project keeps finding: one of them acquires the verification and the other does not.

    **`checkout` writes the working tree, and the source-leak check needs it.** Gate 2b reads only
    `git log`, so its clones carry no files at all; `assert_no_source_in_pack.py` searches the
    repository's actual SOURCE for stored values, and against a bare tree it would find nothing
    and report a clean run -- a check whose subject is absent passes for the wrong reason.
    """
    if _head_of(dest) == sha and (not checkout or (dest / "README.md").exists()):
        return (name, sha, False)
    if not dest.exists():
        # No --filter: see the module docstring. --no-checkout is the whole history with no
        # working tree, which is everything `git log --name-only` reads.
        done = _git(["clone", "--no-checkout", "-q", url, str(dest)], CLONE_TIMEOUT_S)
        if done.returncode != 0:
            raise FixtureCloneFailed(name, f"clone exited {done.returncode}: {done.stderr[:200]!r}")
    _pin_head(dest, name, sha)
    if checkout:
        done = _git(["-C", str(dest), "reset", "--hard", "--quiet", sha], CLONE_TIMEOUT_S)
        if done.returncode != 0:
            raise FixtureCloneFailed(
                name, f"could not write the working tree: {done.stderr[:200]!r}"
            )
    return (name, sha, True)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Clone the pinned corpus at its exact commits.")
    parser.add_argument("--manifest", type=Path, default=root / "tests/fixtures/pinned.json")
    parser.add_argument("--dest", type=Path, default=root / "tests/fixtures/repos")
    args = parser.parse_args()

    try:
        rows = materialise(args.manifest, args.dest)
    except FixtureCloneFailed as exc:
        print(f"  FAILED — {exc}", flush=True)
        return 1

    for name, sha, fresh in rows:
        print(f"  {'cloned ' if fresh else 'present'}  {name:26s} {sha[:12]}", flush=True)
    print(f"\n  {len(rows)} repositories at their pinned commits in {args.dest}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
