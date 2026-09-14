"""`quantamind scan` -- the first history walk over a clone, and what it found.

WHAT: `run_scan(clone, repo, explain)` walks a clone's history into a scratch index, prints where
      rework has concentrated, and -- only when `explain` names a GCP project -- appends a model's
      reading of the counts.
WHY:  **THIS IS THE FIRST THING A PROSPECT RUNS, SO IT MUST COST THEM NOTHING AND REVEAL NOTHING.**
      The default path opens no socket: `ingest/history.read_touches` shells out to git in their
      clone, the index is a `TemporaryDirectory`, and the report is printed. Nothing is uploaded,
      no account exists, and there is no install. That is the same contract `run_retrospective`
      already offers and the reason either can be handed to a stranger.

      **THE INDEX IS SCRATCH ON PURPOSE.** A first scan that wrote into the real store would make
      running it twice produce different numbers -- `store/touches.index` is idempotent per row but
      a customer's store is not a scratchpad, and a sales command must not leave state behind.

      **`--explain` IS OFF BY DEFAULT AND SAYS WHAT IT SENDS BEFORE IT SENDS IT.** Reading a
      repository and transmitting anything about it are two different acts; `ingest/context/
      egress.py` draws the same line for a ticket. File paths and counts leave the machine, source
      code does not, and the line printed before the call is how the person running it finds that
      out in time to press Ctrl-C.

      **A MISSING CLONE IS REFUSED, NOT WALKED.** `read_touches` on a directory that is not a
      repository returns nothing, and an empty report reads exactly like a repository with no
      history. The two are separated here rather than in the renderer.
IMPORTS: ingest.history, store.{schema,touches}, render.scan_report, infer.history_digest. All
      leftward of serve, and `infer` is imported inside the branch that uses it so the default
      path does not even load the transport.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind.ingest.history import read_touches
from quantamind.render.scan_report import as_of, report
from quantamind.store.schema import open_store
from quantamind.store.touches import ensure_repo, hotspots, index


def _named(clone: Path) -> str:
    """owner/name from the clone's own origin remote, falling back to `local/<directory>`.

    **THE HEADING IS WHAT THE REPOSITORY CALLS ITSELF, NOT WHAT THE DIRECTORY IS CALLED.**
    A clone in `/tmp/x` is still `pallets/flask`, and a heading that said `local/x` would make two
    scans of the same repository look like two repositories.

    **A MISSING OR ODD REMOTE IS NOT AN ERROR.** A clone with no origin is a normal thing to scan;
    it just cannot name itself, and `local/` says which case the reader is in rather than guessing.
    """
    try:
        url = subprocess.run(
            ["git", "-C", str(clone), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return f"local/{clone.resolve().name}"
    tail = url.removesuffix(".git").replace(":", "/").rstrip("/").split("/")
    return (
        f"{tail[-2]}/{tail[-1]}" if len(tail) >= 2 and tail[-1] else f"local/{clone.resolve().name}"
    )


SENDING = (
    "[scan] --explain is on: {n} file path(s) and their commit counts will be sent to Vertex AI "
    "in project {project}. Your source code will not be."
)


def run_scan(clone: Path, repo: str = "", *, explain: str = "", limit: int = 10) -> int:
    """Walk one clone's history and print where rework has landed. Returns an exit code."""
    if not (clone / ".git").exists():
        print(f"{clone} is not a git clone; a scan reads git history and nothing else")
        return 1

    name = repo or _named(clone)

    touches = read_touches(clone)
    with TemporaryDirectory() as scratch:
        conn = open_store(Path(scratch) / "scan.db")
        try:
            repo_id = ensure_repo(conn, "github.com", name)
            written = index(conn, repo_id, touches)
            spots = hotspots(conn, repo_id, limit=limit)
        finally:
            conn.close()

    # **PRINTED BEFORE THE NARRATION IS ASKED FOR.** The table is the product; if the model call
    # hangs or refuses, the person running this has already got what they came for.
    print(report(name, spots))
    print(f"\n[scan] {written:,} touch(es) indexed; newest commit read: {as_of(spots)}")

    if not explain:
        return 0

    print(SENDING.format(n=len(spots.files), project=explain), flush=True)
    from quantamind.infer.history_digest import digest

    print(report(name, spots, narration=digest(spots, project=explain)))
    return 0
