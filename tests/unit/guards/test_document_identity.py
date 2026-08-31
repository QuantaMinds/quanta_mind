"""Two documents with one name, driven through `citations/identity.main()`.

WHAT: Builds miniature `docs/` trees, runs the guard over each, and asserts on the collisions it
      must catch, the honest shapes it must leave alone, and that a green run on the real tree is
      green because it read something.
WHY:  **THE COMMIT THAT CREATED THIS RISK ALSO SPECIFIED THIS GUARD, AND IT WAS WRITTEN EIGHTEEN
      DAYS LATE.** `a38c2d1` moved eight loose documents into folders and closed by noting that
      the citation resolver's basename fallback would pick arbitrarily between two documents of
      one name, that `check_module_identity.py` enforces this for `src/`, and that **nothing
      enforced it for `docs/`**. A file was then created at the vacated `docs/CORRECTIONS.md`.
      The corrections log ran as two files; twenty-five citations named the old path and about
      half pointed at an entry living only in the other copy; and the half left behind opened by
      declaring the missing entries fabricated. `docs/engineering/CORRECTIONS.md` entry 12 is the
      account.

      **THE HONEST SHAPES ARE TESTED AS HARD AS THE BROKEN ONE.** Nine basenames repeat elsewhere
      in this tree and every one is deliberate — eleven `chunk_0.md` are parallel rater corpora,
      thirteen `README.md` are one per directory. That is why the guard is scoped to `docs/`, and
      a test that only proved it fires would not have caught a version that fires on everything.
IMPORTS: scripts/guard/citations/identity.py. No product imports.
CONSUMED BY: `just check`.
SEE ALSO: `tests/unit/guards/hooks/test_session_end_map_path.py`, the other half of the same
      rename — the map moved and one of its two `MAP_PATH` constants did not follow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from citations.identity import main  # noqa: E402


def _tree(root: Path, *relative: str) -> None:
    """Write each named document with enough body that it is a document, not a marker."""
    for name in relative:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {Path(name).stem}\n\nBody.\n", encoding="utf-8")


def test_two_documents_with_one_name_fail_however_far_apart_they_sit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The exact collision that ran for eighteen days: one loose, one inside a folder."""
    _tree(tmp_path, "docs/CORRECTIONS.md", "docs/engineering/CORRECTIONS.md")

    assert main(["identity", str(tmp_path)]) == 1
    printed = capsys.readouterr().out
    assert "CORRECTIONS.md" in printed
    assert "docs/engineering/CORRECTIONS.md" in printed, printed
    assert "document-identity" in printed


def test_a_collision_between_two_subfolders_is_caught_too(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Neither copy has to sit at the top level, or the rule is one about a single directory
    wearing a rule about `docs/`."""
    _tree(tmp_path, "docs/findings/pricing.md", "docs/product/pricing.md")

    assert main(["identity", str(tmp_path)]) == 1
    assert "pricing.md" in capsys.readouterr().out


def test_documents_with_different_names_in_the_same_folders_are_left_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shape of the real tree. A guard that fires here is a guard people disable."""
    _tree(
        tmp_path,
        "docs/engineering/CODEBASE.md",
        "docs/engineering/CORRECTIONS.md",
        "docs/product/pricing.md",
        "docs/product/QUANTAMIND.md",
        "docs/findings/PHASE0_RUNBOOK.md",
        "docs/plans/implementation.md",
    )

    assert main(["identity", str(tmp_path)]) == 0
    assert "ok" in capsys.readouterr().out


def test_session_records_may_collide_because_nobody_can_rename_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """They are gitignored transcripts named for a branch. Governing them makes the guard fire on
    something no edit to a document can fix, which is how a guard stops being read."""
    _tree(tmp_path, "docs/plans/session-feat-x.md", "docs/plans/old/session-feat-x.md")

    assert main(["identity", str(tmp_path)]) == 0, capsys.readouterr().out


def test_the_real_tree_is_clean_and_the_guard_actually_read_it() -> None:
    """**A GREEN RUN OVER NOTHING PRINTS THE SAME `ok`.** The floor inside `main()` raises rather
    than passing when discovery collapses; this asserts the population it is floored against is
    really there, so the green above is green for the right reason."""
    documents = list((ROOT / "docs").rglob("*.md"))

    assert len(documents) > 100, f"only {len(documents)} documents found under docs/"
    assert main(["identity", str(ROOT)]) == 0
