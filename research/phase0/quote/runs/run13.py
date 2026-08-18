"""Design thirteen: the same ninety pull requests reviewed three ways, paired.

WHAT: Arm A is design nine unchanged. Arm B adds enclosing-function expansion. Arm C adds the
      repository's own conventions file. Every published finding is written with its arm for a
      blind adjudication that never sees the label.
WHY:  Both mechanisms are Qodo's, the top tool of 49 on Martian's offline layer, and this project
      discards both. Bars, corpus and power are fixed in
      docs/plans/preregistrations/expansion-conventions-preregistration.md before this ran.

      THE ANCHOR INVARIANT IS CHECKED PER PULL REQUEST AND ABORTS THE RUN. Expansion rewrites the
      diff the gate derives every line number from. A silent shift would corrupt every anchor in
      arms B and C while every gate still reported success -- the exact shape of defect this
      project has shipped before.
IMPORTS: stdlib only (collections, concurrent.futures, json, pathlib, sys). Local: `conventions`,
      `corpus`, `expand`, `gate`, `paths`, `reviewer`, and the Vertex `client`.
CONSUMED BY: nobody -- it prints and writes results/quote13_run.json.
"""

from __future__ import annotations

import collections
import concurrent.futures
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "vertex"))

import conventions
import expand
import gate
import paths
import reviewer
from client import Client

import corpus

MODEL = "gemini-2.5-pro"
OUT = pathlib.Path(__file__).resolve().parent.parent / "results" / "quote13_run.json"
WORKERS = 4


class AnchorShift(RuntimeError):
    """Expansion moved an added line. Never recoverable, never counted and continued past."""


def anchors(d: str) -> list[tuple[str, int, str]]:
    added, _ = gate.added_lines(d)
    return [(p, ln, t) for p, ln, t, _h in added]


def rules_for(repo: str) -> tuple[str, dict[str, object] | None]:
    """The repository's conventions block, or ('', None) when it has none."""
    try:
        names = corpus.root_names(repo, "HEAD")
    except corpus.FetchFailed:
        return "", None
    bodies: dict[str, str] = {}
    for name in conventions.names_to_try(names):
        got = corpus.blob(repo, "HEAD", name)
        if got:
            bodies[name] = "\n".join(got)
    picked = conventions.select(bodies)
    if not picked:
        return "", None
    block, sent = conventions.render(picked, bodies[picked])
    return block, sent


def prepare(pr: dict) -> dict | None:
    """Everything one pull request needs, fetched once and shared by all three arms."""
    repo, num = str(pr["repo"]), int(str(pr["number"]))
    try:
        full = corpus.diff(repo, num)
        sha = corpus.base_sha(repo, num)
    except corpus.FetchFailed as exc:
        return {"repo": repo, "pr": num, "error": f"fetch: {str(exc)[:70]}"}
    d, _removed, kept = paths.filter_diff(full)
    if kept == 0 or not d.strip():
        return {"repo": repo, "pr": num, "error": "nothing reviewable"}

    cache: dict[str, list[str] | None] = {}

    def fetch(path: str) -> list[str] | None:
        if path not in cache:
            try:
                cache[path] = corpus.blob(repo, sha, path)
            except corpus.FetchFailed:
                cache[path] = None
        return cache[path]

    expanded, st = expand.expand(d, fetch)
    if anchors(expanded) != anchors(d):
        raise AnchorShift(f"{repo}#{num}: expansion moved an added line")
    return {
        "repo": repo,
        "pr": num,
        "title": str(pr["title"]),
        "url": str(pr.get("url") or ""),
        "plain": d,
        "expanded": expanded,
        "expand_stats": st,
        "files": kept,
    }


def review_arms(client: Client, job: dict, rules: str) -> dict:
    """Three reviews of one pull request. A gate failure is recorded, never dropped silently."""
    out: dict[str, object] = {"raw": {}, "published": {}, "failed": {}}
    for arm, diff_text, rule_text in (
        ("A", job["plain"], ""),
        ("B", job["expanded"], ""),
        ("C", job["expanded"], rules),
    ):
        try:
            findings, finish = reviewer.review(client, job["title"], diff_text, rules=rule_text)
        except reviewer.ReviewFailed as exc:
            out["failed"][arm] = str(exc)[:90]  # type: ignore[index]
            continue
        added, sizes = gate.added_lines(diff_text)
        pub = []
        for f in findings:
            v = gate.check(f, diff_text, added, sizes)
            if v["ok"]:
                v |= {"repo": job["repo"], "pr": job["pr"], "arm": arm, "url": job["url"]}
                pub.append(v)
        out["raw"][arm] = len(findings)  # type: ignore[index]
        out["published"][arm] = pub  # type: ignore[index]
        out["finish_" + arm] = finish
    return out


def main() -> int:
    prs = corpus.pulls(corpus.REPOS_D13, corpus.PER_REPO_D13)
    print(f"  {len(prs)} pull requests, {len(corpus.REPOS_D13)} repositories never touched\n")

    rules: dict[str, str] = {}
    sent: dict[str, object] = {}
    for repo in corpus.REPOS_D13:
        block, meta = rules_for(repo)
        rules[repo] = block
        sent[repo] = meta
        m = meta or {}
        print(f"    rules {repo:24s} {m.get('file', '-- none --')} {m.get('lines_sent', 0)} lines")

    print("\n  fetching and expanding...")
    jobs: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for j in pool.map(prepare, prs):
            if j and not j.get("error"):
                jobs.append(j)
    ex = collections.Counter()
    for j in jobs:
        ex.update(j["expand_stats"])
    h = ex["hunks"] or 1
    print(
        f"  {len(jobs)}/{len(prs)} usable   hunks {ex['hunks']}  expanded {ex['expanded']} "
        f"({ex['expanded'] / h:.1%})   ANCHOR SHIFTS 0 (a shift would have aborted)"
    )

    client = Client(MODEL)
    results: list[dict] = []
    print("\n  reviewing three arms each...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(review_arms, client, j, rules[j["repo"]]): j for j in jobs}
        for n, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            j = futs[fut]
            r = fut.result()
            r |= {"repo": j["repo"], "pr": j["pr"], "url": j["url"]}
            results.append(r)
            c = {a: len(r["published"].get(a, [])) for a in "ABC"}
            print(
                f"    {n:3d}/{len(jobs)} {j['repo'].split('/')[-1][:13]:13s} #{j['pr']:<6d} "
                f"A {c['A']}  B {c['B']}  C {c['C']}   {r['failed'] or ''}"
            )

    per_arm = {a: [f for r in results for f in r["published"].get(a, [])] for a in "ABC"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"results": results, "rules_sent": sent, "expand": dict(ex), "prs": len(jobs)}, indent=1
        )
    )
    print(f"\n  published   A {len(per_arm['A'])}   B {len(per_arm['B'])}   C {len(per_arm['C'])}")
    for a in "ABC":
        print(f"  H4 yield arm {a}: {len(per_arm[a]) / max(1, len(jobs)):.2f} per PR   bar >= 0.30")
    print("\n  Wrong-rates need the blind adjudication. Run adjudicate.py 13 next.")
    return 0


sys.exit(main())
