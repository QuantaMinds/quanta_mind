# The firing rule does not implement the firing claim

**Found end-to-end on a live TypeScript repository before a client demo, not in a unit test.**

## The measurement

`trpc/trpc`, 200 real changes from the last 30% of history, no size filter, scored strictly against
history before each change:

| | |
|---|---|
| `ranking.fired` | **198 / 200 = 99.0%** |
| posted a comment | **198 / 200 = 99.0%** |
| `docs/product/QUANTAMIND.md` claims | **"Fires on 10–12% of changes"** |

## The cause, which the code already admits

`rank/order.py`'s `fires()` decides on **`max(scores) > 0`** — it speaks whenever *any* changed file
has been touched before. On a repository with history that is nearly always true.

**`types/ranking.py` already says so, in the `Score` docstring:**

> **THE PERCENTILE IS NOT USED BY ANY FIRING RULE, AND THIS DOCSTRING USED TO SAY IT WAS.**
> `rank.order.fires()` decides on `max(scores) > 0`; `Settings.threshold_percentile` is read from
> the environment, validated and printed by `quantamind config`, and **governs nothing**.

and:

> an absolute threshold on the top file's score fires at **94.5–99.8%**

**So this was known internally and is measured now on a language and repository the product had
never been run against.** `threshold_percentile` is a setting a customer can set that changes
nothing — the shape of defect this project has a rule about.

## Why it matters more than a wrong number in a document

**"Quiet" is one of the four properties the product claims**, and it is the one that makes the rest
survivable: a coverage line on every pull request is noise, and the pitch is explicitly that we
speak rarely. **At 99% we are the thing we say we are not.** A client running this on their
repository sees a comment on every change in week one.

## What I am NOT doing

**Not tuning the threshold until it reads 11%.** That is fitting a parameter to a sentence, and this
project has a rule about a cap lowered to make it bind. The claim and the mechanism have to be
reconciled by deciding which is right, not by moving a number until they agree.

## The options, and what each costs

1. **Make `fires()` use the percentile it already carries.** Speak only when the top file's score is
   unusual *for this repository*. Self-calibrating, and it is what `threshold_percentile` was
   evidently meant to do. **Risk: an untested rule in the layer that decides what customers see.**
2. **Fire on discrimination, not level.** Speak only when the ranking actually separates — when the
   top file's score is meaningfully above the second. A flat ranking says "we cannot tell you where
   to look", which is precisely when speaking is worthless. **This is the honest version and it
   matches what `Discrimination` already computes.**
3. **Accept 99% and change the claim.** Defensible only if the comment is worth reading every time,
   and at 3.46 useful findings per pull request from human reviewers, a routing line on a two-file
   docs change is not.

## What has to be true before any of this ships

**The firing rate must be measured out-of-sample on a repository the rule was not tuned on**, the
way the ranker itself was. The rate is a product property, not a taste, and it has never been
measured on anything but the corpus it was designed against.

**Nothing in `rank/` changes until this plan is reviewed.** That is the rule for this layer and it
exists because a wrong turn here is a correctness bug, not a style bug.

---

# The five-minute question, answered: it is a bug AND a claim that does not transfer

**"Did the research ever measure this?" Yes. On an arm the product does not ship, with a mechanism
the product does not contain.**

## What was measured

`docs/findings/RETROSPECTIVE_SWEEP_2026-08.md` — eight repositories, **function-level ranking**,
**PCTL≥90** (fire on the top decile of prior touch counts):

| Repository | Fire |
|---|---|
| browser-use | 10% |
| Skyvern | 10% |
| cartography | 11% |
| AGI-Alpha | 11% |
| OpenPipe ART | 12% |
| TabPFN | 12% |

> **The fire rate lands at 10–12% on every repository across an 80× velocity range.** That is the
> percentile doing its job, and it is the property no absolute threshold had.

**So the figure is real and it is not invented.** It is also three things it is not usually quoted
as being.

## One: the mechanism was never built

The measured rule is **a percentile** — the sweep's own heading is *"The firing rule that works: a
percentile, not a threshold"*, and its argument is that an absolute threshold fired on **11% of
cartography and 53% of Skyvern**, which is exactly the failure `rank/order.py` now has.

**`fires()` implements the threshold the sweep rejected, not the percentile it recommended.**
`types/ranking.py` already says `threshold_percentile` "governs nothing". The research answer exists
and was not carried into the code.

## Two: it was measured on the arm that LOST

**The sweep is FUNCTION-level. The product ships FILE-level**, and the canonical document is
emphatic about why: file-level misses **1.22%** of the changes a later fix returns to against
function-level's **8.84%**, *"the file arm is the one that replicated out-of-sample"*, and
*"allocation is file-level everywhere"*.

**The firing rate of the shipped unit has never been measured.** There is no file-level fire-rate
number anywhere in `research/`.

## Three: at PCTL≥90 the number is close to definitional, and the document says so

`QUANTAMIND.md` already carries the caveat: *"Close to definitional rather than discovered — a
percentile threshold fires on a fixed share of its own distribution by construction."* A top-decile
rule fires on about a tenth of its distribution because that is what a top decile is. **The
transferable finding is the CONTRAST — 11% versus 53% for an absolute threshold — not the 10–12%
itself.**

## What this changes

**Building the percentile gate is not "fixing a bug to hit 11%".** It is implementing the rule the
research chose, and then **measuring what rate it produces at file level, on repositories it was not
built from** — because the number that has been quoted belongs to a different unit.

**Whatever comes out is the number, and the claim is rewritten to match it.** If file-level PCTL≥90
fires on 30% of pull requests, the table says 30%.

**And "Quiet" cannot be quoted as a measured property of the shipped product until that exists.**
Today it is a measurement of the function-level arm, produced by a mechanism the code does not have.
That is the sentence that would not survive a client asking how it was obtained.
