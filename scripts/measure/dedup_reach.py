"""What the dedup rule would actually remove, and whether that is the redundancy it was built for.

WHAT: Runs `verify/repeats`'s similarity over the judged benchmark comments in
      `research/phase0/bench/results/candidate_labels.json` and reports, per arm, how many comments
      repeat an earlier one WITHIN a file (which the rule collapses) versus ACROSS files in the same
      pull request (which it does not). Prints the semantic redundancy from `redundancy.json`
      beside it, because those are the two numbers the dedup case rests on.
WHY:  **THE BAR 1 RESULT HAD NO COMMITTED INSTRUMENT.** Its table names arms — `graphite`,
      `copilot` — that appear in no results file in this repository, and the commit that recorded
      the result added only the product module, its tests and documentation. A measurement nobody
      can re-run is a claim, and this file exists so the next one is not.

      **IT ALSO ANSWERS THE QUESTION THE PRE-REGISTRATION LEFT OPEN.** That document says whether
      the rule detects the phenomenon the 17.3% figure counted is unverified, and that the two
      cannot be compared because our per-comment output is not on disk. It is on disk:
      `candidate_labels.json` holds all 194 OURS comments with their text and TP/FP verdict, and
      its per-arm counts match `redundancy.json`'s `emitted` exactly for all four arms.
IMPORTS: stdlib, plus `quantamind.verify.repeats` — the product rule itself, so this measures what
      ships rather than a restatement of it.
CONSUMED BY: read by a human; writes nothing.
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

from quantamind.verify.repeats import SIMILAR_AT, alike

RESULTS = pathlib.Path("research/phase0/bench/results")
PATH_IN_TEXT = re.compile(r"`([^`]*[/.][^`]*)`")
"""Only OURS states the file in its comment. **Rival arms do not**, so a within-file count for them
is not a measurement — it is the absence of a path, and it is reported as `nopath` rather than 0."""


def main() -> int:
    labels = RESULTS / "candidate_labels.json"
    counts = RESULTS / "redundancy.json"
    for needed in (labels, counts):
        if not needed.exists():
            print(f"missing {needed}; run the bench first", file=sys.stderr)
            return 1
    rows = json.loads(labels.read_text())
    semantic = json.loads(counts.read_text())

    by_arm: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in rows:
        by_arm[str(row["arm"])].append(row)

    print(f"similarity threshold {SIMILAR_AT}, autojunk disabled\n")
    header = (
        f"{'arm':<20}{'n':>5}{'nopath':>8}{'within':>8}{'across':>8}{'semantic':>10}{'sem %':>8}"
    )
    print(header)
    print("-" * len(header))
    for arm, group in by_arm.items():
        seen_by_pr: dict[str, list[dict[str, str | None]]] = collections.defaultdict(list)
        within = across = nopath = 0
        for row in group:
            found = PATH_IN_TEXT.search(str(row["text"]))
            path = found.group(1) if found else None
            nopath += path is None
            here = seen_by_pr[str(row["pr"])]
            same = [
                s
                for s in here
                if path is not None
                and s["path"] == path
                and alike(str(row["text"]), str(s["text"])) >= SIMILAR_AT
            ]
            other = [
                s
                for s in here
                if not (path is not None and s["path"] == path)
                and alike(str(row["text"]), str(s["text"])) >= SIMILAR_AT
            ]
            if same:
                within += 1
            elif other:
                across += 1
            here.append({"path": path, "text": str(row["text"])})
        stat = semantic.get(arm, {})
        matching = int(stat.get("candidates_matching", 0))
        redundant = int(stat.get("redundant", 0))
        share = f"{100.0 * redundant / matching:.1f}%" if matching else "n/a"
        print(f"{arm:<20}{len(group):>5}{nopath:>8}{within:>8}{across:>8}{redundant:>10}{share:>8}")

    print(
        "\nwithin  = repeats of an earlier claim about the SAME file — what `repeats()` collapses"
    )
    print("across  = same claim on a DIFFERENT file in one pull request — the rule keeps both")
    print("semantic= comments matching a golden a sibling already covered (redundancy.json)")
    print("\nThe rule collapses `within` only. If `within` is 0 while `semantic` is not, the rule")
    print("and the figure that justified it are measuring different things.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
