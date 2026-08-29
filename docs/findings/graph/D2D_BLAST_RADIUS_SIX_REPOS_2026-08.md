# Blast radius on six unseen repositories — INCONCLUSIVE by the bar, and the shipped signal wins

**Run 2026-08-29 against `blast-radius-preregistration.md`, committed in `c7201eb` before any
repository was cloned. 3,591 events, 1,301 non-degenerate, six repositories the method had never
seen. Rows in `research/phase0/results/blast_six/`.**

## The registered verdict

| | |
|---|---|
| discordant pairs, importers vs alphabetical | **10** |
| pre-registered floor | 20 |
| **verdict** | **INCONCLUSIVE** |

The bar was fixed in advance and it is honoured: fewer than 20 discordant pairs is inconclusive,
reported as such, and **there is no seventh repository**, which is how a null becomes a hunt.

## But this is not the flask problem repeated

| | flask | the six |
|---|---|---|
| non-degenerate events | 79 | **1,301** |
| discordant pairs | 2 | 10 |
| discordance rate | 2.53% | **0.77%** |

**Sixteen times the data made disagreement rarer, not commoner.** The flask run was underpowered.
This one is not: with 1,301 events, ranking by import in-degree produces the same top three as
alphabetical order on **99.2%** of them. **Even had importers won all ten discordant events, that
is 0.77% of the corpus.** The effect is bounded small by the data rather than hidden by it.

## The secondary comparison is decisive, and it settles the build question

| arm | hits | miss rate |
|---|---|---|
| prior fix count (shipped) | 1263 / 1301 | **2.92%** |
| import in-degree (D2a) | 1211 / 1301 | 6.92% |
| alphabetical (control) | 1207 / 1301 | 7.23% |

| comparison | discordant | p |
|---|---|---|
| prior fixes vs alphabetical | 80 (68–12) | **< 0.0001** |
| prior fixes vs importers | 78 (65–13) | **< 0.0001** |
| importers vs alphabetical | 10 (7–3) | 0.34 |

Both were registered as "recorded but not the gate", and both cleared the floor comfortably.

**The ranking claim replicates on six repositories it had never seen.** Fix history beats
alphabetical at p < 0.0001 on 80 discordant pairs — a different corpus and a different metric
from the published 1.21%-against-3.12%, reaching the same conclusion.

**And fix history beats import in-degree just as decisively**, 65 to 13. So the signal D2d would
add is significantly *worse* than the one already shipping, and statistically indistinguishable
from alphabetical order.

## What happens to D2b and D2d

**They stay on hold, and the recommendation is to drop D2d.**

The registered gate says INCONCLUSIVE, so this is not a FAIL and is not written up as one. But
the build decision does not need the gate: a signal that reorders 0.8% of changes, and loses to
the shipped signal at p < 0.0001 when it does, is not worth a `dependency` table, an incremental
watermark, and a line in every comment.

**D2a stays.** It is a working, labelled, tested detector with a measured base rate, and the
import graph is a prerequisite for other questions — D2c duplicated logic, D2e architectural
drift, D3 cross-repo links. What this run rules out is one specific use of it: **in-degree as a
ranking signal for where a fix will return.**

## What this does not say

**Nothing about blast radius as information for a human.** "This module is imported by fourteen
others" may be worth telling a reviewer even if it does not predict the fix-return outcome. That
is a different claim needing a different test, and it must not be smuggled in on this one.

**One outcome definition.** `rank/events.admissible` — 2 to 12 `.py` files, returned to within
ninety days by a fix-shaped commit. A signal can be useless for that and useful for another.

**`encode/django-rest-framework` needed a second attempt**, having failed on `git-lfs: command
not found` with the objects already fetched. The harness reads through `ls-tree` and `cat-file`
and never needs a checkout, so `--no-checkout` fixed it. Recorded because an infrastructure
retry and a result-driven retry look identical afterwards, and only one of them is legitimate.
