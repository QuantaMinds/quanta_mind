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


---

# THE EXECUTION GATE — 27.8% wrong, the first design under the bar, and the control says why not to believe it yet

**24 pull requests merged 2010–2012, every one past the outcome window, enforced by
`corpus_age.assert_corpus_age` at fetch time.** The model emits a claim *and* a self-contained
snippet that would demonstrate it; the snippet is executed; only `CONFIRMED` is published.

| outcome | n | |
|---|---|---|
| **CONFIRMED** | 18 | published |
| REFUTED | 5 | the model's own snippet contradicted its own claim |
| REFUSED | 5 | snippet attempted I/O |
| CRASHED | 2 | snippet raised |

## The published findings clear the bar

| | published (18) | **killed (12)** |
|---|---|---|
| CORRECT | 11.1% | 16.7% |
| **WRONG** | **27.8%** | **50.0%** |
| UNFALSIFIABLE | 44.4% | 25.0% |
| TRIVIAL | 16.7% | 8.3% |

**27.8% wrong against a 50% bar — the first of six designs to clear it**, after 82.1%, 77.8% and
66.7% on the previous corpus.

## Three reasons not to believe it yet, in order of severity

**1. The separation is not significant.** Published 27.8% against killed 50.0% is **+22.2 points,
p = 0.216**. The gate looks like it works and n = 30 cannot show that it does. The Wilson intervals
overlap heavily: [12.5%, 50.9%] against [25.4%, 74.6%].

**2. The gate discarded half the real findings it saw.** Two CORRECT findings were published and
**two were killed** — the `render_template` signature rename that genuinely breaks callers passing
`template_name=`, and a `fname, fields = fname` unpack that genuinely raises on a non-two-element
spec. **Both were killed by the model writing a bad snippet, not by the claim being wrong.** A gate
that throws away 50% of true findings is not a filter, it is a coin with a good story.

**3. The corpus is easier and that alone could explain the result.** 2010–2012 flask, scrapy and
celery are far simpler than modern vllm and transformers. **This design has never been run on the
hard corpus, and the hard corpus is where every previous design failed.**

## And the number that moved most is not the good one

**UNFALSIFIABLE went from 10–20% to 44.4%.** Nearly half of what is published cannot be decided
from what the reviewer was shown — *"whether `cache` is class-level depends on `__init__`, which is
not shown"*. **That is the wrong-rate converting into undecidability rather than into correctness**,
and an undecidable comment is no more actionable than a false one.

**Counting UNFALSIFIABLE as unpublishable, the useful yield is 2 of 18 findings across 24 pull
requests — 0.08 per pull request.**

## What it does establish

**The interpreter catches self-contradiction for free.** Five findings died because the model's own
demonstration refuted its own claim. That is a real, deterministic, zero-cost class of rejection and
it needs no rater.

**And one flaw of mine is in the numbers:** the snippet screen bans substrings, so it refused
`requests` as a *variable name* and `import os` where it was legitimate — 5 of 30, some wrongly. It
should screen `ast` import nodes, not text.

## The one test that would settle it

**Run the identical gate on the hard corpus** — the 20 unseen pull requests from scikit-learn,
pandas, django, ansible, scrapy and celery where the same model scored 82.1% wrong and zero correct.
Same schema, same gate, same rubric. **If 27.8% is the gate, it survives. If it is the corpus, it
collapses back toward 80%.** That is one run and it is the only way to attribute this number.


---

# THE GATE ON THE HARD CORPUS — **52.4% wrong. FAILS.** And the easy corpus was most of the story.

| | easy 2010–12 (18) | **hard, recent (21)** |
|---|---|---|
| CORRECT | 11.1% | **4.8%** |
| **WRONG** | **27.8%** | **52.4%**, Wilson [32.4%, 71.7%] |
| UNFALSIFIABLE | 44.4% | 14.3% |
| TRIVIAL | 16.7% | **28.6%** |

**52.4% against a bar of under 50%. It fails, and the 27.8% did not transfer.** Easy versus hard is
+24.6 points at p = 0.119 — not significant on these numbers, but the point estimate nearly doubles
and the gate lands on the wrong side of the bar exactly where every previous design did.

## But the gate is not nothing, and this is the one honest positive

Same model, same hard corpus, four designs:

| design | wrong | correct |
|---|---|---|
| line anchors | 82.1% | 0.0% |
| symbol anchors | 77.8% | 2.8% |
| ±10 window | 66.7% | 2.6% |
| **execution gate** | **52.4%** | 4.8% |

**Gate against line anchors on the same corpus: p = 0.0150.** That is the first statistically
detectable improvement any design has produced. **It is real and it is not enough** — 52.4% is
still worse than a coin, and the bar was fixed at 50% before any of this ran.

## What the gate actually buys, and it is not correctness

**TRIVIAL rose from 7.7% ungated to 28.6% gated.** The raters' words:

> *"Two SETTINGS frames are genuinely queued, but they flush in one `_write_to_transport()` write"*
> *"`or {}` does swallow a falsy non-mapping, but an empty list yields the identical result"*
> *"NaN yielding NaT under `errors="raise"` is the documented, comment-stated intent"*

**True, demonstrable, correctly anchored, worth nothing.** Requiring a runnable snippet biases the
model toward claims it *can* reduce to a self-contained program, and those are the small, local,
inconsequential ones. **The gate buys precision by trading away importance.**

**Useful yield: 1 correct finding of 21 published, across 20 pull requests — 0.05 per pull
request.** One comment every twenty reviews.

## And the crash rate says something about the claims themselves

| | easy | hard |
|---|---|---|
| CRASHED | 6.7% | **31.7%** |

**On hard code the model cannot write a demonstration that runs, a third of the time.** A crash is
not a refutation — those 13 findings are undecided, not disproven — but it measures how far the
claims are from being reducible to a program.

## Two caveats on this run, both mine

**It used the pre-fix substring screen.** `execute.py` was corrected to screen `ast` import nodes
after this process had loaded the module, so the 5 REFUSED here still come from the crude version
that wrongly rejected `requests` as a variable name.

**And n = 21 is small.** The Wilson interval [32.4%, 71.7%] spans the bar. This is a failure by
point estimate on a sample that cannot resolve much — which is itself the answer to whether to keep
going.

## The reading

**Six designs, six failures.** 82.1%, 77.8%, 66.7%, 61.1%, and now 52.4% — a real downward trend,
statistically detectable at the ends, and it stops above the bar while the useful yield stays at
roughly one finding per twenty pull requests.

**The review half does not work, and the sequence of attempts is now informative enough to say
why**: every fix that helped did so by narrowing what the model was allowed to claim, and the
narrowing that finally moved the number also emptied it of content.
