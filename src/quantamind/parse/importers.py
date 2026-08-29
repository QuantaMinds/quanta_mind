"""Which files import the one that changed — the evidence for "did it disturb anything else".

WHAT: `importers(clone, sha, path)` returns the repository files whose imports resolve to `path`,
      at that commit. `Unresolved` records for files that would not parse.
WHY:  **"WITHOUT DISTURBING ANYTHING ELSE" IS HALF THE QUESTION A REVIEW ANSWERS, AND NOTHING
      COULD ANSWER IT.** The reviewer could say what a change did and not whether anything
      depended on it, so every comment ended with a line admitting cross-file impact was unchecked.
      This is the first thing that checks it.

      **A GREP SHORTLIST, THEN A PARSE — NEITHER ALONE IS HONEST.** Scanning every file with `ast`
      costs a parse of the whole repository on every review. Grepping alone matches the name in a
      comment, a string, or a longer name that merely contains it. So `git grep` narrows the
      candidates and `parse/python_names` decides, which is exact on the files it can read.

      **WHAT THIS CANNOT SEE IS NAMED, NOT ASSUMED AWAY.** A dynamic `importlib` call, a re-export
      through a package `__init__`, and an import in a language we do not parse are all invisible
      here. An empty result therefore means "no STATIC Python import found", never "nothing depends
      on this" — and the caller must render it as the former. A file that will not parse comes back
      as `Unresolved`, because a syntax error is not the absence of a dependency.
IMPORTS: stdlib, plus `parse.python_names` and `types.verdict`. Leftward only.
CONSUMED BY: `serve/deep_review.py`, for the impact half of the review.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.parse.python_names import UnparseableSource, names_in
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

GREP_TIMEOUT_S = 60
SHOW_TIMEOUT_S = 30
MAX_CANDIDATES = 200


def module_of(path: str) -> str:
    """`src/quantamind/infer/gemini.py` -> `quantamind.infer.gemini`. Empty for a non-module."""
    if not path.endswith(".py"):
        return ""
    parts = Path(path).with_suffix("").parts
    trimmed = [p for p in parts if p not in {"src", "."}]
    if trimmed and trimmed[-1] == "__init__":
        trimmed = trimmed[:-1]
    return ".".join(trimmed)


def _candidates(clone: Path, sha: str, module: str) -> list[str]:
    """Files mentioning the module's last two segments. A shortlist, not an answer."""
    needle = ".".join(module.split(".")[-2:]) if "." in module else module
    done = subprocess.run(
        ["git", "-C", str(clone), "grep", "-l", "-F", needle, sha, "--", "*.py"],
        capture_output=True,
        text=True,
        timeout=GREP_TIMEOUT_S,
    )
    if done.returncode not in (0, 1):  # 1 is "no match", which is a result
        return []
    found = [line.split(":", 1)[1] for line in done.stdout.splitlines() if ":" in line]
    return found[:MAX_CANDIDATES]


def _source(clone: Path, sha: str, path: str) -> str | None:
    done = subprocess.run(
        ["git", "-C", str(clone), "show", f"{sha}:{path}"],
        capture_output=True,
        timeout=SHOW_TIMEOUT_S,
    )
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else None


def importers(clone: Path, sha: str, path: str) -> tuple[tuple[str, ...], tuple[Unresolved, ...]]:
    """Files importing `path`'s module at `sha`, and the ones we could not read.

    **AN EMPTY RESULT MEANS NO STATIC PYTHON IMPORT WAS FOUND.** It does not mean nothing depends
    on this file, and a caller that renders it as "nothing is affected" is making a claim this
    cannot support.
    """
    module = module_of(path)
    if not module:
        return (), ()

    found: list[str] = []
    unreadable: list[Unresolved] = []
    for candidate in _candidates(clone, sha, module):
        if candidate == path:
            continue
        source = _source(clone, sha, candidate)
        if source is None:
            continue
        try:
            names = names_in(source)
        except UnparseableSource:
            unreadable.append(
                Unresolved(Site(candidate), Reason.UNPARSEABLE_SYNTAX, Construct.IMPORT)
            )
            continue
        beneath = module + "."
        if any(m.name == module or m.name.startswith(beneath) for m in names.imports):
            found.append(candidate)
    return tuple(sorted(found)), tuple(unreadable)
