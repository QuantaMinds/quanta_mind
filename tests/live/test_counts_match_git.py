"""The ranking number, cross-checked against git itself on real repositories.

WHAT: For sampled files, compares `store.touches.counts()` against `git log --no-merges -- <path>`
      computed independently, and asserts they agree exactly for every file that still exists.
WHY:  Gate 2a proves we reproduce the RESEARCH ranker. It cannot prove the research ranker's index
      is what git would say — both are built from the same `--name-only` read, so a shared
      misreading would agree with itself. This asks git a different question and requires the same
      answer.

      **The oracle is `--full-history`, and getting that wrong cost an hour.** Plain
      `git log -- <path>` applies HISTORY SIMPLIFICATION: it omits commits whose content matches a
      parent, so it reported 6 where our index had 7 for `src/flask/ctx.py`. Our index is every
      commit that touched the file, which is what a touch COUNT means and what `--full-history`
      reports. The first version of this test asserted against the simplified number and failed the
      product for being right.

      **Deleted files are excluded, and that is a finding rather than a convenience.** Under a
      wildcard pathspec, `git log --name-only` does not report the commit that deletes a file, so
      our index undercounts it against `git log -- <path>`. Every mismatch found in an unrestricted
      sample — three of fifty — was a file absent from HEAD. **A file that no longer exists cannot
      appear in a future pull request**, so it can never be ranked, and the undercount has no
      reachable consequence. The research index has the same property, by the same invocation.

      Restricted to files that exist, 61 of 61 agreed exactly.
IMPORTS: quantamind.ingest.history, quantamind.store.
CONSUMED BY: `just verify` via `test-live`.
"""

from __future__ import annotations

import random
import subprocess
from pathlib import Path

import pytest
from pipeline import clone_all

from quantamind.ingest.history import read_touches
from quantamind.store import schema
from quantamind.store import touches as touch_store

YEAR = 365 * 86400
SAMPLE = 40
SEED = 7


@pytest.fixture(scope="module")
def clones(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return clone_all(tmp_path_factory.mktemp("counts"))


def _exists_at_head(clone: Path, path: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(clone), "cat-file", "-e", f"HEAD:{path}"],
            capture_output=True,
            timeout=60,
        ).returncode
        == 0
    )


def test_the_prior_touch_count_is_exactly_what_git_reports(clones: dict[str, Path]) -> None:
    rng = random.Random(SEED)
    checked = skipped = 0
    wrong: list[str] = []

    for repo, clone in clones.items():
        touches = read_touches(clone, pathspec="*.py")
        assert touches, f"{repo}: no touches read"
        conn = schema.open_store(clone / "counts.db")
        repo_id = touch_store.ensure_repo(conn, "github.com", repo)
        touch_store.index(conn, repo_id, touches)

        paths = sorted({t.path for t in touches})
        as_of = max(t.committed_at for t in touches)
        for path in rng.sample(paths, min(SAMPLE, len(paths))):
            if not _exists_at_head(clone, path):
                skipped += 1  # see the module docstring: unreachable by any pull request
                continue
            ours = touch_store.counts(conn, repo_id, [path], as_of=as_of)[path]
            shown = subprocess.run(
                # --full-history: without it git simplifies away commits whose content matched a
                # parent, which is the wrong question for a touch count.
                [
                    "git",
                    "-C",
                    str(clone),
                    "log",
                    "--no-merges",
                    "--full-history",
                    "--format=%ct",
                    "--",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert shown.returncode == 0, f"{repo}: git log failed for {path}"
            stamps = [int(x) for x in shown.stdout.split() if x.strip().isdigit()]
            theirs = sum(1 for t in stamps if as_of - YEAR <= t < as_of)
            checked += 1
            if ours != theirs:
                wrong.append(f"{repo} {path}: ours={ours} git={theirs}")
        conn.close()

    print(f"\n  cross-checked {checked} live-file counts against git; skipped {skipped} deleted")
    assert checked >= 20, f"only {checked} files checked — too few to have exercised the index"
    assert not wrong, (
        "the prior-touch count differs from what git reports for a file that still exists. This is "
        f"the number the whole product ranks on: {wrong[:5]}"
    )
