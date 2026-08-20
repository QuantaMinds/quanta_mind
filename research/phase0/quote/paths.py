"""Strip generated and non-code files out of a diff before the model ever sees it.

WHAT: `reviewable()` decides whether one path may be reviewed; `filter_diff()` rebuilds a unified
      diff containing only reviewable files, and reports what it removed.
WHY:  Design eight published 18 findings about lockfiles and **every one of them was WRONG** -- the
      model claimed versions did not exist on PyPI and that 2026 timestamps were future dates, on
      merged pull requests with machine-generated hashes and passing CI. It cannot query a package
      index from a diff, and its training cutoff makes the dates look impossible.

      THE FILTER RUNS BEFORE THE CALL, NOT AFTER. Removing these findings afterwards would leave
      the model spending its attention budget on files it cannot reason about. Removing the files
      means the budget goes to code.

      `.github/` IS KEPT ON PURPOSE. CI configuration is hand-written and produced three of design
      eight's eight CORRECT findings. Excluding it because it is YAML would repeat the bucketing
      error that made the design-eight stratification wrong the first time it was computed.
IMPORTS: stdlib only (re).
CONSUMED BY: `run9.py` and `run14.py` in this package.
"""

from __future__ import annotations

import re

# Fixed in docs/plans/preregistrations/reviewer/path-filter-preregistration.md before the run.
LOCKFILE = re.compile(r"(^|/)([^/]*\.lock|package-lock\.json|yarn\.lock|pylock[^/]*\.toml)$")
MANIFEST = re.compile(r"(^|/)(pyproject\.toml|requirements[^/]*\.txt|Pipfile|package\.json)$")
DOCS = re.compile(r"\.(md|mdx|rst|html)$")
# Design fourteen only. Fixed in
# docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md before the run.
CI = re.compile(r"^\.github/")
CONFIG = re.compile(r"\.(ya?ml|cfg|ini|toml)$")


def reason(path: str) -> str | None:
    """Why this path is excluded, or None if it is reviewable. Named, never a bare boolean."""
    if LOCKFILE.search(path):
        return "lockfile"
    if MANIFEST.search(path):
        return "dependency manifest"
    if DOCS.search(path):
        return "documentation"
    return None


def reviewable(path: str) -> bool:
    return reason(path) is None


def reason_strict(path: str) -> str | None:
    """`reason()`, plus the CI and config paths design fourteen excludes.

    **`reason()` IS LEFT EXACTLY AS IT WAS, and that is the point.** Designs nine through thirteen
    ran against it; editing it in place would silently change what those runs are recorded as
    having done, and this project has voided measurements over an instrument that changed
    mid-study. The new rule is a new function.

    **The `.github/` decision is REVERSED here, on evidence, and the old reason is still true.**
    This module says CI configuration is kept on purpose because it "produced three of design
    eight's eight CORRECT findings". Design thirteen's blind adjudication, recomputed from
    `adj13/verdicts.json` against its sealed key, says `.github/` is **65.6% wrong** across 32
    findings and supplies **21 of the 28 EXTERNAL failures** -- the model asserting that a pinned
    action SHA is not tagged what it is tagged, which no diff can settle. Design eight's reading
    was right on design eight's data and is outlived.
    """
    named = reason(path)
    if named:
        return named
    if CI.search(path):
        return "CI configuration"
    if CONFIG.search(path):
        return "configuration"
    return None


def filter_diff(diff: str, strict: bool = False) -> tuple[str, dict[str, int], int]:
    """(filtered diff, {reason: files removed}, files kept).

    Splits on `diff --git` so a removed file takes its whole hunk set with it. Returning the counts
    rather than logging them means a run that filtered everything is distinguishable from a run
    whose model found nothing -- the collapse this project keeps having to undo.
    """
    removed: dict[str, int] = {}
    kept_chunks: list[str] = []
    kept = 0
    for chunk in diff.split("diff --git "):
        if not chunk.strip():
            continue
        # **ANCHORED, BECAUSE `re.search(r"b/(\S+)")` MATCHED THE `b/` INSIDE `.github/`.**
        # "github" ends in b, so `.github/workflows/ci.yml` extracted as `workflows/ci.yml` and
        # every CI path escaped a filter written to catch it. The `.yml` rule still caught most of
        # them by extension, which is why this survived: the filter looked like it worked because a
        # DIFFERENT rule was doing its job. `.github/workflows/tpu-tests.yml.disabled` is the one
        # that got through and put four findings into design fourteen's pool.
        m = re.match(r"a/(.*?) b/(.+)$", chunk.split("\n", 1)[0])
        path = m.group(2) if m else ""
        why = reason_strict(path) if strict else reason(path)
        if why:
            removed[why] = removed.get(why, 0) + 1
            continue
        kept += 1
        kept_chunks.append("diff --git " + chunk)
    return "".join(kept_chunks), removed, kept
