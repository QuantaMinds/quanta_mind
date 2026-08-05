"""Whether this machine can bound a subprocess's memory, asked of the kernel.

WHAT: A probed capability check for RLIMIT_AS, and the preexec hook that applies the
      cap when the answer is yes.
WHY:  run_graph capped PyCG behind a `sys.platform == "win32"` guard, which encodes
      "POSIX, therefore supported". macOS is POSIX and refuses: lowering RLIMIT_AS
      under an unlimited hard limit raises ValueError, soft-only included. The
      exception fires inside preexec_fn, so subprocess.run raises before PyCG starts
      and run() recorded GraphStatus.CRASHED -- a status that asserts something about
      the analysed repository. Measured on darwin arm64: 100% of invocations, which
      is a corpus run that finishes, reports total attrition, and yields a null drawn
      from zero measurements.

      ENVIRONMENT.lock Finding 4 is this shape one platform over, and the lesson it
      records is the one taken here: the guard must ask the kernel rather than the
      platform name. `enforceable` is therefore probed at first use, not assumed from
      `sys.platform`, and the answer travels with the result so a run cannot quietly
      claim a bound it never had.

      The probe moves the SOFT limit only and restores it. Lowering the hard limit is
      irreversible for a non-root process, so a probe that touched it could cap this
      interpreter at the study's limit for the rest of the run -- a probe that breaks
      what it measures.

      Probe and hook call ONE function, `_lower_soft`, because they diverged once: the
      probe tested `(limit, hard)` and the hook applied `(limit, limit)`, so the answer
      authorised a call nobody had tried. Sharing the call is what keeps "we checked"
      and "we did" the same sentence.
IMPORTS: stdlib dataclasses, functools, resource, sys. Nothing from phase0.
CONSUMED BY: graph/run_graph.py; tests/test_memory_cap.py.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

BYTES_PER_GB = 1024**3


@dataclass(frozen=True, slots=True)
class MemoryCap:
    """A memory bound, and whether this machine will actually apply it.

    `reason` is empty when `enforceable` is True. When it is False the reason is the
    kernel's own refusal text, because "unavailable" without a cause is the kind of
    absence this project spends its time removing.
    """

    limit_gb: int
    enforceable: bool
    reason: str = ""

    @property
    def provenance(self) -> str:
        """How a result should record the bound it ran under."""
        if self.enforceable:
            return f"rlimit_as={self.limit_gb}gb"
        return f"rlimit_as=unavailable ({self.reason})"


def _lower_soft(limit_bytes: int) -> None:
    """The one call both the probe and the hook make. Soft only, hard as found.

    Probe and apply must be the SAME operation, or the probe authorises something it
    never tested. The first version probed `(limit, hard)` and applied `(limit, limit)`:
    a platform permitting the first and refusing the second would have answered
    "enforceable" and then raised inside preexec_fn, one fork later.

    Soft-only is what a probe can undo -- lowering the HARD limit is irreversible for a
    non-root process, so a probe that touched it would cap this interpreter at the
    study's limit for the rest of the run. The cost of soft-only is stated rather than
    hidden: a child that raises its own soft limit back escapes the bound. PyCG does not,
    and `GraphResult.mem_cap` records the bound so a run that outlived it is checkable.
    """
    import resource

    _, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))


@cache
def _probe(limit_bytes: int) -> tuple[bool, str]:
    """Can RLIMIT_AS actually be lowered to `limit_bytes` here? Ask, then undo.

    Cached because the answer is a property of the platform, and the study makes one
    of these calls per repository.
    """
    if sys.platform == "win32":
        return False, "RLIMIT_AS does not exist on win32"

    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    try:
        _lower_soft(limit_bytes)
    except (ValueError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"

    resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    return True, ""


def resolve(mem_limit_gb: int) -> MemoryCap:
    """The cap this machine will honour, measured rather than assumed."""
    enforceable, reason = _probe(mem_limit_gb * BYTES_PER_GB)
    return MemoryCap(limit_gb=mem_limit_gb, enforceable=enforceable, reason=reason)


def preexec_for(cap: MemoryCap) -> Callable[[], None] | None:
    """A preexec_fn applying `cap`, or None when this machine cannot apply it.

    None rather than a hook that swallows its own failure: a preexec_fn that catches
    the error would leave the child running unbounded while the parent believed
    otherwise, which is the bound-that-was-never-there in a quieter form.
    """
    if not cap.enforceable:
        return None

    limit = cap.limit_gb * BYTES_PER_GB

    def apply() -> None:
        _lower_soft(limit)

    return apply
