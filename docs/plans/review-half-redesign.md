# How to fix the review half — the literature and our own data say the same thing

**Four fixes failed.** Anchor snapping, structured context, a rejection filter, and symbol-derived
anchors each moved the failure *mode* and left the failure *rate* untouched. This records what the
evidence says the actual fix is, and why the four that failed could not have worked.

## The constraint no filter escapes

**Across every adjudicated run: 14 correct findings of 195 = 7.2%.**

| run | correct | n |
|---|---|---|
| first (seen corpus) | 6 | 66 |
| enriched (seen) | 7 | 54 |
| line anchors (unseen) | 0 | 39 |
| symbol anchors (unseen) | 1 | 36 |

**A filter cannot exceed the base rate.** Reject every wrong finding perfectly and 195 attempts
still yield 14 comments. That is why the rejection filter failed and why any future one will:
**filtering is arithmetic on a number that is already too small.** The fix has to raise the base
rate, not clean up after it.

## The asymmetry we measured without noticing we had measured it

| the model's role | how it performed | evidence |
|---|---|---|
| **finder** — generate candidate defects | **7.2% correct** | 195 findings, four runs, blind adjudication |
| **judge** — decide whether a finding is right | **κ = 0.82**, 92.4% agreement on the binary | two independent rater pools on the same 66 findings |

**The same model family, on the same code, is unreliable generating and reliable judging.** Every
blind rater in this project was an LLM, and they caught the errors the finder made — *"`callable()`
is exactly the check that excludes non-callables"*, *"line 1892 already sets it to `None`"*,
*"1450804465901089690 − 1450804465901089614 = 76, exactly the comment's value"*.

## The literature reports the same asymmetry, and has built on it

Every system with strong measured precision uses the LLM as a **triager of a sound analyzer's
alarms**, never as the generator:

| work | setup | result |
|---|---|---|
| [Reducing False Positives in Static Bug Detection with LLMs](https://arxiv.org/html/2601.18844v1) (Tencent, 433 alarms) | static analyzer finds, LLM classifies | **94–98% of false positives eliminated**, $0.0011–$0.12 per alarm |
| [LLM4FPM](https://arxiv.org/pdf/2411.03079) | precise, complete code context on existing alarms | **>85% false-positive reduction** |
| [ZeroFalse](https://arxiv.org/html/2510.02534) | LLM improves precision *of static analysis* | precision gains on analyzer output |
| [Refute-or-Promote](https://arxiv.org/abs/2604.19049) | adversarial kill-gates, cross-model critic | **79–83% of candidates killed**; 3 CVEs over a 31-day campaign with a human orchestrator |

**And the sentence that settles it, from the Tencent study's own conclusion:** *"LLMs show strong
potential in filtering false positives, their capacity to discover new bugs remains **bounded by
the detection capabilities of static analyzers themselves**."*

**We used the model in the one role the literature says it cannot hold.** That is the fix, and it
is not a prompt change.

## The redesign

```
  rank        →  which units to examine       MEASURED: replicated on 20 repositories
  detect      →  a SOUND analyzer emits candidates    ruff, mypy --strict, bandit, semgrep
  triage      →  the model judges each alarm   MEASURED: kappa 0.82 in this project
  verify      →  parser checks the surviving claim's anchor
  coverage    →  what was not analysed, typed
```

**Every component runs in the role it is measured to be good at, and the model never invents a
candidate.** It also satisfies this project's own rule — *"if a parser can answer it, a model must
not"* — which the current design violates at exactly the step that fails.

**What this costs:** recall is bounded by the analyzer. We would find only what `ruff`, `mypy` and
`semgrep` can flag, and never a novel semantic defect. **That is a real ceiling and it should be
stated rather than discovered** — but the current design's recall is 7.2% precision at any recall,
which is not a trade worth defending.

## What it does not change

**Nothing about the shipped product.** The measurement layer — ranking, the corrected attribution
rule, typed coverage — is unaffected and remains the only measured, replicated thing here. This is
a plan for a separate project, and the bar it must clear is unchanged: **under 50% wrong, blind
adjudication, pre-registered.**

**And the cheapest first test is small.** Run `ruff` and `mypy --strict` over the top-3 ranked units
of the same 20 unseen pull requests, have the model triage the alarms, and adjudicate blind. No new
model work, and it answers whether the asymmetry survives contact with our corpus before anything
is built on it.
