# D1c — model-checked rules, clearly separated

**State:** planned, not built. Written before any code, because this changes `verify/`.

---

## What the row asks for

> **D1c Model-checked rules, clearly separated.** For rules a parser genuinely cannot answer.
> Each result carries `Provenance.PARSER` or `Provenance.MODEL` so an auditor can see which
> claims are reproducible. **They must never render alike.**

Verified again today, and `docs/plans/product/product-build.md` already says it: **the half that
separates is built and the half that checks is not.** `CheckKind.MODEL_JUDGED` exists,
`Rule.provenance` derives `Provenance.MODEL` and refuses to be set by a caller,
`store/rule_checks.py` writes the column, `render/compliance_table.py` gives `deferred` its own
column outside the rate. `verify/rule_check.py:check` returns `Outcome.DEFERRED` and stops.

So this row is not "wire a model in". It is: **decide what a model verdict is allowed to be**, and
build only that.

---

## The decision this row actually turns on

A model-judged rule that returns an answer must land somewhere in `Outcome`. The two available
landing spots both do damage:

- **`PASSED` / `VIOLATED`** — `types/checked.py:counts_toward_compliance` returns True for both, so
  a Gemini opinion enters the same compliance rate as a parser's verdict. The rate is the number a
  customer shows an auditor. Our raw model findings are **66.7–82.1% wrong** across four blind
  pools. Putting that into a defensible number destroys the number.
- **`DEFERRED` forever** — what we have. Honest, and the capability does not exist.

**Decision: a model verdict is published as a finding, and never as a compliance row.**

`Checked` stays `DEFERRED` for every `MODEL_JUDGED` rule, permanently and by design. The audit
trail keeps saying "a parser did not decide this", which is true. What D1c adds is a *second
output* from the same pass: a `Judged` record that flows to the comment through the existing model
gate, and never into `store/rule_checks.py`.

This satisfies "they must never render alike" in the strongest available way — they are not the
same kind of object, do not share a table, and do not share a renderer.

### Why not a third rate

Rejected: a "judged compliance rate" printed beside the reproducible one. Two rates on one table is
how the weaker number gets quoted as the stronger. `render/compliance_table.py` already carries the
line "the rate is violations over checks that could be DECIDED" — one rate, one meaning.

---

## Layering, and a mismatch worth naming

`AGENTS.md` rule 7 says the layer order is "what stops `verify` importing `infer`: the layer
adjudicating the model's claims cannot start trusting them."

**It does not stop it.** `infer` is at index 6 and `verify` at index 7 in
`scripts/guard/discovery.py:LAYER_ORDER`, and `scripts/guard/check_conventions.py:check_layering`
only flags a target at or to the *right* of the importer. `verify` may import `infer` today and no
guard objects. The sentence describes an intent the mechanism does not implement — rule 14's own
shape, in the rules file.

I am not silently working around it and I am not quietly relying on it. **The judge is injected**,
matching the precedent already in `verify/consumers.py`, whose docstring says the clone is injected
"because `verify/` may not reach into `serve/`":

```
Judge = Callable[[str, str, str], Verdict | None]   # rule description, path, source
```

`serve/` supplies the Gemini-backed implementation. `verify/` imports nothing from `infer/`. This
is raised in the PR description rather than fixed here — making the guard match the sentence is a
change to every layer's contract and does not belong in a product row.

---

## What gets built

1. **`src/quantamind/verify/judged_rule.py`** — new.
   - `Judged(rule_id, site, verdict, quote, why)`; `Verdict` is `MET | BROKEN | UNDECIDED`.
   - `judge_all(rules, path, source, ask)` returns one `Judged` per `MODEL_JUDGED` rule that
     `applies_to` the path, and `()` when `ask` is `None` — **the model is opt-in, and its absence
     is not an error.**
   - **`UNDECIDED` is the default on every failure path**: no reply, an unparseable reply, a reply
     whose quote is not in the source. Never `MET`. `docs/engineering/CORRECTIONS.md` entry 8 is a
     verifier that defaulted the other way and confirmed every false claim it existed to refute.
   - **`BROKEN` requires a quote that appears verbatim in the source.** Same anchoring rule
     `verify/anchor.py` applies to review findings, for the same reason: a claim we cannot locate
     is a claim the reader cannot check.

