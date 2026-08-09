"""Every cited document and line number must resolve to something that exists.

WHAT: Scans prose for citations and fails when one points at nothing:
      a `.md` path with no such file, or a `file.py:NNN` past that file's end.
WHY:  A document was cited in review as established policy -- by path AND section
      number -- and the file had never been committed. The section it quoted did not
      exist either. Nothing objected, because prose does not fail a test, and the
      citation was acted on: work was done under a rule nobody had written down.

      That is the same class as A31 recording a withdrawal the code never enacted, and
      as a validation tool reconstructing the artefact it was meant to consume. Stated
      authority with nothing behind it. Two of the three are mechanically catchable and
      this is one of them.

      The likelier future failure is drift rather than fabrication: a line reference that
      was right when written and wrong after an edit. `file.py:NNN` is checked against the
      file's actual length for that reason.

      Deliberately NOT checked: whether the cited line still says what the citing prose
      claims. No guard can read intent, and a guard that appeared to would be worse than
      none -- the argument `AGENTS.md` already makes for tagging things ADVISORY.
IMPORTS: scripts/guard/discovery.py; stdlib re, sys, pathlib. No project imports.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from discovery import Violation, report

# A markdown path: at least one path-ish character, ending `.md`. Bare basenames count,
# because that is how this repository cites its own documents.
MD = re.compile(r"(?<![\w/.-])([A-Za-z0-9_][A-Za-z0-9_./-]*\.md)\b")

# `path/to/file.py:123`. The line number is what makes it checkable.
PY_LINE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_][A-Za-z0-9_./-]*\.py):(\d+)\b")

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "vendor", ".mypy_cache"}

# Prose that talks ABOUT a citation rather than making one. The guard exists because a
# fabricated citation was acted on; a line demonstrating the ban must not trip it.
ALLOW = "citation:allow"


def _scan_roots(root: Path) -> list[Path]:
    """The prose this guard governs: docs, plus the rule files at the top level."""
    found = [p for p in (root / "docs").rglob("*.md") if not _skipped(p)]
    found += [root / name for name in ("AGENTS.md", "CLAUDE.md", "README.md", "BRIEFING.md")]
    return [p for p in found if p.is_file()]


def _skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _index(root: Path, suffix: str) -> dict[str, list[Path]]:
    """basename -> every file with it. Citations here are often bare basenames."""
    out: dict[str, list[Path]] = {}
    for path in root.rglob(f"*{suffix}"):
        if _skipped(path):
            continue
        out.setdefault(path.name, []).append(path)
    return out


def _resolves(root: Path, token: str, index: dict[str, list[Path]]) -> Path | None:
    """The file a citation names, by relative path or by basename."""
    direct = root / token
    if direct.is_file():
        return direct
    matches = index.get(Path(token).name)
    return matches[0] if matches else None


def check(root: Path) -> list[Violation]:
    """Every citation in prose, resolved against the tree."""
    violations: list[Violation] = []
    md_index = _index(root, ".md")
    py_index = _index(root, ".py")

    for doc in _scan_roots(root):
        fenced = False
        for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            # A fenced block is an EXAMPLE, not a citation. `README.md` shows sample tool
            # output naming `plugins/legacy.py:88`, a file that is supposed not to exist --
            # it illustrates the product's own "cannot be determined statically" verdict.
            # Reading that as a broken reference would make the guard fire on the very
            # thing the product is for.
            if fenced or ALLOW in line:
                continue
            # A URL is somebody else's namespace and this guard cannot resolve it.
            stripped = re.sub(r"https?://\S+", " ", line)

            for token in MD.findall(stripped):
                if _resolves(root, token, md_index) is None:
                    violations.append(
                        Violation(
                            doc,
                            number,
                            "citation-unresolved",
                            f"cites {token!r}, which does not exist. A citation to a "
                            f"document that was never written reads as established "
                            f"authority and gets acted on.",
                        )
                    )

            for token, raw in PY_LINE.findall(stripped):
                target = _resolves(root, token, py_index)
                if target is None:
                    violations.append(
                        Violation(
                            doc,
                            number,
                            "citation-unresolved",
                            f"cites {token!r}, which does not exist.",
                        )
                    )
                    continue
                length = len(target.read_text(encoding="utf-8").splitlines())
                if int(raw) > length:
                    violations.append(
                        Violation(
                            doc,
                            number,
                            "citation-past-eof",
                            f"cites {token}:{raw}, but that file has {length} lines. "
                            f"A line reference that was right when written and wrong "
                            f"after an edit is the likelier failure than a fabricated one.",
                        )
                    )
    return violations


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    return report(check(root), root, "citations")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
