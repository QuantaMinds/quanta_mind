"""Map every previously drawn PR URL to its AIDev `pr_id`, so A47's `unseen` half exists.

WHAT: Reads the prior draws' blind sheets, extracts `(repo, number)` from each PR URL,
      and resolves each pair against the agent population to a `pr_id`. Writes the id
      list plus every pair that would NOT resolve.
WHY:  A47's stopping rule counts UNSEEN records, and the two sides speak different
      languages: a blind sheet carries `owner/repo/pull/N`, the journal carries an AIDev
      `pr_id`, and nothing joined them. Without this the rule can only be evaluated on
      the raw or capped count, both of which OVERSTATE what a draw can reach.

      Reads ONLY the blind sheets (`label_id,pr_url`). **No `_key.csv` is opened**: a key
      carries the classifier's verdict, and the overlap filter needs identity. Identity
      is what a draw must not repeat; the verdict is not needed to know that, and opening
      a key to compute something that does not need it is how blindness stops being
      provable.

      Unresolved pairs are NAMED, never dropped. A pair that will not resolve is a
      `pr_id` the unseen filter cannot exclude, so the residual pool is overstated by
      exactly that count and the number must travel with the filter.
IMPORTS: stdlib csv/json/re/pathlib; phase0.population.agent for the population.
CONSUMED BY: the A47 evaluation; `results/drawn_pr_ids.json`.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from phase0.population.agent import agent_prs

URL = re.compile(r"github\.com/([^/]+/[^/]+)/pull/(\d+)")


def drawn_urls(sheets: list[Path]) -> dict[tuple[str, int], list[str]]:
    found: dict[tuple[str, int], list[str]] = {}
    for sheet in sheets:
        if not sheet.exists():
            print(f"  MISSING {sheet}", file=sys.stderr)
            continue
        n = 0
        with sheet.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                match = URL.search(row.get("pr_url", ""))
                if not match:
                    continue
                key = (match.group(1), int(match.group(2)))
                found.setdefault(key, []).append(sheet.parent.name or sheet.stem)
                n += 1
        print(f"  {n:3d} rows from {sheet}", file=sys.stderr)
    return found


def main() -> int:
    aidev = Path(sys.argv[1])
    sheets = [Path(p) for p in sys.argv[2:-1]]
    out = Path(sys.argv[-1])

    print("reading blind sheets (no key opened):", file=sys.stderr)
    drawn = drawn_urls(sheets)
    print(f"  {len(drawn)} DISTINCT (repo, number) pairs drawn", file=sys.stderr)

    print("loading the agent population...", file=sys.stderr)
    population = agent_prs(aidev)
    index = {(c.repo, c.number): str(c.pr_id) for c in population}
    print(f"  {len(population)} candidates, {len(index)} distinct (repo, number)", file=sys.stderr)

    resolved: dict[str, dict[str, object]] = {}
    unresolved: list[str] = []
    for (repo, number), seeds in sorted(drawn.items()):
        pr_id = index.get((repo, number))
        if pr_id is None:
            unresolved.append(f"{repo}#{number}")
            continue
        resolved[pr_id] = {"repo": repo, "number": number, "seeds": sorted(set(seeds))}

    out.write_text(
        json.dumps(
            {
                "drawn_pairs": len(drawn),
                "resolved_pr_ids": sorted(resolved),
                "resolved": resolved,
                # Named, never dropped. A pair that will not resolve is a pr_id the
                # unseen filter cannot exclude, so the residual pool is overstated by
                # exactly this count and the number has to travel with the filter.
                "unresolved": sorted(unresolved),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"resolved {len(resolved)} / {len(drawn)}; unresolved {len(unresolved)}", file=sys.stderr)
    for u in unresolved:
        print(f"  UNRESOLVED {u}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
