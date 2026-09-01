"""A standard a parser genuinely cannot answer, put to a model — and kept out of the audit trail.

WHAT: `judge_all(rules, path, source, ask)` returns one `Judged` per `MODEL_JUDGED` rule that
      governs `path`. `Judged` carries `Verdict.MET | BROKEN | UNDECIDED`, and `BROKEN` carries a
      quote that was found verbatim in the source.
WHY:  **D1c, AND THE HALF THAT WAS MISSING WAS NEVER THE WIRING.** `CheckKind.MODEL_JUDGED`,
      `Rule.provenance` and the `provenance` column have existed for weeks; what did not exist was
      a decision about what a model verdict is ALLOWED to be. This module is that decision.

      **A MODEL VERDICT IS A FINDING, NEVER A COMPLIANCE ROW.** `types/checked.py` counts both
      `PASSED` and `VIOLATED` toward the rate, so any outcome but `DEFERRED` would put a Gemini
      opinion into the number a customer shows an auditor. Raw model findings measure **66.7-82.1%
      wrong** across four blind pools. So `verify/rule_check.py:check` still returns `DEFERRED` for
      every model-judged rule, permanently and on purpose, and `Judged` is a SEPARATE object that
      never reaches `store/rule_checks.py`. They are not the same type, not in the same table, and
      not rendered by the same code — which is the strongest available reading of the row's
      requirement that the two "must never render alike".

      **`UNDECIDED` IS THE DEFAULT ON EVERY FAILURE PATH.** No reply, a malformed reply, a quote
      that is not in the file, an exception from the transport: all `UNDECIDED`, never `MET`.
      `docs/engineering/CORRECTIONS.md` entry 8 records a verifier that defaulted the other way and
      confirmed every false claim it had been built to refute. **"The model did not answer" and
      "the model said this is fine" must never be the same value on the wire.**

      **`BROKEN` REQUIRES A QUOTE THAT IS ACTUALLY IN THE SOURCE.** `verify/anchor.py` applies the
      same rule to review findings for the same reason: a claim the reader cannot locate is a claim
      they cannot check. A model that reports a violation and quotes a line it invented is reporting
      nothing, and it is the failure shape most likely to survive review — the prose still reads
      correctly.

      **THE JUDGE IS INJECTED, NOT IMPORTED**, and that is now enforced rather than intended.
      `AGENTS.md` rule 7 says the layer order is "what stops `verify` importing `infer`" — it did
      not: `infer` sits to the LEFT of `verify` in `scripts/guard/discovery.py:LAYER_ORDER`, so the
      import ran leftward and `check_layering` waved it through. Building this module is what found
      that, and `scripts/guard/check_conventions.py:FORBIDDEN` now refuses the pair outright. The
      judge arrives as a parameter — the precedent `verify/consumers.py` set for its clone — so the
      layer adjudicating the model's claims cannot import the layer that makes them.
IMPORTS: ingest.blob, types.{judged,rule,verdict}. Nothing to its right, nothing from `infer`.
CONSUMED BY: `verify/rule_check.py:enforce`, which passes the judge through from `serve/`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from quantamind.ingest.blob import at
from quantamind.types.standards.judged import MIN_QUOTE_CHARS, Judged, Verdict
from quantamind.types.standards.rule import CheckKind, Rule
from quantamind.types.verdict import Site

JUDGE_CAP = 10
"""Files judged per change, taken from the FRONT of the ranked order.

One model call per rule per file multiplies fast: a 76-file change with three prose rules is 228
calls. `serve/` reports how many were left unjudged — **a truncation that does not announce itself
reads as full coverage**, which is what `render/blocks/file_table.py` exists to prevent."""


Ask = Callable[[Rule, str, str], tuple[Verdict, str, str]]
"""Put one rule to a model: `(rule, path, source) -> (verdict, quote, why)`.

**INJECTED BY `serve/`, NEVER IMPORTED HERE.** See the module docstring. An implementation that
raises is treated as `UNDECIDED`, so a transport failure cannot read as compliance."""


def _normalise(text: str) -> str:
    """Whitespace-insensitive form, so a quote survives the model reflowing it."""
    return " ".join(text.split())


def anchored(quote: str, source: str) -> bool:
    """Whether `quote` really appears in `source`.

    **THIS IS WHAT SEPARATES A FINDING FROM A SENTENCE.** A model reporting a violation it cannot
    quote from the file has reported nothing, and the prose reads correctly either way.
    """
    if len(quote.strip()) < MIN_QUOTE_CHARS:
        return False
    return _normalise(quote) in _normalise(source)


def _line_of(quote: str, source: str) -> int:
    """The 1-indexed line the quote sits on, or 0 when it spans lines or is not found."""
    wanted = _normalise(quote)
    for number, line in enumerate(source.splitlines(), 1):
        if wanted in _normalise(line):
            return number
    return 0


def judge(rule: Rule, path: str, source: str, ask: Ask) -> Judged:
    """One model-judged rule against one file. **Exactly one record, whatever happened.**

    Every way this can go wrong lands on `UNDECIDED`: the transport raised, the reply named a
    verdict we do not have, or it claimed `BROKEN` and quoted something the file does not contain.
    """
    try:
        verdict, quote, why = ask(rule, path, source)
    except Exception as exc:
        # **NOT A BARE `except: pass`.** The reason is kept and rendered; what is refused is
        # letting a transport failure read as "the standard is met".
        return Judged(rule.id, Site(path), Verdict.UNDECIDED, why=f"could not be asked: {exc}")

    if verdict is Verdict.BROKEN:
        if not anchored(quote, source):
            return Judged(
                rule.id,
                Site(path),
                Verdict.UNDECIDED,
                why="reported a violation but quoted text that is not in the file",
            )
        return Judged(rule.id, Site(path, _line_of(quote, source)), verdict, quote.strip(), why)
    if verdict is Verdict.MET:
        return Judged(rule.id, Site(path), Verdict.MET, why=why)
    return Judged(rule.id, Site(path), Verdict.UNDECIDED, why=why or "no answer")


def judge_all(rules: Sequence[Rule], path: str, source: str, ask: Ask | None) -> tuple[Judged, ...]:
    """Every model-judged rule that governs `path`.

    **`ask=None` RETURNS NOTHING AND IS NOT AN ERROR.** The model is opt-in: a deployment with no
    inference configured runs the whole deterministic half unchanged, which is the half that
    carries the product.
    """
    if ask is None:
        return ()
    return tuple(
        judge(rule, path, source, ask)
        for rule in rules
        if rule.check is CheckKind.MODEL_JUDGED and rule.applies_to(path)
    )


def judge_change(
    rules: Sequence[Rule], clone: Path, sha: str, paths: Sequence[str], ask: Ask | None
) -> tuple[Judged, ...]:
    """Every model-judged rule against the files it governs, capped and honest about the cap.

    **THE CAP IS THE COST CONTROL AND IT IS ANNOUNCED, NOT HIDDEN.** One model call per rule per
    file multiplies fast: a 76-file change with three prose rules is 228 calls. `paths` arrives in
    the order the ranker chose, so the cap keeps the files fix history ranked highest and
    `serve/` reports how many were left unjudged. A truncation that does not say it truncated reads
    as full coverage — the failure `render/blocks/file_table.py` was built to stop.
    """
    if ask is None:
        return ()
    rows: list[Judged] = []
    for path in paths[:JUDGE_CAP]:
        source = at(clone, sha, path)
        if source is None:
            continue
        rows.extend(judge_all(rules, path, source, ask))
    return tuple(rows)
