"""Every changed file, what changed in it, and what was found there.

WHAT: `table(paths, funded, effort, verdicts, findings)` renders the file breakdown: a markdown
      table of the files worth a glance, and the quiet remainder behind a fold.
WHY:  **THIS IS THE ONE THING BOTH COMPETITORS DO THAT WE DID NOT, AND THEY ARE RIGHT.** Greptile
      posts "Files Changed & Issues" — what changed and what was found, per file, in the open — and
      Qodo posts a file-level change overview. A reviewer opening a pull request with eighty
      changed files is orienting, and a list of bare paths does not help them do it.
      → `docs/product/comment-golden-rules.md`

      **THE QUIET FILES FOLD AND THE LOUD ONES DO NOT.** Working memory holds about four items and
      review performance decays past roughly four hundred lines, so an eighty-row table in the open
      would be the wall it was meant to replace. A file is in the open when something was found in
      it or it was read closely; everything else is one click away, counted, never dropped.

      **NO SCORE, NO SEVERITY, NO CONFIDENCE.** Greptile publishes 0-5 per file and per comment. We
      measured ours — findings are 25.0% correct and a same-family judge agreed with a careful
      rater on 34.9% — so a number from us would be one we have disproven our ability to
      produce. The `found` column carries what actually happened instead: a violation of a rule
      the customer wrote, a claim to check, or a count of their rules that passed. Every one of
      those is re-runnable by them.

      **AND NO COLUMN COMES FROM `rank/`.** Lines changed and the declaration are the diff's, which
      GitHub already prints; rule outcomes are the customer's own. *What the ranking is built from*
      is first on the never-publish list, and "read closely" is the only trace of it here.
IMPORTS: parse.change_effort, types.{checked,finding}. Leftward only.
CONSUMED BY: `render/blocks/scope_block.py`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from quantamind.parse.change_effort import Effort
from quantamind.types.finding import Finding
from quantamind.types.standards.checked import Checked, Outcome

HEAD = "| file | changed | where | found |"
RULE = "|---|---|---|---|"
QUIET = "<details><summary>{count} more file(s), nothing found</summary>"
QUIET_DIR = "- `{directory}` — {names}"
ROOT = "(root)"
READ = " ⟵ read closely"
DASH = "—"
WHERE_CAP = 44
"""Characters of the declaration in the `where` cell.

A column that wraps is a table nobody reads."""


def _cell(text: str) -> str:
    """Text safe to put in a markdown table cell.

    **A PIPE IN A CELL SILENTLY CORRUPTS THE WHOLE TABLE**, and the very first example rendered
    carried one: `def units_in(diff: str, scope: Collection[str] | None = None) -> Parsed:` is a
    real declaration from this repository, and a union type is ordinary Python. GitHub does not
    warn — it splits the row and the reader sees a mangled line with no idea why.
    """
    return text.replace("|", "\\|")


def _where(size: Effort | None) -> str:
    """The first declaration, escaped and capped, or a dash.

    **ONE DECLARATION, NOT ALL OF THEM.** A cell holding six is a cell nobody reads; the column
    exists to give a starting line rather than an inventory. Truncation is marked, because a
    signature cut in silence reads as a signature that short.
    """
    if size is None or not size.functions:
        return DASH
    name = size.functions[0].strip()
    if len(name) > WHERE_CAP:
        name = name[:WHERE_CAP].rstrip() + "…"
    return f"`{_cell(name)}`"


def _found(path: str, verdicts: Mapping[str, str], claims: Mapping[str, int]) -> str:
    """What happened in this file. **A rule the customer wrote outranks a claim of ours.**

    Their rule is exact and re-runnable; our finding is 25.0% correct. When both landed on one
    file the violation is what they should read first, and the ordering says so without a
    sentence explaining our machinery to somebody who did not ask.
    """
    said = verdicts.get(path, "")
    claimed = claims.get(path, 0)
    thing = "thing" if claimed == 1 else "things"
    if claimed and "violated" in said:
        return f"{said}, {claimed} {thing} to check"
    if claimed:
        return f"**{claimed} {thing} to check**"
    return said or DASH


def _row(
    path: str,
    read: bool,
    effort: Mapping[str, Effort],
    verdicts: Mapping[str, str],
    claims: Mapping[str, int],
) -> str:
    size = effort.get(path)
    changed = f"{size.lines} lines" if size is not None else DASH
    name = f"`{_cell(path)}`{READ if read else ''}"
    return f"| {name} | {changed} | {_where(size)} | {_found(path, verdicts, claims)} |"


def table(
    paths: Sequence[str],
    funded: frozenset[str],
    effort: Mapping[str, Effort],
    verdicts: Mapping[str, str],
    findings: Sequence[Finding] = (),
    checks: Sequence[Checked] = (),
) -> list[str]:
    """The table, then the fold. Empty list when there is nothing changed to describe."""
    if not paths:
        return []

    claims: dict[str, int] = {}
    for finding in findings:
        claims[finding.path] = claims.get(finding.path, 0) + 1
    for check in checks:
        if check.outcome is Outcome.VIOLATED:
            claims.setdefault(check.site.path, 0)

    loud = [p for p in paths if p in funded or p in claims or "violated" in verdicts.get(p, "")]
    quiet = [p for p in paths if p not in loud]

    # **A TABLE OF DASHES IS FURNITURE.** The CLI renders a ranking with no diff parsed and no
    # rules run, so every cell would be an em dash and the columns would carry nothing. A live run
    # against `pallets/flask#6133` printed exactly that. The paths are still all listed.
    if not any(_row(p, False, effort, verdicts, claims).count(DASH) < 3 for p in paths):
        return ["", *[f"- `{_cell(path)}`{READ if path in funded else ''}" for path in paths]]

    out = ["", HEAD, RULE]
    out += [_row(p, p in funded, effort, verdicts, claims) for p in loud]
    if quiet:
        out += ["", QUIET.format(count=len(quiet)), "", *_grouped(quiet), "", "</details>"]
    return out


def _grouped(paths: Sequence[str]) -> list[str]:
    """The quiet files, by directory, names only.

    **EIGHTY-SEVEN TABLE ROWS IS THE WALL THE TABLE WAS BUILT TO REPLACE.** The first version
    repeated all four columns inside the fold, and on a real ninety-file pull request that was
    eighty-seven near-identical lines reading "4 rules passed". Working memory holds about four
    items; the golden rules call this out as *four things, not forty*.

    **THE COLUMNS CARRY NOTHING HERE BY DEFINITION.** A file is in this group because nothing was
    found in it, so `found` is the same for all of them and `where` is a location in code nobody
    is being sent to. What a reader wants from this list is *is my file in it*, and a name under
    its directory answers that in a fifth of the lines.

    **EVERY PATH IS STILL PRESENT.** Grouping is not truncation: no file is dropped, no count is
    rounded, and a reader can still find any name they are looking for.
    """
    by_directory: dict[str, list[str]] = {}
    for path in paths:
        directory, _, name = path.rpartition("/")
        by_directory.setdefault(directory or ROOT, []).append(name)
    return [
        QUIET_DIR.format(directory=directory, names=", ".join(f"`{n}`" for n in sorted(names)))
        for directory, names in sorted(by_directory.items())
    ]
