"""Do the versions real projects pin actually exist on PyPI, and does the reviewer think so?

WHAT: Reads pinned requirements from real repositories, asks PyPI whether each version exists, and
      separately shows the reviewer a real dependency diff to see whether it claims a version is
      absent. Two questions, reported separately, because they have different answers.
WHY:  **THE DETECTOR AND THE VERIFIER ARE WORTH DIFFERENT AMOUNTS HERE AND CONFLATING THEM WOULD
      HIDE IT.** For the SHA class both mattered: real pins are sometimes mis-commented (0.24%), so
      a detector fires. For registry versions the prior is the opposite -- a pinned version that
      does not exist fails CI immediately, so almost none survive in a repository's main branch.
      **A detector for it would be correct and never fire.**

      The verifier is a different claim. Blind raters recorded findings asserting `awscli 1.45.34`
      is not on PyPI and that `PyCQA/isort 9.0.0b2` does not exist -- both wrong, both about
      versions that do exist. That is 3 of 45 real wrong findings, and killing them needs only the
      lookup this module performs.

      **SO THE PREVALENCE SCAN IS EXPECTED TO RETURN ~0 AND IS RUN ANYWAY.** An expectation that is
      not checked is the thing this project keeps being wrong about, and the scan is cheap.
IMPORTS: stdlib only. PyPI's JSON API, which needs no token.
CONSUMED BY: read by a human; writes `results/registry_prevalence.json`.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "registry_prevalence.json"
GH_TIMEOUT_S = 60
PYPI_TIMEOUT_S = 20

# `name==1.2.3`, the only form whose existence is decidable without resolving a range.
PINNED = re.compile(r"^([A-Za-z0-9][\w.-]*)==([0-9][\w.!+-]*)\s*$", re.M)

# **PATHS READ FROM EACH REPOSITORY'S TREE, NOT GUESSED.** The first version listed plausible
# names -- `requirements/tests.txt`, `requirements/dev.txt` -- and every one 404'd, so the scan
# read 0 pins and would have reported a base rate of 0 over an empty denominator. That is the same
# failure shape as the last two runs: a zero that describes the instrument, not the world.
SOURCES = (
    ("psf/requests", "requirements-dev.txt"),
    ("psf/requests", "docs/requirements.txt"),
    ("scrapy/scrapy", "docs/requirements.txt"),
    ("aio-libs/aiohttp", "requirements/base.txt"),
    ("aio-libs/aiohttp", "requirements/constraints.txt"),
    ("aio-libs/aiohttp", "requirements/cython.txt"),
    ("celery/celery", "requirements/default.txt"),
    ("celery/celery", "requirements/constraints.txt"),
    ("celery/celery", "requirements/deps/mock.txt"),
    ("pallets/flask", "examples/celery/requirements.txt"),
)


def fetch(repo: str, path: str) -> str:
    done = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/contents/{path}",
            "--header",
            "Accept: application/vnd.github.raw",
        ],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    return done.stdout if done.returncode == 0 else ""


def on_pypi(name: str, version: str) -> tuple[bool, bool]:
    """(reached, exists). A 404 is an answer; a timeout is not, and they are not merged."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=PYPI_TIMEOUT_S) as r:
            return True, r.status == 200
    except urllib.error.HTTPError as e:
        return True, e.code != 404
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, False


def main() -> int:
    seen: set[tuple[str, str]] = set()
    missing: list[dict[str, str]] = []
    unreachable = 0

    for repo, path in SOURCES:
        text = fetch(repo, path)
        found = PINNED.findall(text)
        for name, version in found:
            if (name.lower(), version) in seen:
                continue
            seen.add((name.lower(), version))
            reached, exists = on_pypi(name, version)
            if not reached:
                unreachable += 1
                continue
            if not exists:
                missing.append({"repo": repo, "path": path, "name": name, "version": version})
        print(f"  {repo + '/' + path:<44} {len(found):>3} pinned", flush=True)

    checked = len(seen) - unreachable
    OUT.write_text(
        json.dumps(
            {
                "distinct_pins": len(seen),
                "checked": checked,
                "unreachable": unreachable,
                "missing": missing,
            },
            indent=1,
        )
    )
    print(
        f"\n  {len(seen)} distinct pinned versions, {unreachable} unreachable and NOT counted clean"
    )
    print(f"  {checked} checked against PyPI, {len(missing)} do not exist")
    if checked:
        print(f"\n  BASE RATE = {len(missing) / checked:.2%}")
    if not missing:
        print("  ZERO. A detector for this class would be correct and would never fire.")
        print("  The VERIFIER is unaffected: it kills the model's false 'does not exist' claims,")
        print("  which is 3 of 45 wrong findings and does not depend on this rate at all.")
    for m in missing[:10]:
        print(f"    {m['repo']:<20} {m['name']}=={m['version']}")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
