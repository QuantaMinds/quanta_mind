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
