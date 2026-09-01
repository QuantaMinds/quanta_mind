# Churn is a worse target than fixes — the reframe is dropped

**Pre-registered reading, fixed before the run:** *higher lift against churn means a cleaner target
and a cleaner label; lower means the reframe is wrong and it is dropped.*

## The harness reproduced the published figure first

`fix_90d` came back at **1.21% against 3.12% on 2,400 events** — the number in
`implementation.md` and `defect_return_external.json`, from a reimplementation that shares no code
with the original beyond the commit reader. **The known-answer check passed before any new arm was
read.**

## Result

Same six out-of-sample repositories, same window logic, same budget, same tie-skip, same
alphabetical control. **The only variable that moved is the outcome.**

| outcome | ours | alphabetical | ratio | gap | discordant b:c | McNemar p |
|---|---|---|---|---|---|---|
| **fix, 90 days** | **1.21%** | **3.12%** | **2.58×** | **1.91 pt** | 62:16 | 1.5e-07 |
| churn, 30 days | 0.62% | 1.12% | 1.81× | 0.50 pt | 17:5 | 1.7e-02 |
| churn, 14 days | 0.96% | 1.79% | 1.86× | 0.83 pt | 26:6 | 5.4e-04 |

**The lift is lower against churn on every reading** — ratio, absolute gap, and the count of
discordant pairs that carry the test. Both churn arms are still significant, so the ranker does
predict churn; it predicts fixes **better**.

## What this says about the label, which is the opposite of what was assumed

The reframe rested on the fix-word filter being contamination — *"a rewrite is a rewrite, so
filtering on intent only costs precision."*

**Filtering on the fix-word raises the ranker's relative advantage from 1.86× to 2.58×.** If the
filter were noise, removing it would leave the lift alone or improve it. It does neither.
**Whatever the fix-word selects for, the ranker predicts it better than it predicts rewriting in
general.**

That is a partial defence of a proxy this project has been sceptical of all week — and it arrived
from a study designed to replace it.

## The honest caveat

**Both arms miss less under churn because the churn target is larger**: over 30 days most files in
an active repository are touched again, so more of the top three lands on a target by construction
and there is less room for either ordering to differentiate. **The ratio is the fairer comparison
than the gap for that reason**, and it points the same way.

The degenerate extreme is visible in the per-repository table: `ansible` at 30 days scores
**0.00% against 0.00%** — the target swallowed the change and the comparison measured nothing
there.

## What is dropped and what is not

**Dropped:** churn as a replacement outcome variable. It is a worse target on this design and the
pre-registration said so in advance.

**Not dropped:** the label's contamination is still real and still unquantified at the file level.
This says the fix-word filter carries signal, not that the label is clean. Those are different
claims, and the second still needs an independent label — which is what Jira and Datadog were
always for.
