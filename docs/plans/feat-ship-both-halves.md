# Shipping both halves — what it takes, and the one measurement that decides it

**Decision taken 2026-08-23: both halves ship.** This plan says what that costs and what is still
unmeasured, so the client engagement is not the place we find out.

## Half A — the gap nobody had named: the webhook does not review

**`serve/run_endpoint.py:work()` logs and returns.** It prints `NOT REVIEWED: no pipeline is
attached to this callback` and does nothing else. Half A works through the CLI (`quantamind look`,
`retrospective`); through the webhook it authenticates, refuses replays, answers 202 — and reviews
nothing. AGENTS.md has always said so; I had been reporting "merged and running" without the
qualifier, which was true of the CLI and false of the endpoint.

**This is the single biggest gap between the measured asset and a sellable product**, and it is
larger than anything on the reviewer side. The pieces all exist — `review()` ranks and renders,
`ingest/github_comments.post()` writes idempotently keyed on head SHA, `ingest/diff.changed_files()`
reads the file list. What is missing is a clone at review time and the join between them.

A `working_clone.py` for the first half of that was written and then deleted rather than left
unreferenced: it would have implied a delivery path that does not exist. **Build it when the join
is built, not before.**

## Half A's evidence — and the client's tools upgrade it

Merged and running through the CLI. `serve/run_review.py:review()` is rank → render, model-free, with a firing
forecast computed from the customer's own history.

**Jira and Datadog belong here, not on the reviewer.** The ranker is currently validated against a
proxy — *a later commit whose message matched a fix-word touched this file* — and **85.3% of
admitted events are not genuine repairs.** Datadog incidents are the outcome itself, not a proxy.
Jira bug-links are a second label that does not depend on commit-message wording at all. **The
founding correlation test died on a proxy (RR 1.040)**; an independent label is precisely what
stops that recurring. → `docs/product/jira-datadog.md`

## Half B — the code exists; three things are missing

`infer/gemini.py`, `verify/anchor.py`, `serve/deep_review.py` — reachable only via a suppressed
`--deep` flag and **not in the webhook path**. What it does today: the model reads only the ranked
files, and a finding publishes only if its quoted code is provably in the added lines.

What is missing, in the order it blocks shipping:

### 1. A judge that clears its bars — this is the whole blocker

| judge | discarded | precision | F1 | verdict |
|---|---|---|---|---|
| target (`why-their-f1-is-higher.md`) | ~85% of FPs | 64.7% | 61.0% | — |
| gemini-2.5-pro, same family | 98 of 464 (21%) | 28.0% | 37.3% | **FAIL** |
| gemini-2.5-flash, same family | 137 of 464 (30%) | 26.7% | 34.4% | **FAIL** |
| **different family** | — | — | — | **NEVER RUN** |

Both failures are same-family, which is the *weak* case — a judge sharing the subject's blind spots
keeps false positives it happens to agree with, so **what they discarded is a floor.** The
different-family arm is the one thing this project has argued for and never measured.

**It requires Anthropic models enabled on Vertex in `quantamind-oss`.** A probe on 2026-08-23 was
inconclusive: every request returned 404, but the control request to a Google model returned 401,
so the instrument was broken and the 404s mean nothing. **Re-run the probe with working auth before
concluding anything about availability.**

### 2. The generator cannot be asked to do the judge's job

Three prompt arms failed. Asked to keep only what it would defend, the model deleted three-quarters
of its findings and retained **8.5–16.8%** of the available discrimination. Five prompt levers have
now moved nothing. **Do not spend another arm here.**
→ `docs/plans/preregistrations/reviewer/prompt-direction-preregistration.md`

### 3. Jira context will not rescue it, and the record says so before we try

The wrong findings are `EXTERNAL` (28 of 45 — needs a fact the diff cannot supply) and `TRACE` (17
— the model read the code and got it wrong). **A ticket describing intent settles neither.** It is
the same shape as a conventions file: prose appended to a prompt, and both nearest precedents
failed. If tried anyway it is design fifteen, pre-registered, with those two nulls as the prior.

## What ships if the different-family judge fails too

Half B still ships, in the only configuration the evidence supports:

- **off by default, opt-in per repository** — never a silent upgrade
- **at most one finding per pull request**, the highest-confidence anchored one — the volume/
  correctness relationship is measured and ours is flat, so more output buys nothing
- **the comment states the base rate** — raw findings are 66.7–82.1% wrong across four blind pools,
  and a customer reading a finding is entitled to that number
- **every discard counted**, `raw` / `anchored` / `unanchored`, never a silence

**This is a defensible product and an unusual one: a reviewer that tells you how often it is
wrong.** It is not a defensible *default*, which is why it is opt-in.

## Bars, fixed here

The different-family judge ships only if, on a corpus it was not built on:

- it discards **≥ 60%** of false positives, and
- keeps **≥ 80%** of true positives, and
- the resulting precision clears **50%** — the bar the review half failed seven times

A near-miss is a fail. An interval spanning a bar is INCONCLUSIVE and does not ship.

## Order of work

1. Re-run the Anthropic-on-Vertex probe with working auth *(blocked: `gcloud auth login`)*
2. If reachable — run the different-family judge against the stored 464 candidates, bars above
3. Wire `deep_review` into the webhook path behind a per-repository opt-in, regardless of outcome
4. Jira/Datadog ingestion as **ranker validation**, on the client's repository

**Step 3 does not depend on steps 1–2.** The opt-in reviewer with anchoring and honest counts is
shippable now; the judge decides whether it is on by default, not whether it exists.

## What could still silently fail

The anchor check proves a quoted line is in the diff. **It does not prove the claim about that line
is true**, and 0 of 45 wrong findings were refutable by a parser. Anchoring is a filter on *form*,
and form does not predict truth — measured, null, `research/phase0/quote/form_vs_truth.py`. Nothing
in this plan changes that; the judge is the only thing that would.
