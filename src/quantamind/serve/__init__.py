"""The serve layer.

WHAT: The outside edges: HTTP webhook, CLI, health, configuration. Contracts live here.
WHY:  Two thin adapters over identical layers, so the pipeline cannot know which one called
      it. If the two paths can diverge, what a customer verified with the CLI is not what the
      App runs.
IMPORTS: everything.
CONSUMED BY: nobody -- this is the boundary.
"""

from __future__ import annotations
