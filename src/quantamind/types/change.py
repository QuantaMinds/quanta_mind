"""What arrived: a repository, a pull request, and the units its diff touched.

WHAT: `Repo`, `PullRequest`, `Language` and `ChangedUnit` -- the input side of the pipeline
      expressed as values, with no reference to git or to HTTP.
WHY:  The unit that matters is the FUNCTION, not the file. That choice took the longest to
      arrive at and it is encoded here rather than left to each caller: a file-level type
      would let file-level ranking back in silently, and file-level ranking measures which
      file is busy, not which one comes back.
IMPORTS: stdlib only (dataclasses, enum), and types.verdict for Site.
CONSUMED BY: ingest constructs these; parse fills them; rank orders them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from quantamind.types.verdict import Site, Unresolved


class Language(Enum):
    """Languages we can parse, plus the honest catch-all.

    UNSUPPORTED is a member rather than a `None`, so a file in a language we cannot read
    carries a value that renders into the coverage line instead of vanishing from it.
    """

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    CPP = "cpp"
    UNSUPPORTED = "unsupported"


# **THE SUFFIX MAP LIVES HERE, NOT IN `parse/`, AND THE LAYER ORDER IS WHY.** `ingest/` must decide
# which changed files to fetch, and `ingest` sits LEFT of `parse` -- it may not import
# `parse/languages.py`. Putting the map in the leftmost layer lets both read one source of truth
# instead of two lists that drift. `parse/languages.py` re-exports it.
#
# **A suffix absent here is UNSUPPORTED, which is a VALUE that renders into the coverage line.**
# Widening this set is how a language is added, and it is deliberately one edit.
BY_SUFFIX: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".cc": Language.CPP,
    ".cpp": Language.CPP,
    ".hpp": Language.CPP,
}

REVIEWABLE_SUFFIXES: tuple[str, ...] = tuple(sorted(BY_SUFFIX))
"""Every suffix the product will look at. `ingest/` filters on this; `parse/` maps it."""


def language_of(path: str) -> Language:
    """The language of a path, or `UNSUPPORTED`. Never `None`: absence must render."""
    from pathlib import PurePosixPath

    return BY_SUFFIX.get(PurePosixPath(path).suffix.lower(), Language.UNSUPPORTED)


@dataclass(frozen=True, slots=True)
class Repo:
    """A repository we have been asked to look at.

    `clone_filter` is recorded because a blob-filtered clone reads differently from a
    complete one, and a history read against one is not deterministic until its object
    store is warm. That fact voided measurements before it was written down.
    """

    host: str
    name: str
    default_branch: str = "main"
    clone_filter: str = ""

    def __post_init__(self) -> None:
        if "/" not in self.name:
            raise ValueError(f"Repo.name must be owner/name, got {self.name!r}")

    @property
    def is_partial_clone(self) -> bool:
        return bool(self.clone_filter)


@dataclass(frozen=True, slots=True)
class PullRequest:
    """The change under review, pinned to the commit we actually read.

    `head_sha` is not decoration. It is the idempotency key: a redelivered webhook for the
    same head must not produce a second comment, and a review that cannot name the commit
    it read cannot be reproduced.
    """

    repo: Repo
    number: int
    head_sha: str
    base_sha: str
    author: str = ""

    def __post_init__(self) -> None:
        if self.number <= 0:
            raise ValueError(f"PullRequest.number must be positive, got {self.number}")
        if len(self.head_sha) < 7:
            raise ValueError(
                f"PullRequest.head_sha is too short to identify a commit: {self.head_sha!r}"
            )

    @property
    def key(self) -> str:
        """Stable identity for deduplication: repository, number, and the commit read."""
        return f"{self.repo.name}#{self.number}@{self.head_sha[:12]}"


@dataclass(frozen=True, slots=True)
class ChangedUnit:
    """One function the diff touched, which is the unit the ranking and the budget use.

    `qualified_name` is the identity that survives a file being renamed, which is why it
    is what the outcome rule matches on. A unit whose name could not be recovered is not
    constructed as a unit with an empty name -- the caller emits an Unresolved instead.
    """

    site: Site
    qualified_name: str
    language: Language
    lines_added: int = 0
    lines_removed: int = 0

    def __post_init__(self) -> None:
        if not self.qualified_name:
            raise ValueError(
                f"ChangedUnit at {self.site.render()} has no qualified_name; "
                "emit an Unresolved rather than a nameless unit"
            )

    @property
    def churn(self) -> int:
        return self.lines_added + self.lines_removed


@dataclass(frozen=True, slots=True)
class Diff:
    """Everything one pull request changed: what we understood, and what we did not.

    The two lists together are the conservation invariant. Anything the parser saw ends up
    in exactly one of them, and a reader can add them up. A Diff with an empty `unresolved`
    is a claim that nothing was skipped, and that claim is checkable.
    """

    pull_request: PullRequest
    units: tuple[ChangedUnit, ...] = field(default_factory=tuple)
    unresolved: tuple[Unresolved, ...] = field(default_factory=tuple)
    files_seen: int = 0

    @property
    def is_empty(self) -> bool:
        return not self.units and not self.unresolved

    def coverage_ratio(self) -> float:
        """Share of everything we looked at that we actually resolved.

        Returns 0.0 when nothing was seen at all, which is honest: no denominator means no
        coverage claim, not full coverage. A version of this that returned 1.0 on an empty
        diff would report perfect coverage for a review that read nothing.
        """
        total = len(self.units) + len(self.unresolved)
        if total == 0:
            return 0.0
        return len(self.units) / total
