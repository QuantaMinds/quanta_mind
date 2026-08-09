"""Verify a resolved parent by the files the diff produces. Detection may guess; this may not.

WHAT: Compares `git diff parent..merge` against GitHub's own file list for the PR, and
      returns a typed rejection when they are not the same set.
WHY:  Split from `assemble.py` because resolving a parent and proving it right are
      different jobs, and only the second is allowed to be strict.

      Exact equality, not a ratio. A SUPERSET is not a near miss. When a PR's commits
      land via another pull request, `merge_commit_sha` belongs to that other PR: the
      subject sequence does not match, so shape detection routes to squash and resolves
      a parent confidently -- and if the other PR carried nothing else, the diff differs
      only by the files they share and a threshold gate waves it through. That is a
      wrong parent that passes verification, which is the single failure mode surviving
      every downstream check, on the primary variable. Set equality refuses it.

      The ratio survives in ONE place: when GitHub's list came back at the page limit and
      may be truncated. There the authority is still GitHub, merely possibly incomplete,
      and strict equality would reject a perfectly correct parent.

      There is no corpus fallback. `authority = merge.api_files or corpus_files` used to
      substitute the corpus's list when GitHub supplied none, and no amendment ever
      authorised that -- it was inherited, never argued. The corpus OVER-attributes, so
      the substitution had a direction: measured against GitHub, it claimed 104, 65 and 40
      `.py` files for PRs whose real lists were 2, 9 and 2 with none of them Python. A
      correct diff against an inflated expectation scores low agreement and is rejected at
      `file_set` -- an `integrity` verdict, blaming the repository's account of itself for
      a gap that was ours, landing hardest on the PRs the corpus mis-attributes most, which
      correlates with size. That is A16's confounder entering through our own gate.

      An absent authority is now `no_file_authority`, categorised `resource` and counted.
IMPORTS: phase0.github_pulls, phase0.pipeline.{changed,rejection}.
CONSUMED BY: pipeline/assemble.py; tests/pipeline/test_assemble.py.
"""

from __future__ import annotations

from phase0.github_pulls import MergeInfo
from phase0.pipeline.changed import file_agreement
from phase0.pipeline.rejection import Rejection

MIN_FILE_AGREEMENT = 0.6

# `/pulls/{n}/files` is fetched one page deep. A list exactly this long may be truncated.
API_FILE_PAGE = 100


def verify_files(pr_id: str, merge: MergeInfo, found: frozenset[str]) -> Rejection | None:
    """None when the parent is corroborated, a `Rejection` when it is not.

    Takes no corpus list. There is nothing to fall back TO: verification either has
    GitHub's account of the PR or it does not, and the second is a typed absence.
    """
    if not merge.api_files:
        return Rejection(
            pr_id,
            "no_file_authority",
            "GitHub supplied no file list; there is nothing to verify the parent against.",
        )

    trusted = len(merge.api_files) < API_FILE_PAGE
    expected = frozenset(f for f in merge.api_files if f.endswith(".py"))
    agreement = file_agreement(expected, found)

    if trusted:
        if expected != found:
            extra = sorted(found - expected)[:3]
            missing = sorted(expected - found)[:3]
            return Rejection(
                pr_id,
                "file_set",
                f"diff and GitHub's file list are not equal: {len(found)} vs "
                f"{len(expected)} .py files. Extra in diff: {extra or 'none'}; absent "
                f"from diff: {missing or 'none'}. A superset means the walk went too far "
                f"back or the PR was merged indirectly.",
                agreement,
            )
        return None

    # Only reachable when GitHub's list is exactly one page long and so may be cut. The
    # authority IS GitHub here, merely possibly incomplete, and strict equality would
    # reject a correct parent for files the second page would have listed.
    if agreement < MIN_FILE_AGREEMENT:
        return Rejection(
            pr_id,
            "file_set",
            f"github (truncated at {API_FILE_PAGE}) lists {len(expected)} .py files, the "
            f"diff shows {len(found)}; agreement {agreement:.2f} < {MIN_FILE_AGREEMENT}.",
            agreement,
        )
    return None
