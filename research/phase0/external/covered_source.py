"""Can any corpus support the execution-grounding arm? Measure the ceiling before building one.

WHAT: For repositories this project has never measured, classify the files recent changes touch
      and report what share of changed SOURCE files are named by some test file.
WHY:  **THE EXECUTION ARM DIED AT A CEILING, NOT AT A RESULT.** Step 0 of
      `docs/plans/preregistrations/reviewer/execution-grounding-preregistration.md` measured 31%
      of findings about source a suite even names, against a 50% bar, and stopped rather than
      running an arm whose number would have described the corpus. Seven of sixteen findings were
      about test files themselves, where the suite that would adjudicate IS the subject.

      **THE PROXY IS DELIBERATELY THE SAME ONE STEP 0 USED** — "a test names the module" rather
      than "a test executes the line" — so the numbers are comparable. It over-counts, which is
      the direction that makes a FAIL trustworthy: a repository that cannot clear this cannot
      clear the stronger check either.

      **A KNOWN-ANSWER CHECK RUNS FIRST.** A classifier that called everything `source` would
      report a wonderful share, and would look exactly like a working one.
IMPORTS: stdlib only. No product import — this measures repositories, not the pipeline.
CONSUMED BY: a person, and the pre-registration it answers.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass

GIT_TIMEOUT_S = 300
COMMITS = 200
SOURCE_BAR = 0.50
MIN_SOURCE_FILES = 50

TEST_PART = re.compile(r"(^|/)(tests?|testing|spec)(/|$)|(^|/)test_[^/]*\.py$|_test\.py$")
CONFIG_SUFFIX = (".toml", ".cfg", ".ini", ".yaml", ".yml", ".json", ".txt", ".md", ".rst")


class NoSuite(RuntimeError):
    """No test file was found at all. Distinct from a suite that names nothing.

    **A CLONE THAT FAILED TO CHECK OUT REPORTED 0% AND LOOKED LIKE A REPOSITORY WITHOUT TESTS.**
    `django-rest-framework` came back 0 of 76 covered on the first run; the clone held no Python
    file whatsoever. A share of zero over a real suite is a finding about that repository; a share
    of zero over no suite is a finding about this instrument, and they must not print the same
    number.
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
    """`test`, `config`, `source` or `other`. A claim about a test cannot be judged by that test."""
    if TEST_PART.search(path):
        return "test"
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
    """Every path the last `commits` non-merge commits touched, with repeats."""
    out = _run(clone, ["log", f"-{commits}", "--no-merges", "--name-only", "--format="])
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_vocabulary(clone: pathlib.Path) -> set[str]:
    """Every module name any test file mentions. The same proxy Step 0 used, over the whole tree."""
    words: set[str] = set()
    for path in clone.rglob("*.py"):
        rel = path.relative_to(clone).as_posix()
        if classify(rel) != "test":
            continue
        try:
            words |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", path.read_text(errors="ignore")))
        except OSError:
            continue
    return words


def shape_of(clone: pathlib.Path, repo: str) -> Shape:
    """Classify what recent changes touched, and how much of the source a test names."""
    counts: Counter[str] = Counter()
    sources: set[str] = set()
    for path in changed_files(clone):
        kind = classify(path)
        counts[kind] += 1
        if kind == "source":
            sources.add(path)

    vocabulary = test_vocabulary(clone)
    if not vocabulary:
        raise NoSuite(
            f"{repo}: no test file in the tree; a 0% share would describe this "
            f"instrument rather than the repository"
        )
    covered = sum(1 for path in sources if pathlib.PurePosixPath(path).stem in vocabulary)
    return Shape(repo, len(sources), counts["test"], counts["config"], counts["other"], covered)


def known_answer() -> None:
    """A classifier that called everything `source` would report a wonderful share. Refuse first."""
    cases = {
        "src/pkg/thing.py": "source",
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
