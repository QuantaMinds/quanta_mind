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

      Two tests spawn a real child, because the rest of this file only ever checked
      that the cap was ACCEPTED. A16's memory bound is a study parameter, and until a
      child was actually killed by it the parameter was a string in a docstring. They
      SKIP where the cap is unenforceable -- on darwin that is every run, so on darwin
      enforcement remains unproven and the skip says so out loud.
IMPORTS: phase0.graph.memory_cap, phase0.graph.pycg_failure, pytest, stdlib
      resource/subprocess/sys.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from phase0.graph.memory_cap import BYTES_PER_GB, MemoryCap, preexec_for, resolve
from phase0.graph.pycg_failure import GraphStatus, classify

CHILD_TIMEOUT_S = 60

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


def _enforceable_or_skip(limit_gb: int) -> MemoryCap:
    """These two tests need a cap that this kernel will actually apply.

    Skipped rather than passed on darwin, and the reason is printed. A green run on a
    platform that refuses RLIMIT_AS says nothing about enforcement, and reading it as
    "the cap works" is the mistake this whole amendment exists to correct.
    """
    cap = resolve(limit_gb)
    if not cap.enforceable:
        pytest.skip(f"cap unenforceable here, so enforcement is untested: {cap.reason}")
    return cap


def test_the_hook_applies_exactly_the_call_the_probe_tested() -> None:
    """Soft lowered, hard untouched -- read out of a real child, not asserted of code.

    The probe tested `(limit, hard)` and the hook applied `(limit, limit)`. Both
    succeed on linux, so nothing failed; on a kernel permitting one and refusing the
    other the probe would have authorised a call it never made.
    """
    import ast
    import resource

    cap = _enforceable_or_skip(1)
    completed = subprocess.run(
        [sys.executable, "-c", "import resource;print(resource.getrlimit(resource.RLIMIT_AS))"],
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
        preexec_fn=preexec_for(cap),
    )
    assert completed.returncode == 0, completed.stderr
    soft, hard = ast.literal_eval(completed.stdout.strip())
    assert soft == BYTES_PER_GB
    assert hard == resource.getrlimit(resource.RLIMIT_AS)[1]


def test_the_cap_kills_a_child_that_exceeds_it_and_the_harness_calls_it_oom() -> None:
    """Proven to FIRE, not merely accepted -- and proven through to the label.

    Every other assertion here is about the capability answer. This one drives a real
    child past a real bound, so a cap that were silently absent would let the child
    exit 0 and fail this test. It ends at `classify` on purpose: a bound that fires but
    lands on CRASHED would put a resource fact into a claim about the repository.
    """
    cap = _enforceable_or_skip(1)
    completed = subprocess.run(
        [sys.executable, "-c", "bytearray(4 * 1024**3)"],
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
        preexec_fn=preexec_for(cap),
    )
    assert completed.returncode != 0, "the child allocated past its cap and survived"
    status, _ = classify(completed.returncode, completed.stderr)
    assert status is GraphStatus.OOM


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
