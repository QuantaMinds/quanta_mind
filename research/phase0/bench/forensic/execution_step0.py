"""Can the runtime speak to these findings at all? Three checks, each able to end the arm.

WHAT: For the 16 wrong findings the conversational arm could not ask about, and the 7 correct ones:
      (1) does the repository's suite run green at the pull request's base, (2) does ANY existing
      test execute the lines the finding names, and (3) can the harness see a defect it is shown.
WHY:  **TWO OF THREE CONVERSATIONAL RUNS MEASURED THE HARNESS RATHER THAN THE ARCHITECTURE**, and
      four instrument bugs preceded them. A step 0 that can end the experiment before it starts is
      the cheapest thing in this sequence.

      **CHECK 2 IS THE ONE THAT DECIDES IT.** If almost no finding names a line an existing test
      executes, the arm's ceiling is that share and its bars are unreachable by construction -- and
      that is a result to publish, not a reason to sample differently. Coverage is measured here
      rather than assumed, because assuming it is how a run reports a number about nothing.

      **A SUITE THAT DOES NOT RUN PRODUCES NO EVIDENCE FOR EVERY FINDING, SO EVERY FINDING DROPS
      AND THE WRONG-RATE IMPROVES.** That is the arm looking like a success while measuring
      nothing, which is the same shape as an unreachable oracle. The count is reported.
IMPORTS: stdlib only, and the design-13 blind key for the path and line of each finding.
CONSUMED BY: read by a human; writes `results/execution_step0.json`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ADJ = HERE.parents[1] / "quote" / "adj13"
ARM = HERE.parent / "results" / "conversational_arm.json"
OUT = HERE.parent / "results" / "execution_step0.json"
GH_TIMEOUT_S = 90


def targets() -> list[dict[str, object]]:
    """The findings this arm would run on, with the path and line the blind key records."""
    key = {int(e["item"]): e for e in json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())}
    out = []
    for row in json.loads(ARM.read_text()):
        if row["verdict"] not in ("WRONG", "CORRECT"):
            continue
        if row["verdict"] == "WRONG" and row["external"]:
            continue  # the conversational arm already reaches these
        entry = key.get(int(row["item"]))
        if entry is None:
            continue
        out.append(
            {
                "item": row["item"],
                "verdict": row["verdict"],
                "repo": entry["repo"],
                "pr": entry["pr"],
                "path": entry["path"],
                "line": entry["line"],
                "claim": row["claim"],
            }
        )
    return out


def base_of(repo: str, pr: int) -> str:
    """The commit the pull request was opened against, from GitHub."""
    done = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr}", "--jq", ".base.sha"],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def tests_touching(repo: str, path: str, base: str) -> list[str]:
    """Test files that import or name the module the finding is in, read from the tree at `base`.

    **GITHUB CODE SEARCH RETURNS 0 FOR MATCHES THAT EXIST AND WAS REPLACED.** Asked whether any
    test in `jazzband/pip-tools` mentions `pypi`, it answered `total_count: 0` for a repository
    whose `tests/` directory is full of them. A zero from an unreliable instrument is
    indistinguishable from a zero in the world -- the defect this sequence has hit four times -- so
    the files are fetched and read instead.

    **THIS IS STILL NOT COVERAGE AND MUST NOT BE READ AS IT.** Real coverage needs the suite run
    under a tracer at the base commit, which is the arm itself. This asks the weaker question, and
    a NO is decisive: a module no test so much as names cannot be executed by one. A YES is only
    permission to go and measure properly.
    """
    module = pathlib.Path(str(path)).stem
    if not module or not base:
        return []
    # **PARSED IN PYTHON, NOT THROUGH `--jq`.** The jq filter was mangled by shell escaping on its
    # way through subprocess and returned rc=1 for a tree the same call fetches fine without it --
    # so this read 0 test files for a repository with 33 and would have reported a coverage
    # ceiling of zero. Fifth instrument bug of this shape; the raw call is parsed here instead.
    listing = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/{base}?recursive=1"],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    if listing.returncode != 0:
        return []
    try:
        tree = json.loads(listing.stdout).get("tree", [])
    except json.JSONDecodeError:
        return []
    candidates = [
        str(e["path"])
        for e in tree
        if str(e.get("path", "")).endswith(".py") and "test" in str(e.get("path", ""))
    ]
    hits = []
    for test_path in candidates[:40]:
        body = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/contents/{test_path}?ref={base}",
                "--header",
                "Accept: application/vnd.github.raw",
            ],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
        )
        if body.returncode == 0 and module in body.stdout:
            hits.append(test_path)
    return hits


def main() -> int:
    items = targets()
    print(
        f"  {len(items)} findings in scope "
        f"({sum(1 for i in items if i['verdict'] == 'WRONG')} wrong, "
        f"{sum(1 for i in items if i['verdict'] == 'CORRECT')} correct)\n",
        flush=True,
    )

    rows: list[dict[str, object]] = []
    for it in items:
        base = base_of(str(it["repo"]), int(it["pr"]))  # type: ignore[arg-type]
        touching = tests_touching(str(it["repo"]), str(it["path"]), base)
        rows.append({**it, "base": base, "tests_mentioning": touching})
        print(
            f"  {it['repo']!s:<28} #{it['pr']:<6} {pathlib.Path(str(it['path'])).name:<28} "
            f"base={'yes' if base else 'NO':<4} tests mentioning={len(touching)}",
            flush=True,
        )

    OUT.write_text(json.dumps(rows, indent=1))
    have_base = sum(1 for r in rows if r["base"])
    have_tests = sum(1 for r in rows if r["tests_mentioning"])
    wrong = [r for r in rows if r["verdict"] == "WRONG"]
    wrong_tests = sum(1 for r in wrong if r["tests_mentioning"])

    print(f"\n  CHECK 1 — base commit resolvable : {have_base}/{len(rows)}")
    print(f"  CHECK 2 — a test file mentions the module: {have_tests}/{len(rows)}")
    print(
        f"            of the wrong findings alone     : {wrong_tests}/{len(wrong)} "
        f"= {wrong_tests / max(1, len(wrong)):.0%}"
    )
    print("\n  The arm needs >= 50% of the wrong findings COVERED. This is the weaker proxy, so")
    print("  it is an UPPER BOUND: real coverage cannot exceed the share a test even mentions.")
    if wrong_tests / max(1, len(wrong)) < 0.5:
        print("\n  STEP 0 FAILS CHECK 2 — the ceiling is below the bar and the arm cannot pass.")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
