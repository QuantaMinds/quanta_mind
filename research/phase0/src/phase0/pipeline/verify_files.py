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

      The ratio survives only where equality cannot be trusted: when the authority is
      the corpus rather than GitHub, or when GitHub's list came back at the page limit
      and may be truncated -- a truncated list would reject a perfectly correct parent.
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


def verify_files(
    pr_id: str, merge: MergeInfo, corpus_files: tuple[str, ...], found: frozenset[str]
) -> Rejection | None:
    """None when the parent is corroborated, a `Rejection` when it is not."""
    authority = merge.api_files or corpus_files
    trusted = bool(merge.api_files) and len(merge.api_files) < API_FILE_PAGE
    expected = frozenset(f for f in authority if f.endswith(".py"))
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

    if agreement < MIN_FILE_AGREEMENT:
        source = "github (truncated)" if merge.api_files else "corpus"
        return Rejection(
            pr_id,
            "file_set",
            f"{source} lists {len(expected)} .py files, the diff shows {len(found)}; "
            f"agreement {agreement:.2f} < {MIN_FILE_AGREEMENT}.",
            agreement,
        )
    return None
