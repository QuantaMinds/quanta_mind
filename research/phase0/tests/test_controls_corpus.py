"""Verification of the control corpus — the three degeneracies it shipped with.

WHAT: Asserts the synthetic corpus is non-degenerate in the three ways it initially
      was not, and that the gate derives its answers rather than assigning them.
WHY:  Every test here exists because running the gate found the bug it guards.

      A control corpus can pass its own gate for reasons that say nothing about a
      real corpus, and all three failures were silent:

      1. `i % 10 < 8` over `range(8)` yields 8/8, not 80%. Perfect separation makes
         the ratio unbounded and the GEE fit unidentified — the interval came back
         [8.000, 8.000].
      2. Four `repo_id` values across 80 repositories made exposure perfectly
         confounded with cluster, so the robust variance had nothing to separate.
      3. Every symbol was `mod.target`, so every symbol-derived nonsense variable
         was constant and its 2x2 had an empty margin.

      The fourth was in the gate logic itself and is asserted in test_controls.py:
      an uncomputable negative control used to **pass**.
IMPORTS: phase0.controls.corpus, phase0.controls.gate, pytest.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from phase0.controls.corpus import (
    BREAK_FRACTION_CONTROL,
    BREAK_FRACTION_EXPOSED,
    build_corpus,
)
from phase0.controls.gate import detection_by_mechanism, measure


def test_break_fractions_are_not_perfect_separation() -> None:
    """80/10, not 100/0. Perfect separation makes the fit unidentified."""
    assert (BREAK_FRACTION_EXPOSED, BREAK_FRACTION_CONTROL) == (0.8, 0.1)


def test_planted_breaks_match_the_intended_fraction(tmp_path: Path) -> None:
    """The bug: a modular index over a shorter range silently gives 100%."""
    built = build_corpus(tmp_path, per_mechanism=10)
    exposed = [b for b in built if "-exp-" in b.record.pr_id]
    broke = sum(1 for b in exposed if b.planted_break)
    assert broke / len(exposed) == BREAK_FRACTION_EXPOSED


def test_every_repository_is_its_own_cluster(tmp_path: Path) -> None:
    """80 repositories sharing 4 repo_ids confounds exposure with cluster entirely."""
    built = build_corpus(tmp_path, per_mechanism=5)
    assert len({b.record.repo_id for b in built}) == len(built)


def test_symbols_vary_enough_for_the_nonsense_variables(tmp_path: Path) -> None:
    """A negative control with a constant predicate has an empty margin and tests nothing."""
    built = build_corpus(tmp_path, per_mechanism=5)
    symbols = [b.record.changed_symbols[0] for b in built]
    initials = {s[:1].lower() < "n" for s in symbols}
    lengths = {len(s) % 2 == 0 for s in symbols}
    assert initials == {True, False} and lengths == {True, False}


def test_changed_files_match_the_commits(tmp_path: Path) -> None:
    """The record's file set must be what the merge commit actually touched.

    They diverged once — the record named a per-PR module while the commits still
    wrote `acme/mod.py` — which would have broken A2's diff-coverage detection.
    """
    built = build_corpus(tmp_path, per_mechanism=2)
    missing = [
        s.record.pr_id for s in built if not (s.repo_path / s.record.changed_files[0]).is_file()
    ]
    assert missing == []


@pytest.mark.timeout(600)
def test_gate_derives_exposure_rather_than_assigning_it(tmp_path: Path) -> None:
    """The whole point: `super()` is detected, value-dispatch is not — from real output.

    This is A10's capability profile confirmed through the full pipeline (census,
    PyCG, join) rather than the static probe.
    """
    built = build_corpus(tmp_path, per_mechanism=2)
    tally = detection_by_mechanism(measure(built, timeout_s=120))
    assert tally["super_chain"][0] == tally["super_chain"][1]
    assert [m for m, (hit, _) in tally.items() if hit] == ["super_chain"]
