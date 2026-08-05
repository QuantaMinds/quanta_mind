"""Which decision rules would survive being deleted?

WHAT: Breaks one load-bearing rule at a time, runs the suite, and records whether anything
      failed. Restores the file whatever happens.
WHY:  `by_subject` -- the rule A28 rests on, and the reason `parent_commit` failure fell
      from 15.6% to about 1% -- had no test. Disabling it outright left 232 tests passing.
      It was found by accident, while correcting a docstring that named a test file which
      did not exist.

      Coverage percentages would not have caught it: the module was IMPORTED and its lines
      RUN, through `resolve()`, on inputs that made it return on its first line. Executed
      is not asserted. The only question that separates the two is the one rule 14 asks --
      what does the suite output when the thing it checks is broken? -- and the only way
      to answer it is to break the thing.

      Targets are the rules that decide something: what counts as breakage, which branch
      is walked, how a verdict is coded, what the thresholds are. A rule here that
      survives sabotage is a rule the study is trusting on inspection alone.

      `pytest -x` stops at the first failure, so a protected rule is cheap to confirm and
      only an unprotected one costs a full run.
IMPORTS: stdlib subprocess/pathlib. Nothing from phase0 -- it edits phase0's source.
CONSUMED BY: run by hand; prints a table and exits non-zero if any rule survives.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SRC = Path("E:/Code/quanta_mind/research/phase0/src/phase0")
PYTHON = "E:/Code/quanta_mind/research/phase0/.venv/Scripts/python.exe"

# (label, file, original fragment, degenerate replacement). Each replacement makes the
# rule answer the same thing always -- which is exactly what a rule that is never
# exercised would do without anyone noticing.
TARGETS: tuple[tuple[str, str, str, str], ...] = (
    (
        "signals.mentions_breakage -> always False",
        "outcome/signals.py",
        "def mentions_breakage(message: str) -> bool:",
        "def mentions_breakage(message: str) -> bool:\n    return False  # SABOTAGE",
    ),
    (
        "signals.reverts -> always False",
        "outcome/signals.py",
        "def reverts(message: str, target_sha: str) -> bool:",
        "def reverts(message: str, target_sha: str) -> bool:\n    return False  # SABOTAGE",
    ),
    (
        "window.base_ref_of -> always HEAD (the original defect)",
        "outcome/window.py",
        '    if not base_ref:\n        return "HEAD"',
        '    if True:\n        return "HEAD"  # SABOTAGE',
    ),
    (
        "window.reachable -> always True",
        "outcome/window.py",
        "def reachable(repo: Repo, sha: str, ref: str) -> bool:",
        "def reachable(repo: Repo, sha: str, ref: str) -> bool:\n    return True  # SABOTAGE",
    ),
    (
        "conclusion.table_coding -> UNSCANNABLE counts as clean",
        "outcome/conclusion.py",
        "        case Outcome.UNSCANNABLE:\n            return None",
        "        case Outcome.UNSCANNABLE:\n            return 0  # SABOTAGE",
    ),
    (
        "verify_files -> never rejects",
        "pipeline/verify_files.py",
        "def verify_files(",
        "def _disabled_verify_files(",
    ),
)


def _read(path: Path) -> str:
    """Read preserving line endings. `Path.read_text(newline=...)` needs 3.13; PyCG pins
    this project to 3.10, so the keyword exists in the docs and not in the interpreter."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: Path, text: str) -> None:
    """Write without touching line endings."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _run_suite() -> tuple[bool, str]:
    out = subprocess.run(
        [PYTHON, "-m", "pytest", "tests", "-x", "-q"],
        cwd=SRC.parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
        check=False,
    )
    tail = [line for line in out.stdout.splitlines() if line.strip()][-1:]
    return out.returncode != 0, (tail[0] if tail else "")


def probe(label: str, relative: str, old: str, new: str) -> dict[str, object]:
    path = SRC / relative
    # newline="" preserves CRLF exactly. `read_text`/`write_text` normalise to LF, so a
    # faithful restore still showed as modified -- and an assertion that cries wolf on
    # every clean run is one nobody reads, which is how the 1.6 GB cleanup bug survived.
    original = _read(path)
    # Patterns are written with \n; the files are CRLF. Reading faithfully (which the
    # restore requires) means a multi-line pattern stops matching, and the run before this
    # one reported `base_ref_of` as NOT PROBED for exactly that reason -- correctly, which
    # is the point of having the third label at all. Translate the pattern to the file's
    # own ending rather than normalising the file and writing back a changed one.
    if "\r\n" in original:
        old = old.replace("\n", "\r\n")
        new = new.replace("\n", "\r\n")
    if old not in original:
        # THREE states, not two. On the first run this returned caught=None and the
        # caller printed `"caught" if row.get("caught") else "SURVIVED"` -- and None is
        # falsy, so a rule that was never probed was reported as a rule that survived
        # sabotage. "We could not check" rendered as "we checked and it is unprotected",
        # inside the tool built to find that exact substitution. The signature had gained
        # a renamed parameter and the pattern silently stopped matching.
        return {"rule": label, "caught": None, "detail": f"pattern not found: {old[:60]}"}
    try:
        _write(path, original.replace(old, new, 1))
        caught, detail = _run_suite()
    finally:
        _write(path, original)
    return {"rule": label, "caught": caught, "detail": detail}


def main() -> int:
    results = []
    for label, relative, old, new in TARGETS:
        row = probe(label, relative, old, new)
        results.append(row)
        # Three labels for three states. Collapsing NOT-PROBED into SURVIVED is what this
        # tool exists to catch, and it did it to itself on the first run.
        mark = {True: "caught", False: "SURVIVED", None: "NOT PROBED"}[row.get("caught")]
        print(f"  {mark:<11}{label}", flush=True)

    survived = [r for r in results if r.get("caught") is False]
    unknown = [r for r in results if r.get("caught") is None]
    print(f"\n{len(results) - len(survived) - len(unknown)}/{len(results)} rules protected")
    for row in survived:
        print(f"  UNPROTECTED: {row['rule']}")
    for row in unknown:
        print(f"  NOT PROBED, so UNKNOWN: {row['rule']} -- {row.get('detail')}")

    # The tree must be exactly as it was found. This edits tracked source, and an
    # in-process `finally` does not survive a kill -- which has happened to several long
    # jobs in this session. A left-behind `return False` in the rule that decides what
    # counts as breakage is worse than never running the probe.
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "src/"],
        cwd=SRC.parents[1],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    ).stdout.strip()
    if dirty:
        print(f"\nSOURCE NOT RESTORED -- run `git checkout -- src/`:\n{dirty}")
        return 1
    print("\nsource restored clean")
    return 1 if survived or unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
