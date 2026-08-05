"""Writing the blind sheet and the sealed key, as two functions that cannot be confused.

WHAT: `write_blind` takes only `(label_id, pr_url)` pairs. `write_key` takes `KeyRow`s.
WHY:  The contamination risk in this gate is one careless column. Splitting the writers
      by argument type means the blind sheet physically cannot carry a verdict: there is
      no code path that hands `write_blind` anything but an integer and a URL, and the
      type checker enforces it.

      `write_blind` also refuses a URL that is not a PR link, which catches the one way
      a leak could still arrive -- somebody widening `Candidate.url` later to include a
      commit or compare view that encodes the answer.
IMPORTS: stdlib csv, phase0.handlabel.draw.
CONSUMED BY: phase0/sample_for_labelling.py, phase0/score_labelling.py; tests/handlabel/.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Sequence
from pathlib import Path

from phase0.handlabel.draw import KeyRow

BLIND_COLUMNS = ("label_id", "pr_url")
KEY_COLUMNS = ("label_id", "pr_id", "repo", "number", "verdict", "criterion", "evidence_sha")
PR_URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/pull/\d+$")


def write_blind(path: Path, rows: Sequence[tuple[int, str]]) -> None:
    """The labeller's sheet: two columns, nothing else, ever."""
    for label_id, url in rows:
        if not PR_URL.match(url):
            raise ValueError(
                f"label {label_id}: {url!r} is not a plain pull-request URL. Anything "
                f"richer can encode the answer; the sheet carries the link and no more."
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(BLIND_COLUMNS)
        writer.writerows(rows)


def write_key(path: Path, rows: Sequence[KeyRow]) -> None:
    """The sealed answers. Gitignored, and not to be opened before labelling is done."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(KEY_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    row.label_id,
                    row.pr_id,
                    row.repo,
                    row.number,
                    row.verdict,
                    row.criterion,
                    row.evidence_sha,
                ]
            )


def read_key(path: Path) -> list[KeyRow]:
    """Load the sealed answers for scoring."""
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found. Draw a sample first.")
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            KeyRow(
                label_id=int(row["label_id"]),
                pr_id=int(row["pr_id"]),
                repo=row["repo"],
                number=int(row["number"]),
                verdict=row["verdict"],
                criterion=row["criterion"],
                evidence_sha=row["evidence_sha"],
            )
            for row in csv.DictReader(handle)
        ]


def write_label_template(path: Path, label_ids: Sequence[int]) -> None:
    """A blank sheet with the required columns, so the labeller does not invent them."""
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("label_id", "verdict", "confidence", "evidence", "reasoning", "minutes"))
        for label_id in label_ids:
            writer.writerow((label_id, "", "", "", "", ""))
