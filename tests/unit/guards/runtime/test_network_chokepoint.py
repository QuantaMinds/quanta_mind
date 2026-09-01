"""The guard that makes D7f's refusal a mechanism rather than a promise.

WHAT: `check_network_chokepoint` against modules that reach the network with and without asking.
WHY:  **A REFUSAL SPREAD OVER NINE CALL SITES IS NINE CHANCES TO FORGET ONE.** A module added next
      month that calls `urlopen` without `permit` would reintroduce exactly the failure D7f names.
      This is the known-answer test for the guard: it must fire on a real outbound call, stay quiet
      on one that asks first, and stay quiet on a module that merely uses the WORD.

      **THE THIRD CASE IS NOT HYPOTHETICAL.** Two successive versions of the guard flagged
      `serve/cli.py`, which names an argparse argument `"clone"` and calls a local function `run`.
      A guard that fires on deliberate code teaches a reader to scroll past it.
IMPORTS: scripts/guard/runtime/check_network_chokepoint.py (via sys.path).
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))
sys.path.insert(0, str(ROOT / "scripts" / "guard" / "runtime"))

from check_network_chokepoint import check_chokepoint  # noqa: E402

REACHES_WITHOUT_ASKING = '''"""A module that calls out.

WHAT: nothing real.
WHY:  it must be refused.
IMPORTS: urllib.
"""

import urllib.request


def go():
    return urllib.request.urlopen("https://example.com")
'''

ASKS_FIRST = '''"""A module that asks first.

WHAT: nothing real.
WHY:  it must pass.
IMPORTS: urllib, types.deployment.
"""

import urllib.request

from quantamind.types.deployment import Destination, permit


def go():
    permit(Destination.GITHUB_API)
    return urllib.request.urlopen("https://example.com")
'''

WORD_ONLY = '''"""A module that only mentions cloning.

WHAT: nothing real.
WHY:  it must NOT be flagged -- it opens no socket and runs no process.
IMPORTS: nothing.
"""


def build(parser):
    parser.add_argument("clone", help="a full clone; nothing is sent anywhere")
'''


def _module(root: Path, source: str) -> Path:
    layer = root / "src" / "quantamind" / "ingest"
    layer.mkdir(parents=True, exist_ok=True)
    (layer / "subject.py").write_text(source, encoding="utf-8")
    return root


def test_an_outbound_call_without_permission_is_reported(tmp_path: Path) -> None:
    """**THE ARTEFACT: this module, named, with the primitive it used.**"""
    found = check_chokepoint(_module(tmp_path, REACHES_WITHOUT_ASKING))

    assert len(found) == 1, f"expected one violation, got {found}"
    assert found[0].rule == "network-without-permission"
    assert "urlopen" in found[0].detail
    assert found[0].path.name == "subject.py"


def test_a_call_that_asks_first_is_not_reported(tmp_path: Path) -> None:
    """The other half. Without this, a guard flagging everything would pass the test above."""
    assert check_chokepoint(_module(tmp_path, ASKS_FIRST)) == []


def test_a_module_that_only_says_clone_is_not_reported(tmp_path: Path) -> None:
    """**`serve/cli.py` NAMES AN ARGUMENT `clone` AND WAS FLAGGED TWICE WHILE THIS WAS WRITTEN.**"""
    assert check_chokepoint(_module(tmp_path, WORD_ONLY)) == []


def test_the_real_source_tree_is_clean() -> None:
    """**THE GUARD RUNS ON THE PRODUCT, NOT ONLY ON FIXTURES.** A guard green on invented input and
    unexamined on the real tree is the shape this project records as a harness failure."""
    assert check_chokepoint(ROOT) == []
