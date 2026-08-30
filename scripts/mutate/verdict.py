"""Decide what a set of mutation results MEANS, which is not the same as counting them.

WHAT: `verdict(results)` turns `(target, caught)` pairs into the lines a person should read:
      how many constants are genuinely pinned, which are caught only by breaking, which are
      unseen.
WHY:  **A CATCH IS NOT AUTOMATICALLY COVERAGE, AND COUNTING THEM TOGETHER HID THAT FOR A WHOLE
      SWEEP.** On `src/quantamind`, 29 of 130 mutations were caught and that was reported as the
      coverage figure. 20 of those 29 were the `-> 0` case, and zero rarely fails an assertion —
      it breaks the code. `BLOB_TIMEOUT_S = 0` failed 23 tests with 69 `TimeoutExpired` and 7
      assertions: the suite saw a crash, not a wrong number.

      **READ AS VALUES ACTUALLY PINNED, THAT RUN COVERED 8 CONSTANTS OF 62.** The difference
      between 8 and 29 is entirely collateral breakage, and nothing in the output said so. A
      constant caught only at zero is WEAK: the suite executes the code, so it notices the
      constant being catastrophic and would not notice it being wrong.

      **THIS IS ITS OWN MODULE BECAUSE IT IS ITS OWN DECISION.** The sweep runs mutations; this
      says what they mean. They were one file until that file needed an "and" to describe itself,
      which is `AGENTS.md` rule 6.
IMPORTS: stdlib only.
CONSUMED BY: `scripts/mutate/sweep.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

ZERO = ("0", "0.0")


class Mutation(Protocol):
    """The part of a sweep target this module needs: which constant, where, and what it became."""

    # Read-only on purpose: `sweep.Target` is a frozen dataclass, and a Protocol declaring
    # plain attributes demands settable ones, which a frozen dataclass does not provide.
    @property
    def name(self) -> str: ...

    @property
    def new(self) -> str: ...

    @property
    def path(self) -> Path: ...


def _by_constant(results: Sequence[tuple[Mutation, bool]]) -> dict[str, dict[bool, bool]]:
    """{constant: {was_the_zero_mutation: caught}}. Keyed by file too, so two cannot merge."""
    seen: dict[str, dict[bool, bool]] = {}
    for target, caught in results:
        seen.setdefault(f"{target.name} ({target.path})", {})[target.new in ZERO] = caught
    return seen


def verdict(results: Sequence[tuple[Mutation, bool]]) -> list[str]:
    """The lines to print. Empty results is a caller error, not a clean sweep."""
    if not results:
        raise ValueError("no mutation results to judge; a sweep of nothing is not a clean sweep")

    seen = _by_constant(results)
    weak = sorted(k for k, v in seen.items() if v.get(True) and not v.get(False, True))
    unseen = sorted(k for k, v in seen.items() if not any(v.values()))
    covered = len(seen) - len(weak) - len(unseen)

    lines = [
        "",
        f"[mutate] {covered} constant(s) pinned, {len(weak)} WEAK, {len(unseen)} unseen"
        f"  ({len(results)} mutations over {len(seen)} constants)",
    ]
    lines += [
        f"  WEAK   {name} — caught only at 0, which breaks the code rather than checking the value"
        for name in weak
    ]
    lines += [f"  unseen {name}" for name in unseen]
    if weak:
        lines.append(
            "  A WEAK constant is not covered. The suite executes the code, so it notices the "
            "number being catastrophic and would not notice it being wrong."
        )
    return lines
