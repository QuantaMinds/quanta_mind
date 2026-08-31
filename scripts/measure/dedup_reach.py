"""What the dedup rule would actually remove, and whether that is the redundancy it was built for.

WHAT: Runs `verify/repeats`'s similarity over the judged benchmark comments in
      `research/phase0/bench/results/candidate_labels.json` and reports, per arm, how many comments
      repeat an earlier one WITHIN a file (which the rule collapses) versus ACROSS files in the same
      pull request (which it does not), beside the semantic redundancy from `redundancy.json`.
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
from difflib import SequenceMatcher

from quantamind.verify.repeats import SIMILAR_AT, _plain, alike

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

    _localise(rows)
    _grouping_reach(rows)
    print("\nwithin = repeat of an earlier claim about the SAME file — all `repeats()` collapses")
    print("across = same claim on a DIFFERENT file in one pull request — the rule keeps both")
    print("semantic = comments matching a golden a sibling already covered. `within` is 0 while")
    print("`semantic` is not, so the rule and the figure justifying it measure different things.")
    return 0


def _localise(rows: list[dict[str, str]]) -> None:
    """Which pull requests hold the redundant comments, and what they have in common.

    **`redundant` IS A SUBTRACTION AND NAMES NOBODY.** `redundancy.json` records only totals, so
    the individual comments are recovered here: per pull request, TP comments minus goldens
    covered. The positive excesses sum to 17 for OURS -- the figure the aggregate reports -- while
    a naive total gives 13, because the two judge passes disagree by four comments.
    """
    detail = RESULTS / "gap_detail.json"
    if not detail.exists():
        return
    gap = {r["key"]: r for r in json.loads(detail.read_text())}
    tp_by_pr: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in rows:
        if row["arm"] == "OURS" and row["verdict"] == "TP":
            tp_by_pr[str(row["pr"])].append(row)

    excesses = [
        (len(tp_by_pr[key]) - len(rec["ours_caught"]), key)
        for key, rec in gap.items()
        if len(tp_by_pr[key]) > len(rec["ours_caught"])
    ]
    if not excesses:
        return
    no_file = shared = 0
    for _excess, key in excesses:
        found = [PATH_IN_TEXT.search(str(t["text"])) for t in tp_by_pr[key]]
        named = [m.group(1) for m in found if m]
        no_file += sum(1 for m in found if m is None)
        shared += sum(n - 1 for n in collections.Counter(named).values() if n > 1)

    total = sum(e for e, _ in excesses)
    print(f"\nOURS: {total} redundant comment(s) across {len(excesses)} pull request(s)")
    print(f"  keyed on a function, naming no file: {no_file}")
    print(
        f"  sharing a file with a sibling:       {shared}"
        "  <- the most a within-file rule could reach"
    )


IDENTIFIER = re.compile(r"`[^`]*`")
"""Backticked spans -- paths, functions, symbols -- the part that differs between two reports of ONE
defect at different sites. Removing them is the most favourable test a text grouper can be given,
so the reach below is a CEILING, not an estimate."""


def _grouping_reach(rows: list[dict[str, str]]) -> None:
    """Could a text rule GROUP one defect's sites into a single finding? Measured, and it cannot.

    **THE MECHANISM WAS DESIGNED AFTER READING FIVE PULL REQUESTS OF THIS CORPUS**, so this is a
    fit, not a test. It counts against the mechanism rather than for it: the rule fails on the very
    data it was shaped to fit. A confirmatory number would need a corpus nobody has read.
    """
    detail = RESULTS / "gap_detail.json"
    if not detail.exists():
        return
    gap = {r["key"]: r for r in json.loads(detail.read_text())}
    tp_by_pr: dict[str, list[str]] = collections.defaultdict(list)
    for row in rows:
        if row["arm"] == "OURS" and row["verdict"] == "TP":
            tp_by_pr[str(row["pr"])].append(str(row["text"]))

    excess = {
        key: len(tp_by_pr[key]) - len(rec["ours_caught"])
        for key, rec in gap.items()
        if len(tp_by_pr[key]) > len(rec["ours_caught"])
    }
    total = sum(excess.values())
    if not total:
        return

    def site_free(text: str) -> str:
        return _plain(IDENTIFIER.sub(" ", text))

    print(f"\ngrouping reach — could one finding carry N sites? ({total} redundant comments)")
    for threshold in (SIMILAR_AT, 0.70, 0.60, 0.50):
        grouped = 0
        for key in excess:
            claims = tp_by_pr[key]
            taken: set[int] = set()
            for i in range(len(claims)):
                if i in taken:
                    continue
                for j in range(i + 1, len(claims)):
                    if j in taken:
                        continue
                    ratio = SequenceMatcher(
                        None, site_free(claims[i]), site_free(claims[j]), autojunk=False
                    ).ratio()
                    if ratio >= threshold:
                        taken.add(j)
                        grouped += 1
        pct = 100 * grouped // total
        print(f"  threshold {threshold:.2f}: {grouped:>2} of {total} grouped ({pct}%)")
    print("  below ~0.60 a text rule fuses different defects, undetectably: identity is semantic.")


if __name__ == "__main__":
    raise SystemExit(main())
