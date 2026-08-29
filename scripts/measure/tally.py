"""The pull-request numbers a benchmark entry names.

WHAT: `pull_numbers(entries)` -> the sorted pull numbers, ignoring commit-URL entries.
WHY:  Split from `pulls.py` for the same reason research split its own copy: that file crosses
      the 200-line cap otherwise. The seam is real — this is pure parsing with no disk and no
      clone, and everything left in `pulls.py` touches both.

      **THIS IS A DELIBERATE COPY OF `research/phase0/bench/forensic/shape/tally.py`.** That
      module stays in research because `shape_context.py` needs it there, and the two projects
      run different interpreters — PyCG caps research at 3.10, the product needs >=3.12 for
      `sys.monitoring`, and a shared environment cannot satisfy both. An import across that
      boundary cannot work, so the code is duplicated and both copies say so. Edit them together.
      → `scripts/measure/README.md` “Duplicated across the interpreter boundary”
IMPORTS: stdlib only.
CONSUMED BY: `scripts/measure/pulls.py`.
"""

from __future__ import annotations


def pull_numbers(entries: list[dict[str, object]]) -> list[int]:
    """The pull-request numbers in `entries`, sorted. Commit-URL entries contribute none.

    **THIS IS WHAT STOPS THE FETCH ASKING FOR 83,202 REFS TO RESOLVE TEN.** grafana carries that
    many pull heads and discourse 42,495; `ensure(pull_refs=...)` takes this list instead of the
    wildcard. Ten of the fifty golden entries name a commit rather than a pull request and
    correctly contribute nothing here.

    **COPIED FROM `shape/tally.py`, NOT IMPORTED** — that module stays in research, which runs
    a different interpreter. Fourteen lines duplicated deliberately; edit both.
    """
    out: set[int] = set()
    for entry in entries:
        url = str(entry["original"]).rstrip("/")
        tail = url.split("/")[-1]
        if "/pull/" in url and tail.isdigit():
            out.add(int(tail))
    return sorted(out)
