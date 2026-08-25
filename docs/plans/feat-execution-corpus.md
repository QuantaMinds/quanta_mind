# The one thing left that is fixable — and what the Aug 2026 literature says it is worth

**Written after searching the field, and after correcting a comparison this project's own rules
barred.**

## What the search establishes, and it is not encouraging for "fully fixable"

| result | number | what it measures |
|---|---|---|
| best published research, LLM Go code review | **28.0% RefineEM** | did the comment induce a matching human change — **behavioural** |
| its supervised baseline (CodeReviewer) | 15.0% | same |
| 8 tools against 67 **planted** production bugs | **best F1 47%** | ground truth, recall and precision against known defects |
| strict blind adjudication of whether findings are TRUE | **nothing published** | — |

**The state of the art in published research is 28% on a behavioural measure.** The best tool
against planted ground truth reaches F1 47%. **Nobody is near "fixed", and nobody publishes the
strict number at all.**

**And the same paper reproduces our own null.** Adding a third context type *underperformed* two by
0.72 points: *"more context is not always beneficial… additional context can redirect attention
away from recoverable issues."* Our hunk expansion moved nothing, and the field found the same
thing on a different language and corpus. → `arxiv 2606.01859`

A second 2026 result states the mechanism: context augmentation *"is not merely a retrieval problem
in which higher contextual recall necessarily leads to better review quality. Even when useful
context is successfully retrieved, the model may still fail to prioritize or exploit it."*

**That is the generation failure named from outside.** Retrieval is solved well enough; using what
was retrieved is not.

## So the answer to "is it fully fixable" is no, and the plan is not a fix

**What is fixable is one specific unknown**, and it is the only mechanism with published evidence
that this project has never been able to test.

## The corpus that unblocks execution grounding

Step 0 failed on the pool we have: of 16 semantic wrong findings, **44% are claims about test
files** — the suite that would adjudicate is the subject of the claim — **19% are about
configuration no test imports**, and only **31%** touch source a suite runs. Two coverable correct
findings is not a population.

**What is needed, stated as a specification rather than a wish:**

| property | requirement | why |
|---|---|---|
| subject | findings about **source**, not tests or config | a suite cannot adjudicate its own assertion |
| coverage | the named lines are executed by an existing test | measured at selection, not assumed |
| size | **≥ 15 correct findings**, not 7 | so a hard stop is a bar and not a coin flip — see the cost table |
| labelling | one person who did **not** write the definition | design 14's judge agreed with a careful rater on 34.9% |
| corpus | repositories whose suite runs green at the base commit | check 1 passed 23/23 here; keep it |

**This is the fifth time the hand-labelling debt has come up and the first time it buys something
named.** Previously it was a general obligation. Now it is: *the only untested mechanism, and this
is the instrument it needs.*

## What a PASS would and would not mean

**Would:** establish that execution grounding **transfers** from vulnerability discovery against
library source — where its published results come from — to pull-request review. That is a new
result, not a confirmation of a known one.

**Would not:** move the yield. **12 correct of 207 stands**, and a filter that adjudicates the
semantic class more accurately still only removes. The 16.7% perfect-filter ceiling is unchanged.

**And it starts against a hostile prior**: our own execution arm inverted at p = 0.001 controlling
for length. The explanation — that the design selected for the model's capacity to author a proof
rather than for the defect being real — is itself untested, and this corpus is what would test it.

## Cost, honestly — and the first version of this section was wrong by 3x

**It said "~200 findings by one independent rater. Days, not hours."** At the pool's 5.8%
correct-rate, 200 findings yields **11.6 correct** — which is the pool we already have, and the
size that collapsed to 2 coverable at step 0. **The spec required 30 correct and the cost stated
would have produced 12.** The arithmetic was never done.

Done now. The correct-count requirement drives everything linearly:

| correct needed | findings to grade | pull requests | hours at 6 min each | null predicts lost |
|---|---|---|---|---|
| 10 | 172 | 136 | **17** | 6.0 |
| **15** | **259** | **204** | **26** | **9.0** |
| 20 | 345 | 272 | 34 | 12.0 |
| 30 | 518 | 407 | 52 | 18.0 |

**Thirty correct findings is 518 hand-graded findings across 407 pull requests — around 52 hours,
which is a fortnight of one person, not "a few days".**

### Why 15 and not 30

The bar exists to distinguish *"it loses correct findings at the same rate as wrong ones"* from
*"it loses far fewer"*. At a 60% wrong-drop rate:

- **7 correct** — the null predicts 4.2 lost; observing 1 is suggestive and not decisive. This is
  exactly where the last arm landed.
- **15 correct** — the null predicts 9; observing ≤ 2 is decisive.
- **30 correct** — the null predicts 18; more power than the question needs.

**15 is the smallest number that answers the question**, and it halves the spend to ~26 hours over
259 findings. Stated as the recommendation; 30 is available if the result has to survive a hostile
reading.

### The 3x saving that makes even this affordable

**Select the corpus for coverage BEFORE adjudicating, never after.** Only 31% of semantic findings
were about source a suite touches. Grading a random pool and filtering afterwards needs
15 / (0.058 × 0.31) = **835 findings**. Selecting first needs **259**.

That selection is mechanical — a pull request touching source files whose modules have tests — and
it is the difference between a fortnight and two months.

## What NOT to do, on the evidence

**Do not add context.** Two independent 2026 results and our own hunk-expansion null all say the
same thing, and one of them measured it going backwards.

**Do not build another filter.** Nine have been built. The best of them — the conversational
architecture — drops 40% of wrong findings for 1 of 7 correct, and the correct-rate is unmoved
because a filter selects from what was generated.

**Do not quote a behavioural precision beside a truth-adjudicated one.** That rule was already
written and this project broke it again this week.
