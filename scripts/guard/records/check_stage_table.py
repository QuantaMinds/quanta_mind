"""The plan's prose about what is built must agree with what is on disk.

WHAT: Cross-checks three places `docs/plans/implementation.md` records progress -- the summary
      table, each `# Stage —` heading's status, and the numbered steps -- against `src/quantamind/`
      and against each other. Four sound rules, none of which decides whether work is FINISHED:
      a claim of absence about a module that exists, a `DONE` step naming a module that does not,
      a stage called not-begun whose every named artefact is present, and a stage naming no
      artefact at all.
WHY:  **Its sibling `check_plan_state.py` says in its own docstring that it "cannot check that a
      stage's prose is honest".** That was true, and the prose then drifted in four rows while the
      machine-checked block twelve lines below it stayed correct. The summary table claimed
      `ingest/diff.py` and `parse/` "not begun" and `rank/order.py` "still to come" when all three
      were built, and marked render and the retrospective "not begun" when both were shipping. A
      resuming reader acts on that table first.

      **THE GUARD REFUSES TO JUDGE COMPLETION, AND THAT IS WHAT MAKES IT SOUND.** Whether a stage
      is DONE depends on its gate, which is prose about evidence and not mechanisable. Every rule
      here is one-directional: it fires only on a contradiction between a claim and the filesystem.
      A guard that guessed at DONE would produce false failures, and a guard people override is one
      they delete.

      **A stage that names no module is a violation, not a skip.** Two stages were written as
      future plans whose steps named no file -- "Walk closed pull requests, rank each against
      history" -- so nothing about them could ever be checked and their rows sat at "not begun"
      through the entire build. Silently passing an unverifiable stage is the unreachable-check
      defect: the output is identical whether the stage is honest or three months stale.
IMPORTS: scripts/guard/{discovery,plan_claims}.py; stdlib re. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discovery import Violation, project_root, report
from plan_claims import PACKAGE, normalise, referenced, sentences, steps

PLAN = Path("docs/plans/implementation.md")
# The summary table is identified by its header row, not by its shape. See main().
HEADER = "| stage | status | evidence |"

# Explicit only. "Nothing is wired to the work callback" is a true statement about behaviour, not a
# claim that a file is missing, and a looser pattern read it as one.
ABSENT = re.compile(r"not begun|not built|not yet built|not started|still to come", re.I)
STATUSES = ("DONE", "STARTED", "NOT BEGUN", "NOT SCHEDULED")
STAGE = re.compile(r"^# Stage — (.+?)\s*(?:·\s*(.+))?$")
# The one summary row with no stage section: the layers closed on evidence.
RESERVE = "held in reserve"


def _check_claims(root: Path, plan: Path, number: int, text: str, where: str) -> list[Violation]:
    """Rules 1 and 2: an absence claim about a present module, a DONE claim about a missing one."""
    out: list[Violation] = []
    for sentence in sentences(text):
        denied = ABSENT.search(sentence)
        done = "**DONE" in sentence or "**NOT BUILT" in sentence
        for name, present in referenced(root, sentence):
            if denied and present:
                out.append(
                    Violation(
                        plan,
                        number,
                        "stage-table",
                        f"{where} says {name} is {denied.group(0)!r}, and it exists on disk. A "
                        f"resuming reader acts on this table before anything else in the file.",
                    )
                )
            elif done and not denied and not present and "NOT BUILT" not in sentence:
                out.append(
                    Violation(
                        plan,
                        number,
                        "stage-table",
                        f"{where} marks {name} DONE and there is no such file under "
                        f"{PACKAGE}/. Either it was never written, or it was renamed "
                        f"without git mv.",
                    )
                )
    return out


def main() -> int:
    root = project_root()
    plan = root / PLAN
    if not plan.is_file():
        print(f"[stage-table] {PLAN} not found")
        return 1
    text = plan.read_text(encoding="utf-8")
    lines = text.splitlines()
    violations: list[Violation] = []

    # --- the summary table ------------------------------------------------------------------
    # **SCOPED TO ONE TABLE, BY ITS HEADER.** The document holds other three-column tables -- gate
    # results, ordering identity -- and a shape-based scan condemned five of their rows for not
    # carrying a stage status. A guard whose first run produces mostly false positives gets an
    # exemption list bolted on, and the exemption list is what rots.
    try:
        header = lines.index(HEADER)
    except ValueError:
        print(f"[stage-table] {HEADER!r} not found in {PLAN}; the summary table cannot be checked")
        return 1
    rows: dict[str, tuple[int, str]] = {}
    for offset, line in enumerate(lines[header + 2 :]):
        if not line.startswith("|"):
            break
        number = header + 3 + offset
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        name, status, evidence = cells
        if RESERVE in normalise(name):
            continue
        rows[normalise(name)] = (number, status)
        violations += _check_claims(root, plan, number, evidence, f"the summary row for {name!r}")
        if not any(word in status.upper() for word in STATUSES):
            violations.append(
                Violation(
                    plan,
                    number,
                    "stage-table",
                    f"status {status!r} is not one of {STATUSES}. 'NEXT' is a schedule, not "
                    f"a state; what is next belongs under 'The exact next action'.",
                )
            )

    # --- the stage sections -----------------------------------------------------------------
    starts = [(n, m) for n, line in enumerate(lines, 1) if (m := STAGE.match(line))]
    for index, (number, match) in enumerate(starts):
        name, declared = normalise(match.group(1)), (match.group(2) or "").strip()
        stop = starts[index + 1][0] - 1 if index + 1 < len(starts) else len(lines)
        body = "\n".join(lines[number:stop])
        entries = steps(body)
        named = [ref for step in entries for ref in referenced(root, step)]

        if name not in rows:
            violations.append(
                Violation(
                    plan,
                    number,
                    "stage-table",
                    f"stage {name!r} has no row in the summary table, so the table a reader "
                    f"consults first cannot mention it at all.",
                )
            )
        elif declared and normalise(declared) != normalise(rows[name][1]):
            violations.append(
                Violation(
                    plan,
                    number,
                    "stage-table",
                    f"the heading says {declared!r} and the summary row says "
                    f"{rows[name][1]!r}. Two places recording one state is one place too many "
                    f"unless something checks they agree.",
                )
            )
        # Rule 4: unverifiable. A stage naming no file passes this guard forever.
        if not named:
            violations.append(
                Violation(
                    plan,
                    number,
                    "stage-table",
                    f"stage {name!r} names no module in its steps, so NOTHING about it can "
                    f"be checked against the filesystem. Name the files the steps produce. "
                    f"Two stages sat at 'not begun' through their entire build this way.",
                )
            )
        # Rule 3: called not-begun while every artefact it names is present.
        elif name in rows and "NOT BEGUN" in rows[name][1].upper() and all(p for _, p in named):
            violations.append(
                Violation(
                    plan,
                    rows[name][0],
                    "stage-table",
                    f"stage {name!r} is marked not begun, and every module its steps name "
                    f"exists: {', '.join(n for n, _ in named)}.",
                )
            )
        for step_number, step in enumerate(entries, 1):
            violations += _check_claims(
                root, plan, number, step, f"stage {name!r} step {step_number}"
            )

    print(f"[stage-table] {len(rows)} summary row(s), {len(starts)} stage section(s)", flush=True)
    return report(violations, root, "stage-table")


if __name__ == "__main__":
    sys.exit(main())
