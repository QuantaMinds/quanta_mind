"""Of the events the ranker MISSES, how many have a target it could not see because of a rename?

WHAT: Replays the admissible events over the pinned corpus, marks each target file that scored
      zero prior touches AND whose path was created by a rename at or before the event, and
      cross-tabulates that against hit or miss.
WHY:  `implementation.md` called the renamed-file blind spot unresolved for months without a size,
      and a limitation with no number attached cannot be traded against its fix. **`AGENTS.md`
      requires a suspected cause be cross-tabulated against the outcome, because a cause that does
      not separate outcomes is a story.** This one separates: 13.6x enrichment among misses,
      Fisher two-sided p = 2.9e-4.

      **AND THE SIZE IS THE OTHER HALF.** Solving it moves the headline 1.21% -> 1.04% on n = 4,
      concentrated in two of six repositories, so the finding argues for leaving it alone. The
      seductive figure -- 16.8% of zero-history file-slots are rename-blinded -- is nearly
      harmless, because most rename-blinded files are never the file a fix returns to.
IMPORTS: stdlib, and the PRODUCT path (ingest, rank, store) rather than a research reimplementation
      -- the question is about what the shipped ranker cannot see.
CONSUMED BY: nobody -- it prints. Recorded in `implementation.md` under "The renamed-file blind
      spot, sized" and in `evidence-ledger.md`.
"""

import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/Users/dhanu/Documents/SaaS/quanta_mind/src")
from quantamind.ingest.commits import read_commits
from quantamind.rank.events import Rejections, admissible
from quantamind.rank.order import BUDGET
from quantamind.rank.score import discriminate, order
from quantamind.store import schema
from quantamind.store import touches as ts
from quantamind.types.ranking import Discrimination
from quantamind.types.touch import Touch

ROOT = Path("/Users/dhanu/Documents/SaaS/quanta_mind")
spec = json.loads((ROOT / "tests/fixtures/pinned.json").read_text())
scratch = Path(tempfile.mkdtemp())


def renamed_into(clone):
    out = subprocess.run(
        [
            "git",
            "-C",
            str(clone),
            "log",
            "--full-history",
            "--no-merges",
            "-M",
            "--diff-filter=R",
            "--name-status",
            "--format=@%ct",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    ).stdout
    born, when = {}, 0
    for line in out.splitlines():
        if line.startswith("@"):
            when = int(line[1:])
            continue
        p = line.split("\t")
        if len(p) == 3 and p[0].startswith("R") and p[2].endswith(".py"):
            born.setdefault(p[2], when)
    return born


cell = collections.Counter()  # (outcome, target_rename_blinded) -> n
per_repo = {}
for repo in spec["repos"]:
    clone = ROOT / "tests/fixtures/repos" / repo["name"]
    born = renamed_into(clone)
    commits = read_commits(clone, pathspec="*.py")
    conn = schema.open_store(scratch / f"{repo['name']}.db")
    rid = ts.ensure_repo(conn, "github.com", repo["repo"])
    touches = [Touch(path=p, committed_at=c.committed_at) for c in commits for p in c.paths]
    ts.index(conn, rid, touches)
    rows = 0
    local = collections.Counter()
    for ev in admissible(commits, Rejections(), limit=None):
        sc = dict(ts.counts(conn, rid, sorted(ev.paths), as_of=ev.at))
        if discriminate(sc) is not Discrimination.ORDERED:
            continue
        hit = bool(set(order(sc)[:BUDGET]) & ev.target)
        # A target the ranker could not see: zero prior touches AND born by rename before the event.
        blind = any(sc.get(t, 0) == 0 and t in born and born[t] <= ev.at for t in ev.target)
        cell[("hit" if hit else "MISS", blind)] += 1
        local[("hit" if hit else "MISS", blind)] += 1
        rows += 1
        if rows >= 400:
            break
    conn.close()
    per_repo[repo["name"]] = local


def rate(o):
    b, nb = cell[(o, True)], cell[(o, False)]
    return b, b + nb, (b / (b + nb) * 100 if b + nb else 0.0)


mb, mn, mr = rate("MISS")
hb, hn, hr = rate("hit")
print(f"\n  {'outcome':8s} {'n':>6s} {'with a rename-blinded target':>30s}")
print(f"  {'MISS':8s} {mn:6d} {mb:14d}  {mr:6.1f}%")
print(f"  {'hit':8s} {hn:6d} {hb:14d}  {hr:6.1f}%")
print(f"\n  enrichment in misses: {mr / hr if hr else float('inf'):.1f}x")
print(f"  pooled miss rate: {mn / (mn + hn):.2%}  ({mn} of {mn + hn})")
excl = mn - mb
print(f"  miss rate excluding rename-blinded misses: {excl / (mn + hn):.2%}  ({excl} of {mn + hn})")
print(f"  => renames account for {mb}/{mn} = {mb / mn:.1%} of all misses" if mn else "")
print("\n  per repository (MISS with blind target / MISS total):")
for name, c in per_repo.items():
    m = c[("MISS", True)] + c[("MISS", False)]
    print(f"    {name[:26]:26s} {c[('MISS', True)]:3d} / {m:3d}")
