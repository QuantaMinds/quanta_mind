"""How much of the breakage drop each of A26's two fixes is responsible for.

WHAT: Re-walks the outcome window and evaluates all four rule variants in one pass --
      neither fix, subject-only, focus-only, both -- so each is attributed separately.
WHY:  "Both changes can only remove verdicts" protects against inflation. It says nothing
      about OVER-removal, and `a >= 20` binds on the exposed arm, so a fix that quietly
      deletes real events is as damaging as one that invents them.

      The focus threshold is the one to watch. A legitimate repair that also does
      unrelated cleanup across ten files scores 2/10 = 0.2 and is excluded. If
      `MIN_COMMIT_FOCUS` removes more than subject-matching does, the excluded set has to
      be read by hand before the threshold stands.

      Four variants in one clone visit rather than four runs: cloning is the entire cost
      here, and four passes would take two hours to answer a question one pass answers.
IMPORTS: phase0.outcome.{signals,scan,window}, phase0.{handlabel.select,github_pulls},
         phase0.pipeline.*.
CONSUMED BY: run by hand; result recorded in the pre-registration.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

from phase0.github_pulls import merge_info, require_token
from phase0.handlabel.select import eligible_prs
from phase0.outcome import signals
from phase0.outcome.scan import GIT_LOOKUP_ERRORS, WINDOW_DAYS, _merged_at
from phase0.outcome.window import candidates
from phase0.pipeline.assemble import Rejection, build_record
from phase0.pipeline.worktree import CloneFailed, cloned

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
WORKSPACE = ROOT / "data" / "attribute_clones"
CACHE = ROOT / "data" / "gh_cache"

VARIANTS = ("neither", "subject_only", "focus_only", "both")


def _verdicts(repo_path: Path, record: object) -> dict[str, bool]:
    """BROKE under each of the four rule variants, from one history walk."""
    start = _merged_at(record)  # type: ignore[arg-type]
    if start is None:
        return dict.fromkeys(VARIANTS, False)

    from git import Repo

    changed = frozenset(record.changed_files)  # type: ignore[attr-defined]
    broke = dict.fromkeys(VARIANTS, False)
    try:
        repo = Repo(repo_path)
    except GIT_LOOKUP_ERRORS:
        return broke

    try:
        window = candidates(
            repo,
            start,
            start + timedelta(days=WINDOW_DAYS),
            record.merged_sha,  # type: ignore[attr-defined]
        )
        for commit in window:
            message = str(commit.message)
            if signals.reverts(message, record.merged_sha):  # type: ignore[attr-defined]
                return dict.fromkeys(VARIANTS, True)
            try:
                touched = frozenset(str(n) for n in commit.stats.files)
            except GIT_LOOKUP_ERRORS:
                continue
            overlap_any = bool(touched & changed)
            overlap_focused = signals.is_focused(touched, changed)
            body_hit = signals.mentions_breakage(message)
            subject_hit = signals.mentions_breakage(signals.subject(message))
            revert_hit = signals.looks_like_a_revert(message)

            broke["neither"] |= overlap_any and (body_hit or revert_hit)
            broke["subject_only"] |= overlap_any and (subject_hit or revert_hit)
            broke["focus_only"] |= overlap_focused and (body_hit or revert_hit)
            broke["both"] |= overlap_focused and (subject_hit or revert_hit)
    finally:
        repo.close()
    return broke


def main() -> int:
    token = require_token()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    grouped: dict[str, list] = {}
    for candidate in eligible_prs(PACKAGE):
        grouped.setdefault(candidate.repo, []).append(candidate)

    tally: Counter[str] = Counter()
    scanned = 0
    lost_to_focus: list[str] = []

    for position, repo in enumerate(sorted(grouped)[:limit], start=1):
        print(f"[{position}/{limit}] {repo}", flush=True)
        try:
            with cloned(repo, WORKSPACE) as clone:
                for candidate in grouped[repo][:5]:
                    merge = merge_info(repo, candidate.number, str(candidate.pr_id), CACHE, token)
                    if merge is None:
                        continue
                    record = build_record(
                        clone,
                        merge,
                        pr_id=str(candidate.pr_id),
                        repo=repo,
                        merged_at=candidate.merged_at,
                        corpus_files=candidate.changed_files,
                        # From the CANDIDATE, which is what the journal uses, so the
                        # record and the journal cannot disagree about the arm.
                        arm=candidate.arm,
                    )
                    if isinstance(record, Rejection):
                        continue
                    scanned += 1
                    broke = _verdicts(clone, record)
                    for name, hit in broke.items():
                        tally[name] += hit
                    # A verdict the focus threshold removed but subject-matching kept is
                    # the one to eyeball: it is a real repair candidate, dropped for
                    # breadth rather than for wording.
                    if broke["subject_only"] and not broke["both"]:
                        lost_to_focus.append(f"{repo}#{candidate.number}")
        except CloneFailed as exc:
            print(f"     clone failed: {exc}", flush=True)

    out = {
        "scanned": scanned,
        "broke_by_variant": dict(tally),
        "rate_by_variant": {k: round(v / scanned, 4) for k, v in tally.items()} if scanned else {},
        "removed_by_subject_only": tally["neither"] - tally["subject_only"],
        "removed_by_focus_only": tally["neither"] - tally["focus_only"],
        "removed_by_both": tally["neither"] - tally["both"],
        "dropped_by_focus_after_subject": lost_to_focus,
    }
    path = ROOT / "results" / "rule_attribution.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("\n" + json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
