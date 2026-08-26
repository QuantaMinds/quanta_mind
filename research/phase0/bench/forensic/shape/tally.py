"""How much of the corpus actually carries context, and whether any repository carries none.

WHAT: `coverage(pulls, contexts)` -> (changes with context, {repo: (got, total)}, repos with none).
WHY:  **THE GATE THIS FEEDS WAS UNTESTABLE AND WOULD HAVE PASSED A BROKEN RUN.** It sat inside
      `shape_context.main()`, behind a model client and a corpus fetch, so the only way to
      exercise it was to run the whole experiment. Here it takes two dictionaries and returns
      three values, and a known answer takes milliseconds.

      **A CHANGE WITH NO CONTEXT HAS A `WITH_SHAPE` ARM BYTE-IDENTICAL TO `PLAIN`**, so it
      contributes exactly zero signal and pulls the result toward null. grafana timed out
      mid-clone and would have taken 10 of 50 with it -- and `40 < 50 * 0.8` is `40 < 40`, FALSE,
      so a percentage gate passed it at exactly the boundary.

      Split from `pulls.py` because that file crossed the 200-line cap, and because resolving a
      clone and counting what came back are two concerns.
IMPORTS: stdlib only.
CONSUMED BY: `bench/forensic/shape_context.py`.
"""

from __future__ import annotations


def coverage(
    pulls: list[dict[str, object]], contexts: dict[str, str]
) -> tuple[int, dict[str, tuple[int, int]], list[str]]:
    """(changes with context, {repo: (got, total)}, repos that produced NOTHING).

    **A PURE FUNCTION BECAUSE THE GATE IT FEEDS WAS UNTESTABLE.** It lived inside `main()`, behind
    a model client and a corpus fetch, so the only way to exercise it was to run the whole
    experiment -- and a gate nobody can put a known answer through is the shape this project keeps
    finding broken. Here it takes two dictionaries and returns three values.

    The third is the one that matters: a repository contributing NOTHING is a systematic gap, not
    sampling noise. grafana timed out mid-clone and would have taken 10 of 50 with it, and
    `40 < 50 * 0.8` is `40 < 40` -- FALSE -- so a percentage gate passed it at exactly the
    boundary and would have scored a corpus one fifth inert.
    """
    by_repo: dict[str, tuple[int, int]] = {}
    for pull in pulls:
        repo = "/".join(str(pull["original"]).split("/")[3:5])
        got, total = by_repo.get(repo, (0, 0))
        by_repo[repo] = (got + (1 if contexts.get(str(pull["key"])) else 0), total + 1)
    empty = sorted(r for r, (got, _) in by_repo.items() if got == 0)
    return sum(1 for v in contexts.values() if v), by_repo, empty
