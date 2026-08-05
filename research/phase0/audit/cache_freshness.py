"""Is anything in `data/gh_cache` stale on the fields the analysis actually consumes?

WHAT: Re-fetches a random sample of cached pull-request payloads live and diffs them
      field by field against the copies on disk.
WHY:  Several recorded numbers -- rebase prevalence, the k distribution, changed-lines
      quartiles -- are computed from cached GitHub payloads. If the cache were stale those
      numbers would be wrong in a way nothing else would reveal, because a stale payload
      parses perfectly and produces a plausible answer.

      **The result is expected, and the reason matters more than the result.** Every field
      consumed here is immutable once a pull request is merged: `merge_commit_sha`,
      `merged_at`, `base.ref`, `commits`, `additions`, `deletions` and `changed_files`
      cannot change after the merge, because the merge is what fixed them. So the honest
      claim is not "we tested it and it matched" -- which would be weak evidence from a
      small sample -- but "these fields are immutable post-merge, and a sample confirms no
      corruption or partial write". A mismatch would mean a bug in the cache writer, not a
      changed upstream.

      Checked by re-fetching rather than by reasoning about file dates or TTLs. A cache
      file written today can still hold a payload captured under a stale conditional
      request, and mtime cannot tell the difference.
IMPORTS: stdlib json/glob/random/subprocess; the `gh` CLI. Nothing from phase0.
CONSUMED BY: run by hand; prints a per-PR verdict and a total.
"""

from __future__ import annotations

import glob
import json
import random
import subprocess
import sys
from pathlib import Path

CACHE = Path("E:/Code/quanta_mind/research/phase0/data/gh_cache")

# Immutable once merged. Anything mutable -- title, labels, review state -- is excluded on
# purpose: a difference there would be a real upstream change and not a cache fault, and
# including it would produce failures that mean nothing.
FIELDS = ("merge_commit_sha", "commits", "additions", "deletions", "merged_at", "changed_files")


def main() -> int:
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    files = [
        f
        for f in sorted(glob.glob(str(CACHE / "pr-*.json")))
        if "-commits" not in f and "-files" not in f and "probe" not in f
    ]
    random.Random(seed).shuffle(files)

    mismatched = 0
    checked = 0
    for path in files[:size]:
        cached = json.loads(Path(path).read_text(encoding="utf-8"))
        repo = ((cached.get("base") or {}).get("repo") or {}).get("full_name")
        number = cached.get("number")
        if not repo or not number:
            continue
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls/{number}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if out.returncode != 0:
            print(f"  {repo}#{number}: LIVE FETCH FAILED -- not counted either way")
            continue
        live = json.loads(out.stdout)
        checked += 1
        differs = {k: (cached.get(k), live.get(k)) for k in FIELDS if cached.get(k) != live.get(k)}
        if (cached.get("base") or {}).get("ref") != (live.get("base") or {}).get("ref"):
            differs["base.ref"] = (
                (cached.get("base") or {}).get("ref"),
                (live.get("base") or {}).get("ref"),
            )
        if differs:
            mismatched += 1
        print(f"  {repo}#{number}: {'OK' if not differs else f'DIFFERS {differs}'}")

    print(f"\n{checked - mismatched}/{checked} cached payloads identical to live")
    print("Expected: these fields are immutable once merged. A mismatch is a cache-writer")
    print("bug, not a changed upstream, and should be treated as one.")
    return 1 if mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
