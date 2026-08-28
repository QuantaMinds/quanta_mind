"""The reviewer pass: read the ranked files with a model, then keep only what a parser can anchor.

WHAT: `examine(...)` is the delivery-facing entry point: it applies the allocation and the
      settings policy, then calls `deep(clone, sha, ranked, project)`, which runs `infer/` over
      the diff restricted to the files the
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
IMPORTS: infer.gemini, verify.{anchor,publishable}, ingest.change_shape, types.deep, and
      render.{deep_report,shape_line}. Rightmost layer, so all of them are allowed here -- and
      `verify/` still cannot see `infer/`, which is the property rule 7 protects.

      **THE RECORD AND THE PRINTING BOTH LEFT THIS FILE.** `Deep` is in `types/` because `render/`
      prints it and may not import `serve/`; `render/deep_report.py` holds the text. What is left
      here is one concern -- running the pass -- which is rule 6, and what pushed the split was
      this file crossing the 200-line cap while `serve/` sat at its 15-file directory cap.
CONSUMED BY: `serve/cli.py` behind `--deep`.
"""

from __future__ import annotations

import subprocess
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from quantamind.allocate.depth import Reading
from quantamind.infer import gemini
from quantamind.infer.gemini import InferenceFailed, Unavailable
from quantamind.ingest.change_shape import shape
from quantamind.ingest.review_window import WindowUnreadable
from quantamind.render.deep_report import lines
from quantamind.render.shape_line import block
from quantamind.serve.settle import settle
from quantamind.types.deep import Deep
from quantamind.types.settings import Settings
from quantamind.verify import publishable
from quantamind.verify.anchor import locate

GIT_TIMEOUT_S = 60

if TYPE_CHECKING:  # `Reviewed` lives in run_review, which imports THIS module at runtime.
    from quantamind.serve.run_review import Reviewed


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


def context_for(clone: Path, sha: str, changed: list[str]) -> str:
    """The change's shape as prompt text. Empty when git could not settle the commit's own time.

    **A SHAPE THAT CANNOT BE MEASURED YIELDS NO CONTEXT, NEVER A GUESSED ONE.** `change_shape`
    raises rather than falling back to a wall-clock window, and the honest response to that here
    is the empty string -- the prompt the model saw before any of this was measured.
    """
    try:
        return block(shape(clone, sha, changed))
    except WindowUnreadable:
        return ""


def deep(
    clone: Path,
    sha: str,
    ranked: list[str],
    *,
    project: str,
    changed: list[str] | None = None,
    gcloud: str = "gcloud",
) -> Deep:
    """Read `ranked` with the model, keep only findings a parser can place in the diff.

    **THE MODEL READS ONLY `ranked`, BUT IS TOLD THE SHAPE OF THE WHOLE CHANGE.** Those are
    different scopes on purpose: the thesis is that inference goes only where the ranker pointed,
    while "6 files where your median is 2" is a fact about the change and would be false if
    counted over the three files we happened to fund.
    """
    text = diff_for(clone, sha, ranked)
    if not text.strip():
        # Not "the model found nothing" -- it was never asked, because those paths carry no diff.
        return Deep((), 0, 0, 0, 0, tuple(ranked), consulted=False)
    found, spent = gemini.read(
        text,
        ranked,
        project=project,
        context=context_for(clone, sha, changed or ranked),
        gcloud=gcloud,
    )
    located = [f for f in (locate(x, text) for x in found) if f is not None]

    # **ANCHOR, THEN ORACLE, THEN THE MODEL'S OWN SECOND LOOK.** Ordered by cost: anchoring is
    # local and free, an oracle is one network call, and settling is two model calls. A finding
    # whose quote is not in the diff never reaches GitHub.
    surviving, refuted = [], 0
    for finding in located:
        if publishable.gate(finding, text).publishes:
            surviving.append(finding)
        else:
            refuted += 1

    kept, withdrawn = [], 0
    for finding in surviving:
        try:
            decided = settle(finding, project=project, today=date.today().isoformat())
        except (InferenceFailed, Unavailable):
            # **A SETTLE THAT COULD NOT RUN KEEPS THE FINDING.** Dropping on failure would make an
            # outage look like a filter working, which is the shape this project keeps catching.
            kept.append(finding)
            continue
        if decided.publishes:
            kept.append(finding)
        else:
            withdrawn += 1

    return Deep(
        tuple(kept),
        len(found),
        len(found) - len(located),
        refuted,
        withdrawn,
        tuple(ranked),
        # **A FLOOR WHEN ANYTHING WAS SETTLED.** `settle()` asks the model per surviving finding
        # through `infer/prompt_once`, which reports no usage — so this is a floor, and says so.
        spend=spent if not surviving else replace(spent, complete=False),
    )


def report(clone: Path, sha: str, out: Reviewed, project: str, gcloud: str = "gcloud") -> None:
    """The reviewer pass, printed with its discards. Never raises into the ranking's result.

    **`gcloud` IS THREADED HERE BECAUSE IT WAS THREADED EVERYWHERE ELSE AND MISSED HERE.**
    `examine()` took it from settings for the webhook; this path kept the bare default, so a
    developer whose SDK is not on PATH got "no access token" from the CLI while the endpoint
    worked. Found by running it, and only because the failure named both sources it tried.
    """
    ranked = [u.unit.site.path for u in out.ranking.units if u.allocation.value != "cold"]
    # `considered` are the paths we scored and `skipped` the ones in a language we do not read.
    # Together they are the whole change, which is the population the shape figures describe.
    changed = list(out.considered) + list(out.skipped)
    try:
        result = deep(clone, sha, ranked, project=project, changed=changed, gcloud=gcloud)
    except (Unavailable, InferenceFailed) as exc:
        # The ranking already printed and is not retracted by an inference failure.
        print(f"\n[deep] NOT RUN: {type(exc).__name__}: {exc}")
        return
    print("")
    for line in lines(result):
        print(line)


def examine(
    clone: Path, head_sha: str, reading: Reading, changed: list[str], settings: Settings
) -> Deep | None:
    """Run the model over what the allocation funded, or say plainly it was never asked.

    **`None` IS NOT-CONSULTED, NOT A FINDING OF NOTHING**, and `runs_model` needs two deliberate
    acts, so no delivery costs money by default. **An outage returns `consulted=False`**, because a
    model that could not be reached must not read like one that read the diff and approved it.
    """
    if not settings.runs_model or not reading.paths:
        return None
    try:
        return deep(
            clone,
            head_sha,
            list(reading.paths),
            project=settings.inference_project,
            changed=changed,
            gcloud=settings.gcloud_path,
        )
    except (InferenceFailed, Unavailable) as exc:
        print(f"[deliver] the model was unreachable, ranking still stands: {exc}", flush=True)
        return Deep((), 0, 0, 0, 0, tuple(reading.paths), consulted=False)
