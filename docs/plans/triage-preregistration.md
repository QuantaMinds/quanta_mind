# Pre-registration — the model as triager of a sound analyzer's alarms

**Written before the harness exists.** Four fixes failed with the model as the finder, at a 7.2%
base rate a filter cannot exceed. The literature's working systems all invert the roles. This tests
whether that inversion holds on our corpus.

## Setup

| stage | who does it |
|---|---|
| which units to examine | the **ranker** — top 3 by prior fix history |
| candidate generation | **`ruff`**, defect-oriented rules only (`F`, `B`, `S`, `ASYNC`, `PLE`, `RUF`) — no style, no formatting |
| triage | the **model**, one alarm at a time, with the enclosing function |
| adjudication | blind raters, same rubric, same bar |

**Population: the same 20 unseen pull requests** the reviewer scored 82.1% wrong and 77.8% wrong on.
Same corpus so the comparison is against a measured number, not a remembered one.

**`mypy --strict` is excluded and the reason is recorded**: it needs the whole project and its
installed dependencies, and on a single file pulled from a foreign repository it emits import
errors rather than type errors. Using it here would measure our setup, not the method.

## What is measured

| quantity | why |
|---|---|
| **alarms raised** in the funded units | whether a sound analyzer finds anything there at all |
| **kill rate** — alarms the model rejects | the literature reports 79–98%; a wildly different number means our setup differs from theirs |
| **wrong-rate among PROMOTED alarms** | the decision |

## The bar, unchanged

**Under 50% wrong among promoted alarms**, blind adjudication. The same threshold every review-half
test has been held to.

## What each outcome means

**Clears the bar** — the asymmetry holds on our corpus. The model cannot find defects but can
triage them, and the review half has a design worth building: ranker picks the units, analyzer
finds candidates, model triages, parser verifies.

**Fails the bar** — the asymmetry does not transfer, and the honest conclusion is that this model
is unreliable about this code in *either* role. That would close the review half completely rather
than redirecting it, and it is the more decisive outcome of the two.

**No alarms raised in the funded units** — a real possibility and it is not a null. It would mean
the ranker points at code a sound analyzer has nothing to say about, which is informative about the
*ranker*: the units that attract later fixes are not the units that fail lint. **Report it as a
finding about the ranking half, not as a failed run.**

## Stated so it cannot be claimed afterwards

**A high kill rate is not success.** If the model rejects 95% of alarms and the 5% it promotes are
still mostly wrong, that is the same failure with fewer comments. **The number that decides is the
wrong-rate among what survives, not how much was discarded.**
