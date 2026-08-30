# Decision thresholds in `rank/` and `verify/` are not exercised by any test

## What the measurement was

Every module-level numeric constant in `src/quantamind` was mutated twice — to `0` and to
`2n+1` — with the bytecode cleared between runs, and `tests/unit` plus `tests/property` run in
full after each. 130 mutations over 65 constants.

**95 of 130 survived. 41 of the 65 constants survived both mutations**, meaning no unit or
property test distinguishes their shipped value from either replacement.

## The caveat that changes the reading

`tests/live` was excluded for runtime, and **there is no `tests/unit/layers/rank/` directory at
all** — `rank/` is exercised live, against real repositories, not in unit tests. So "survived"
above means "not caught by the unit and property tiers", which for `rank/` is close to expected
and for `verify/` is not.

The four highest-consequence survivors were therefore re-run against `tests/live` before any
conclusion was drawn. Only those confirmed against the full suite are treated as gaps.

## What this changes

Nothing in `src/`. The constants are not wrong and are not being altered — several carry
docstrings deriving them from measurement, `rank/firing.ALWAYS_AT` among them. The gap is that
no test would notice if they were altered, which is a test-coverage defect, not a ranking defect.

## The work

- `tests/unit/layers/verify/test_anchor.py` — `locate` is a pure function of a `Finding` and a
  diff, and has no unit test. Pin the `MIN_QUOTE_CHARS` boundary from both sides: a quote one
  character short is refused, a quote at the boundary that is present in the diff anchors and
  carries the added line's number. **A refusal and an absence must stay distinguishable**, which
  is the module's stated reason to exist.
- `tests/unit/layers/render/test_json_report.py` — extend: the emitted `schema` field is the wire
  contract every consumer keys off, and changing it broke nothing.
- `rank/` boundaries are reached only through a store connection. Whether they are worth a unit
  test at all depends on whether the live tier already covers them; that is what the live re-run
  decides, and it is reported either way rather than assumed.

## What the live re-run decided

All four of the highest-consequence survivors survive `tests/live` as well, so none of them was
covered by the live tier either:

| mutation | unit + property | live |
|---|---|---|
| `verify/anchor.MIN_QUOTE_CHARS` 8 → 0 | survives | survives |
| `rank/firing.ALWAYS_AT` 0.50 → 0.0 | survives | survives |
| `rank/order.DEFAULT_THRESHOLD` 0.9 → 0.0 | survives | survives |
| `render/json_report.SCHEMA` 1 → 99 | survives | survives |

Seven constants are now covered, and the 14 mutations that were applied to them are all caught:
`MIN_QUOTE_CHARS`, the three `rank/firing` boundaries, and the three separate declarations of the
0.9 decile in `rank/order`, `types/settings` and `types/ranking`.

**The threshold turned out to be written in three layers with nothing requiring them to agree.**
`rank.order.DEFAULT_THRESHOLD`, `types.settings.DEFAULT_THRESHOLD_PERCENTILE` and the default on
`Ranking.threshold_percentile` are each 0.9 and each independently mutable. That is now an
asserted invariant rather than a coincidence.

**`rank/firing`'s branch is still not exercised.** The three boundaries are pinned and ordered so
no branch can be made dead, but reaching `estimate()` needs a populated store and that fixture is
not written. Said plainly in the test file rather than left to be inferred.

## What could still silently fail

A pinned boundary proves the branch is reachable and the number is the one that ships. It does
not prove the number is *right* — `ALWAYS_AT = 0.50` is defended by a docstring citing four
repositories, and no test can confirm that reasoning. Only the measurement behind it can.
