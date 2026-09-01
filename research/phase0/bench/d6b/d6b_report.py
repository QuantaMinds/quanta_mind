"""Score the D6b arms, apply the bars as WRITTEN, and write the artefact.

**NAMED `d6b_report`, NOT `report`.** `research/phase0/vertex/report.py` already exists and is on
the same `sys.path`; a module called `report.py` here shadowed it and `import report` executed the
wrong file, which ran to a FileNotFoundError on a corpus path. That is AGENTS.md rule 13 — never
two files with one name — arriving in the research tree, where the guard does not reach.

WHAT: `report(detail, placebo)` — the paired counts, the exact sign test, the per-repository
      split, and the verdict.
WHY:  **THE BAR IS COMPUTED FROM THE CORPUS AND AN UNMEETABLE BAR VOIDS THE RUN.** The first
      version hard-coded `positive >= 4` against four repositories, so CONFIRMED required 4 of 4
      rather than the pre-registered 4 of 6, and NULL was a property of the harness rather than a
      fact about context.

      **DEGRADATION IS PRINTED.** Judge errors and non-STOP finishes were dropped entirely by the
      first run. An unjudged pair scores identically to a non-match, so the arm issuing more judge
      calls is undercounted for a reason unrelated to its findings — the rival mechanism an
      adversarial audit raised, and one this run can now rule in or out rather than argue about.

      **SPLIT FROM `run_d6b.py` AT THE 200-LINE CAP**, and it is a seam: that module runs arms,
      this one decides what the numbers mean.
IMPORTS: run_d6b for the bar constants; stdlib collections, json, math, pathlib.
CONSUMED BY: `run_d6b.py`.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from d6b_population import mcnemar
from run_d6b import (
    OUT,
    PREREGISTERED_BAR,
    PREREGISTERED_REPOSITORIES,
    REPOSITORY_SHARE,
)


def report(
    detail: list,
    placebo: bool,
    exposed: list,
    thin: list[str],
    unreadable: list[str],
    not_a_pull: list[str],
) -> int:
    """Everything after the arms have run.

    The population counts arrive as arguments because **"could not be read" is its own bucket**:
    folding it into "too thin" is how a GitHub outage became "the author wrote little".
    """
    scored = [d for d in detail if "skipped" not in d]
    better = sum(1 for d in scored if d["tp_context"] > d["tp_control"])
    worse = sum(1 for d in scored if d["tp_context"] < d["tp_control"])
    same = len(scored) - better - worse
    p = mcnemar(better, worse)

    by_repo: dict[str, int] = collections.defaultdict(int)
    for d in scored:
        by_repo[d["repo_file"]] += d["tp_context"] - d["tp_control"]
    positive = sum(1 for v in by_repo.values() if v > 0)

    total_c = sum(d["tp_control"] for d in scored)
    total_a = sum(d["tp_context"] for d in scored)

    print(f"\n  scored {len(scored)} changes")
    print(f"  golden defects found: control {total_c}, context {total_a} ({total_a - total_c:+d})")
    print(f"  per change: context better on {better}, worse on {worse}, equal on {same}")
    print(f"  McNemar exact p = {p:.4f}")
    print(f"  repositories positive: {positive} of {len(by_repo)}  {dict(by_repo)}")

    # **THE BAR IS COMPUTED FROM THE CORPUS, AND AN UNMEETABLE BAR VOIDS THE RUN.** `positive >= 4`
    # executed as 4 of 4 on this four-repository corpus, so CONFIRMED was unreachable and NULL was
    # a property of the harness. A bar nobody checked was satisfiable is not a bar.
    required = math.ceil(REPOSITORY_SHARE * len(by_repo))
    if len(by_repo) < PREREGISTERED_REPOSITORIES:
        print(
            f"\n  [VOID] the pre-registration requires {PREREGISTERED_BAR} of "
            f"{PREREGISTERED_REPOSITORIES} repositories positive; this corpus has {len(by_repo)}. "
            f"No result from it can clear that bar, so none is reported.\n"
            f"  For the record only: effect {total_a - total_c:+d}, p = {p:.4f}, "
            f"{positive} of {len(by_repo)} positive (would need {required} at the same share)."
        )
        confirmed, verdict = False, "VOID"
    else:
        confirmed = total_a > total_c and p < 0.05 and positive >= required
        verdict = "CONFIRMED" if confirmed else "NULL"
        print(f"\n  [{verdict}] against the pre-registered bars")

    degraded = sum(d["judge_errors_control"] + d["judge_errors_context"] for d in scored)
    truncated = sum(
        1 for d in scored if d["finish_control"] != "STOP" or d["finish_context"] != "STOP"
    )
    print(f"  judge errors {degraded}; non-STOP finishes {truncated}")
    if degraded or truncated:
        print("  ** arms not scored under equal conditions; treat the comparison as void **")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "exposed": len(exposed),
                "too_thin": len(thin),
                "not_a_pull": len(not_a_pull),
                "unreadable": len(unreadable),
                "scored": len(scored),
                "tp_control": total_c,
                "tp_context": total_a,
                "better": better,
                "worse": worse,
                "same": same,
                "mcnemar_p": p,
                "by_repo": dict(by_repo),
                "repositories_positive": positive,
                "confirmed": confirmed,
                "verdict": verdict,
                "placebo": placebo,
                "judge_errors": degraded,
                "non_stop_finishes": truncated,
                "detail": detail,
            },
            indent=2,
        )
    )
    return 0
