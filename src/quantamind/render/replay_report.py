"""Print a retrospective so it cannot be quoted as the validated result.

WHAT: `report(outcomes)` renders one block per repository plus a pooled block, each headed by
      which corpus it is and what that does and does not establish.
WHY:  The two numbers have the same units and the same shape. `rank/` reproduces
      `defect_return_external.json` event for event on the six pinned repositories -- 2,400
      events, gate 2b -- and that reproduction carries the p-value. **A retrospective run is not
      that**: it is the same code on a repository nobody has measured, unreplicated, chosen by the
      person the output will be shown to.

      They will be pasted into the same slide the first time someone finds them useful, so the
      distinction lives HERE, above the numbers, and not in anyone's head.

      **NO ARITHMETIC ACROSS THE TWO.** No "compared with", no ratio, no "in line with". A run on
      one repository can neither confirm nor refute the published figure, and a reader holding
      both in one paragraph will assume it does.

      **NOR IS A COLLECTION OF THESE EVIDENCE.** A prospect who dislikes their number does not
      send it back, so an accumulated set skews favourable. Aggregating requires pre-committing to
      report every run including the bad ones -- stated in `docs/plans/feat-retrospective.md`.

      **THE HEADLINE IS THE INFORMATIVE STRATUM.** Events touching three or fewer files are read
      entirely by a budget of three, so no arm can miss; they are printed as decided-by-
      construction rather than folded into an average that flatters everyone.
IMPORTS: types.replay_outcome. Nothing to its right.
CONSUMED BY: serve/cli.py.
"""

from __future__ import annotations

from collections.abc import Sequence

from quantamind.types.replay_outcome import Outcome, Stratum

# What gate 2b re-proves, quoted as a separate measurement and never combined with a run below.
PUBLISHED = (
    "Measured ELSEWHERE: on six repositories the method never saw, top-three-by-fix-history "
    "missed 1.21% of the changes a later fix returned to, against an alphabetical control's "
    "3.12% (n = 2,400, McNemar p < 1e-6, 6 of 6 positive). `just gate-2b` re-proves that this "
    "code reproduces it event for event."
)
PROVENANCE = (
    "THIS IS NOT THAT NUMBER. Below is a first measurement of one repository, unreplicated, on "
    "history chosen by whoever ran it. It cannot confirm or refute the figure above, and the two "
    "must not be combined, averaged or compared."
)


def _row(stratum: Stratum) -> str:
    return (
        f"  {stratum.label:16s} n={stratum.events:6d}   "
        f"ranker {stratum.miss:6.2f}%   alphabetical {stratum.alpha_miss:6.2f}%   "
        f"chance {stratum.chance_miss:6.2f}%   ranker vs chance {stratum.lift:+6.2f}"
    )


def _block(outcome: Outcome) -> list[str]:
    lines = [f"{outcome.repo}", "-" * len(outcome.repo)]

    refusal = outcome.inconclusive()
    if refusal:
        lines.append(f"  INCONCLUSIVE — {refusal}.")
        lines.append(
            "  The pre-registered floors are not a formality: below them an impressive-looking "
            "number is most likely noise. Events run 22-57% of commits on the corpora we have "
            "measured, so roughly 900-2,500 commits of history reaches the floor."
        )

    lines.append(_row(outcome.whole))
    lines.append(_row(outcome.informative))
    lines.append(_row(outcome.degenerate))
    lines.append(
        f"  {outcome.degenerate_share:.1f}% of events touch <=3 files, which a budget of three "
        f"reads entirely — no ordering could have missed them, so they decide nothing and the "
        f"headline belongs to the row above them."
    )
    if outcome.degenerate.events and not outcome.degenerate.decides_nothing:
        lines.append(
            "  WARNING: the degenerate stratum did NOT score identically across arms. That is "
            "arithmetically impossible when the budget covers the change, so the budget, the "
            "stratum boundary or the target set disagree. Do not quote this run."
        )

    lines.append(
        f"  discordant pairs: ranker {outcome.b}, control {outcome.c}; "
        f"exact McNemar p = {outcome.p_value():.5f}"
    )
    lines.append(
        f"  alphabetical vs chance {outcome.whole.alpha_lift:+.2f} — near zero means the control "
        f"was genuinely uninformative here; well above it means layout made it a poor one."
    )
    if outcome.rejected:
        named = ", ".join(f"{k}: {v}" for k, v in sorted(outcome.rejected.items()))
        lines.append(f"  not admitted by the event definition — {named}")
    return lines


def report(outcomes: Sequence[Outcome]) -> str:
    """The whole retrospective, provenance first.

    Raises on an empty sequence rather than printing a header over nothing: a report with no
    repository in it reads exactly like a repository with no events.
    """
    if not outcomes:
        raise ValueError("no repositories to report on; a retrospective over nothing is not one")

    lines = ["", PUBLISHED, "", PROVENANCE, ""]
    for outcome in outcomes:
        lines.extend(_block(outcome))
        lines.append("")
    return "\n".join(lines)
