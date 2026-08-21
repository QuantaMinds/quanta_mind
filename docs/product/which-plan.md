# Which plan, after the trial and error

**Short answer: ship the half that replicated, and go find out whether anyone wants it.**

> **PLAN A OF THE FIRST DRAFT — "ship the reviewer at parity" — IS WITHDRAWN.** It reopened the half
> this project closed on evidence, and it rested on two claims of mine that do not survive the
> canonical document. Both are corrected below rather than deleted; the error is more instructive
> than the conclusion was.

---

## 1. The count, because it is the argument

**Fourteen attempts to make the model half better. Every one null or inverted.**

| what was tried | outcome |
|---|---|
| 8 reviewer designs — line anchors, structured context, symbol anchors, ±10-line tolerance, execution gate, analyzer-triage, expansion, conventions file | **66.7–82.1% wrong throughout**; design 7 emitted nothing at all |
| reject-on-imprecise-anchor filter | +9.9 points against a +15 bar |
| anchor snapping | p = 0.53 |
| >40-line hard gate | p = 0.281, and it discarded 2 of 12 correct findings |
| execution gate | **INVERTED, p = 0.003** |
| same-family judge (`gemini-2.5-pro`) | 21% discarded, F1 37.3% |
| same-family judge (`gemini-2.5-flash`) | worse — F1 34.4%, 16 true findings lost |
| judge prompt: truth → materiality | keep-rate 79% → 80%. Nothing |
| mechanical gate, arm A | **INVERTED — D/L 1.40 against chance 3.64** |

**Two of them came back significantly backwards.** That is not a run of bad luck to push through; it
is a body of evidence about where the value is not.

## 2. What survived, and it is a short list

| | evidence |
|---|---|
| **The ranker** | 1.21% vs 3.12%, **six repositories never seen**, n = 2,400, p < 1e-6, positive in 6 of 6. **The only out-of-sample replication this project has** |
| **Typed silence / the coverage line** | verified unavailable to all seven competitors; Greptile's `Failed` means the run broke, not that analysis was incomplete |
| **The retrospective** | one clone, no install, no access — and it is built and live-tested |
| **Publishing the judge's own numbers** | nobody does it; calibration drift is a named failure mode and every rival's filter is a sealed box |

## 3. Where we actually stand against them

| arm | precision | recall | F1 | noise/PR |
|---|---|---|---|---|
| qodo-extended-v2 | 65.1% | 57.2% | **60.1%** | 1.1 |
| greptile-v4-1 | 56.5% | 52.6% | 54.5% | 1.4 |
| coderabbit | 36.5% | **60.7%** | 45.6% | 3.7 |
| **ours, best arm** | 43.6% | 45.7% | **44.6%** | **2.0** |

**We are BELOW CodeRabbit once our own number is corrected, and behind the other two.** Our arm
was judged by its own model family; a blind out-of-family adjudication put our over-match rate at
**15.0% against the rivals' 5.0%**, moving 43.6% to **37.1%** — level with CodeRabbit's 36.5%
rather than above it. That has been in the canonical document since commit `7ba0391`. **The
self-preference effect this thread spent days measuring was inflating our own headline**, and the
first draft of this page quoted the uncorrected figure.

**And the decisive structural fact, stated correctly.** With nits allowed our recall is 57.8%
against Qodo's 57.2% — **but that arm runs at 21.6% precision, 464 candidates, 7.3 noise per pull
request.** It is a statement about *detection capacity*. **It is not a statement about anything
shippable**; the arm that could ship is the strict one at **45.7%** recall. The first draft quoted
one arm's recall and the other arm's shippability in the same sentence.

## 4. The one lever never pulled — and why it is still not the plan

**Every design this project has run was ONE generalist prompt trying to catch everything.** Qodo
runs **more than a dozen specialist agents** — backend bugs, UI, runtime, rules, security,
performance, accessibility — then a judge that dedupes and filters. Their stated reason: *"A single
LLM trying to catch everything catches nothing reliably."*

**Decomposition has never been tried here.** It is the only untried mechanism with external
evidence behind it, and unlike a filter it attacks selection *by construction*: a narrow agent
emits fewer irrelevant findings rather than emitting them and then trying to spot them.

