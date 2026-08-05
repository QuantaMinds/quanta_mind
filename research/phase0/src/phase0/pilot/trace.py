"""A timestamped record of a run, flushed after every repository and every PR.

WHAT: `RunTrace` -- an append-only timeline, a per-repository snapshot directory, and a
      running shape report rewritten as each repository closes.
WHY:  The journal already lets a killed run RESUME. It does not let anyone work out WHY
      it died, or what the corpus looked like at the moment it did. Those are different
      questions and the journal deliberately answers only the first: it holds one row per
      attempt, no clock, and no running totals.

      A thirty-hour run that fails at hour twenty-eight leaves the journal saying which
      repositories finished and nothing about the one that did not. Every diagnosis this
      project has needed -- the RLIMIT_AS crash, the blobless-clone empty diffs, the
      human-arm population -- was found by comparing what a stage produced against when
      and where it produced it. Without timestamps the run is a set of outcomes with no
      sequence, and "it slowed down after repository 40" is not a statement anyone can
      make from it.

      So this writes three things and rewrites nothing:
      - `timeline.jsonl`, one timestamped line per event, flushed immediately
      - `repos/NNN_owner__name.json`, a full snapshot as each repository closes
      - `shape_latest.json`, the running report, so the shape is readable mid-run

      The per-repo file carries that repository's rows in full, so a snapshot is
      self-contained: reading it needs neither the journal nor the records file.
IMPORTS: stdlib dataclasses/datetime/json/pathlib; phase0.extract_prs,
      phase0.pilot.{attempt,report}, phase0.pipeline.rejection.
CONSUMED BY: pilot/run.py; tests/pilot/test_trace.py.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from phase0.extract_prs import PRRecord
from phase0.pilot.attempt import Attempt
from phase0.pilot.report import report
from phase0.pipeline.rejection import Rejection


def _now() -> str:
    """UTC, ISO-8601, seconds resolution. One clock for the whole run."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunTrace:
    """Writes the run's diagnostic record. Never raises into the walk it observes.

    A trace that could kill the run it exists to explain would be worse than no trace,
    so every write is best-effort and a failure is reported on the timeline's next line
    rather than propagated. The journal, not this, is what correctness depends on.
    """

    def __init__(self, root: Path, meta: dict[str, object]) -> None:
        self.root = root
        self.repos = root / "repos"
        self.repos.mkdir(parents=True, exist_ok=True)
        self.started = _now()
        self.errors: list[str] = []
        self._write(
            root / "run_meta.json",
            {"started_utc": self.started, **meta},
        )
        self.event("run_start", **meta)

    @staticmethod
    def stamp() -> str:
        """The run's one clock, for a caller timing something across two calls."""
        return _now()

    def _write(self, path: Path, payload: object) -> None:
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
        except OSError as exc:  # observability must not take the run down with it
            self.errors.append(f"{path.name}: {exc}")

    def event(self, kind: str, **fields: object) -> None:
        """One timestamped line, flushed. The minute-by-minute record.

        Flushed per event rather than buffered: a buffered timeline loses exactly the
        lines describing the crash that ended the run, which are the only ones anybody
        will want.
        """
        line = json.dumps({"ts": _now(), "kind": kind, **fields}, sort_keys=True, default=str)
        try:
            with (self.root / "timeline.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
        except OSError as exc:
            self.errors.append(f"timeline: {exc}")

    def repo_done(
        self,
        repo: str,
        position: int,
        total: int,
        rows: list[Attempt],
        all_rows: list[Attempt],
        clone_failures: int,
        started: str,
    ) -> None:
        """Snapshot one repository, then rewrite the running shape.

        `rows` is this repository's attempts; `all_rows` is every attempt so far. Both
        are needed: the snapshot must be self-contained, and the shape must be cumulative.
        """
        stem = f"{position:03d}_{repo.replace('/', '__')}"
        admitted = [a for a in rows if a.admitted]
        scanned = [a for a in rows if a.outcome in ("broke", "clean")]
        self._write(
            self.repos / f"{stem}.json",
            {
                "repo": repo,
                "position": position,
                "of": total,
                "started_utc": started,
                "finished_utc": _now(),
                "attempts": len(rows),
                "admitted": len(admitted),
                "scanned": len(scanned),
                "broke": sum(1 for a in scanned if a.outcome == "broke"),
                "arms": sorted({a.arm for a in rows}),
                "stars": rows[0].stars if rows else -1,
                "rejected_by_stage": _tally(a.stage for a in rows if not a.admitted),
                # In full, so this file answers questions without the journal.
                "rows": [asdict(a) for a in rows],
            },
        )
        self._write(
            self.root / "shape_latest.json",
            {
                "as_of_utc": _now(),
                "repos_finished": position,
                "of": total,
                "trace_write_errors": self.errors,
                "shape": report(all_rows, clone_failures, position),
            },
        )
        self.event(
            "repo_done",
            repo=repo,
            position=position,
            of=total,
            attempts=len(rows),
            admitted=len(admitted),
            broke=sum(1 for a in scanned if a.outcome == "broke"),
        )


def announce(number: int, outcome: PRRecord | Rejection, breakage: str) -> None:
    """One line per PR to the terminal, flushed.

    Beside the file writes because it is the same concern in a different sink, and a
    thirty-hour run is watched as much as it is read. Flushed for the same reason the
    timeline is: buffered progress on a run that dies tells you nothing about the end.

    Branches on the TYPE, not on whether an attribute happens to be truthy. A rejection
    with an empty stage would read as an admission under the looser test, which is the
    silent-conflation this harness exists to avoid.
    """
    if isinstance(outcome, Rejection):
        print(f"     #{number}: rejected [{outcome.stage}/{outcome.category}]", flush=True)
        return
    tail = f", {breakage}" if breakage else ""
    print(
        f"     #{number}: {len(outcome.changed_files)} files, "
        f"{len(outcome.changed_symbols)} symbols{tail}",
        flush=True,
    )


def write_summary(path: Path, summary: dict[str, object]) -> None:
    """The run's final shape, to disk and to the terminal.

    Beside the per-repo writes rather than in the runner: emitting the record is one
    concern and walking repositories is another, and `shape_latest.json` already holds
    the same structure mid-run. A reader comparing the two is comparing like with like.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(summary, indent=2, sort_keys=True, default=str)
    path.write_text(rendered + "\n", encoding="utf-8")
    print("\n" + rendered)
    print(f"\nwritten to {path}")


def _tally(values: object) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:  # type: ignore[attr-defined]  # any iterable of str
        out[str(value)] = out.get(str(value), 0) + 1
    return out
