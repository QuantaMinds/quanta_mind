"""What we read closely, what we did not, and every changed file behind a fold.

WHAT: `coverage(ranking, unresolved)` renders the comment's last block: the scope line and a
      `<details>` list of every changed file.
WHY:  **"3 OF 56 FILE(S) REVIEWED; 53 NOT REVIEWED" READ AS A FAILURE, AND IT IS THE PRODUCT
      WORKING.** A developer waiting to merge saw a large number beside the words "not reviewed"
      and had no way to tell a deliberate budget from a crash. Reported by the person who ships
      this, reading a real comment.

      **THE COUNT IS NOT SOFTENED AND NOTHING IS HIDDEN.** `AGENTS.md` calls the residual the
      product, and a scope line that shrank to spare feelings would be the one dishonest sentence
      in the whole comment. What changed is that a deliberate scope now reads as one, and the
      files it did not read closely are one click away instead of absent.

      **THE LIST CARRIES PATHS AND NOTHING ELSE, AND IT IS ALPHABETICAL. THAT IS A PUBLISHING RULE,
      NOT A LAYOUT CHOICE.** `docs/product/publishing-rules.md` never-publishes *what the ranking
      is built from* and *how the budget is split across a change*. A per-file fix count is the
      first — it was in this comment once and was removed for a different reason — and printing
      the list in RANK order is the second, because a reader could count down to the cut and read
      the budget straight off it. Alphabetical shows a developer every file we saw and hands a
      competitor nothing.

      **AND THE SENTENCE SAYS NOTHING ABOUT HOW THE THREE WERE CHOSEN, WHICH GOES FURTHER THAN THE
      RULES REQUIRE.** *"Your repository's own history"* is phrasing `publishing-rules.md` permits,
      and it was used here until somebody read a real comment and pointed out that it is still OUR
      METHOD in a message that should be about THEIR code. A developer opening a pull request wants
      to know what happened to their change, not how we decide. The words "ranked", "history" and
      "budget" appear nowhere a customer can see them.

      **TESTS ARE GROUPED, NEVER DROPPED, AND THAT WAS RESEARCHED BEFORE IT WAS DECIDED.** The ask
      was to hide them so a developer stops wading through forty test paths. Two things argued
      against it. GitHub's own answer to the same problem is COLLAPSE — even `linguist-generated`
      files stay in the list and only their diff folds — and the review literature is explicit that
      spotting inadequate testing is one of the few things human review is reliably good at, which
      needs the tests visible. A list that silently omitted forty files would also be the
      "truncation reads as covered everything" failure this product exists to refuse. So they are
      under their own heading with their own count: skippable by eye, absent from nothing.

      **`<details>` IS MARKDOWN GITHUB RENDERS AND NEEDS NO SCRIPT.** A link would point at a page
      the reader is not signed in to; a button needs a surface we do not serve on their pull
      request. `dependencies = []` holds either way.
IMPORTS: parse.{change_effort,suite_reach}, types.{checked,ranking,verdict}. Leftward only.
CONSUMED BY: `render/comment.py`, as the last block.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from quantamind.parse.change_effort import Effort
from quantamind.parse.suite_reach import is_test
from quantamind.types.checked import Checked, Outcome
from quantamind.types.ranking import Ranking
from quantamind.types.verdict import Unresolved

SCOPE = "_This change touches **{total}** file(s){checked}. **{read}** were read line by line._"
ALL_CHECKED = ", and every one was checked against the rules you declared"
SOME_CHECKED = ", and **{decided}** were checked against the rules you declared"
NOTHING = "_Nothing to review._"
ALL_FILES = "<details><summary>All {total} changed file(s)</summary>"
SOURCE_HEADING = "**Source — {count}**"
TEST_HEADING = "**Tests — {count}**"
READ = " — read closely"


@dataclass(frozen=True, slots=True)
class Verdicts:
    """What the declared rules said about one file. Counts, never a score."""

    passed: int = 0
    violated: int = 0
    unchecked: int = 0

    @property
    def decided(self) -> bool:
        return bool(self.passed or self.violated)

    def render(self) -> str:
        """**NO CONFIDENCE, NO SEVERITY, NO PRIORITY — COUNTS OF THE CUSTOMER'S OWN RULES.**

        A per-file "importance" or "confidence" was asked for and is refused, and the refusal is
        `render/comment.py`'s own rule: *no severity we cannot calibrate, no confidence we have not
        measured*. We have measured neither. Any label we invented would be the ranking wearing a
        friendlier word, and `publishing-rules.md` never-publishes the ranking besides.

        What is true and reassuring is what actually ran. A rule the customer wrote, checked and
        passed on this file, is a fact they can re-run themselves.
        """
        if self.violated:
            return f"**{self.violated} rule violated**"
        if self.passed:
            return f"{self.passed} rule{'' if self.passed == 1 else 's'} passed"
        if self.unchecked:
            return "no rule could be checked here"
        return ""


def _by_path(checks: Sequence[Checked]) -> dict[str, Verdicts]:
    """One `Verdicts` per file. `DEFERRED` counts as neither: a model was going to decide it."""
    out: dict[str, Verdicts] = {}
    for check in checks:
        now = out.get(check.site.path, Verdicts())
        if check.outcome is Outcome.PASSED:
            now = replace(now, passed=now.passed + 1)
        elif check.outcome is Outcome.VIOLATED:
            now = replace(now, violated=now.violated + 1)
        elif check.outcome is Outcome.UNCHECKABLE:
            now = replace(now, unchecked=now.unchecked + 1)
        out[check.site.path] = now
    return out


def _line(
    path: str, read: bool, effort: Mapping[str, Effort], verdicts: Mapping[str, Verdicts]
) -> str:
    """One file: where it is, how much of it moved, which functions, and what the rules said.

    **THE SIZE IS ABSENT WHEN WE DO NOT HAVE IT, RATHER THAN PRINTED AS ZERO.** A pure rename, a
    mode change and a binary all reach here with no parsed hunk, and "0 lines" beside a file that
    certainly changed is a wrong statement where saying nothing is merely a quiet one.
    """
    parts = []
    size = effort.get(path)
    if size is not None:
        parts.append(size.render())
    said = verdicts.get(path)
    if said is not None and said.render():
        parts.append(said.render())
    detail = f" — {' · '.join(parts)}" if parts else ""
    return f"- `{path}`{detail}{READ if read else ''}"


def coverage(
    ranking: Ranking,
    unresolved: Sequence[Unresolved],
    effort: Mapping[str, Effort] | None = None,
    checks: Sequence[Checked] | None = None,
) -> list[str]:
    """The scope line, and the full file list behind a fold.

    **"3 OF 56 REVIEWED; 53 NOT REVIEWED" READ AS A FAILURE, AND IT IS THE PRODUCT WORKING.**
    A developer waiting to merge saw a large number next to the words "not reviewed" and had no
    way to tell a deliberate budget from a crash. The count is not softened and nothing is hidden
    — `AGENTS.md` calls the residual the product — but a scope stated as a choice reads as one,
    and the files are one click away rather than absent.

    **THE LIST CARRIES PATHS AND NOTHING ELSE, AND IT IS ALPHABETICAL.**
    `docs/product/publishing-rules.md` never-publishes *what the ranking is built from* and *how
    the budget is split across a change*. Per-file fix counts are the first; printing the list in
    RANK order would be the second, since the reader could read the budget straight off it.
    Alphabetical order shows a developer every file we saw without handing a competitor the
    mechanism. The sentence goes further and says nothing about HOW the read files were chosen:
    the comment is about the customer's change, not about our method.

    **THE FOLD IS `<details>`, WHICH IS MARKDOWN GITHUB RENDERS AND NEEDS NO SCRIPT.** A link
    would point somewhere a reader is not signed in to; a button needs a page we do not serve.
    """
    effort = effort or {}
    verdicts = _by_path(checks or ())
    total = len(ranking.units)
    if not total:
        return [NOTHING]

    funded = {unit.unit.site.path for unit in ranking.funded()}
    decided = sum(1 for outcomes in verdicts.values() if outcomes.decided)
    if not decided:
        checked = ""
    elif decided == total:
        checked = ALL_CHECKED
    else:
        checked = SOME_CHECKED.format(decided=decided)
    out = [SCOPE.format(total=total, read=len(funded), checked=checked)]
    if unresolved:
        out.append("")
        out.append(f"_{len(unresolved)} construct(s) could not be parsed._")

    paths = sorted({unit.unit.site.path for unit in ranking.units})
    source = [path for path in paths if not is_test(path)]
    tests = [path for path in paths if is_test(path)]

    out += ["", ALL_FILES.format(total=total), ""]
    if tests and source:
        out += [SOURCE_HEADING.format(count=len(source)), ""]
    out += [_line(path, path in funded, effort, verdicts) for path in source]
    if tests:
        out += ["", TEST_HEADING.format(count=len(tests)), ""]
        out += [_line(path, path in funded, effort, verdicts) for path in tests]
    out += ["", "</details>"]
    return out
