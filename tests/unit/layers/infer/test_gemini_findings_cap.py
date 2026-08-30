"""Verification that the model's reply is capped and filtered before anything is published.

WHAT: Drives `infer/gemini._findings`, the parse boundary between a model reply and the product's
      own `Finding` type — the cap on how many are kept, and the filter that drops claims about
      files the ranker never sent.
WHY:  **`infer/` HAD NO UNIT TESTS AND `MAX_FINDINGS` WAS FREELY MUTABLE.** It bounds what a
      single model reply can put on a customer's pull request. At 17 a talkative reply doubles the
      comment; at 0 the product posts a review with no findings at all and reads as a clean run.
      Both mutations left every tier of the suite green.

      **THE PATH FILTER IS THE MORE IMPORTANT HALF.** A claim about a file we never sent cannot
      have been read off the diff — the model has been observed attaching a claim to an unrelated
      path — and it is dropped rather than published. That is the module's stated reason to exist
      and nothing exercised it either.

      Eight is written out. `MAX_FINDINGS + 1` reads the value under test and passes at any value.
IMPORTS: pytest, quantamind.infer.gemini.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

import pytest

from quantamind.infer.gemini import InferenceFailed, _findings

CAP = 8
"""The shipped cap, written out. See the module docstring."""


def _reply(count: int, path: str = "src/a.py") -> str:
    rows = [
        {"path": path, "quote": f"compute_{n}(alpha)", "claim": f"claim number {n}", "fix": ""}
        for n in range(count)
    ]
    return f"Here is what I found:\n{json.dumps(rows)}\nThat is all."


def test_a_reply_longer_than_the_cap_is_truncated_to_it() -> None:
    """Twenty findings offered, eight kept. At MAX_FINDINGS = 17 this returns seventeen."""
    kept = _findings(_reply(20), {"src/a.py"})

    assert len(kept) == CAP


def test_a_reply_within_the_cap_is_kept_whole() -> None:
    """The false-positive direction: the cap must not truncate an ordinary reply.

    This is the assertion that fails at MAX_FINDINGS = 0, where every reply comes back empty
    and the product publishes a clean review of a change it did have findings on.
    """
    kept = _findings(_reply(3), {"src/a.py"})

    assert len(kept) == 3
    assert [f.claim for f in kept] == ["claim number 0", "claim number 1", "claim number 2"]


def test_a_finding_about_a_file_we_never_sent_is_dropped() -> None:
    """A claim about code nobody showed the model cannot have been read off the diff."""
    kept = _findings(_reply(2, path="src/never_sent.py"), {"src/a.py"})

    assert kept == []


def test_the_cap_counts_rows_offered_not_rows_kept() -> None:
    """Ten unusable rows then two good ones: the cap is spent before the good ones are reached.

    Asserted because it is a real property of `rows[:MAX_FINDINGS]` rather than an oversight to
    paper over — a caller reading "eight findings maximum" should know the bound is on what the
    model said, not on what survived the filter.
    """
    rows = [{"path": "src/other.py", "quote": f"q{n}xxxxxx", "claim": f"c{n}"} for n in range(10)]
    rows += [{"path": "src/a.py", "quote": "compute(alpha)", "claim": "a real one"}]

    assert _findings(json.dumps(rows), {"src/a.py"}) == []


def test_a_reply_with_no_json_array_is_a_failure_not_an_empty_list() -> None:
    """An unparseable reply must never read as 'the model found nothing'."""
    with pytest.raises(InferenceFailed, match="no JSON array"):
        _findings("I could not review this change.", {"src/a.py"})


def test_an_array_that_is_not_valid_json_is_a_failure() -> None:
    """Bracket-shaped but unparseable. A truncated reply is a failed read, not a clean review.

    Single quotes rather than a truncated string on purpose: a truncated array never matches the
    array pattern at all and takes the `no JSON array` path above, so it would not reach here.
    """
    with pytest.raises(InferenceFailed, match="not JSON"):
        _findings("[{'path': 'src/a.py'}]", {"src/a.py"})
