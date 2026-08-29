"""One clone root shared by every experiment, bounded on entry. Never a fresh mkdtemp per run.

WHAT: `root()` returns the shared clone directory and sweeps it first. `borrow(repo)` returns a
      current clone of `repo` inside it.
WHY:  **ELEVEN GIGABYTES ACCUMULATED IN ONE WORKING SESSION AND FILLED A 228 GB DISK.** Every
      harness here called `tempfile.mkdtemp()` and cloned into it: `attention.py`,
      `firing_by_size.py` and `shape_context.py` each re-cloned the same six repositories into a
      **ELEVEN GIGABYTES ACCUMULATED IN ONE WORKING SESSION AND FILLED A 228 GB DISK.**
      Every harness here called `tempfile.mkdtemp()` and cloned into it.

      **THE LEAK WAS NOT A MISSING CLEANUP — IT WAS A NEW ROOT EVERY RUN.** `working_clone.sweep()`
      already existed, already returned the count it removed, and could not help: it bounds ONE
      root, and each run made a root of its own. Cleaning up after the duplication would have been
      the smaller half of the fix.

      **SO CLONES ARE REUSED, WHICH ALSO MAKES THE EXPERIMENTS FASTER.** A second run against the
      same repository fetches instead of cloning. Much of this session's wall-clock was spent
      re-cloning pandas.

      **THE ROOT LIVES UNDER THE JOB DIRECTORY, not `/var/folders`.** A path somebody can find, and
      delete, without being told which of nine random suffixes belongs to which experiment.
      **TWIN, EDIT BOTH:** `research/phase0/bench/forensic/borrowed_clones.py`
      → `scripts/measure/README.md` “Duplicated across the boundary”
IMPORTS: the product's `working_clone`. stdlib otherwise.
CONSUMED BY: every harness in this package that needs a repository.
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from quantamind.serve.working_clone import ensure, sweep

KEEP = 8
SHARED = pathlib.Path(
    os.environ.get("QUANTAMIND_BENCH_CLONES")
    or pathlib.Path.home() / ".cache" / "quantamind-bench-clones"
)


def root(keep: int = KEEP) -> pathlib.Path:
    """The shared clone directory, swept down to `keep` repositories. Reports what it removed.

    **THE STEADY STATE IS `keep + 1`, NOT `keep`, AND THE FIRST VERSION OF THIS SAID OTHERWISE.**
    `root()` sweeps and then the caller's `ensure()` adds one, so a run asking for keep=3 settles
    at four clones on disk. Measured: 1, 2, 3, 4, 4, 4 across six successive borrows.

    The bound holds either way — that is the property that matters — but "never exceeds `keep`" was
    a claim the run in front of me contradicted, and this file exists because of a cleanup that was
    asserted rather than counted.
    """
    SHARED.mkdir(parents=True, exist_ok=True)
    removed = sweep(SHARED, keep)
    if removed:
        print(f"  [clones] removed {removed} stale clone(s) from {SHARED}", flush=True)
    return SHARED


def borrow(repo: str, keep: int = KEEP) -> pathlib.Path:
    """A current clone of `repo` in the shared root. Clones on first use, fetches after."""
    return ensure(repo, root(keep))