2. **`src/quantamind/verify/rule_check.py`** — changed, minimally.
   - `check()` keeps returning `DEFERRED` for `MODEL_JUDGED`. **Unchanged on purpose.**
   - `enforce()` gains an optional `ask: Judge | None = None` and returns
     `tuple[Checked, ...], tuple[Judged, ...]`. The `Checked` half is byte-identical to today.

3. **`src/quantamind/render/blocks/judged_block.py`** — new.
   - Renders under its own heading, with its own sentence saying a model decided it and the verdict
     cannot be re-run. Never inside the rule table, never counted in the file table's "N rules
     passed" column.

4. **`src/quantamind/serve/review_delivery.py`** — wires `ask`, and routes each `BROKEN` through
   `verify/publishable.py:gate` exactly as a review finding is routed. **A model-judged rule
   violation is a model finding**; it does not get a private path to the customer that skips the
   oracles.

---

## What this must not do, stated so a reviewer can check it

- No `MODEL_JUDGED` rule may produce a `Checked` row with an outcome other than `DEFERRED`.
- No `Judged` record may reach `store/rule_checks.py`.
- The compliance rate must be numerically identical before and after this change, on the same
  store. **This is a test, not a claim.**
- With `ask=None` the entire pipeline must behave exactly as it does today.

---

## How each of those is checked

Per rule 14 — ask what the check prints when the thing it checks is broken.

| Claim | Check | What it prints when broken |
|---|---|---|
| Model verdicts stay out of the rate | `test_rate_unmoved_by_judging` — build a store, read the rate, run `enforce` with a judge that returns `BROKEN` for everything, read it again | the two rates differ |
| `Judged` never persists | `test_judged_never_stored` — count `rule_check` rows either side | the count moved |
| `UNDECIDED` on every failure | parametrised over: `ask` raises, returns `""`, returns junk, returns a quote absent from the source | any case that is not `UNDECIDED` |
| `ask=None` changes nothing | run the real `enforce` both ways over a fixture, compare `Checked` tuples | the tuples differ |
| A `BROKEN` verdict is anchored | a judge returning a fabricated quote | the record survives as `BROKEN` |

**Known-answer test, naming its artefact:** a fixture module that genuinely breaks a stated
prose rule ("every public function has a docstring") with a stub judge that returns the real
quote — the test asserts the `Judged` record names *that* function, not merely that one exists.

**Sabotage list** (whole mechanism, not the entry point — and rebuild bytecode first, per
`sabotage-can-run-on-stale-bytecode`):
1. Make `judge_all` default to `MET` instead of `UNDECIDED`.
2. Drop the quote-anchoring requirement from `BROKEN`.
3. Let `enforce` write `Judged` rows into `rule_check`.
4. Make `check()` return `VIOLATED` for a `MODEL_JUDGED` rule.
5. Ignore `ask=None` and judge anyway.

Each must fail a *named* test. Any that disables cleanly means the test was watching the entry
point, not the mechanism.

---

## Cost

One model call per `(MODEL_JUDGED rule × changed file it governs)`. Uncapped, that is the
`enforce()` loop multiplied by the rule count — a 76-file change with 3 prose rules is 228 calls.
**Capped at `JUDGE_CAP` files per rule, ranked by the existing fix-history order**, and the render
says how many were judged and how many were not, in the shape `render/blocks/file_table.py`
already uses for unread files. A cap that does not say it is a cap is a silent truncation.

---

## Out of scope

- Mining rules from review history — that is D1d.
- Org-wide inheritance — D1e.
- Making `check_conventions.py` enforce what rule 7 says. Raised in the PR, not fixed here.
