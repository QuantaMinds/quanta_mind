"""No test may carry its own copy of the event definition. One definition, imported.

WHAT: Reads the live gate tests as text and asserts none of them contains a fix-word list, a
      file-count bound or a ninety-day window of its own.
WHY:  **This exact drift already happened.** `test_event_replay_gate.py` and
      `test_gate_2b_pinned_corpus.py` each wrote the definition out, and the two copies diverged:
      one matched fix-words against the RAW subject under a comment claiming that is what the
      research does, while `commit_stream.py` lowercases first. It admitted strictly fewer events
      for as long as it stood, and every number the gate printed was computed on the wrong corpus.

      **Gate 2b passing is not enough on its own.** It proves TODAY's definition is faithful,
      because it reproduces a checked-in artefact event for event. It cannot stop someone
      reintroducing a local copy tomorrow that agrees on this corpus and drifts on the next one --
      which is precisely how the first copy survived review.

      **THE CHECK IS ON TEXT, DELIBERATELY.** Importing the module and comparing values would pass
      against a file that defines its own identical constants, and identical-today is the failure
      mode. What must be absent is the DECLARATION.
IMPORTS: stdlib only (pathlib, re). No project imports -- reading source, not running it.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARDED = (
    "tests/live/test_event_replay_gate.py",
    "tests/live/test_gate_2b_pinned_corpus.py",
    "tests/live/test_retrospective_live.py",
)

# Each pattern is one clause of the definition, in the shape a re-implementation would take.
RESTATEMENTS = {
    "a fix-word list": re.compile(r'["\']fix["\']\s*,\s*["\']bug["\']'),
    "a file-count bound": re.compile(r"MAX_FILES\s*=|<=\s*MAX_FILES|2\s*<=\s*len\("),
    "a ninety-day window": re.compile(r"WINDOW\w*\s*=\s*90\s*\*"),
    "a subject scan": re.compile(r"\.subject\.lower\(\)"),
}


@pytest.mark.parametrize("relative", GUARDED)
def test_the_gate_tests_import_the_definition_rather_than_restating_it(relative: str) -> None:
    path = ROOT / relative
    if not path.is_file():
        pytest.skip(f"{relative} does not exist")
    source = path.read_text(encoding="utf-8")

    found = [name for name, pattern in RESTATEMENTS.items() if pattern.search(source)]
    assert not found, (
        f"{relative} restates {', '.join(found)}. The event definition lives in "
        f"`quantamind.rank.events` and carries the p-value; a second copy agrees on the corpus it "
        f"was written against and drifts on the next one, which has already happened once."
    )


def test_the_patterns_would_actually_catch_a_restatement() -> None:
    """A guard that matches nothing reports exactly what a clean run reports.

    `rank/events.py` is the file these patterns are meant to describe, so every one of them must
    fire against it. If a clause is ever reworded there and this stops matching, the guard above
    silently protects nothing.
    """
    definition = (ROOT / "src/quantamind/rank/events.py").read_text(encoding="utf-8")

    missed = [name for name, pattern in RESTATEMENTS.items() if not pattern.search(definition)]
    assert not missed, (
        f"{missed} no longer match `rank/events.py`, so those clauses of the definition could be "
        f"copied into a test without this guard noticing"
    )
