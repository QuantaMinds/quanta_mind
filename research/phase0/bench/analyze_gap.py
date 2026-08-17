"""Does the Greptile gap concentrate in issues whose evidence is outside the diff?

WHAT: Takes `gap_detail.json` and cross-tabulates the four outcome cells -- caught by both, only
      by Greptile, only by us, by neither -- against the golden comment's category, its severity,
      and a MECHANICAL marker of whether the issue can be seen in the diff at all.
WHY:  The hypothesis is that Greptile wins because it indexes the whole repository while we are
      shown one diff. That predicts a specific, checkable thing: the issues they catch and we miss
      should disproportionately name code we were never given.

      A CAUSE THAT DOES NOT SEPARATE OUTCOMES IS A STORY. So "needs outside context" is not read
      off the comment's prose; it is computed by pulling every backticked identifier out of the
      golden comment and asking whether it appears in the diff text we sent to the model.
IMPORTS: stdlib only (collections, json, pathlib, re, sys). Local: `corpus`.
CONSUMED BY: nobody -- it prints.
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import corpus

DETAIL = pathlib.Path(__file__).resolve().parent / "results" / "gap_detail.json"
IDENT = re.compile(r"`([^`]{2,80})`")
MIN_CELL = 10  # below this a percentage is decoration


def golden_meta() -> dict[str, tuple[str, str]]:
    """{comment text: (category, severity)} from the benchmark's own golden files."""
    out: dict[str, tuple[str, str]] = {}
    for f in sorted((corpus.BENCH / "golden_comments").glob("*.json")):
        for pr in json.loads(f.read_text()):
            for c in pr["comments"]:
                out[c["comment"]] = (c.get("category", "?"), c.get("severity", "?"))
    return out


def visible_in_diff(golden: str, diff: str) -> bool | None:
    """True when every identifier the golden names appears in the diff. None when it names none.

    A golden comment quoting `isConditionalPasskeysEnabled` is answerable from the diff only if
    that symbol is in the diff. If it is not, the issue was decidable only with repository context
    we never supplied. Comments quoting nothing are excluded rather than guessed at -- that is the
    third value, and collapsing it into either side is the defect this project keeps finding.
    """
    names = [n.strip() for n in IDENT.findall(golden) if n.strip()]
    names = [n for n in names if not n.startswith("http")]
    if not names:
        return None
    return all(n.split("(")[0].split(".")[-1] in diff for n in names)


def cell(d: dict[str, object], g: str) -> str:
    o = g in set(d["ours_caught"])  # type: ignore[arg-type]
    t = g in set(d["theirs_caught"])  # type: ignore[arg-type]
    return "both" if o and t else "onlyTHEM" if t else "onlyUS" if o else "neither"


def table(title: str, rows: dict[str, collections.Counter], order: list[str]) -> None:
    print(f"\n  {title}")
    print(f"    {'':22s} {'n':>5} {'both':>7} {'onlyTHEM':>9} {'onlyUS':>7} {'neither':>8}")
    for k in order:
        c = rows.get(k)
        if not c:
            continue
        n = sum(c.values())
        flag = "" if n >= MIN_CELL else "  (small)"
        print(
            f"    {k[:22]:22s} {n:5d} {c['both'] / n:6.0%} {c['onlyTHEM'] / n:8.0%} "
            f"{c['onlyUS'] / n:6.0%} {c['neither'] / n:7.0%}{flag}"
        )


def main() -> int:
    detail = json.loads(DETAIL.read_text())
    meta = golden_meta()

    by_cell: collections.Counter[str] = collections.Counter()
    by_cat: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_sev: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_vis: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_repo: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    gap_examples: list[tuple[str, str]] = []

    for d in detail:
        diff = corpus.diff(str(d["original"]))
        for g in d["golden"]:  # type: ignore[union-attr]
            c = cell(d, g)
            by_cell[c] += 1
            cat, sev = meta.get(g, ("?", "?"))
            by_cat[cat][c] += 1
            by_sev[sev][c] += 1
            by_repo[str(d["repo"])][c] += 1
            v = visible_in_diff(g, diff)
            by_vis["names nothing" if v is None else "visible" if v else "NOT in diff"][c] += 1
            if c == "onlyTHEM" and len(gap_examples) < 12:
                gap_examples.append((str(d["repo"]), g))

    tot = sum(by_cell.values())
    print(f"  {tot} golden comments, {len(detail)} pull requests\n")
    for k in ("both", "onlyTHEM", "onlyUS", "neither"):
        print(f"    {k:10s} {by_cell[k]:4d} {by_cell[k] / tot:7.1%}")
    print(f"\n  net gap: {by_cell['onlyTHEM'] - by_cell['onlyUS']:+d} issues")

    table(
        "THE HYPOTHESIS TEST — is the issue visible in the diff we were given?",
        by_vis,
        ["visible", "NOT in diff", "names nothing"],
    )
    table(
        "by category",
        by_cat,
        [k for k, _ in sorted(by_cat.items(), key=lambda kv: -sum(kv[1].values()))],
    )
    table("by severity", by_sev, ["Critical", "High", "Medium", "Low"])
    table("by repository", by_repo, sorted(by_repo))

    print("\n  ISSUES GREPTILE CAUGHT AND WE MISSED — first 12 verbatim")
    for repo, g in gap_examples:
        print(f"    [{repo}] {g[:150]}")
    return 0


sys.exit(main())
