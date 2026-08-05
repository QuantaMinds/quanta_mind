"""Reading the labeller's sheet, and refusing it when it is not finished.

WHAT: Parses `human_labels.csv` into `HumanLabel` records, validating every field.
WHY:  Split from `score.py` because reading what a person wrote and comparing it to the
      key are different concerns, and only the first has to be strict about input.

      Strict on purpose. A partial sheet scored against whatever is present would let
      the gate be met by labelling only the easy ones, and a mistyped verdict silently
      coerced to CLEAN would be a fabricated judgement. Both refuse, naming the line.

      `UNSURE` is a first-class verdict here, not a parse failure. A forced guess is
      worse than an honest gap: it turns "I could not tell" into evidence.
IMPORTS: stdlib csv, re.
CONSUMED BY: handlabel/score.py; tests/handlabel/.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

VERDICTS = ("BROKE", "CLEAN", "UNSURE")
CONFIDENCES = ("high", "low")
REQUIRED_COLUMNS = ("label_id", "verdict", "confidence", "evidence", "reasoning", "minutes")


@dataclass(frozen=True, slots=True)
class HumanLabel:
    """One row of the labeller's sheet."""

    label_id: int
    verdict: str
    confidence: str
    evidence: str
    reasoning: str
    minutes: float


def _minutes(raw: str) -> float:
    """Tolerant of "6", "6.5" and "~6 min"; a duration is metadata, not a measurement."""
    match = re.search(r"\d+(?:\.\d+)?", raw or "")
    return float(match.group(0)) if match else 0.0


def read_labels(path: Path, expected: int) -> dict[int, HumanLabel]:
    """Parse the sheet, refusing anything incomplete or unrecognised."""
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Label the sample first -- the labels must exist, and be "
            f"committed, before the key is opened."
        )
    labels: dict[int, HumanLabel] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        absent_columns = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if absent_columns:
            raise ValueError(f"{path}: missing column(s) {absent_columns}")
        for line, row in enumerate(reader, start=2):
            verdict = (row["verdict"] or "").strip().upper()
            if verdict not in VERDICTS:
                raise ValueError(
                    f"{path}:{line}: verdict must be one of {VERDICTS}, got {verdict!r}"
                )
            confidence = (row["confidence"] or "").strip().lower()
            if confidence not in CONFIDENCES:
                raise ValueError(
                    f"{path}:{line}: confidence must be one of {CONFIDENCES}, got {confidence!r}"
                )
            labels[int(row["label_id"])] = HumanLabel(
                label_id=int(row["label_id"]),
                verdict=verdict,
                confidence=confidence,
                evidence=(row["evidence"] or "").strip(),
                reasoning=(row["reasoning"] or "").strip(),
                minutes=_minutes(row["minutes"]),
            )
    absent = sorted(set(range(1, expected + 1)) - labels.keys())
    if absent:
        raise ValueError(
            f"{path}: missing labels for {absent}. All {expected} must be labelled before "
            f"scoring; a partial sheet lets the gate be met on the easy ones."
        )
    return labels
