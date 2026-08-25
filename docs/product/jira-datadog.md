# Jira and Datadog: the wrong use is as model context, the right use is as outcome data

**Short answer: do not feed Jira tickets to the reviewer. Do connect both — as the outcome variable
this project has never had.**

---

## 1. "Ticket context makes the review better" is attempt fifteen of a class that failed twice

**The class is: give the model more information and hope the findings improve.** It has been run
twice here, both pre-registered, both against the same headline.

| what was added | result |
|---|---|
| **structured context** + parser-snapped anchors (design 2) | **61.1% wrong. FAIL** |
| the repository's **own conventions file** (design 13 arm C) | headline moved nothing; the file *"made the model more cautious, not more accurate"*, and **−12.6 points** on the one hypothesis it was built for |
| hunk expansion — more surrounding code | moved nothing |

**A Jira ticket is the same shape of intervention as a conventions file: prose about intent,
appended to the prompt.** There is no reason from this record to expect it to behave differently,
and the two nearest precedents both failed.

**And the failure taxonomy predicts it will not help where the errors actually are.** The wrong
findings are `EXTERNAL` (28 of 45 — needs a fact the diff cannot supply, mostly whether a pinned SHA
carries a tag) and `TRACE` (17 — the model read the code and got it wrong). **A ticket describing
intent settles neither.** It cannot tell the model what tag `9c091bb2` carries, and it cannot make
it trace a `for` loop correctly.

**If it is tried anyway it must be pre-registered as design fifteen with a bar fixed first**, and
the prior should be the two nulls above.

## 2. What they are actually worth: closing the chain

**The canonical document states the gap plainly:**

> we rank the risky file (**measured**) → the reviewer reads it (**unmeasured**) → they find the
> defect (**unmeasured**) → it never reaches production (**unmeasured**). Only the first link has
> evidence.

**Datadog is the only thing that closes the last link.** Today the ranker is validated against a
proxy: *a later commit whose message matched a fix-word touched this file*. **A proxy is not the
outcome**, however well it is ranked, and that is the whole of the argument — the sentence that
used to stand here was an inversion. Incidents are not a proxy.

**THE INVERSION, RECORDED RATHER THAN QUIETLY DELETED.** This paragraph read *"the firing
precision caps at roughly one in seven — 85.3% of admitted events are not genuine repairs"*.
**85.3% is the ranker's top-1 HIT rate** against a 72.0% null, n = 4,293, 17 of 17 repositories;
one in seven — **14.7% — is its ERROR rate**, halved from the null's 28.0%. The success figure and
its complement were both reported as failures. → `docs/CORRECTIONS.md` entry 11

**What survives without them:** the label carries known contamination — blind labelling put roughly
**86% of symbol-overlap pairs** in the not-a-genuine-repair class, a different population reached a
different way — and a fix-word proxy cannot answer whether anything reached production at all. They are the outcome the customer actually cares about, and
this company has never held one.

**Jira gives a second, independent label.** Pull requests linked to bug tickets are defect labels
that do not depend on commit-message wording at all. **The founding correlation test died on a
proxy (RR 1.040).** An independent label is exactly what would keep that from happening again.

## 3. The on-thesis use, and it upgrades the half that works

**The ranker counts prior fixes per file. Its ceiling is set by the quality of "fix".**

Counting *incident-linked* changes per file, or *bug-ticket-linked* changes, is **the same mechanism
with a better outcome variable** — deterministic, no model, and it strengthens the only claim in
this project that replicated out-of-sample.

That is on-thesis in the strict sense: *if a parser can answer it, a model must not.* A ticket link
and an incident timestamp are parser-answerable. **This is a ranking signal, not a prompt.**

**And it satisfies the product criteria the reviewer fails.** It adds **zero** comments per pull
request and it makes the ranking more accurate rather than less.

## 4. What it costs, stated before anyone builds it

**`pyproject.toml` declares `dependencies = []`.** The HTTP endpoint was written on the standard
library specifically to keep it there. **Jira and Datadog mean OAuth, token storage, refresh, scope
management and two vendor APIs that version independently** — the first real runtime dependencies
this product would take, and the first credentials it would hold beyond a webhook secret.

**The security posture changes.** Today the App is read-only on code and write-only on one comment.
Incident data and ticket contents are customer-confidential in a different way, and a breach of them
is not the same conversation as a breach of a repository we could already read.

**Coverage is partial and must not be assumed.** Not every team links pull requests to tickets; not
every team runs Datadog. **Whatever fraction does is the fraction this signal exists for** — measure
it on the first three customers before designing around it, because a ranking signal available to
40% of customers is an enhancement, not a core mechanism.

## 5. Recommendation

1. **No Jira in the reviewer prompt.** Two prior context interventions failed and the failure
   taxonomy says it targets neither error class.
2. **Connect both as outcome data, during the thirty-day trial.** This is the calibration the plan
   already says is missing, and the trial has to happen anyway. Read-only, no product change.
3. **Then, and only if the labels are dense enough: an incident-weighted ranking signal**, built
   model-free, pre-registered, validated against the existing fix-history ranker on a corpus it has
   not seen. **If it does not beat the current ranker out-of-sample, it does not ship** — the same
   bar the ranker itself had to clear.
