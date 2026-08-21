# Which plan, after the trial and error

**Short answer: stop trying to win on F1. Ship the reviewer at parity, and compete on the three
things that actually replicated. Spend the next month on distribution, not on the filter.**

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

**We are level with CodeRabbit and behind the other two.** And the decisive structural fact:
**with nits allowed our recall is 57.8% against Qodo's 57.2%.** We find as much as the leader. We
cannot tell which of our findings are the good ones, and fourteen attempts say so.

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

**A. The reviewer is table stakes. Treat it as a cost, not as the product.**
Ship the arm we have — F1 44.6%, level with CodeRabbit, at 45% less noise per pull request. Put
whatever filter is available in front of it. **Do not spend another month trying to reach 60%.**

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
