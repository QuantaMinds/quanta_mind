"""Two documents under `docs/` may not claim the same basename.

WHAT: Fails when `docs/` holds two files with one name -- `CORRECTIONS.md` in two folders,
      say. One check, one rule, over one tree.
WHY:  **THIS GUARD WAS SPECIFIED BY THE COMMIT THAT CREATED THE RISK, AND WRITTEN EIGHTEEN DAYS
      LATE.** `a38c2d1` moved eight loose documents into folders by `git mv` and closed with:
      *"the citation guard's basename fallback ... means two documents with one basename in
      different folders would resolve to whichever the index happened to keep. Nothing in the
      tree collides today. `check_module_identity.py` enforces this for `src/` and nothing
      enforces it for `docs/`."*

      A file was then created at the vacated path. The corrections log ran as two files for
      eighteen days; twenty-five citations named the old path and about half of them pointed at
      an entry that lived only in the other copy; and the half left behind opened by declaring
      the missing entries fabricated. `docs/engineering/CORRECTIONS.md` entry 12 is the whole
      account. Every existing guard passed the entire time, because **each half was individually
      well-formed** -- both files parsed, both were cited, both had readers.

      **THE COLLISION IS CAUGHT AT CREATION, NOT AT CITATION, AND THAT ORDER IS THE POINT.**
      `resolve.py` catches an ambiguous BARE-BASENAME citation, which is the narrower half: only
      one of the twenty-six citations was bare, so that check alone would have found one instance
      in twenty-six. The other twenty-five spelled the full path, resolved cleanly, and were
      wrong. **A citation that resolves is not a citation that resolves to the right thing** --
      no resolver can see that, and only forbidding the collision can.

      **`docs/` ONLY, AND THE SCOPE IS A MEASUREMENT RATHER THAN A GUESS.** Nine basenames repeat
      elsewhere in this tree and every one is deliberate: eleven `chunk_0.md` across the rater
      directories are parallel corpora, five `RUBRIC.md` are one rubric per rater, thirteen
      `README.md` are one per directory. Governing those would fire on correct structure, and a
      guard that fires on correct structure is one people learn to skip.
IMPORTS: scripts/guard/{coverage,discovery}.py; stdlib collections, sys, pathlib.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The guards import each other by bare name, which works because Python puts a script's own
# directory on sys.path[0]. This one lives a level down, so the parent is added explicitly --
# the same reason `resolve.py` and `freshness.py` do it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import defaultdict

from coverage import assert_examined, guarded
from discovery import Violation, report

# Hook-written session records, named for their branch. They are gitignored and regenerated, so
# two of them colliding is not a defect anybody can fix by renaming a document.
SESSION_RECORD = "session-"

DOCS = "docs"


def collisions(root: Path) -> list[Violation]:
    """Every basename under `docs/` held by more than one file."""
    by_name: dict[str, list[Path]] = defaultdict(list)
    for path in sorted((root / DOCS).rglob("*.md")):
        if path.name.startswith(SESSION_RECORD):
            continue
        by_name[path.name].append(path)

    out: list[Violation] = []
    for name, paths in sorted(by_name.items()):
        if len(paths) < 2:
            continue
        others = ", ".join(str(p.relative_to(root)) for p in paths[1:])
        out.append(
            Violation(
                paths[0],
                1,
                "document-identity",
                f"{name!r} is also at {others}. Two documents with one name are "
                f"indistinguishable to every citation that spells the basename, and a "
                f"citation spelling the full path resolves cleanly to whichever copy it "
                f"names -- which is how half a corrections log came to be declared "
                f"fabricated. Merge them, or rename one so a reader can tell which is live.",
            )
        )
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    # **THE POPULATION IS ASSERTED BECAUSE AN EMPTY SCAN PRINTS THE SAME `ok` AS A CLEAN ONE.**
    # A wrong root, a renamed `docs/`, or an rglob that stops matching all report zero
    # collisions, which is also what a healthy tree reports. `docs/` holds well over a hundred
    # documents; a run that sees fewer than twenty is reading the wrong tree.
    assert_examined("documents", sum(1 for _ in (root / DOCS).rglob("*.md")), 20, root)
    return report(collisions(root), root, "document-identity")


if __name__ == "__main__":
    raise SystemExit(guarded(lambda: main(sys.argv)))
