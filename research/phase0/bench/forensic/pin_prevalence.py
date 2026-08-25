"""How often is a pinned action's version comment actually wrong, in the wild?

WHAT: Reads the workflow files of many real repositories at HEAD, extracts every action pinned to a
      SHA with a trailing `# vX.Y.Z` comment, and resolves each against GitHub's tag list. Reports
      how many pins carry a comment the tag list contradicts.
WHY:  **THIS IS THE CHEAPEST WAY TO FALSIFY THE DETECTOR BEFORE ANYTHING IS BUILT ON IT.**
      `verify/pin_mismatch.detect()` scored 24 of 24 on constructed trials -- but those trials were
      built to contain mismatches. **If real pins are never mis-commented, the detector is correct
      and useless**, and the honest thing is to find that out first rather than after shipping it.

      **THE STOCK BOUNDS THE FLOW.** The product fires on pull requests, so what it would actually
      catch is how often a change INTRODUCES a wrong comment. That is rarer and much more expensive
      to sample. The stock -- how many pins are wrong right now, across many repositories -- is
      cheap and is an upper bound worth having first: a defect that does not exist in the stock
      cannot be introduced by the flow.

      **A PIN WITH NO COMMENT IS NOT A DEFECT AND IS NOT COUNTED.** `uses: x/y@<sha>` with no
      trailing version is honest; there is nothing to contradict. Counting it would inflate the
      denominator with pins the detector would never speak about.

      **AN UNRESOLVABLE PIN IS COUNTED SEPARATELY, NEVER AS CLEAN.** A repository we could not read
      tags for produces no mismatch, which is indistinguishable from one with none.
IMPORTS: stdlib; the product's `verify.pin_mismatch` resolvers, so the base rate is measured with
      the same code that would fire.
CONSUMED BY: read by a human; writes `results/pin_prevalence.json`.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "src"))

from quantamind.verify.external_facts import tags_at  # noqa: E402

OUT = HERE.parent / "results" / "pin_prevalence.json"
GH_TIMEOUT_S = 60
PIN = re.compile(
    r"uses:\s*([A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*)@([0-9a-f]{7,40})\s*#\s*(v?\d[\w.]*)"
)

REPOS = (
    "psf/requests",
    "pallets/flask",
    "encode/httpx",
    "pydantic/pydantic",
    "astral-sh/ruff",
    "tiangolo/fastapi",
    "scrapy/scrapy",
    "python-poetry/poetry",
    "pypa/pip",
    "sqlalchemy/alembic",
    "home-assistant/core",
    "numpy/numpy",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "django/django",
    "celery/celery",
    "aio-libs/aiohttp",
    "prometheus/prometheus",
    "grafana/grafana",
    "kubernetes/kubernetes",
    "cli/cli",
    "hashicorp/terraform",
)


def workflows(repo: str) -> list[tuple[str, str]]:
    """[(path, text)] for each workflow file at HEAD. Empty when the repo has none we can read."""
    done = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/.github/workflows"],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    if done.returncode != 0:
        return []
    try:
        listing = json.loads(done.stdout)
    except json.JSONDecodeError:
        return []
    out = []
    for entry in listing if isinstance(listing, list) else []:
        name = str(entry.get("name", ""))
        if not name.endswith((".yml", ".yaml")):
            continue
        got = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/contents/.github/workflows/{name}",
                # **`--jq` AND the raw header together return NOTHING.** raw emits YAML, jq then
                # fails, the command exits non-zero, and this read that as "no workflow files":
                # the first run reported 0 files from a repository with four, which would have
                # produced a base rate over an empty denominator.
                "--header",
                "Accept: application/vnd.github.raw",
            ],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
        )
        if got.returncode == 0 and got.stdout.strip():
            out.append((name, got.stdout))
    return out


def main() -> int:
    cache: dict[tuple[str, str], list[str]] = {}
    pins = mismatched = unresolved = 0
    findings: list[dict[str, str]] = []

    for repo in REPOS:
        here = 0
        for _name, text in workflows(repo):
            for action, sha, comment in PIN.findall(text):
                pins += 1
                here += 1
                key = (action, sha[:12])
                if key not in cache:
                    reached, tags = tags_at(action, sha)
                    cache[key] = tags if reached else []
                    if not reached:
                        unresolved += 1
                        continue
                tags = cache[key]
                if not tags:
                    unresolved += 1
                    continue
                want = comment.lstrip("v")
                if not any(t.lstrip("v") == want for t in tags):
                    mismatched += 1
                    findings.append(
                        {
                            "repo": repo,
                            "action": action,
                            "sha": sha[:12],
                            "commented": comment,
                            "actual": ", ".join(tags),
                        }
                    )
        print(f"  {repo:<32} {here:>3} commented pin(s)", flush=True)

    OUT.write_text(
        json.dumps(
            {
                "pins": pins,
                "mismatched": mismatched,
                "unresolved": unresolved,
                "repos": len(REPOS),
                "findings": findings,
            },
            indent=1,
        )
    )

    checkable = pins - unresolved
    print(f"\n  {pins} commented pins across {len(REPOS)} repositories")
    print(f"  {unresolved} could not be resolved and are NOT counted as clean")
    print(f"  {checkable} checkable, of which {mismatched} carry a comment GitHub contradicts")
    if checkable:
        print(f"\n  BASE RATE = {mismatched / checkable:.2%} of resolvable commented pins")
    if not mismatched:
        print("\n  ZERO. The detector is correct and would never fire. Recorded as a closed road.")
    for f in findings[:12]:
        print(f"    {f['repo']:<26} {f['action']:<28} says {f['commented']:<9} is {f['actual']}")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
