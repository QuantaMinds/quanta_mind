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

      **AND THE PAIRWISE CHECK ONLY READ ONE FILE, WHICH IS HOW NINE BURNED REPOSITORIES SAT IN A
      CORPUS LIST AND THIS GUARD PRINTED `ok`.** `research/phase0/bench/forensic/execution_corpus.
      py` names its pool `CANDIDATES`, not `REPOS`, and lives elsewhere — so `aio-libs/aiohttp`,
      `encode/httpx`, `pydantic/pydantic` and six more were queued for a fresh corpus having
      already been measured. The guard existed for exactly that and could not see it, because it
      was pointed at the file the last mistake happened in. `pools()` now reads every corpus-shaped
      literal under `research/`, which is the population the rule was always about.
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


POOL = re.compile(r"^(CANDIDATES|REPOS|CORPUS|POOL)\w*\s*[:=]", re.M)


def pools(root: pathlib.Path) -> dict[str, list[str]]:
    """{file::literal: [repositories]} for every corpus-shaped list anywhere under `research/`.

    **A CORPUS IS A CORPUS WHATEVER ITS VARIABLE IS CALLED.** Matching only `REPOS` in one file
    let `CANDIDATES` in another hold nine already-measured repositories.
    """
    found: dict[str, list[str]] = {}
    research = root / "research"
    for path in sorted(research.rglob("*.py")) if research.is_dir() else []:
        if path.resolve() == (root / CORPUS).resolve():
            continue
        text = path.read_text(errors="ignore")
        for match in POOL.finditer(text):
            try:
                end = text.index(")", match.end())
            except ValueError:
                continue
            names = REPO.findall(text[match.end() : end])
            if names:
                found[f"{path.relative_to(root)}::{match.group(1)}"] = names
    return found


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
    # Every corpus-shaped literal ANYWHERE under research/, against the ones already spent.
    for where, names in pools(root).items():
        for name in names:
            if name in seen:
                bad.append(f"  {name}: already in {seen[name]}, and queued again by {where}")
    if bad:
        print(f"[burned-corpora] {len(bad)} repository reused across corpora:")
        print("\n".join(bad))
        print("  A repository measured twice is a design tuned on its own test set.")
        return 1
    print(
        f"[burned-corpora] ok — {len(seen)} repositories across {len(lits)} corpora "
        f"and {len(pools(root))} other pool(s), none reused"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
