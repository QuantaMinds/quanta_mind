"""Which clones carry complete objects, and therefore can be read for patch content.

WHAT: `full_object_clones`, returning the clone directories with no partial-clone filter.
WHY:  Symbol-level work needs patch bodies, and `git log -p` exits non-zero on a blob-filtered
      clone while emitting a partial stream -- identical invocations once returned 710 and 918
      commits against 3,313. Every harness that reads patches needs this same census, so it
      lives once rather than being copied and drifting.
IMPORTS: stdlib only (os, subprocess).
CONSUMED BY: research/phase0/gate3c_paired.py, and any harness reading patch content.
"""

from __future__ import annotations

import os
import subprocess


def full_object_clones(clones_dir: str) -> list[str]:
    """Clone directory names with complete objects, in sorted order."""
    full: list[str] = []
    for name in sorted(os.listdir(clones_dir)):
        path = os.path.join(clones_dir, name)
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        filtered = subprocess.run(
            ["git", "-C", path, "config", "--get", "remote.origin.partialclonefilter"],
            capture_output=True,
        )
        if filtered.returncode != 0:
            full.append(name)
    print(f"  full-object clones: {len(full)}\n")
    return full
