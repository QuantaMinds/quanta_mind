# Why the correct-rate is 5.8% — the forensics nobody had run

> **The corpus this rests on has a ±4-point noise floor**, measured 2026-08-26 by running the same
> arm twice: 91 against 84 of 173 defects from nothing but model nondeterminism. Compare any effect
> below to 4 points before believing it; large effects survive, small ones were never resolvable.
> → `corpus-noise-floor.md`


**Every investigation in this project has been on the 135 wrong findings. This one is on the 12
correct ones, because the correct-rate is the number that closed Half B.**

Run 2026-08-25 over `research/phase0/results/all_verdicts.json`, 207 hand-adjudicated findings.

## Finding 1 — there is no slice where the reviewer is good

The obvious hope is that the reviewer is strong somewhere and weak elsewhere, so a filter could
keep the strong part. **It is not.** Best correct-rate on any factor, at n ≥ 15:

| factor | best value | n | correct | C/n |
|---|---|---|---|---|
| design | `1_line_v1` | 54 | 7 | **13.0%** |
| claim type | `unhandled_case` | 41 | 5 | **12.2%** |
| corpus | easy | 18 | 2 | 11.1% |
| is_test | source, not test | 96 | 8 | 8.3% |
| unit size | ≤ 20 lines | 85 | 6 | 7.1% |

**The best slice of anything is 13.0%.**

**AND IT IS NOT COMPARED TO 49%, THOUGH THIS DOCUMENT DID SO WHEN FIRST WRITTEN.**
`docs/product/publishing-rules.md` bars exactly that: *"Never quote a competitor's ONLINE precision
beside one of our own numbers… That band is quotable about them, never as a backdrop for us."* The
49–76% band is **behavioural** — did a developer change the code. Our 5.8% is a blind
adjudication of whether a claim is *true*. Two instruments, one column, and it is the fourth
instance of that defect in this project.

**The comparable layer is Martian's offline scoring**, where every tool meets the same 50 pull
requests and the same human-verified issues: **Greptile 56.5%, ours 43.6%, CodeRabbit 36.5%** —
corrected to ~37.1% for out-of-family judging, so *at level with CodeRabbit, behind Greptile*.

**And the 5.8% has no comparator at all.** No rival has ever been put through a strict blind
adjudication of whether its findings are true, by us or in the published literature. What that
number licenses is a decision about *our own* shipping — under the rule that when two measurements
disagree the stricter one governs — and nothing whatever about a gap to anyone else.

There is no category, no design, no repository, and no function size where this reviewer approaches
usable. **A filter selects a subset, and every subset is bad.**

## Finding 2 — not-wrong and useful are different axes, and one row proves it

| claim type | n | wrong | correct |
|---|---|---|---|
| `resource_leak` | 21 | **33%** — the lowest | **0** |
| `unhandled_case` | 41 | 66% | 5 — the highest |

**The claim type the reviewer is least wrong about, it is never useful about.** The type it is most
useful about, it is wrong about two thirds of the time.

Optimising the wrong-rate does not walk toward the correct-rate. It walks away from it.

## Finding 3 — four designs on one corpus halved the error rate and never moved the useful rate

Holding the corpus constant, so difficulty cannot explain it:

| design | n | wrong-rate | correct |
|---|---|---|---|
| `2_line_hard` | 39 | **82%** | **0** |
| `3_symbol_hard` | 36 | 78% | 1 |
| `4_window_hard` | 39 | 67% | 1 |
| `6_exec_hard` | 21 | **52%** | 1 |

**The wrong-rate fell 30 points. The correct count went 0, 1, 1, 1.**

That is not a trade-off where one axis was sacrificed for the other. **The correct-rate was never
engaged.** Four designs of anchoring, expansion and execution improved what the reviewer says
wrongly and left untouched what it says rightly, because none of them changed how it reasons — they
changed what it was allowed to publish.

## Finding 4 — more output is not more coverage

If the reviewer found real defects at a low rate, emitting more would find more. It does not.
One judge, same 50 pull requests, same 173 golden defects:

| arm | comments emitted | goldens covered | covered per comment |
|---|---|---|---|
| qodo-extended-v2 | 152 | **98** | **0.64** |
| greptile-v4-1 | 168 | 86 | 0.51 |
| **OURS** | **194** | **81** | **0.42** |
| coderabbit | 318 | 106 | 0.33 |

