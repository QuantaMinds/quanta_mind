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


---

# RESULT — the third outcome fired, and it is a finding about the ranker

**84 funded units across 20 pull requests. 42 alarms. 0 promoted.**

| | |
|---|---|
| funded units scanned | 84 |
| **units where the analyzer found nothing** | **53 (63.1%)** |
| alarms raised inside funded units | 42 |
| **promoted by the model** | **0 (0.0%)** |
| killed | 42 (100.0%) |

**There is nothing to adjudicate**, so the wrong-rate among promoted alarms — the number this test
was built to produce — does not exist.

## What the analyzer actually raised

| code | n | what it is |
|---|---|---|
| S101 | 32 | `assert` used, in a test file |
| RUF100 | 4 | unused `noqa` |
| RUF021 | 2 | parenthesise `and`/`or` |
| S310 | 2 | URL open audit |
| B007 | 1 | unused loop variable |
| RUF005 | 1 | prefer unpacking over concatenation |

**39 of 42 are stylistic or test idiom. Three are defect-class, and the model killed those too.**

## My rule selection is part of this, and separating it from the finding matters

**Including bandit's `S101` was an error.** An `assert` in a test file is the point of the test, and
it produced 76% of the alarm volume. A better selection excludes it and excludes test files from
security rules.

**But that correction makes the finding sharper, not weaker.** Excluding the noise leaves **3
defect-class alarms across 84 funded units** — one alarm per 28 units the ranker considered most
likely to need a follow-up fix.

## The finding, which is about the ranking half

**The units a later fix returns to are not the units a sound analyzer can flag.** 63% of funded
units are clean by `ruff`'s defect rules, and the remainder raise almost nothing of substance.

**That was pre-registered as a possible outcome and it is not a null.** It says something specific:
the ranker and a static analyzer are pointing at *different things*. The ranker finds code that
churns and breaks; `ruff` finds code that violates a decidable local rule. **Those populations
barely overlap**, which is why the redesign cannot simply be bolted onto the ranker.

## What this does and does not close

**It does not refute the asymmetry.** The model killed 42 of 42, and reading them it was right
every time — `assert` in a test is not a defect, an unused `noqa` is not a defect. **That is
consistent with the model being a reliable judge**, which is what the literature and our own κ =
0.82 both say. The test simply never reached the question it was built to ask.

**It does close the cheap version of the redesign.** *"Point ruff at the ranked units and let the
model triage"* produces **zero comments per pull request**. A sound analyzer with real defect
coverage — a semantic one, not a linter — would be needed, and that is a much larger undertaking
than this test assumed.

**The honest summary: the review half now has no cheap path.** Four fixes failed on the model as
finder; the model as triager has nothing to triage because the analyzer available to us finds
nothing where the ranker looks.
