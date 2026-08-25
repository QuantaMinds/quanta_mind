"""Stamp every run with what produced it, so two runs claiming different parameters cannot match.

WHAT: `stamp(params, source)` returns a dict carrying a hash of the parameter set, a hash of the
      analysis source, and the git revision. `assert_differs(a, b)` raises when two results claim
      different parameters and carry the same fingerprint.
WHY:  **A PARAMETER EDIT SILENTLY FAILED THREE TIMES IN ONE SESSION AND EACH TIME THE RUN LOOKED
      LIKE IT HAD TAKEN THE CHANGE.** The worst was a widened corpus scan that reported identical
      totals -- 305 considered, 117 qualify -- because `ruff` had reformatted the repository tuple
      to one entry per line, so a multi-line `str.replace()` matched nothing and returned the
      unchanged text. A *different* edit in the same script DID apply, so the output format changed
      and the numbers did not, which reads exactly like a real null result.

      **THE ROOT CAUSE IS THAT RUN PARAMETERS LIVE IN SOURCE AND ARE CHANGED BY STRING MATCHING**
      against text a formatter rewrites. This does not fix that. What it does is make the failure
      LOUD: a fingerprint in the result file turns "the numbers did not move" into "these two runs
      claim different parameters and are byte-identical", which is an error rather than a finding.

      **IT IS THE WRONG-IN-YOUR-FAVOUR DIRECTION THAT MAKES THIS WORTH BUILDING.** A silent no-op
      produces the previous answer, and the previous answer is the one already believed.
IMPORTS: stdlib only.
CONSUMED BY: any harness in `bench/forensic/` that writes a results file.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


class FingerprintCollision(RuntimeError):
    """Two runs claim different parameters and share a fingerprint: an edit did not apply."""


def _git_rev() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=30
    )
    return done.stdout.strip() if done.returncode == 0 else "unknown"


def stamp(params: dict[str, Any], source: Path) -> dict[str, str]:
    """The provenance of one run: what it was given, what code ran, and at which revision."""
    given = json.dumps(params, sort_keys=True, default=str).encode()
    return {
        "params_sha": hashlib.sha256(given).hexdigest()[:16],
        "source_sha": hashlib.sha256(source.read_bytes()).hexdigest()[:16],
        "git_rev": _git_rev(),
        "params": json.dumps(params, sort_keys=True, default=str)[:400],
    }


def assert_differs(earlier: dict[str, str], later: dict[str, str]) -> None:
    """Raise when two runs were meant to differ and did not. **The whole point of the module.**

    A run whose parameters were edited must carry a different `params_sha`. If the intent was to
    change the run and the fingerprint is identical, the edit did not apply and whatever the second
    run reported is the first run's answer wearing the second run's label.
    """
    if earlier.get("params_sha") == later.get("params_sha"):
        raise FingerprintCollision(
            f"both runs carry params_sha {later.get('params_sha')}: the parameter edit did not "
            f"apply, so the second result is the first one relabelled. Params were "
            f"{later.get('params', '?')[:200]}"
        )
