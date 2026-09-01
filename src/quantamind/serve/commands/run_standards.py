"""`quantamind standards` — read a repository's recent review comments and report what recurs.

WHAT: `run_standards(repo, pulls)` reads the comments on the given pull requests, mines repeated
      points, and prints the report. Returns a process exit code.
WHY:  **D1d. THE PULL REQUESTS ARE NAMED BY THE CALLER, NOT DISCOVERED**, and that is the honest
      shape: `ingest/publish/github_comments.py:existing` reads one pull request's comments, and
      inventing a "recent pull requests" crawl here would add a search this product has never run
      and cannot yet defend. A team knows which changes their seniors reviewed.

      **THE PULL NUMBER TRAVELS WITH EVERY COMMENT, WHICH THE RESEARCH CORPUS COULD NOT DO.**
      `Proposal.across_changes` is only meaningful when it is known, and here it always is — so
      this command produces the stronger form of the evidence the finding was measured on.

      **BOT COMMENTS ARE EXCLUDED AND COUNTED.** The first real run of this command proposed three
      standards and every one was this product's own review comment, repeated across heads. GitHub
      labels the author, so `user.type == "Bot"` decides it rather than a guess about the prose.

      **IT WRITES NOTHING.** No rule is declared, no file is touched, no store is opened. The
      output is a page a human reads. → `render/mined_rules.py` says the same thing to the reader.
IMPORTS: ingest.{publish.github_comments,standards.mined}, render.mined_rules,
      types.standards.proposal. Leftward only.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.ingest.publish.github_comments import CommentFailed, existing
from quantamind.ingest.standards.mined import mine
from quantamind.render.mined_rules import report
from quantamind.types.standards.proposal import Comment


def gather(repo: str, pulls: Sequence[int]) -> tuple[tuple[Comment, ...], tuple[int, ...]]:
    """Every comment on those pull requests, and the ones that could not be read.

    **A PULL REQUEST WE COULD NOT READ IS RETURNED, NOT SKIPPED.** Mining over four of six changes
    and reporting as though it were six would understate recurrence and overstate coverage in the
    same breath.
    """
    found: list[Comment] = []
    refused: list[int] = []
    for number in pulls:
        try:
            raw = existing(repo, number)
        except CommentFailed:
            refused.append(number)
            continue
        for item in raw:
            user = item.get("user") or {}
            found.append(
                Comment(
                    str(item.get("body") or ""),
                    str(item.get("path") or ""),
                    pull=number,
                    author=str(user.get("login") or ""),
                    machine=str(user.get("type") or "") == "Bot",
                )
            )
    return tuple(found), tuple(refused)


def run_standards(repo: str, pulls: Sequence[int]) -> int:
    """Read, mine, print. **Nothing is written anywhere.**"""
    if not pulls:
        print("standards: name at least one pull request to read, e.g. --pulls 91 92 93")
        return 2

    comments, refused = gather(repo, pulls)
    if refused:
        # **NOT A FOOTNOTE.** The denominator of everything below just changed.
        print(
            f"standards: {len(refused)} of {len(pulls)} pull request(s) could not be read "
            f"({', '.join(f'#{n}' for n in refused)}); nothing in them was mined.\n"
        )
    if not comments and refused:
        print("standards: no comments could be read at all, so nothing was mined.")
        return 1

    written_by_people = [c for c in comments if not c.machine]
    if len(written_by_people) != len(comments):
        # **STATED, NOT SILENT.** The denominator below is people-written comments only.
        print(
            f"standards: {len(comments) - len(written_by_people)} of {len(comments)} comment(s) "
            f"were written by bots and were not mined.\n"
        )
    print(report(mine(comments), repo, len(written_by_people)))
    return 0
