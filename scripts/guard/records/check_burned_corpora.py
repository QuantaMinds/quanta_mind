"""No repository may appear in two corpus literals, and tell me where a candidate already appears.

WHAT: Reads every `REPOS*` literal in `research/phase0/quote/corpus.py`, fails if any repository is
      named by more than one, and in `--check owner/name` mode prints every file under `research/`
      that already mentions a candidate before it is added to a corpus.
WHY:  `tornadoweb/tornado` was put into design thirteen's corpus by eye and turned out to be burned
      -- it sits in the aged corpus and in two rater pools' chunks. It was caught by luck, one
      manual grep, at a point where 38 repositories were already spent. **Eyeballing does not
      scale, and a corpus that has seen the method is a design tuned on its own test set**, which
      this project has already voided measurements over twice.

      THE PAIRWISE CHECK RUNS EVERY BUILD. The `--check` mode is the part a human runs BEFORE
      choosing a corpus, and it exists because the failure it prevents cannot be detected after the
      run: a contaminated result looks exactly like a clean one.
IMPORTS: stdlib only (pathlib, re, sys).
CONSUMED BY: `just check` via the `guards` recipe; a human before writing a new corpus literal.
"""

from __future__ import annotations

import pathlib
import re
import sys

CORPUS = pathlib.Path("research/phase0/quote/corpus.py")
LITERAL = re.compile(r"^(REPOS\w*)\s*=\s*\(", re.M)
REPO = re.compile(r'"([\w.-]+/[\w.-]+)"')
# Where prior evidence lives. A repository named here has already been measured on.
EVIDENCE = (
    "research/phase0/results",
    "research/phase0/vertex",
    "research/phase0/quote/results",
    "research/phase0/claims",
    "research/phase0/external",
    "research/phase0/runs",
)


def literals(text: str) -> dict[str, list[str]]:
    """{literal name: [repositories]} for every REPOS* tuple in the file."""
    out: dict[str, list[str]] = {}
    for m in LITERAL.finditer(text):
        end = text.index(")", m.end())
        out[m.group(1)] = REPO.findall(text[m.end() : end])
    return out


def mentions(root: pathlib.Path, repo: str) -> list[str]:
    """Files under the evidence directories that already name this repository."""
    hits: list[str] = []
    for area in EVIDENCE:
        base = root / area
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.stat().st_size > 20_000_000:
                continue
            try:
                if repo in p.read_text(errors="ignore"):
                    hits.append(str(p.relative_to(root)))
            except OSError:
                continue
    return hits


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    if len(argv) > 3 and argv[2] == "--check":
        cand = argv[3]
        hits = mentions(root, cand)
        print(f"[burned-corpora] {cand}: {len(hits)} prior mention(s)")
        for h in hits[:12]:
            print(f"    {h}")
        if hits:
            print("  BURNED — this repository has already been measured on. Choose another.")
        else:
            print("  FRESH — no prior mention under research/.")
        return 1 if hits else 0

    path = root / CORPUS
    if not path.exists():
        # **NOT `return 0`.** "Nothing to check" printed the same word as "checked everything
        # and found no reuse", so a moved or renamed corpus file would have read as a clean
        # run forever. The same defect was fixed in check_schema_shape; this is its twin.
        print(
            f"[burned-corpora] {CORPUS} not found — the guard is watching nothing", file=sys.stderr
        )
        return 2
    lits = literals(path.read_text())
    seen: dict[str, str] = {}
    bad: list[str] = []
    for name, repos in lits.items():
        for r in repos:
            if r in seen and seen[r] != name:
                bad.append(f"  {r}: in both {seen[r]} and {name}")
            else:
                seen[r] = name
    if bad:
        print(f"[burned-corpora] {len(bad)} repository reused across corpora:")
        print("\n".join(bad))
        print("  A repository measured twice is a design tuned on its own test set.")
        return 1
    print(f"[burned-corpora] ok — {len(seen)} repositories across {len(lits)} corpora, none reused")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
