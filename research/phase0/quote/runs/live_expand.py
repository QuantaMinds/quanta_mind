"""Live mechanical test: does expansion fire on real diffs, and do the anchors survive?

WHAT: Expands every hunk of real merged pull requests and asserts, per pull request, that the added
      lines land on exactly the same (path, line, text) as before. Prints the expansion rate.
WHY:  The unit test proves the mechanism on one hand-built hunk. Real diffs bring renames, new
      files, binary files, `\\ No newline at end of file`, headers git could not compute, and files
      whose base content moved -- none of which a fixture contains. A silent anchor shift would
      corrupt every finding's line number while every gate still passed.

      IT RUNS ON ALREADY-BURNED REPOSITORIES ON PURPOSE. This measures a string transform, not a
      wrong-rate, so it cannot leak into a correctness result -- and spending fresh repositories on
      a mechanical check would leave fewer for the measurement that actually needs them.
IMPORTS: stdlib only (collections, sys). Local: `corpus`, `expand`, `gate`.
CONSUMED BY: nobody -- it prints and exits non-zero on any anchor shift.
"""

from __future__ import annotations

import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import expand
import gate

import corpus

TOTAL: collections.Counter[str] = collections.Counter()
shifted: list[str] = []


def _fetcher(repo: str, sha: str, cache: dict[str, list[str] | None]):
    """A per-pull-request blob reader. Bound here so the closure cannot capture a loop variable."""

    def fetch(path: str) -> list[str] | None:
        if path not in cache:
            try:
                cache[path] = corpus.blob(repo, sha, path)
            except corpus.FetchFailed:
                cache[path] = None
        return cache[path]

    return fetch


def anchors(d: str) -> list[tuple[str, int, str]]:
    added, _ = gate.added_lines(d)
    return [(p, ln, t) for p, ln, t, _h in added]


prs = corpus.pulls(corpus.REPOS_D10, 6)
print(f"  {len(prs)} merged pull requests, {len(corpus.REPOS_D10)} repositories (already burned)\n")
for i, pr in enumerate(prs, 1):
    repo, num = str(pr["repo"]), int(str(pr["number"]))
    try:
        d = corpus.diff(repo, num)
        sha = corpus.base_sha(repo, num)
    except corpus.FetchFailed as exc:
        print(f"  {i:2d} {repo}#{num} FETCH FAILED {str(exc)[:50]}")
        TOTAL["fetch_failed"] += 1
        continue

    cache: dict[str, list[str] | None] = {}

    fetch = _fetcher(repo, sha, cache)

    out, st = expand.expand(d, fetch)
    for k, v in st.items():
        TOTAL[k] += v
    before, after = anchors(d), anchors(out)
    ok = before == after
    if not ok:
        shifted.append(f"{repo}#{num}")
        TOTAL["ANCHOR_SHIFT"] += 1
    grew = len(out) - len(d)
    print(
        f"  {i:2d} {repo.split('/')[-1][:14]:14s} #{num:<6d} hunks {st['hunks']:3d}  "
        f"expanded {st['expanded']:3d}  no-header {st['no_header']:3d}  "
        f"+{grew:5d} chars  anchors {'OK' if ok else 'SHIFTED'}"
    )

h = TOTAL["hunks"] or 1
print(f"\n  hunks {TOTAL['hunks']}   expanded {TOTAL['expanded']} ({TOTAL['expanded'] / h:.1%})")
print(
    f"  not expanded: no_header {TOTAL['no_header']} ({TOTAL['no_header'] / h:.1%})  "
    f"no_file {TOTAL['no_file']} ({TOTAL['no_file'] / h:.1%})  "
    f"not_found {TOTAL['not_found']} ({TOTAL['not_found'] / h:.1%})"
)
print(f"\n  ANCHOR SHIFTS: {len(shifted)} {shifted if shifted else '-- the invariant held'}")
sys.exit(1 if shifted else 0)
