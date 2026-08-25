"""Select pull requests an execution arm could actually adjudicate, and report the selection rate.

WHAT: Scans merged pull requests across candidate repositories and keeps those that change SOURCE
      whose modules an existing test names. Reports how many were considered against how many
      survived, and writes the candidate list a grader would work from.
WHY:  **STEP 0 KILLED THE LAST ARM BECAUSE THE POOL WAS THE WRONG SHAPE**, not because the
      mechanism failed: 44% of its semantic findings were claims about test files -- where the suite
      that would adjudicate is the subject of the claim -- 19% about configuration no test imports,
      and 31% about source a suite runs. Selecting for that property up front is what makes a
      labelling round affordable: filtering AFTER adjudication needs 835 findings for 15 correct,
      selecting first needs 180.

      **THE SELECTION RATE IS THE POINT, NOT A DIAGNOSTIC.** If very few pull requests survive, the
      corpus is the subset of code that happens to be well tested, and that is a real limit on what
      a pass would transfer to. It is reported whatever it is, because a rate nobody looks at is
      how a corpus becomes unrepresentative quietly.

      **A TEST NAMING THE MODULE IS NOT COVERAGE AND IS NOT CALLED IT.** Real coverage needs the
      suite run under a tracer, which is the arm itself. A NO here is decisive -- a module no test
      mentions cannot be executed by one -- and a YES is permission to go and measure properly.
IMPORTS: stdlib only. GitHub through `gh`.
CONSUMED BY: read by a human; writes `results/execution_corpus.json` — the grader's worklist.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "execution_corpus.json"
GH_TIMEOUT_S = 90
PER_REPO = 30

# Config and lockfiles are excluded because no test imports them, and a finding about one cannot be
# adjudicated by running anything. This is the 19% step 0 found.
NOT_SOURCE = (".yml", ".yaml", ".toml", ".cfg", ".ini", ".txt", ".md", ".lock", ".json")

CANDIDATES = (
    "psf/requests",
    "pallets/flask",
    "encode/httpx",
    "pydantic/pydantic",
    "scrapy/scrapy",
    "aio-libs/aiohttp",
    "celery/celery",
    "jazzband/pip-tools",
    "tornadoweb/tornado",
    "urllib3/urllib3",
    "pypa/packaging",
    "kevin1024/vcrpy",
)


def gh(path: str, raw: bool = False) -> str:
    args = ["gh", "api", path]
    if raw:
        args += ["--header", "Accept: application/vnd.github.raw"]
    done = subprocess.run(args, capture_output=True, text=True, timeout=GH_TIMEOUT_S)
    return done.stdout if done.returncode == 0 else ""


def merged(repo: str, limit: int) -> list[dict[str, object]]:
    body = gh(f"repos/{repo}/pulls?state=closed&per_page={limit * 2}")
    if not body:
        return []
    try:
        return [p for p in json.loads(body) if p.get("merged_at")][:limit]
    except json.JSONDecodeError:
        return []


def source_touched(repo: str, number: int) -> list[str]:
    """Source files the pull request changed. Tests and configuration are excluded here."""
    body = gh(f"repos/{repo}/pulls/{number}/files?per_page=100")
    if not body:
        return []
    try:
        files = json.loads(body)
    except json.JSONDecodeError:
        return []
    out = []
    for f in files:
        path = str(f.get("filename", ""))
        name = path.rsplit("/", 1)[-1]
        if not path.endswith(".py") or path.endswith(NOT_SOURCE):
            continue
        if "test" in name or "/tests/" in path or name == "conftest.py":
            continue
        out.append(path)
    return out


def test_names(repo: str, base: str) -> str:
    """Every test file's text at `base`, concatenated. One read per repository, not per finding."""
    body = gh(f"repos/{repo}/git/trees/{base}?recursive=1")
    if not body:
        return ""
    try:
        tree = json.loads(body).get("tree", [])
    except json.JSONDecodeError:
        return ""
    paths = [
        str(e["path"])
        for e in tree
        if str(e.get("path", "")).endswith(".py") and "test" in str(e.get("path", ""))
    ][:50]
    return "\n".join(gh(f"repos/{repo}/contents/{p}?ref={base}", raw=True) for p in paths)


def main() -> int:
    rows: list[dict[str, object]] = []
    considered = 0

    for repo in CANDIDATES:
        pulls = merged(repo, PER_REPO)
        if not pulls:
            print(f"  {repo:<24} unreachable or no merged pull requests", flush=True)
            continue
        corpus = test_names(repo, str(pulls[0].get("base", {}).get("sha", "")))
        kept = 0
        for pull in pulls:
            considered += 1
            number = int(pull["number"])
            touched = source_touched(repo, number)
            if not touched:
                continue
            covered = [p for p in touched if p.rsplit("/", 1)[-1][:-3] in corpus]
            if not covered:
                continue
            kept += 1
            rows.append(
                {
                    "repo": repo,
                    "pr": number,
                    "base": pull.get("base", {}).get("sha", ""),
                    "source_changed": touched,
                    "named_by_a_test": covered,
                    "url": pull.get("html_url", ""),
                }
            )
        print(f"  {repo:<24} {len(pulls):>3} merged, {kept:>2} qualify", flush=True)

    OUT.write_text(json.dumps({"considered": considered, "selected": rows}, indent=2))
    rate = len(rows) / considered if considered else 0.0
    print(f"\n  {considered} merged pull requests considered, {len(rows)} qualify = {rate:.0%}")
    print("\n  A LOW RATE IS A LIMIT ON TRANSFER, not a reason to widen the filter: the corpus")
    print("  would be the subset of code that happens to be well tested.")
    print("\n  at 8.3% correct on source findings and 1.27 findings per pull request,")
    if rows:
        print(
            f"  {len(rows)} pull requests yield about {len(rows) * 1.27:.0f} findings "
            f"and {len(rows) * 1.27 * 0.083:.1f} correct."
        )
        print(f"  15 correct needs about {15 / 0.083 / 1.27:.0f} qualifying pull requests.")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
