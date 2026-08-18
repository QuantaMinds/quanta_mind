"""Which languages we parse, to what depth, and the honest answer for the rest.

WHAT: `language_of()` maps a path to a `Language`, and `depth_of()` says how far we can actually
      read that language today.
WHY:  **This table is public and prints in the coverage line.** A reviewer that silently skips a
      language is indistinguishable from one that read it and found nothing, which is the ambiguity
      this whole product exists to remove — so "we do not parse Rust" is a value we render, not an
      absence in a list.

      **Depth is stated separately from language, because the two diverge.** We recognise a `.go`
      file and cannot read a single function in it; claiming Go support because the enum has a
      member would be the drift `docs/product/publishing-rules.md` exists to catch.

      **Today every language is at most `HEADER` depth**, which is git's funcname hunk header —
      free, deterministic, and already proven on 664 real hunks. `EXACT` is what a tree-sitter pass
      would buy, and tree-sitter is **not a dependency of this project**: `pyproject.toml` declares
      `dependencies = []`. `AGENTS.md` asserted it was pinned there; it never was, and that line is
      corrected in this change rather than left to be believed.
IMPORTS: types (Language). Nothing to its right.
CONSUMED BY: parse.units, and render.coverage_line, which prints the depth.
"""

from __future__ import annotations

from enum import Enum
from pathlib import PurePosixPath

from quantamind.types.change import Language


class Depth(Enum):
    """How far we can read a language. Ordered least to most capable."""

    NONE = "none"
    """Recognised, and not read at all."""

    HEADER = "header"
    """The enclosing declaration git names in the hunk header. Free and deterministic."""

    EXACT = "exact"
    """A real parse of the file. Requires tree-sitter, which is not a dependency today."""


# Suffix to language. A suffix absent here is UNSUPPORTED, which is a value that renders.
BY_SUFFIX: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".cc": Language.CPP,
    ".cpp": Language.CPP,
    ".hpp": Language.CPP,
}

# What we can actually do, which is not the same as what we recognise. Every entry here is
# HEADER because git's funcname driver is the only pass built; nothing reaches EXACT.
BY_LANGUAGE: dict[Language, Depth] = {
    Language.PYTHON: Depth.HEADER,
    Language.TYPESCRIPT: Depth.HEADER,
    Language.JAVASCRIPT: Depth.HEADER,
    Language.JAVA: Depth.HEADER,
    Language.GO: Depth.HEADER,
    Language.CPP: Depth.HEADER,
}


def language_of(path: str) -> Language:
    """The language of a path, or `UNSUPPORTED`. Never `None`: absence must render."""
    return BY_SUFFIX.get(PurePosixPath(path).suffix.lower(), Language.UNSUPPORTED)


def depth_of(language: Language) -> Depth:
    """How far we can read this language today."""
    return BY_LANGUAGE.get(language, Depth.NONE)


def supported() -> list[str]:
    """The languages we read at all, for the coverage line. Sorted, so the line is stable."""
    return sorted(lang.value for lang, depth in BY_LANGUAGE.items() if depth is not Depth.NONE)
