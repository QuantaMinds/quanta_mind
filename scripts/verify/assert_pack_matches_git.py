"""Recompute every row of the pack from git, and require the same answer.

WHAT: Groups the pack's `touch` rows by path, asks `git log --full-history --no-merges` the same
      question per path, and compares the timestamp lists exactly. Every path, not a sample.
WHY:  **This is the research's verification model applied to the pack.**
      `research/phase0/claims/verify.py` recomputes every headline number from its stored artefact
      and asserts nothing from memory or from a document, because this project has already shipped
      a kappa of 0.66 reported as 0.92 and an anchor check that read 98.1% while blind raters found
      the anchors wrong. **A claim with no receipt is a claim waiting to drift, and a human
      signature is not a receipt** -- that anchor check was signed and wrong.

      So the pack is not reviewed and frozen. It is RE-DERIVED, on every run, from a source that
      knows nothing about our code.

      **The oracle asks git a DIFFERENT question than we did.** `ingest` reads one
      `git log --name-only` over the whole history and splits it; this asks per path. A shared
      misreading of a single stream cannot make both agree, which is the failure gate 2a cannot
      see: it compares us to the research ranker, and both are built from the same read.

      **`--full-history` or the oracle is wrong.** Plain `git log -- <path>` applies history
      simplification and omits commits whose content matched a parent -- 6 against our 7 for
      `src/flask/ctx.py`. `test_counts_match_git.py` failed the product for being right once
      already, and `ingest/commits.py` carried the same defect in the other direction.

      **A SHORTFALL IS EXCUSED ONLY BY A VERIFIED DELETION.** Under a wildcard pathspec
      `git log --name-only` does not report the commit that DELETES a file, so the pack runs short
      there. That is not taken on trust: each missing timestamp is checked against
      `--diff-filter=D` for the same path, and anything git does not record as a deletion is a
      complaint. On the pinned corpus 100 of 261 paths are short and every one is a real deletion.

      **"PRESENT IN HEAD" IS NOT "NEVER DELETED", and assuming it was cost this check two false
      disagreements on its first run.** `src/flask/app.py` was renamed into `sansio/` -- a deletion
      of the old path -- and later re-created as a shim, so it sits in HEAD with a deletion in its
      history. A rename is a deletion for the path it left.
IMPORTS: scripts/verify/git_oracle.py; stdlib otherwise.
CONSUMED BY: `just verify-pack-vs-git`, which `just verify` runs.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys as _sys

_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import shutil
import sqlite3
import subprocess
import sys

from git_oracle import deletions, timestamps


def _pack(pack: pathlib.Path) -> dict[str, list[int]]:
    conn = sqlite3.connect(pack)
    rows: dict[str, list[int]] = collections.defaultdict(list)
    for path, when in conn.execute("SELECT path, committed_at FROM touch"):
        rows[str(path)].append(int(when))
    conn.close()
    for stamps in rows.values():
        stamps.sort()
    return dict(rows)


def compare(pack: pathlib.Path, clone: pathlib.Path) -> tuple[int, int, list[str]]:
    """(paths checked, shortfalls excused by a verified deletion, complaints)."""
    stored = _pack(pack)
    if not stored:
        return 0, 0, ["the pack holds no touches; every comparison over it would pass vacuously"]
    complaints: list[str] = []
    excused = 0

    for path in sorted(stored):
        ours = collections.Counter(stored[path])
        theirs = collections.Counter(timestamps(clone, path))
        if ours == theirs:
            continue
        extra = ours - theirs
        if extra:
            complaints.append(
                f"{path}: the pack holds {sum(extra.values())} touch(es) git does not, at "
                f"{sorted(extra)[:4]} — the pack cannot know more than git"
            )
            continue
        # Short. The ONLY excusable shortfall is a deletion commit, which a wildcard --name-only
        # read does not report. That is verified per timestamp rather than assumed.
        missing = theirs - ours
        removed = deletions(clone, path)
        unexplained = missing - removed
        if unexplained:
            complaints.append(
                f"{path}: the pack is {sum(unexplained.values())} touch(es) short at "
                f"{sorted(unexplained)[:4]}, and git does not record a deletion there"
            )
        else:
            excused += 1
    return len(stored), excused, complaints


def self_test(pack: pathlib.Path, clone: pathlib.Path) -> None:
    """Move one timestamp in a COPY and require the comparison to notice.

    A verifier that cannot be shown to fail is a verifier nobody should read. This project has
    shipped one already: `assert_deterministic.py` declared a wall-clock exclusion list, never
    applied it, and reported success for as long as three runs finished inside one second.
    """
    probe = pack.with_suffix(".selftest.db")
    shutil.copy(pack, probe)
    conn = sqlite3.connect(probe)
    conn.execute(
        "UPDATE touch SET committed_at = committed_at + 1 "
        "WHERE rowid = (SELECT MIN(rowid) FROM touch)"
    )
    conn.commit()
    conn.close()
    _checked, _excused, complaints = compare(probe, clone)
    probe.unlink()
    if not complaints:
        raise SystemExit(
            "[pack-vs-git] SELF-TEST FAILED: moving one timestamp by a second did not produce a "
            "complaint, so this comparison is not reading the data it claims to compare."
        )


def _assert_paired(clone: pathlib.Path) -> None:
    """The clone must be at the pinned commit, or this compares two different histories.

    Nothing in a pack records which commit produced it, so `--pack X --clone Y` is trusted
    pairing. A clone at a LATER commit makes the pack look short everywhere, which reads as data
    corruption rather than as the operator having passed the wrong directory.
    """
    manifest = pathlib.Path(__file__).resolve().parent / "pinned_clone.json"
    want = json.loads(manifest.read_text())["sha"]
    done = subprocess.run(
        ["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, timeout=60
    )
    got = done.stdout.decode("utf-8", "replace").strip()
    if done.returncode != 0 or got != want:
        raise SystemExit(
            f"[pack-vs-git] {clone} is at {got[:12] or '?'}, but the corpus is pinned at "
            f"{want[:12]}. Comparing a pack against a different history reports every difference "
            f"as data corruption. Run `just verify-pack-vs-git`, which builds and checks together."
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=pathlib.Path)
    parser.add_argument("--clone", required=True, type=pathlib.Path)
    args = parser.parse_args(argv[1:])

    _assert_paired(args.clone)

    self_test(args.pack, args.clone)
    checked, excused, complaints = compare(args.pack, args.clone)

    if complaints:
        print(f"[pack-vs-git] {len(complaints)} path(s) disagree with git:", file=sys.stderr)
        for line in complaints[:20]:
            print(f"  {line}", file=sys.stderr)
        print(
            "  The pack was not recomputed from the same read git was asked for. This is the "
            "check that a golden pack would otherwise be trusted to make.",
            file=sys.stderr,
        )
        return 1
    print("[pack-vs-git] self-test ok — a one-second move is detected")
    print(
        f"[pack-vs-git] ok — {checked} path(s) recomputed from git; {excused} short by a "
        f"deletion commit, each one verified to BE a deletion rather than assumed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
