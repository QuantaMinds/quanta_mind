"""Tests for the guards in `scripts/guard/runtime/` — behaviour, not shape.

WHAT: the network chokepoint, and the pinned thresholds every runtime guard depends on.
WHY:  mirrors `scripts/guard/runtime/`, so a guard and its known-answer test move together. They
      drifted apart once already: the thresholds file kept the old flat paths after the guards
      moved, and the suite failed rather than the guard, which is the right way round but only
      because something pinned them.
IMPORTS: nothing itself.
CONSUMED BY: `just test-unit`.
"""
