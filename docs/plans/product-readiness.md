# Next phase: what stands between a validated signal and a product someone buys

**Status: PLAN.** Ordered by what decides the others, not by what is easiest. The first item can
make items 3–6 unnecessary, so it goes first even though it is the only one that needs a person.

## Tier 0 — the two that decide whether the rest is worth building

### 1. Measure minutes-per-file on binding changes, with one design partner

**Every dollar figure this product has is linear in an assumption nothing has measured.**
`roi-preregistration.md` puts the range at $12k–$41k a year on 200 pull requests a month, and the
only thing moving it is minutes-per-file, assumed at 3, 5 or 10 — a **3.3× span**. Its own closing
line says the first thing a pilot instruments is review time per file, not satisfaction.

**B1 already failed at 28.9% against a 50% bar.** If minutes-per-file comes back low, there is no
product, and that is worth knowing before building a GitHub App.

**AN OSS REPOSITORY CANNOT SUBSTITUTE FOR THIS.** It supplies code and history; the measurement is
of human reviewing time. There is no offline proxy — this is the one item on the list that a
benchmark cannot answer, which is exactly why it is first.

### 2. Re-scope the offer to where the three-file budget binds

**Two thirds of changes touch three files or fewer**, so the budget asks for everything and saves
nothing. On the 34% where it binds: **50.3% of effort saved at a 4.11% miss**, against alphabetical
order's 9.20%.

So the product is **a gate on unusually large changes, silent elsewhere** — not a review assistant.
`ingest/change_shape.py` already computes the "unusually large" test and it is model-free and free
to run. **This is a positioning decision and costs nothing to make.**

**Do not quote "we miss 1.53%" without "because two thirds of the time we ask you to read
everything."** `roi-preregistration.md` names that sentence as misleading to a buyer.

## Tier 1 — a customer cannot install this today

| | what is missing | evidence |
|---|---|---|
| **3** | **A GitHub App.** `ingest/github_comments.post()` shells out to the `gh` CLI, so it comments as whoever ran `gh auth login`. Needs app id, private key, per-installation tokens. **The hardest blocker to "a business can buy it."** | `github_comments.py:114` |
| **4** | **Multi-tenancy.** `settings.database_path` defaults to one `quantamind.db`. One store, one customer — and the touch index is now cached per repository, so tenancy is a correctness question, not a layout one. | `types/settings.py` |
| **5** | **Deployment.** No Dockerfile, no compose, no hosting artefact. `just serve` binds 127.0.0.1. | repository root |
| **6** | **An install flow.** Nothing turns "I clicked install" into a first review: no backfill trigger, no first-run path. **Onboarding latency is now measured** — a full clone plus a 31-second index build on a 115k-commit repository. | `CODEBASE.md`, the touch-index section |

## Tier 2 — real, and cheaper than they look

**7. Turn posting on deliberately.** `POSTING_ENABLED=0` is the right default and flipping it is a
product decision with a per-repository opt-in, not a config edit.

**8. Capture the feedback signal from day one.** Greptile's *only* mechanism that worked is a vector
filter blocking comments resembling downvoted ones — **address rate 19% → 55% in two weeks**. It
needs team feedback history, so it is a post-launch asset. **But the signal must be recorded from
the first review or it cannot be built later.** `store/` already has `lifecycle` and `prod_signal`;
nothing writes reactions to them.

**9. Metering.** `max_requests` bounds a review; nothing meters or bills a tenant.

## What NOT to build

**The reviewer half.** Six framings died; raw findings are **66.7–82.1% wrong**; shape context came
back **NULL** against a corpus noise floor of ±4 points. Greptile reached the same two conclusions
independently — prompt engineering cannot separate findings from nits, and a model rating its own
severity is near-random. → `recorded-not-built.md`.

## Using OSS repositories to test — what they can and cannot do

**They can carry all of Tier 1**, which is most of the engineering:

- install the App on a repository **you own or a fork you control**, end to end
- multi-tenancy, by running two installations at once
- deployment, onboarding latency, backfill, the first-review path
- posting, idempotency on redelivery, and the `pr/` branch and 83,202-ref cases that already broke
  `working_clone` twice — both found by pointing it at real repositories

**They cannot carry Tier 0.** Minutes-per-file is human behaviour. No repository supplies it.

**AND POSTING TO A REPOSITORY YOU DO NOT OWN IS NOT A TEST, IT IS SPAM.** Unsolicited review
comments on someone else's project cost a maintainer their time to triage. Test posting on **your
own repositories or your own forks**, with `POSTING_ENABLED=0` everywhere else — which is what that
default is for.

**A good test set already exists on disk**: flask (small), django (medium), home-assistant/core
(115,776 commits), apache/airflow (release-branch traffic, 83k pull refs), grafana. Between them
they cover every scale and refspec pathology found so far.

## Sequencing

```
1  ──▶ 2  ──▶ 3, 4, 5, 6  ──▶ 7, 8, 9
```

**Items 3–6 are a few weeks of ordinary engineering. Item 1 is the only one that can tell you they
are worth doing** — and it does not need them: a pilot can run the CLI against a partner's clone
and measure, with no App, no hosting and no posting.

**The temptation is to build 3–6 first because they are tractable and item 1 needs a person to say
yes.** That is the same instinct that built `change_shape.py` months before anything consumed it,
and pre-registered `shape_context.py` without ever running it. Tractable is not the same as next.
