"""Run the model's own claim as code, and keep only what the interpreter confirms.

WHAT: Takes a finding that carries a self-contained snippet demonstrating its claim, runs it in a
      subprocess, and promotes the finding only when the snippet prints CONFIRMED.
WHY:  Four of the wrong findings asserted things about Python that Python contradicts in one line
      -- that closing a never-started coroutine raises, that `list.insert` can raise ValueError,
      that aware datetimes in different zones compare unequal. All three are false and all three
      were decidable without the repository. The model also claimed `all([])` is falsy and was
      right, and that one is a genuine defect.

      So this is not a research programme, it is a subprocess. It cannot touch claims that need the
      repository -- "refuted by code a few lines away" or "misreads what this function does" -- but
      it removes deterministically the one class where the model is confidently wrong.

      THE SNIPPET IS THE MODEL'S OWN. It is not asked whether it is right; it is asked to write the
      program that would show it, and the interpreter answers. A model that cannot produce a
      demonstrating snippet has told us something too.
IMPORTS: stdlib only (subprocess, sys, tempfile, os).
CONSUMED BY: `execution_run.py` in this package.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

TIMEOUT_S = 10
BANNED = (
    "import os",
    "import shutil",
    "import subprocess",
    "open(",
    "__import__",
    "socket",
    "requests",
    "urllib",
    "eval(",
    "exec(",
)


class Unsafe(RuntimeError):
    """The snippet touches the filesystem, the network or the interpreter's internals."""


def screen(snippet: str) -> None:
    """Refuse a snippet that does anything but compute. A demonstration needs no I/O."""
    low = snippet.lower()
    for b in BANNED:
        if b in low:
            raise Unsafe(f"snippet contains {b!r}; a demonstration needs no I/O")


def run(snippet: str) -> dict[str, object]:
    """Execute and report. CONFIRMED only when the snippet says so on stdout.

    A crash, a timeout, an empty output and a REFUTED are four different results and are kept
    apart -- collapsing them would repeat the defect this project keeps finding.
    """
    try:
        screen(snippet)
    except Unsafe as exc:
        return {"outcome": "REFUSED", "detail": str(exc)}

    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "claim.py")
        with open(f, "w") as fh:
            fh.write(snippet)
        try:
            p = subprocess.run(
                [sys.executable, "-I", "-S", f],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_S,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return {"outcome": "TIMEOUT", "detail": f"exceeded {TIMEOUT_S}s"}

    out = (p.stdout or "").strip()
    if p.returncode != 0:
        return {"outcome": "CRASHED", "detail": (p.stderr or "").strip()[:200], "stdout": out}
    if "CONFIRMED" in out.upper():
        return {"outcome": "CONFIRMED", "detail": out[:200]}
    if "REFUTED" in out.upper():
        return {"outcome": "REFUTED", "detail": out[:200]}
    return {"outcome": "SILENT", "detail": out[:200] or "(no output)"}