**We emit more than Qodo and cover fewer defects.** The extra output is the same defects said
again — measured directly at a **17.3% redundancy rate against Qodo's 1.0%.**

## What is actually causing it

**This is a generation failure, and every mechanism tried against it has been a filter.**

- anchor repair, structured context, a rejection filter, hunk expansion — filters
- three prompt-direction arms — filters (the model deleting its own output)
- the SHA, registry and date oracles — filters, plus one detector at a 0.24% base rate
- the isolated judge — a filter
- the conversational architecture — a filter, and the best one: 40% of wrong findings dropped while
  losing 1 of 7 correct, against a chance null of 2.8

**All of them make it less wrong. None of them make it more right**, because a filter selects from
what was generated and the correct findings were never generated in the first place.

The arithmetic is the same statement in another form: delete all 135 wrong findings and 72 remain,
12 of them correct — **16.7%**, against our own 5.8% and no external comparator on this instrument.

## The one mechanism that could change it, and its status

Making the reviewer **reason better about code it can already see** is the only thing that would
raise the numerator. That is the `TRACE` class — 17 of 45 wrong findings, code fully present in the
diff and traced incorrectly.

**No oracle can reach it**, because the answer is not a fact to look up but a conclusion to derive.
An August 2026 result has LLMs failing to re-localise a fault they had localised correctly in
**78% of cases** under semantic-preserving rewording — that class exactly.

**Execution grounding is the one published mechanism aimed at it, and its status here is UNTESTED
rather than refuted.** Step 0 established that this pool cannot test it: 44% of the semantic residue
is claims about test files, where the suite that would adjudicate is the subject of the claim, 19%
is configuration no test imports, and only 31% is source a suite touches. Two coverable correct
findings is not a population.

**And our own execution arm inverted** — where the model proved its claim the code was *less* likely
to be fixed, p = 0.001 controlling for length. The proposed explanation, that design selected for
the model's capacity to author a proof rather than for the defect being real, is untested.

## The shape of the conclusion

1. **It is right about 6% of the time under strict adjudication**, and there is no slice of the data
   where that is better than 13%. That instrument has no published comparator — the field's numbers
   are behavioural or benchmark-match, and on the comparable one we are level with CodeRabbit.
2. **Nothing anyone deletes raises it** — proven four ways: no good subset, the not-wrong/useful
   axes diverging, four designs moving one axis and not the other, and the 16.7% perfect-filter
   ceiling.
3. **The one thing that would raise it is an open research problem**, and the mechanism with
   published evidence behind it cannot be tested on the corpus we have.

**Not "the reviewer is bad at reviewing."** It is right rarely, the rarity is a property of
generation rather than of selection, and every tool available to this project acts on selection.

---

# The unit-size lever, tested — it is another filter

The published gradient suggested restricting review to small hunks might raise the correct-rate
rather than lower the wrong-rate. **Tested on the 207. It does not.**

| unit size | n | wrong | correct | C/n |
|---|---|---|---|---|
| 0–10 | 37 | 46% | 4 | **10.8%** |
| 11–20 | 48 | 67% | 2 | 4.2% |
| 21–40 | 61 | 62% | 4 | 6.6% |
| 41–80 | 33 | 70% | 1 | 3.0% |
| 81+ | 28 | 89% | 1 | 3.6% |

**The spread is 3.6×, not the 15× the published work reports, and it is not monotonic** — the
21–40 band beats 11–20.

And the restriction behaves like every other mechanism here:

| keep only | findings kept | correct kept | C/n | **correct LOST** |
|---|---|---|---|---|
| ≤ 10 lines | 37 | 4 | **10.8%** | **8 of 12** |
| ≤ 20 lines | 85 | 6 | 7.1% | 6 |
| ≤ 40 lines | 146 | 10 | 6.8% | 2 |

**Restricting to units of ten lines or fewer nearly doubles the correct-rate and throws away two
thirds of the correct findings.** The rate rises because the denominator falls. It is a filter
wearing a generation lever's clothes, and the absolute yield per pull request goes down.

**One thing it does establish, and it is useful:** source findings are adjudicated correct at
**8.3%** against test-file findings at **3.6%**. That is not a lever either — we cannot make a
change touch source — but it is the property the execution corpus selects on, and it cuts that
labelling round from 259 findings to 180.
