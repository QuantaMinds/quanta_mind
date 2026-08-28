"""Did this change do what it said, and does anything else depend on it.

WHAT: `explain(clone, sha, repo, number, paths, settings)` returns a `Summary`, or `None` when no
      model was consulted or the inputs could not be read.
WHY:  **THIS IS THE REVIEW'S ONE QUESTION, ASSEMBLED.** "Did what it said" needs the author's own
      description — a goal inferred from the diff makes the question circular, because a diff
      always achieves what the diff does. "Without disturbing anything else" needs the callers,
      which `parse/importers` finds by static import.

      **IT TAKES `paths`, NOT A `Reading`.** `allocate/` sits to the RIGHT of `infer/` and rule 7
      forbids reaching for it. The caller unpacks the allocation and passes the list, which is all
      this needs and keeps the layer direction intact.

      **`None` IS AN ABSENT SECTION, NOT A RESULT.** Unlike `deep_review.examine()`, where "found
      nothing" and "was unreachable" must stay distinguishable because a finding count is a claim,
      a missing summary simply means the comment renders without it and asserts nothing either way.
      The reason is printed so an operator can see which it was.
IMPORTS: ingest.diff, infer.change_summary, parse.importers, types.settings. Leftward only.
CONSUMED BY: `serve/review_delivery.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from quantamind.infer.change_summary import Summary, summarise
from quantamind.infer.gemini import InferenceFailed, Unavailable
from quantamind.ingest.diff import DiffReadFailed, stated_goal, unified_diff
from quantamind.parse.importers import importers
from quantamind.types.settings import Settings


def explain(
    clone: Path,
    head_sha: str,
    repo: str,
    number: int,
    paths: Sequence[str],
    settings: Settings,
) -> Summary | None:
    """What the change does, whether it did what the author said, and who it affects.

    **THE TWO HALVES OF THE REVIEW'S ONE QUESTION.** "Did what it said" needs the author's own
    description, because a goal inferred from the diff makes the question circular. "Without
    disturbing anything else" needs the callers, which `parse/importers` finds by static import.

    **`None` IS NOT-ASKED, AND AN OUTAGE IS ALSO `None` HERE.** Unlike `examine()`, which must
    distinguish "the model found nothing" from "the model was unreachable" because a finding count
    is a result, an absent summary is simply an absent section: the comment renders without it and
    claims nothing either way. The reason is printed for the operator.
    """
    if not settings.runs_model or not paths:
        return None
    try:
        stated = stated_goal(repo, number)
        diff = unified_diff(repo, number)
        callers: list[str] = []
        for path in paths:
            found, _ = importers(clone, head_sha, path)
            callers.extend(found)
        return summarise(
            diff,
            stated,
            project=settings.inference_project,
            importers=sorted(set(callers)),
            gcloud=settings.gcloud_path,
        )
    except (InferenceFailed, Unavailable, DiffReadFailed) as exc:
        print(f"[deliver] no summary: {type(exc).__name__}: {exc}", flush=True)
        return None
