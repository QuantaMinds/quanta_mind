"""Generate the blind hand-labelling sheet for `PHASE0_PREREGISTRATION.md` “Timeline” day-2 gate.

WHAT: Draws the sample, clones each repository once, walks the seven-day window after
      every selected merge, and writes `results/handlabel_sheet.md` plus a blank
      answers file.
WHY:  Kept as a script rather than a pipeline stage because it runs once, by hand, and
      its output is read by a person. It imports only `select` and `sheet` — never
      `scan_outcome` — so running it cannot produce a verdict to be influenced by.

      Repositories are cloned once and reused across their PRs; the draw puts 20 PRs in
      13 repositories, so this matters.
IMPORTS: phase0.handlabel.select, phase0.handlabel.sheet, phase0.pipeline.worktree.
CONSUMED BY: `just handlabel-sheet`.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from phase0.handlabel.select import Candidate, Selection, select_prs
from phase0.handlabel.sheet import render_sheet
from phase0.handlabel.window import Window, unavailable, window_commits
from phase0.pipeline.worktree import CloneFailed, cloned

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "AIDev_BC_Analyser.zip"
RESULTS = ROOT / "results"
WORKSPACE = ROOT / "data" / "handlabel_clones"


def _gather(selection: Selection) -> dict[int, Window]:
    """One clone per repository, every PR in it walked before moving on."""
    by_repo: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in selection.candidates:
        by_repo[candidate.repo].append(candidate)

    windows: dict[int, Window] = {}
    for position, (repo, candidates) in enumerate(sorted(by_repo.items()), start=1):
        print(f"[{position}/{len(by_repo)}] cloning {repo} …", flush=True)
        try:
            with cloned(repo, WORKSPACE) as path:
                for candidate in candidates:
                    window = window_commits(path, candidate)
                    windows[candidate.pr_id] = window
                    print(
                        f"    #{candidate.number}: {len(window.commits)} commits in window",
                        flush=True,
                    )
        except CloneFailed as exc:
            # Typed, never an empty window: an unreadable repository and a quiet week
            # must not be the same value. The renderer refuses to offer these for
            # labelling and main() exits non-zero.
            print(f"    CLONE FAILED: {exc}", flush=True)
            for candidate in candidates:
                windows[candidate.pr_id] = unavailable(str(exc))
    return windows


def main() -> int:
    if not PACKAGE.is_file():
        print(f"{PACKAGE} not found — see ENVIRONMENT.lock for the figshare URL.")
        return 1

    RESULTS.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    selection = select_prs(PACKAGE)
    print(
        f"drew {len(selection.candidates)} of {selection.population} eligible "
        f"at stride {selection.stride}; manifest {selection.manifest_sha256}",
        flush=True,
    )

    windows = _gather(selection)
    sheet_path = RESULTS / "handlabel_sheet.md"
    sheet_path.write_text(render_sheet(selection, windows), encoding="utf-8")

    unreadable = [c for c in selection.candidates if not windows[c.pr_id].is_labellable]
    if unreadable:
        # Exit non-zero. A sheet built from unreadable history renders twenty quiet
        # weeks, a labeller marks twenty clean, the classifier returns CLEAN on
        # unreadable history too, and the gate reports 20/20 on no data at all.
        print(
            f"\nFAILED: {len(unreadable)} of {len(selection.candidates)} PRs have "
            f"unreadable history. The sheet was written but MUST NOT be labelled.",
            flush=True,
        )
        for candidate in unreadable:
            print(f"  {candidate.repo}#{candidate.number}: {windows[candidate.pr_id].reason[:110]}")
        return 1

    answers = RESULTS / "handlabel_answers.txt"
    if not answers.is_file():
        answers.write_text(
            "# One line per PR: `<index>: broke` or `<index>: clean`.\n"
            "# All twenty must be filled before scoring will run.\n"
            f"# Sheet manifest: {selection.manifest_sha256}\n\n"
            + "".join(f"{i}: \n" for i in range(1, len(selection.candidates) + 1)),
            encoding="utf-8",
        )
        print(f"blank answers file written to {answers}", flush=True)
    else:
        print(f"{answers} already exists — left untouched", flush=True)

    print(f"\nsheet written to {sheet_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
