"""What share of hunks produced a symbol, and why the rest did not.

WHAT: Classifies every `@@` hunk header across the full-object clones as def / class / other /
      bare, so a low symbol count can be told apart from a broken extractor.
WHY:  Gate 3c first reported a 7.4-point gap on m/k = 1.17 symbols per changed file -- low
      enough to be either a property of the changes or a broken parser, and both produce the
      same number and the same p-value. This found the cause: 38.3% of hunks named a `class`,
      because git's DEFAULT funcname heuristic takes the nearest line starting in column 0,
      which in Python is the class and never the indented method. The fix was git's python
      diff driver; the gap survived it.
IMPORTS: stdlib only (collections, os, re, subprocess).
CONSUMED BY: docs/plans/implementation.md, gate 3c.

The gate 3c result rests on m/k = 1.17 symbols per changed file, which is low enough to be
either a true property of these changes or a broken extractor. Those two produce the same
number and the same p-value, so this classifies every hunk header instead of guessing.

  def      -- git named an enclosing function. The extractor took it.
  class    -- git named an enclosing class, not a function. Real code, no symbol recorded.
  other    -- git named something else.
  BARE     -- no funcname text at all. If this dominates, git's python diff driver is not
              active on these repositories and the extraction is broken rather than sparse.

The distinction matters because it points at different fixes. Sparse-but-correct means the
gap stands. Bare-dominated means the function arm was measured against a crippled index and
the 7.4-point gap is an artefact.
"""

from __future__ import annotations

import collections
import os
import re
import subprocess

CL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clones")
DEF = re.compile(r"^@@ .*@@\s*(?:async\s+)?def\s+([A-Za-z_]\w*)")
CLS = re.compile(r"^@@ .*@@\s*class\s+([A-Za-z_]\w*)")
ANY = re.compile(r"^@@ [^@]*@@\s*(\S.*)$")


def main() -> None:
    full = []
    for d in sorted(os.listdir(CL)):
        p = os.path.join(CL, d)
        if not os.path.isdir(os.path.join(p, ".git")):
            continue
        if (
            subprocess.run(
                ["git", "-C", p, "config", "--get", "remote.origin.partialclonefilter"],
                capture_output=True,
            ).returncode
            != 0
        ):
            full.append(d)

    grand = collections.Counter()
    samples: list[str] = []
    print(f"  {'repository':34s} {'hunks':>7} {'def':>7} {'class':>6} {'other':>6} {'BARE':>7}")
    for name in full:
        repo = os.path.join(CL, name)
        out = subprocess.run(
            [
                "git",
                "-C",
                repo,
                "log",
                "--no-merges",
                "-U0",
                "-p",
                "-n",
                "4000",
                "--pretty=format:%x00",
                "--",
                "*.py",
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if out.returncode != 0:
            print(f"  {name:34s} READ FAILED exit {out.returncode}")
            continue
        c = collections.Counter()
        for line in out.stdout.split("\n"):
            if not line.startswith("@@"):
                continue
            c["hunks"] += 1
            if DEF.match(line):
                c["def"] += 1
            elif CLS.match(line):
                c["class"] += 1
            elif ANY.match(line):
                c["other"] += 1
                if len(samples) < 8:
                    samples.append(line[:100])
            else:
                c["bare"] += 1
                if len(samples) < 8:
                    samples.append(line[:100])
        grand.update(c)
        h = c["hunks"] or 1
        print(
            f"  {name:34s} {c['hunks']:7d} {c['def'] / h:6.1%} {c['class'] / h:5.1%} "
            f"{c['other'] / h:5.1%} {c['bare'] / h:6.1%}"
        )

    h = grand["hunks"] or 1
    print(f"\n  TOTAL {grand['hunks']} hunks")
    print(f"    def   (symbol recorded) {grand['def']:7d}  {grand['def'] / h:6.1%}")
    print(f"    class (no symbol)       {grand['class']:7d}  {grand['class'] / h:6.1%}")
    print(f"    other (no symbol)       {grand['other']:7d}  {grand['other'] / h:6.1%}")
    print(f"    BARE  (no funcname)     {grand['bare']:7d}  {grand['bare'] / h:6.1%}")
    print("\n  sample non-def headers:")
    for s in samples:
        print(f"    {s}")


main()
