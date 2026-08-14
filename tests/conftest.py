"""Test-wide path setup.

WHAT: Puts scripts/guard/ on sys.path so tests can import the guard modules.
WHY:  The guards are deliberately not part of the installable package -- they must
      run before quantamind is installable, which is why they import each other by bare
      name (`from discovery import ...`). That works when they are invoked as
      `python scripts/guard/check_x.py`, because Python puts the script's own
      directory on sys.path[0]. Under pytest there is no such directory, so it is
      added here rather than by mutating sys.path inside each test.
IMPORTS: stdlib only (pathlib, sys). No project imports -- this runs at collection.
CONSUMED BY: pytest, for every tier under tests/.
"""

from __future__ import annotations

import sys
from pathlib import Path

GUARD_DIR = Path(__file__).resolve().parent.parent / "scripts" / "guard"

if str(GUARD_DIR) not in sys.path:
    sys.path.insert(0, str(GUARD_DIR))
