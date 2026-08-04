"""Orchestration support for the Phase 0 run.

A subpackage because src/phase0/ is at the 15-file directory cap, and because
these three concerns are genuinely separate from the measurement stages:

- `worktree.py` — clone once per repository, one worktree per parent commit
- `record.py`   — the per-PR audit record, its provenance, and the checkpoint

Nothing here measures anything. The stages do that.
"""

from __future__ import annotations

__all__ = ["record", "worktree"]
