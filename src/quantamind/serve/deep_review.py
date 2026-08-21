"""The reviewer pass: read the ranked files with a model, then keep only what a parser can anchor.

WHAT: `deep(clone, sha, ranked, project)` runs `infer/` over the diff restricted to the files the
      ranker selected, then `verify/anchor.locate()` over every finding it returns. Reports what
      survived and what was dropped, and by which mechanism.
WHY:  **THIS IS THE HALF THE EVIDENCE SAYS IS BAD, AND THE COUNTS ARE PRINTED FOR THAT REASON.**
      Raw findings measure 66.7-82.1% wrong across four blind rater pools at 0.013-0.037 correct
      findings per pull request. Nothing here makes that untrue. What this file does is ensure the
      only findings that reach a caller are ones whose quoted code is provably in the diff, and that
      the number discarded is a value rather than an absence.

      **THE PARSER RUNS AND THE MODEL JUDGE DOES NOT, DELIBERATELY.** A string comparison decides
      whether a snippet occurs in a diff, and it has no blind spots to share with the reviewer. Two
      same-family model judges were measured on 2026-08-20: one discarded 21% of a pool at F1 37.3%,
      the other 30% at F1 34.4% while losing 16 true findings of 100. **Neither is wired in, and a
      judge is not added until one clears its pre-registered bars on a corpus it was not built on.**

      **THE MODEL IS SHOWN ONLY THE RANKED FILES.** That is the thesis and it is also the bill.
IMPORTS: infer.gemini, verify.anchor, types.finding. Rightmost layer, so both are allowed here --
      and `verify/` still cannot see `infer/`, which is the property rule 7 protects.
CONSUMED BY: `serve/cli.py` behind `--deep`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from quantamind.infer import gemini
from quantamind.infer.gemini import InferenceFailed, Unavailable
from quantamind.types.finding import Finding
from quantamind.verify.anchor import locate

GIT_TIMEOUT_S = 60

if TYPE_CHECKING:  # `Reviewed` lives in run_review, which imports THIS module at runtime.
    from quantamind.serve.run_review import Reviewed


@dataclass(frozen=True, slots=True)
class Deep:
    """What the reviewer pass produced, with every discard counted rather than absent."""

    anchored: tuple[Finding, ...]
    raw: int
    """How many the model returned before anything was dropped."""

    unanchored: int
    """Dropped because the quoted code is not in the diff. **A count, never a silence.**"""

    read: tuple[str, ...]
    """The files the model was actually shown."""


def diff_for(clone: Path, sha: str, paths: list[str]) -> str:
    """The diff of `sha` restricted to `paths`. Empty when those files did not change."""
    if not paths:
        return ""
    done = subprocess.run(
        ["git", "-C", str(clone), "show", sha, "--", *paths],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
    )
    if done.returncode != 0:
        raise gemini.InferenceFailed(
            f"git show {sha[:12]} exited {done.returncode}: {done.stderr.strip()[:120]}"
        )
    return done.stdout


def deep(clone: Path, sha: str, ranked: list[str], *, project: str) -> Deep:
    """Read `ranked` with the model, keep only findings a parser can place in the diff."""
    text = diff_for(clone, sha, ranked)
    if not text.strip():
        return Deep((), 0, 0, tuple(ranked))
    found = gemini.read(text, ranked, project=project)
    located = [locate(f, text) for f in found]
    kept = tuple(f for f in located if f is not None)
    return Deep(kept, len(found), len(found) - len(kept), tuple(ranked))


def report(clone: Path, sha: str, out: Reviewed, project: str) -> None:
    """The reviewer pass, printed with its discards. Never raises into the ranking's result."""
    ranked = [u.unit.site.path for u in out.ranking.units if u.allocation.value != "cold"]
    try:
        result = deep(clone, sha, ranked, project=project)
    except (Unavailable, InferenceFailed) as exc:
        # The ranking already printed and is not retracted by an inference failure.
        print(f"\n[deep] NOT RUN: {type(exc).__name__}: {exc}")
        return
    print(f"\n[deep] read {len(result.read)} ranked file(s)")
    print(
        f"[deep] {result.raw} raw finding(s); {result.unanchored} dropped — quote not in the diff"
    )
    for f in result.anchored:
        print(f"  {f.path}:{f.line}  {f.claim}")
    if not result.anchored:
        print("  (nothing survived the anchor check)")
    print("[deep] RAW FINDINGS MEASURE 66.7-82.1% WRONG. Anchored is not verified true.")
