"""The memory cap is probed, and the probe does not break what it measures.

WHAT: Asserts the capability answer is self-consistent, that a cap we cannot apply
      yields no preexec hook, and that probing leaves this interpreter's own limits
      exactly as it found them.
WHY:  Every assertion here corresponds to a way the previous guard was wrong.

      The platform-name guard read "not win32" as "RLIMIT_AS works". On darwin it does
      not, the ValueError surfaced inside preexec_fn, and run() recorded CRASHED --
      100% of invocations on this machine, reported as a property of the corpus.

      The restoration test guards the fix rather than the bug: a probe that lowered
      the HARD limit could not raise it again, so it would cap the study at 16 GB for
      the life of the process. That failure would be invisible until a large
      repository OOMed for a reason nobody planted.
IMPORTS: phase0.graph.memory_cap, pytest, stdlib resource/sys.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import sys

import pytest

from phase0.graph.memory_cap import BYTES_PER_GB, MemoryCap, preexec_for, resolve

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS is POSIX-only")


def test_capability_answer_carries_a_reason_when_it_is_no() -> None:
    """ "Unavailable" without a cause is the absence this project exists to remove."""
    cap = resolve(16)
    assert cap.enforceable == (cap.reason == "")


def test_no_hook_when_the_cap_cannot_be_applied() -> None:
    """A hook that swallowed its own failure leaves the child genuinely unbounded."""
    cap = resolve(16)
    assert (preexec_for(cap) is None) is not cap.enforceable


def test_probe_restores_this_process_limits_exactly() -> None:
    """Lowering the hard limit is irreversible, so the probe must not touch it."""
    import resource

    before = resource.getrlimit(resource.RLIMIT_AS)
    resolve(1)  # a limit low enough that a careless probe would be felt afterwards
    assert resource.getrlimit(resource.RLIMIT_AS) == before


def test_provenance_states_the_bound_that_actually_applied() -> None:
    """A run records the cap it had, not the cap it asked for."""
    applied = MemoryCap(limit_gb=16, enforceable=True)
    absent = MemoryCap(limit_gb=16, enforceable=False, reason="ValueError: refused")
    assert applied.provenance == "rlimit_as=16gb"
    assert absent.provenance == "rlimit_as=unavailable (ValueError: refused)"


def test_probe_agrees_with_what_the_kernel_does_right_now() -> None:
    """The capability claim is checked against a real setrlimit, not against a table."""
    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (16 * BYTES_PER_GB, hard))
    except (ValueError, OSError):
        actually_works = False
    else:
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
        actually_works = True

    assert resolve(16).enforceable is actually_works