**It is still not the plan, for one reason: it is their architecture, and following it means
arriving where they already are, later, at their cost structure.** It is a large build against a
competitor's known strength, funded by a company whose stated weakest point is distribution.

## 5. The plan

**A. WITHDRAWN — do not ship the reviewer.**

*The first draft said: ship the arm we have, F1 44.6%, level with CodeRabbit, 45% less noise.*

**"Level with CodeRabbit" is a shaped truth, and it had already been caught once in this project.**
CodeRabbit is **24th of 49** on that leaderboard. Parity with the 24th tool is not a reason for
anyone to change vendors, and the corrected estimate is 37.1% rather than 43.6%.

**The yield ends it.** **0.013–0.037 correct findings per pull request** — one useful comment per 27
to 77 pull requests. That is the number that closed the review half. A tool posting mostly-wrong
comments at that yield is muted in week three, which is exactly the failure the positioning exists
to avoid. **Publishing the drop counts does not mitigate it**: the honest published sentence reads
*two-thirds of what we post is wrong*.

The canonical document's own words: **the pitch this evidence forbids is "an autonomous senior
engineer."** Shipping the reviewer at parity is a weaker version of that pitch, not a different
one.

**B. Run arm B once, when a cross-family model is reachable — then stop.**
It is one run, it is correct practice rather than a differentiator, and it is the last cheap
question. **If it lands near Greptile, ship it and move on. If it does not, ship at parity and stop
filtering.** Either way the roadmap does not depend on the answer.

**C. Sell the three things that replicated.**
The ranker decides where to look and is the only claim that reproduced out-of-sample. The coverage
line says what was not analysed and no competitor prints it. **And publish the judge's own
numbers** — candidates generated, dropped by rule, dropped by judge, judge model and version,
agreement against the held-out set — per review. That is typed silence one level up, it is the
project's signature applied to a new surface, and it is a sentence no rival can say.

**D. Spend the next month on distribution, because the plan already says that is the weak point.**
The retrospective needs one clone and no install. It is built. **It is the only bottom-up motion
this company has, and it is not gated on any of the fourteen failures above.**

## 6. What this plan risks, stated plainly

**We ship model findings that are 66.7–82.1% wrong raw, behind a filter that is unproven.** That is
in tension with the honesty positioning, and the mitigation is C: publish the drop counts so a
customer can see what was discarded and by what. **If the numbers we publish are bad, we will have
published them** — which is the position this company has taken every previous time.

**And the reviewer may simply not be a wedge.** Parity with CodeRabbit is not a reason to switch
vendors. If customers do not buy the coverage line and the retrospective, the reviewer will not
save it — and that is the question thirty days with a real team answers, not another experiment.


---

# The defect class this thread named

**A mechanism's evidence must cite the run that produced it, not the section it sits in.**

Three instances, and the third was found only by tracing a citation:

| the mechanism credited | the work actually belonged to |
|---|---|
| hunk expansion | the corpus |
| the model's findings | the ranker's location signal |
| **the free keyword rule** | **`decidable.judge_one()`, a model gate** |

**The third is the clearest.** `p = 0.0007` sat in a section about labelling findings, and was cited
as showing that *a rule* separates. It shows that *an inference call* separates, on n = 29, with a
rater whose reasoning correlated with the gate's own criterion. The rule it was credited to was
tested out-of-sample for the first time and **inverted**.

**The figure guard catches a number that does not match its artefact. It does not catch a number
matched to the WRONG artefact.** Extending it to trace which run produced each figure would have
caught this, and that is the check worth building.

## And a sixth instance of the instrument-reporting-on-the-wrong-thing class

`bench/corpus.py` and `quote/corpus.py` both define a module named `corpus`. `sys.path` order
decided which one `import corpus` resolved to, **and there is no error at all** — the wrong module
loads, its API differs, and the failure surfaces as a missing attribute somewhere unrelated or, in
the worse case, as a plausible number computed from the wrong data.

`scripts/guard/check_module_identity.py` already exists for "never leave two modules with one
name", scoped to `src/`. **It does not cover `research/`, which is where the collision is.**
