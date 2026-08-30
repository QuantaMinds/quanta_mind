"""Can any corpus support the execution-grounding arm? Measure the ceiling before building one.

WHAT: For repositories never measured here, report what share of changed SOURCE a test imports.
WHY:  **THE ARM DIED AT A CEILING, NOT A RESULT.** Step 0 of
      `docs/plans/preregistrations/reviewer/execution-grounding-preregistration.md` measured 31%
      of findings about source a suite even names, against a 50% bar, and stopped rather than
      running an arm whose number would have described the corpus.

      **IT COUNTS IMPORTS, NOT MENTIONS: THE MENTION PROXY OVER-COUNTED BY UP TO 43 POINTS.**
      The result document records both columns, so Step 0's number stays comparable.

      **A KNOWN-ANSWER CHECK RUNS FIRST**: a classifier calling everything `source` would report
      a wonderful share and look exactly like a working one.
IMPORTS: stdlib only. No product import — this measures repositories, not the pipeline.
CONSUMED BY: a person, and the pre-registration it answers.
SEE ALSO: `src/quantamind/parse/suite_reach.py`, its twin in the product — same question for ONE
      repository rather than a corpus. Duplicated because research cannot import the product.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass

GIT_TIMEOUT_S = 300
COMMITS = 200
SOURCE_BAR, MIN_SOURCE_FILES = 0.50, 50

TEST_PART = re.compile(r"(^|/)(tests?|testing|spec)(/|$)|(^|/)test_[^/]*\.py$|_test\.py$")
# **TYPER READ 98% AND 91% OF ITS "SOURCE" WAS TUTORIAL SNIPPETS** — `docs_src/tutorial/...`
# examples reached by parametrised path, not import. Excluding them takes typer from 329 changed
# source files to 30, below the floor to read a share at all.
NOT_LIBRARY = re.compile(r"(^|/)(docs?|docs_src|examples?|samples?|benchmarks?|scripts?)(/|$)")
CONFIG_SUFFIX = (".toml", ".cfg", ".ini", ".yaml", ".yml", ".json", ".txt", ".md", ".rst")


class NoSuite(RuntimeError):
    """No test file found at all — distinct from a suite that names nothing.

    `django-rest-framework` read 0 of 76 because `git-lfs` was absent and the checkout left an
    empty tree. A zero over a real suite describes the repository; a zero over no suite describes
    this instrument, and they must not print the same number.
    """


@dataclass(frozen=True)
class Shape:
    """One repository's composition, and the share a suite could speak to."""

    repo: str
    source: int
    test: int
    config: int
    other: int
    covered: int

    @property
    def share(self) -> float | None:
        """Covered source over changed source, or None when there is too little to read."""
        return self.covered / self.source if self.source >= MIN_SOURCE_FILES else None


def classify(path: str) -> str:
    """`test`, `config`, `source` or `other`. A test cannot judge a claim about itself."""
    if TEST_PART.search(path):
        return "test"
    if path.endswith(".py") and NOT_LIBRARY.search(path):
        return "other"
    if path.endswith(".py"):
        return "source"
    if path.endswith(CONFIG_SUFFIX):
        return "config"
    return "other"


def _run(clone: pathlib.Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
    )
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {clone}: {done.stderr.strip()[:200]}")
    return done.stdout


def changed_files(clone: pathlib.Path, commits: int = COMMITS) -> list[str]:
    """Every path the last `commits` non-merge commits touched, repeats included."""
    out = _run(clone, ["log", f"-{commits}", "--no-merges", "--name-only", "--format="])
    return [line.strip() for line in out.splitlines() if line.strip()]


def imported_by_tests(clone: pathlib.Path) -> set[str]:
    """Every module a test file actually IMPORTS, parsed rather than matched as text.

    **THE TEXT PROXY OVER-COUNTED BY 12 TO 43 POINTS** on the same corpus. Three artefacts:
    `__init__`/`__main__` match in any test mentioning a dunder; short stems collide, and sphinx's
    `ru`, `it`, `pt` are LOCALE files counted whenever those letters appear; and documentation
    examples were classified as source. Dunders are dropped: a name every package carries cannot
    identify a module.
    """
    found: set[str] = set()
    for path in clone.rglob("*.py"):
        if classify(path.relative_to(clone).as_posix()) != "test":
            continue
        try:
            tree = ast.parse(path.read_text(errors="ignore"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.update(alias.name.split("."))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    found.update(node.module.split("."))
                found.update(alias.name for alias in node.names)
    return {name for name in found if not name.startswith("__")}


def shape_of(clone: pathlib.Path, repo: str) -> Shape:
    """Classify what recent changes touched, and how much of the source a test names."""
    counts: Counter[str] = Counter()
    sources: set[str] = set()
    for path in changed_files(clone):
        kind = classify(path)
        counts[kind] += 1
        if kind == "source":
            sources.add(path)

    vocabulary = imported_by_tests(clone)
    if not vocabulary:
        raise NoSuite(
            f"{repo}: no test file in the tree; a 0% share would describe this "
            f"instrument rather than the repository"
        )
    stems = [s for s in (pathlib.PurePosixPath(p).stem for p in sources) if not s.startswith("__")]
    covered = sum(1 for stem in stems if stem in vocabulary)
    return Shape(repo, len(sources), counts["test"], counts["config"], counts["other"], covered)


def known_answer() -> None:
    """A classifier that called everything `source` would report a wonderful share. Refuse first."""
    cases = {
        "src/pkg/thing.py": "source",
        "docs_src/tutorial/tutorial001.py": "other",
        "examples/demo.py": "other",
        "tests/test_thing.py": "test",
        "pkg/tests/helpers.py": "test",
        "thing_test.py": "test",
        "pyproject.toml": "config",
        "docs/guide.md": "config",
        "Makefile": "other",
    }
    wrong = {path: classify(path) for path, want in cases.items() if classify(path) != want}
    if wrong:
        raise SystemExit(f"[covered-source] classifier known-answer FAILED: {wrong}")


def main(argv: list[str]) -> int:
    known_answer()
    root = pathlib.Path(argv[1]) if len(argv) > 1 else pathlib.Path("clones")
    if not root.is_dir():
        print(f"[covered-source] no clone root at {root}", file=sys.stderr)
        return 2

    shapes, refused = [], {}
    for clone in sorted(root.iterdir()):
        if not (clone / ".git").is_dir():
            continue
        try:
            shapes.append(shape_of(clone, clone.name))
        except NoSuite as absent:
            refused[clone.name] = str(absent)
    for name, why in refused.items():
        print(f"  REFUSED {name}: {why}", file=sys.stderr)
    if not shapes:
        print(f"[covered-source] no clones under {root}", file=sys.stderr)
        return 2

    print(f"  {'repository':<28}{'source':>8}{'test':>7}{'config':>8}{'covered':>9}{'share':>8}")
    for shape in sorted(shapes, key=lambda s: -(s.share or 0)):
        share = f"{shape.share:.0%}" if shape.share is not None else "too few"
        print(
            f"  {shape.repo:<28}{shape.source:>8}{shape.test:>7}{shape.config:>8}"
            f"{shape.covered:>9}{share:>8}"
        )

    clearing = [s for s in shapes if s.share is not None and s.share >= SOURCE_BAR]
    print(f"\n  {len(clearing)} of {len(shapes)} clear the {SOURCE_BAR:.0%} bar Step 0 used")
    print(json.dumps({s.repo: s.share for s in shapes}, indent=1))
    return 0 if clearing else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
