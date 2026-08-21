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
