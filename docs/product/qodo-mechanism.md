# Qodo leads this benchmark. Their code says why, and it is our exact defect.

**qodo-extended-v2 is the top tool of 49 on Martian's offline layer: 67.9% precision, 61.3% recall,
64.4% F1.** We are at 43.6% / 45.7% / 44.6%. **They emit FEWER comments than we do — 152 across 50
pull requests against our 194** — and find 106 real issues to our 79.

**That is not a volume story. It is selection, and their pipeline is open source.**

Read at `github.com/qodo-ai/pr-agent`, commit `1eea001`, 16 Aug 2026.

**Caveat that must travel with this:** the benchmarked `qodo-extended-v2` is presumably Qodo Merge,
their commercial build. The open-source PR-Agent shares its prompt lineage and configuration but
**may not be the exact binary Martian scored.** Everything below is what the public repository
does.

---

## What "extended" actually means

`qodo-extended-v2` is not their `/review` tool. **It is `/improve --extended`** — code suggestions
in multi-pass mode. From `configuration.toml`:

```
focus_only_on_problems   = true
num_code_suggestions_per_chunk = 3
max_number_of_calls      = 3
parallel_calls           = true
final_clip_factor        = 0.8
```

**Generate up to nine, score every one, publish about three.** Their observed rate is 3.0 per pull
request.

**We generate up to twelve and publish all twelve.** We have no scoring stage at all. That is the
single largest structural difference between the pipelines.

---

## The mechanism that fixes our 87.3%

**Our defect:** the model writes prose naming `flat_data.view()` and separately emits a line number
pointing at `images = flat_data.reshape(...)`. Nothing forces them to agree, and **87.3% of claims
quoting code quote code absent from the line they cite.**

**Qodo does not ask the model for a line number.** It asks for a **quote**:

> `existing_code`: *"A short code snippet, from a `__new hunk__` section after the PR changes, that
> the suggestion aims to enhance or fix. Include only complete code lines."*

Then a **second pass derives the line number from the quote**:

> *"another sub-task you have is to detect the line numbers in the `__new hunk__` of the PR code
> diff section that correspond to the `existing_code` snippet."*

**The anchor is computed from the claim rather than emitted beside it. They cannot disagree,
because one is a function of the other.**

**This is a structural fix to the exact failure five of our designs attacked from the wrong end.**
We tried snapping the model's line number to a statement (p = 0.53), replacing it with a symbol
name (p = 0.644), and widening it to ±10 lines (+2.6 points). **All three repaired the pointer.
Qodo deleted the pointer and kept the quote.**

---

## Their filter is a check, not a rating — which is why it works

This project measured a rejection filter that moved nothing. Greptile published that
LLM-as-judge severity rating was *"nearly random"*. **Both are true and neither refutes what Qodo
does, because Qodo's reflection pass verifies mechanically checkable properties:**

- *"Validate the `existing_code` field by confirming it matches or is accurately derived from code
  lines within a `__new hunk__` section of the PR code diff."* — **does the quote exist in the
  diff?**
- *"Ensure the `improved_code` section accurately reflects the `existing_code` segment after the
  suggested modification is applied."* — **is the fix consistent with the quote?**
- Score **0** where *"the `improved_code` section does not accurately reflect the suggested
  changes, in relation to the `existing_code`"*.

**Asking "how severe is this?" is a matter of taste and scores near random. Asking "does this
snippet appear in the diff?" has an answer.**

### And `improved_code` is a falsifiability device

The model must write the replacement code, not just describe the problem. **If it cannot produce a
coherent fix for the snippet it quoted, the reflection scores it zero.**

**Note the difference from our execution gate**, which ran the model's own snippet and came back
*inverted* — demonstrable claims were **less** likely to sit on code that later broke (36.5%
against 50.5%, p = 0.003). **Qodo does not execute anything.** It checks internal consistency
between a quote and its replacement. Different mechanism, and our inverted result says nothing
about it.

---

## The zero-score list, and the rule aimed at diff-only reviewers

The reflection assigns **score 0** to suggestions that:

