"""How a PyCG run ended, and why that distinction decides the study.

WHAT: The GraphStatus taxonomy and the stderr-reading that assigns it.
WHY:  Split from run_graph.py, which owns invoking the subprocess. This module
      owns interpreting the wreckage, and the interpretation carries more weight
      than it looks:

      - TIMEOUT and OOM form the UNANALYZED_RESOURCE arm. RUNBOOK section 4.4
        reads that arm to decide whether this is a scalability product rather than
        an unsoundness product -- "different company, different pitch".
      - SYNTAX_UNSUPPORTED is excluded from the study as corpus attrition
        (amendment A7). PyCG parses with its host interpreter's ast, pinned at
        CPython 3.10, so `except*` or PEP 695 `type X = ...` fails because our
        toolchain is behind, not because the code is dynamic. Letting that into
        the arm above would let the age of our interpreter decide what company
        this is.
      - CRASHED is everything else, and carries the tail of stderr so a pilot can
        tell whether it is one bug or fifty.
IMPORTS: stdlib re, enum. Nothing from phase0 -- run_graph imports this, not the
      other way round.
CONSUMED BY: run_graph.py, classify_exposure.py; tests/test_run_graph.py.
"""

from __future__ import annotations

import re
from enum import Enum

# PyCG surfaces a parse failure as an unhandled SyntaxError from ast.parse.
_SYNTAX_MARKER = re.compile(r"SyntaxError: (?P<detail>.+)")
_SYNTAX_LOCATION = re.compile(r'File "(?P<path>[^"]+)", line (?P<line>\d+)')

# Killed by the OOM killer, or raised MemoryError before it got there.
OOM_SIGNAL = -9
OOM_MARKERS = ("MemoryError", "Cannot allocate memory", "std::bad_alloc")

STDERR_TAIL = 400


class GraphStatus(Enum):
    """Why we do or do not have a graph for this region."""

    OK = "ok"
    TIMEOUT = "timeout"
    OOM = "oom"
    CRASHED = "crashed"
    # A7: excluded from the study as corpus attrition, never assigned to an arm.
    SYNTAX_UNSUPPORTED = "syntax_unsupported"

    @property
    def is_resource_exhaustion(self) -> bool:
        """TIMEOUT and OOM only -- the UNANALYZED_RESOURCE arm of section 4.4."""
        return self in (GraphStatus.TIMEOUT, GraphStatus.OOM)

    @property
    def is_attrition(self) -> bool:
        """Excluded from the study, like a repository that will not clone."""
        return self is GraphStatus.SYNTAX_UNSUPPORTED


def syntax_location(stderr: str) -> tuple[str, int]:
    """The file the parse actually failed in, not the outermost stack frame.

    A traceback's FIRST `File "..."` line is runpy or the interpreter entry point;
    the offending source is the LAST one before `SyntaxError:`. Taking the first
    match reports our own runpy.py for every failure, which would make A7's
    attrition data useless -- the pilot needs to know which repository file failed
    to tell "syntax newer than 3.10" apart from anything else.
    """
    matches = _SYNTAX_LOCATION.findall(stderr)
    if not matches:
        return "", 0
    path, line = matches[-1]
    return path, int(line)


def classify(returncode: int, stderr: str) -> tuple[GraphStatus, str]:
    """Turn a non-zero exit into a status and a human-readable detail.

    Order matters: a syntax failure can also exit non-zero in ways that look like
    a crash, so it is tested first.
    """
    syntax = _SYNTAX_MARKER.search(stderr)
    if syntax:
        return GraphStatus.SYNTAX_UNSUPPORTED, syntax.group("detail").strip()

    if returncode == OOM_SIGNAL or any(marker in stderr for marker in OOM_MARKERS):
        return GraphStatus.OOM, "memory limit exceeded"

    return GraphStatus.CRASHED, stderr.strip()[-STDERR_TAIL:]
