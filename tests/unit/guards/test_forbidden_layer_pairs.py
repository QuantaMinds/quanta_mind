"""The pairs the left-only layer rule cannot catch, and the sentence that claimed it did.

WHAT: `check_conventions.check_layering` against a `verify/` module that imports `infer/`.
WHY:  **AGENTS.md RULE 7 ASSERTED A MECHANISM THAT DID NOT EXIST FOR MONTHS.** It reads: the layer
      order "is what stops `verify` importing `infer`: the layer adjudicating the model's claims
      cannot start trusting them." It never stopped it — `infer` is at index 6 and `verify` at 7 in
      `discovery.LAYER_ORDER`, so the import runs LEFT and the left-only rule waves it through. The
      rule was true as an intention and false as a claim, which is rule 14's own shape appearing
      inside the rules file.

      **THIS IS THE KNOWN-ANSWER TEST, AND IT NAMES ITS ARTEFACT.** Not "some violation is
      reported" — the violation must name `verify`, name `infer`, and point at the import's own
      line. A guard that reported something else, or reported nothing on a real violation, would
      leave the sentence unbacked again.

      **AND IT ASSERTS THE CLEAN CASE TOO.** A guard that fires on everything is as useless as one
      that fires on nothing, and only the pair of assertions tells them apart.
IMPORTS: scripts/guard/check_conventions.py, scripts/guard/discovery.py (via sys.path).
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from check_conventions import FORBIDDEN, check_layering  # noqa: E402
from discovery import LAYER_ORDER  # noqa: E402

VERIFY_IMPORTING_INFER = '''"""A module in the verify layer that reaches for the model.

WHAT: nothing real.
WHY:  it must be refused.
IMPORTS: infer, which is exactly the problem.
"""

from quantamind.infer.gemini import read
'''

CLEAN = '''"""A module in the verify layer that behaves.

WHAT: nothing real.
WHY:  it must pass.
IMPORTS: types only.
"""

from quantamind.types.verdict import Provenance
'''


def _package(root: Path, source: str) -> Path:
    """A minimal `src/quantamind/verify/` tree the guard's own discovery will walk."""
    layer = root / "src" / "quantamind" / "verify"
    layer.mkdir(parents=True)
    (root / "src" / "quantamind" / "__init__.py").write_text('"""p."""\n', encoding="utf-8")
    (layer / "__init__.py").write_text('"""p."""\n', encoding="utf-8")
    (layer / "subject.py").write_text(source, encoding="utf-8")
    return root / "src" / "quantamind"


def test_the_pair_the_ordering_cannot_catch_is_declared() -> None:
    """**`infer` REALLY IS TO THE LEFT OF `verify`**, which is why FORBIDDEN has to exist.

    If a future reordering ever put `infer` to the right, the left-only rule would catch this on
    its own and this whole mechanism would be redundant. This test says which world we are in.
    """
    assert LAYER_ORDER.index("infer") < LAYER_ORDER.index("verify")
    assert ("verify", "infer") in FORBIDDEN


def test_a_verify_module_importing_infer_is_reported(tmp_path: Path) -> None:
    """**THE ARTEFACT: this exact import, named, at its own line.**"""
    package = _package(tmp_path, VERIFY_IMPORTING_INFER)
    found = check_layering(tmp_path, package)

    assert len(found) == 1, f"expected exactly one violation, got {found}"
    only = found[0]
    assert only.rule == "forbidden-pair"
    assert "verify" in only.detail and "infer" in only.detail
    assert only.path.name == "subject.py"
    assert only.line == 8, "must point at the import, not at the file"


def test_a_verify_module_importing_types_is_not_reported(tmp_path: Path) -> None:
    """**THE OTHER HALF.** Without this, a guard that flagged every import would pass above."""
    package = _package(tmp_path, CLEAN)
    assert check_layering(tmp_path, package) == []