- add docstrings, type hints or comments
- remove unused imports, or add missing imports
- use more specific exception types
- **"question the definition, declaration, import, or initialization of any entity in the PR code,
  that might be done in the outer codebase"**

**That last rule is the one worth stealing.** A reviewer shown only a diff constantly flags symbols
it cannot see defined — and is usually wrong, because they are defined elsewhere. **Qodo scores
that class to zero by rule instead of hoping the model resists.**

Plus calibrated caps on classes that are usually noise: *"only asks the user to verify or
ensure"* ≤ 7; *"error handling or type checking"* ≤ 8; `existing_code == improved_code` ≤ 7.

---

## They also suppress nits — and still lead

`focus_only_on_problems = true`, with an explicit DO NOT list. **So the benchmark leader bans the
same categories we ban and scores 67.9%.**

**This refutes the tempting reading of our own nits experiment.** Turning nits on reversed our gap
to Greptile and destroyed precision at a marginal 8.1%. **Qodo shows the recall was available
without them.** They reach 61.3% recall while suppressing style, docstrings and imports — so the
issues they find and we miss are not nits. They are real defects we are not finding.

**That is a harder and more honest problem than the one the Greptile comparison suggested.**

---

## What we would change, in order of expected effect

**One — replace the line anchor with a quote.** Ask for the code snippet, derive the line from it
mechanically, and refuse any finding whose quote is not present in the diff. **This is the only
change that attacks the 87.3% at its cause**, and it is cheap: a string search, not a model call.

**Two — add a scoring pass, and score checkable properties only.** Does the quote appear in the
diff? Is the proposed replacement consistent with it? Is the finding in a zero-score category?
**Do not score severity** — two independent measurements say that is noise.

**Three — generate more and publish fewer.** We publish everything we generate. Every leading tool
generates a surplus and filters.

**Four — number the diff lines we send.** Qodo presents `__new hunk__` with explicit line numbers.
We send a raw unified diff and ask the model to count.

**None of this reopens the review half.** The bar is unchanged and it is not a benchmark score:
**under 50% of published findings wrong, under adjudication that checks whether a claim is anchored
to the line it cites.** What this document establishes is that a mechanism exists which was never
tested in our seven designs — **quote-derived anchoring** — and that the five anchor designs we did
run all attacked the pointer rather than removing it.

**If the review half is ever restarted, this is the design to pre-register first.**

---

## Both mechanisms were built and measured. This is what came back.

Written before the run: this document proposed expansion and the conventions file as the two
cheapest things Qodo does that we did not. **Both were built, sabotage-tested, and run against 80
merged pull requests from six repositories verified unused**, three arms, blind adjudication, bars
fixed in advance, **10 of 10 sabotaged controls caught**.

| | bar | result |
|---|---|---|
| expansion removes the "did not follow shown code" failure | ≥ 15 point fall | 73.3% → **18.8%** — **PASS** |
| expansion lowers the wrong-rate | ≤ 30% | **59.3%** [40.7, 75.5] — **FAIL** |
| a rules file makes convention-policing worse | ≤ +10 points | **−12.6 points** — **PASS**, but the gain is UNFALSIFIABLE absorbing claims (+4) rather than CORRECT (+1) |
| neither starves the reviewer | ≥ 0.30/PR | 0.41 / 0.40 / 0.46 — **PASS** |

**Expansion did exactly what this document predicted, and that is H1 passing — not a failure.**
The overall rate not moving is a separate fact with a separate cause. The mechanism is
visible: two claims of an infinite loop in falcon's URI decoder died because the
`for pos in range(...)` header that refutes them sits ten lines above the hunk. What this document
did not predict is what took over — **CI-config findings are 66.7% wrong and 23 of 24 of those are
claims a diff cannot settle.** Every one checked against GitHub was false.

**So the gap to Qodo is not the two mechanisms.** It is that a diff-scoped reviewer should not be
reviewing files whose defects are undecidable from a diff. Full result in
`docs/product/expansion-conventions-result.md`; every number recomputed by
`research/phase0/claims/verify.py`.
