"""The blind labelling sheet: evidence, and nothing that resembles an answer.

WHAT: Renders each selected PR as the merge, the files it touched, and every commit in
      the following window — sha, date, message, files — for a human to judge.
WHY:  §7's gate is only worth running if the human decides before the machine does. The
      protection is structural rather than procedural: this module does not import
      `scan_outcome` or `fix_signals`, so there is no code path from here to a verdict,
      and `tests/test_handlabel.py` asserts that the imports stay that way.

      Two subtler leaks are also closed. The fix-word regex is NOT shown and commits are
      NOT annotated by it — a labeller shown `fix|bug|broke|regress|hotfix|revert` stops
      judging and starts pattern-matching, which would validate the classifier against
      itself. A test renders one matching and one non-matching commit and requires
      byte-identical structure. Commits appear in plain chronological order, never
      sorted or grouped by anything the classifier derives.

      §3.2's *definition* is shown, deliberately. A labeller who is not told that a
      revert-or-fix is what counts is labelling a different variable, and the comparison
      would measure nothing. The definition is not the leak; per-commit verdicts are.

      An unreadable window renders as a refusal to label rather than as a quiet week —
      see `window.Window`, which exists because the two were once the same empty list.
IMPORTS: phase0.handlabel.select, phase0.handlabel.window.
CONSUMED BY: `just handlabel-sheet`; tests/test_handlabel.py.
"""

from __future__ import annotations

from phase0.handlabel.select import Candidate, Selection
from phase0.handlabel.window import WINDOW_DAYS, Window, WindowCommit

MAX_FILES_SHOWN = 40
MAX_MESSAGE_LINES = 12


def _files_block(candidate: Candidate) -> str:
    shown = "\n".join(f"  - `{name}`" for name in candidate.changed_files[:MAX_FILES_SHOWN])
    hidden = len(candidate.changed_files) - MAX_FILES_SHOWN
    return shown + (f"\n  - …and {hidden} more" if hidden > 0 else "")


def _commit_block(commit: WindowCommit) -> list[str]:
    touched = commit.touched_pr_files
    overlap = ", ".join(f"`{name}`" for name in touched) if touched else "_none of this PR's files_"
    body = "\n".join(f"  > {line}" for line in commit.message.splitlines()[:MAX_MESSAGE_LINES])
    return [
        f"**`{commit.sha[:10]}`** · {commit.when} · {commit.author}",
        "",
        body,
        "",
        f"  Touches: {overlap}",
        "",
    ]


def _render_candidate(index: int, candidate: Candidate, window: Window) -> str:
    lines = [
        f"## {index}. {candidate.repo}#{candidate.number}",
        "",
        f"- **Merged:** {candidate.merged_at}",
        f"- **Title:** {candidate.title}",
        f"- **Python files this PR changed** ({len(candidate.changed_files)}):",
        _files_block(candidate),
        "",
        f"### Commits in the {WINDOW_DAYS} days after this merge",
        "",
    ]
    if not window.is_labellable:
        lines += [
            f"> **HISTORY UNAVAILABLE — DO NOT LABEL THIS PR.** {window.reason}",
            ">",
            "> This is not an empty week. We could not read the repository, so there is",
            "> no evidence here either way. Scoring refuses to run while any PR is in",
            "> this state; re-generate the sheet once the clone succeeds.",
            "",
            "---",
            "",
        ]
        return "\n".join(lines)

    if not window.commits:
        lines += ["_No commits landed in the window._", ""]
    for commit in window.commits:
        lines += _commit_block(commit)

    lines += [
        "**Your label** — did this PR break something, judged from the commits above?",
        "",
        f"    {index}. broke / clean  ->  ",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def render_sheet(selection: Selection, windows: dict[int, Window]) -> str:
    """The whole sheet. Contains no verdict, no scores and no fix-word list.

    A PR with no entry in `windows` is treated as unavailable rather than as quiet — a
    missing key is a bug in the caller, and defaulting it to an empty window would
    reintroduce exactly the conflation `window.Window` exists to prevent.
    """
    unreadable = sum(
        1
        for c in selection.candidates
        if not windows.get(c.pr_id, Window(available=False, reason="not gathered")).is_labellable
    )
    header = [
        "# Hand-labelling sheet — Phase 0 day-2 gate",
        "",
        f"Manifest sha256: `{selection.manifest_sha256}`",
        f"Drawn from {selection.population} eligible PRs at stride {selection.stride}.",
        "",
    ]
    if unreadable:
        header += [
            f"> **{unreadable} of {len(selection.candidates)} PRs have unreadable history.**",
            "> Do not label those, and do not score this sheet — the gate is invalid",
            "> until every window is readable.",
            "",
        ]
    header += [
        "For each PR below, read the commits that landed in the seven days after it",
        "merged and decide: **did this PR break something?** Judge as a reviewer would —",
        "a later commit that repairs behaviour this PR introduced, or reverts it, counts",
        "as broke. Unrelated work in the same files does not.",
        "",
        "Record `broke` or `clean` for all twenty in `handlabel_answers.txt`, one per",
        "line as `<index>: <label>`. Scoring refuses to run until all twenty are filled.",
        "",
        "**Do not run the classifier before finishing.** The gate measures whether the",
        "machine agrees with an independent human judgement; reading its output first",
        "replaces that with a memory test and the result is worth nothing.",
        "",
        "---",
        "",
    ]
    body = [
        _render_candidate(
            i,
            candidate,
            windows.get(candidate.pr_id, Window(available=False, reason="not gathered")),
        )
        for i, candidate in enumerate(selection.candidates, start=1)
    ]
    return "\n".join(header) + "".join(body)
