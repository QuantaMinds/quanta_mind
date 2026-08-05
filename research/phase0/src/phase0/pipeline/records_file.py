"""Persist the PRRecords the pilot builds, so nothing has to build them twice.

WHAT: `write` and `read` for a JSONL of `PRRecord`, plus `ids` for resume.
WHY:  The pilot clones each repository, fetches merge metadata, resolves the parent and
      re-derives the changed file set — and then kept only counts. Every later stage that
      needs a `PRRecord` therefore had to redo all of it, which is how the outcome scan
      came to need a whole second pass over the corpus. At thirty-one hours for the full
      run, rebuilding records that were already built is the most expensive avoidable
      thing in the study.

      JSONL rather than parquet, matching `pipeline/record.py`: one line per record,
      appended as each is built, readable by a person mid-run, and a truncated final line
      costs one record rather than the file.

      `read` refuses a record it cannot fully reconstruct instead of filling defaults. A
      `PRRecord` with an empty `base_ref` is not a record with a missing field — it is a
      record that would send the outcome scan to the wrong branch, which is precisely the
      defect this corpus was re-measured to remove.
IMPORTS: stdlib json/pathlib; phase0.extract_prs for the record type.
CONSUMED BY: pilot/run.py, run_pipeline.py; tests/pipeline/test_records_file.py.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from phase0.extract_prs import PRRecord

# Fields that must be present and non-empty for a record to be usable downstream. Absent
# ones are refused rather than defaulted: see the module docstring on `base_ref`.
REQUIRED = ("pr_id", "repo", "merged_sha", "merged_at", "base_ref")

TUPLE_FIELDS = ("changed_files", "changed_symbols")


def append(path: Path, pr: PRRecord) -> None:
    """One record, flushed immediately. A killed run keeps everything already written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(pr), sort_keys=True) + "\n")
        handle.flush()


def ids(path: Path) -> set[str]:
    """PR ids already persisted, so a restart does not rebuild them."""
    return {pr.pr_id for pr in read(path)}


def read(path: Path) -> list[PRRecord]:
    """Every complete record in the file.

    A line that is truncated, unparseable, or missing a REQUIRED field is skipped and does
    not stop the read — but it is skipped LOUDLY in the sense that it never becomes a
    half-built record. Returning a `PRRecord` with a defaulted `base_ref` would hand the
    outcome scan the clone's HEAD, which is the exact failure this file exists downstream
    of.
    """
    if not path.is_file():
        return []
    found: list[PRRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn final line from a kill mid-write
        if not all(payload.get(field) for field in REQUIRED):
            continue
        for field in TUPLE_FIELDS:
            payload[field] = tuple(payload.get(field) or ())
        try:
            found.append(PRRecord(**payload))
        except TypeError:
            continue  # a record from a schema this code does not know
    return found
