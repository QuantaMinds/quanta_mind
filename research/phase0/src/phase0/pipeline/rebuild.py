"""Rebuild the PRRecords a journal says were admitted, without a second clone sweep.

WHAT: `records_for` — turns a pilot journal's admitted rows back into `PRRecord`s, using
      the cached GitHub payloads and one clone per repository.
WHY:  The exposure pass needs `PRRecord`s. The pilot that produced the corpus discarded
      them, and `--records` persistence was added after that run had already started, so
      `results/records.jsonl` does not exist for the corpus actually measured.

      Re-running the pilot would not help: it resumes from the journal, finds every
      repository marked done, and writes nothing. A fresh journal would mean two and a
      half hours of clones to recover records whose expensive input — the clone — the
      exposure pass has to pay for anyway.

      So the rebuild happens where the clone is already open. `build_record` is reused
      rather than reimplemented, which matters more than the saved lines: admission is the
      rule that decides which units the study contains, and a second implementation of it
      would drift from the first silently.

      Rows the journal marks rejected are not rebuilt. They were excluded by a rule, and
      recovering them here would quietly widen the corpus past what the journal reports.
IMPORTS: phase0.github_pulls, phase0.pipeline.{assemble,journal,rejection},
      phase0.handlabel.select.
CONSUMED BY: exposure_run.py; tests/pipeline/test_rebuild.py.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.github_pulls import merge_info
from phase0.handlabel.select import Candidate, eligible_prs
from phase0.pipeline import resume
from phase0.pipeline.assemble import build_record
from phase0.pipeline.rejection import Rejection


def admitted_ids(journal_path: Path) -> set[str]:
    """PR ids the journal recorded as admitted. Rejections stay rejected."""
    return {a.pr_id for a in resume.read_attempts(journal_path) if a.admitted}


def _by_id(package: Path, wanted: set[str]) -> dict[str, Candidate]:
    """The corpus rows for those ids, which carry the PR number the API needs."""
    return {str(c.pr_id): c for c in eligible_prs(package) if str(c.pr_id) in wanted}


def records_for(
    journal_path: Path,
    package: Path,
    cache: Path,
    token: str,
    clone_for: object,
) -> Iterator[tuple[str, PRRecord | Rejection]]:
    """Yield `(repo, record-or-rejection)` for every admitted PR, grouped by repository.

    `clone_for` is a callable taking a repository name and returning a context manager
    over a clone — the caller owns cloning, because the caller is already doing it.

    A row that will not rebuild yields its `Rejection` rather than being skipped. The
    journal says these were admitted, so a silent drop here would mean the exposure pass
    ran over fewer units than the corpus reports and nothing would say by how many.
    """
    wanted = admitted_ids(journal_path)
    candidates = _by_id(package, wanted)
    grouped: dict[str, list[Candidate]] = {}
    for candidate in candidates.values():
        grouped.setdefault(candidate.repo, []).append(candidate)

    for repo in sorted(grouped):
        with clone_for(repo) as clone:  # type: ignore[operator]
            if clone is None:
                for candidate in grouped[repo]:
                    yield repo, Rejection(str(candidate.pr_id), "clone", "clone unavailable")
                continue
            for candidate in sorted(grouped[repo], key=lambda c: str(c.pr_id)):
                merge = merge_info(repo, candidate.number, str(candidate.pr_id), cache, token)
                if merge is None:
                    yield repo, Rejection(str(candidate.pr_id), "merge_metadata", "PR or repo gone")
                    continue
                yield (
                    repo,
                    build_record(
                        clone,
                        merge,
                        pr_id=str(candidate.pr_id),
                        repo=repo,
                        merged_at=candidate.merged_at,
                        corpus_files=candidate.changed_files,
                    ),
                )
