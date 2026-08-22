# Pre-registration — remove the model's freedom to invent the anchor

**Written before the schema is changed.** The mechanism found in the failure data is that
**87.3% of claims quote code that is not at the line they cite** — the prose and the line numbers
are generated independently, and nothing forces them to agree.

## The change

The model no longer emits a line number. It emits **`symbol_a`** and **`symbol_b`** — identifiers
it claims are in the code it was shown. The **parser** finds them and derives the lines. If a named
symbol does not occur in the shown function, the finding is **rejected mechanically**, and recorded
as a residual rather than dropped silently.

**Only one of the two is generated, so they cannot disagree.** That is the whole design.

## Why this test is decisive in both directions

**Anchor correctness is no longer a measurement — it is true by construction.** So the interesting
number is not whether anchors improved. It is whether the *wrong-rate* moves.

| outcome | what it establishes |
|---|---|
| **wrong-rate drops below 50%** | The decoupling was **causal**. Binding the claim to a resolvable symbol fixes the reviewer, and the review half reopens with a specific design |
| **wrong-rate stays high, with anchors now correct by construction** | The decoupling was a **symptom, not a cause**. The reasoning was always the problem, the anchors merely showed it, and no anchoring scheme repairs it. **This is the final nail and it should be recorded as one** |

**The second outcome is the more likely and the more useful.** Three fixes have already failed;
this one removes the failure mode by construction rather than treating it, so if the number does
not move there is nothing left to blame but the claims themselves.

## Population and bar

**The unseen corpus** — 20 pull requests from the six repositories where this reviewer scored
**82.1% wrong and zero correct of 39**. Using the harder corpus deliberately: the seen corpus is
contaminated by prompt rules written against its own failures.

**Bar: under 50% wrong**, the same threshold every review-half test has been held to. Blind
adjudication, same rubric, fresh raters.

**Secondary, recorded but not deciding:** the mechanical rejection rate. If the parser rejects most
findings, the reviewer has become quiet rather than correct, and *"0.9 findings per pull request"*
is only a virtue if those findings are right.

**And one thing that must be reported whatever happens:** how many findings name a symbol that does
not exist in the code shown. That count is a direct measure of the decoupling, and it is the number
that says whether the model can even refer to the code in front of it.


---

# RESULT — the second branch fired. **The decoupling was a symptom.**

| | line anchors | **symbol anchors** |
|---|---|---|
| CORRECT | 0.0% | **2.8%** (1 of 36) |
| **WRONG** | 82.1% | **77.8%**, Wilson [61.9%, 88.3%] |
| UNFALSIFIABLE | 10.3% | 13.9% |
| TRIVIAL | 7.7% | 5.6% |

**77.8% against a bar of under 50%. FAILS. And the change from 82.1% is nothing: p = 0.644.**

## The failure mode moved; the failure rate did not

| why the wrong findings are wrong | line anchors | symbol anchors |
|---|---|---|
| anchor-driven | **62.5%** | **32.1%** |
| semantic — wrong about code fully shown | ~12.5% | **53.6%** |
| merged test's assertion passed | 21.9% | 14.3% |

**Anchor failures halved. Semantic failures quadrupled. The total did not move.** Removing the
model's ability to invent a line number did exactly what it was designed to do, and the reviewer is
no more correct than before.

**That is the pre-registered second branch, and it was written down before the run: the decoupling
was a symptom, not a cause. The reasoning was always the problem, and the anchors were how it
showed.**

## What the run established on the way, which is worth more than the verdict

**Asked for a line number, the model is wrong 87.3% of the time. Asked for a symbol, it names one
that exists 36 times out of 36.** The model knows what code it is looking at. It cannot count
lines. Those are separate failures and only the second was ever a parser's to fix.

## Two flaws in this experiment, both mine

**The `IndentationError` that nearly became a finding.** `ast.parse` fails on an indented method
body, so `occurrences()` returned `[]` for every method — indistinguishable from *"the symbol is
absent"*. It reported **77.8% of findings naming non-existent symbols**, and 79.6% of funded units
are methods, which is where that number came from. Caught because the per-request log showed four
consecutive resolutions before collapsing, which is not how a model fails. **`occurrences()` now
raises `Unparseable`**, so rule 3 holds inside the harness: a failure and a real negative can never
again be the same value.

**The anchors are not fully "correct by construction" and the claim should be weakened.** A named
symbol occurs more than once in **91.7%** of findings — up to 22 times. The resolver takes the
first occurrence for `line_a` and the last for `line_b`, which is a guess. **The fix removed the
model's freedom to invent a line and handed the same freedom to me**, and the 32.1% residual anchor
failures are partly that. A stricter design would require the symbol to be unique in the unit, or
have the model name the enclosing statement.

**Neither flaw rescues the result.** Even crediting every anchor-driven failure as repairable, the
remaining 53.6% semantic and 14.3% merged-test failures leave the wrong-rate near 68% — far above
the bar, on a corpus where the reviewer has produced **one** correct finding in 75 attempts across
two designs.

## The reading

**Four fixes, four failures, and the last one removed the failure mode by construction rather than
treating it.** The review half is not anchor-limited, context-limited, or filter-limited. It is
limited by the claims being wrong about code the model can see.

**Recorded as the final nail, which is what the pre-registration said this outcome would be.**
