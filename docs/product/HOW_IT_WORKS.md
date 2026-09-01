# How QuantaMind works, end to end

**Who this is for:** anyone who wants to understand the whole product — what happens from the
moment somebody wants to pay us, through a developer pushing a commit, to the numbers on the
dashboard. Written for someone who joined this morning. Every claim points at the file that makes
it true, so you can check any sentence here against the code.

**One thing to know before you start.** Most review tools show you what an AI thinks is wrong with
your code. This one is built around a different bet: **a model is unreliable, a parser is not, and
the honest product is the one that says which is which.** Almost everything below follows from
that. When a design here looks over-careful, it is usually because the careless version was tried,
measured, and found to be wrong.

---

## Contents

1. [The one-paragraph version](#1--the-one-paragraph-version)
2. [Money: what exists and what does not](#2--money-what-exists-and-what-does-not)
3. [Getting in: installation and the free tier](#3--getting-in-installation-and-the-free-tier)
4. [A developer pushes a commit](#4--a-developer-pushes-a-commit)
5. [The webhook: is this real, and have we seen it?](#5--the-webhook-is-this-real-and-have-we-seen-it)
6. [Getting the code: the clone](#6--getting-the-code-the-clone)
7. [The filter: what we will even look at](#7--the-filter-what-we-will-even-look-at)
8. [The ranking: where to look first](#8--the-ranking-where-to-look-first)
9. [The budget: how much of that order gets funded](#9--the-budget-how-much-of-that-order-gets-funded)
10. [The deterministic half: rules a parser decides](#10--the-deterministic-half-rules-a-parser-decides)
11. [The AI half, and everything that tries to stop it](#11--the-ai-half-and-everything-that-tries-to-stop-it)
12. [Context: what the change is FOR](#12--context-what-the-change-is-for)
13. [Writing the comment](#13--writing-the-comment)
14. [Publishing: comment, status, check run](#14--publishing-comment-status-check-run)
15. [The store: the audit trail](#15--the-store-the-audit-trail)
16. [The dashboard and the reports](#16--the-dashboard-and-the-reports)
17. [Deployment: three shapes, one image](#17--deployment-three-shapes-one-image)
18. [The guards: what stops us lying to ourselves](#18--the-guards-what-stops-us-lying-to-ourselves)
19. [A worked example, start to finish](#19--a-worked-example-start-to-finish)
20. [What is not built, and what is not true](#20--what-is-not-built-and-what-is-not-true)

---

## 1 · The one-paragraph version

A developer opens a pull request. GitHub tells us. We clone the repository, count how many times
each changed file has needed a later fix, and **rank the files by that count**. We read the top few
carefully and say so; we say plainly which files we did not read. Separately, we check every rule
the team wrote down in their own repository — those checks are done by a parser, are reproducible,
and go into an audit trail. A model reads the top-ranked files too, but **most of what it says is
thrown away** by a series of checks, and what survives is labelled as a model's opinion. We post one
comment, one commit status, and one check run marking violations on the diff. All of it is recorded
so a dashboard can later ask: did the thing we commented on actually get fixed?

---

## 2 · Money: what exists and what does not

**Start here, because it is the most common misunderstanding.**

**There is no billing.** Nothing in `src/` talks to Stripe. The only matches in the source are a
Stripe *key pattern* in `src/quantamind/parse/secret_scan.py` — there to catch a customer
committing one by accident — and a comment in `src/quantamind/serve/webhook_github.py` comparing
GitHub's webhook signature scheme to Stripe's.

`docs/plans/roadmap/product-build.md` marks this honestly: row **B3 (Stripe checkout +
subscription webhooks)** is parked, and says what it waits for — an interactive login that needs a
real terminal, and a `STRIPE_WEBHOOK_SECRET` that is not in `.env`. Row **B7 (bring your own model
key)** is parked with it.

**What does exist:**

- **A published price list** — `docs/product/pricing.md`. Free ($0, up to 10 developers), Team ($29
  per developer / month), Enterprise (from $60). That is a *document*, not a system.
- **A seat check in the code** — `deliver()` in `src/quantamind/serve/review/review_delivery.py`
  reads `installations.entitled(...)` before reviewing. The plumbing that reads an entitlement
  exists; the thing that would sell one does not.
- **Cost accounting** — every review records what it spent, and `quantamind cost --repo owner/name`
  reads it back. We know what a review costs us. We cannot yet charge for it.

**Why say this so loudly:** a plan that ticks "billing" because a price page exists is how a
checklist comes to overstate a product. `docs/engineering/CORRECTIONS.md` is a log of times a claim
in this repository turned out not to be backed by what it asserted, and it is long enough to take
seriously.

---

## 3 · Getting in: installation and the free tier

Today the path in is: **install the GitHub App on a repository.** No card, no plan.

### The App

QuantaMind runs as a GitHub App with an ID and a private key, read from `QUANTAMIND_APP_ID` and
`QUANTAMIND_APP_KEY_PATH`. `src/quantamind/ingest/app_auth.py` signs a JWT with the App key and
exchanges it for a short-lived token scoped to one installation.

**Why an App rather than a personal token:** a token belongs to a person and carries everything
that person can reach. An installation token is scoped to the repositories the customer chose, and
it expires. If ours leaks, the blast radius is the repositories somebody deliberately installed us
on, for an hour.

### The free tier is checked, not advertised

`src/quantamind/verify/qualification.py` decides eligibility at install time from what GitHub says
about the repository:

| rule | value |
|---|---|
| `MIN_STARS` | 1,000 |
| `MIN_CONTRIBUTORS` | 50 |
| `MIN_ACTIVE_DAYS` | 180 |
| `MAX_PUSHED_DAYS_AGO` | 30 |
| `FREE_REPOS_TOTAL` | 40 |

Its own docstring gives the reason: *"every rule here is checkable at install time, so it is
enforced rather than advertised. A published eligibility list nobody checks is a promise; this is a
decision the endpoint can make before provisioning anything."*

It returns **every** rule that failed, not the first. If you are rejected for three reasons you are
told three reasons, so you do not fix one and get rejected again.

### Warming up

`src/quantamind/serve/onboarding.py`. The first review on a repository is expensive: a full clone
plus building the index of which files have historically needed fixes — about 31 seconds on a
115,776-commit repository. Onboarding does it **once, at install time**, so the first pull request
does not wait for it.

---

## 4 · A developer pushes a commit

Somebody opens a pull request, or pushes a new commit to an open one. GitHub sends us an HTTP POST.

**That is the only thing that starts a review.** We do not poll and we do not crawl. If GitHub does
not tell us, nothing happens.

---

## 5 · The webhook: is this real, and have we seen it?

`src/quantamind/serve/listener.py` receives it; `src/quantamind/serve/webhook_github.py` decides
whether to believe it.

### Is it really from GitHub?

GitHub signs every webhook with a shared secret. `verify(secret, body, signature)` recomputes the
HMAC and compares.

**The comparison is constant-time, and a guard enforces it.**
`scripts/guard/runtime/check_constant_time_compare.py` parses this exact file and fails the build
unless the digest comparison uses a constant-time function.

*In simple words:* comparing two secrets with `==` stops at the first differing byte. Somebody who
can time your responses can guess the signature one byte at a time. A constant-time comparison
always takes the same time, so there is nothing to measure. It is a famous mistake, so a guard will
not let us make it.

### Have we already seen this?

GitHub retries, and networks duplicate. Posting the same comment twice teaches a reviewer to stop
reading us.

Every posted comment carries a hidden marker naming the commit it reviewed — visible at the bottom
of any of our comments as `<!-- quantamind:head=... -->`. Before posting, `already_posted(...)` in
`src/quantamind/ingest/publish/github_comments.py` reads the existing comments and looks for it.

*Why a marker in the comment rather than a row in our database:* the thread is the truth about what
was posted. Our database can be a fresh instance, a restored backup, or empty; the comment either
exists on that pull request or it does not.

### What kind of event is it?

`interpret(event, body)` returns **`Review`** (a pull request to review), **`Installed`** (somebody
installed us — go and warm the repository), or **`Ignore`**.

`Ignore` is a *value*, not a silence. That pattern runs through the whole codebase and is worth
learning once: **"nothing to do here" and "something failed and we swallowed it" must never look
the same.**

---

## 6 · Getting the code: the clone

`src/quantamind/serve/working_clone.py`.

**It clones with `--no-checkout`.** We never need files on disk as files; we read them out of git
directly — `src/quantamind/ingest/blob.py` runs `git show <sha>:<path>`. Skipping the checkout saves
time and disk.

**It must never use `--filter=blob:none`.** That flag fetches the commit graph and skips file
contents. It looks like a large speed win and it is a trap: a diff over blobs that never arrived
comes back **empty rather than failing**, so the reviewer reports "no changes here" about a file it
never received.

This happened. `docs/engineering/CORRECTIONS.md` entry 2 records it — the flag was declared
abandoned in a document while it stayed in the code, and two research runs were walked under the
strategy the document said had been abandoned. Now
`scripts/guard/runtime/check_no_partial_clone.py` scans every `git clone` argument list in the
source and fails the build on any `--filter`.

**Every subprocess declares a timeout.**
`scripts/guard/runtime/check_subprocess_timeouts.py` walks every `subprocess.run`, `.Popen`,
`.call`, `.check_call` and `.check_output` and fails if one has none. A clone against an
unreachable host with no timeout hangs forever, and a webhook handler that hangs forever eventually
takes the service down.

---

## 7 · The filter: what we will even look at

Before ranking anything, the change is narrowed:

```python
changed = [name for name in every_file if name.endswith(REVIEWABLE_SUFFIXES)]
```

`REVIEWABLE_SUFFIXES` lives in `src/quantamind/types/change.py`. A pull request touching 130 files
may have only 117 we can review; the rest are markdown, JSON, images.

**That number is printed in the comment**, not hidden — *"This change touches 117 file(s)"* is the
count after filtering.

*Why it matters:* filtering is the first place a product can quietly overstate itself. "We reviewed
your pull request" sounds complete. "We looked at 117 of 130 files and read 3 of those closely" is
the truth, and it is what the comment says.

---

## 8 · The ranking: where to look first

**This is the heart of the product, and the only part with a statistical result behind it.**

### The idea, in one sentence

Files that have needed fixing before tend to need fixing again — so read those first.

### Where the counts come from

`src/quantamind/ingest/history.py` walks git history and returns one `Touch` per (file, commit)
pair. The ranking is a count of those and nothing else.

It derives its data from `src/quantamind/ingest/commits.py` rather than running a second `git log`,
because *"two readers meant two decode policies and two places for the exit code to be forgotten."*

**The exit code genuinely matters:** `git log -p` exits non-zero on a blob-filtered clone and emits
a truncated patch stream. Code reading patch content asserts the exit code, because this defect
voided four separate measurements before anyone noticed.

### How the order is decided

`src/quantamind/rank/score.py` — `order()` turns `{path: prior count}` into a ranked list.

It is a **pure function**: it cannot read the repository, open the database, or call anything. That
is deliberate — it makes this file directly comparable to the research implementation in
`research/phase0/external/defect_return.py`, which is what lets us say the shipped ranker and the
measured ranker are the same policy rather than two things that resemble each other.

**The tie-break is `(-score, path)` and it is not cosmetic.** Ties are common — 4.61% of changes
have every file at zero. Any other tie-break produces a different top three on those changes, which
is a different policy with a different miss rate.

**`discriminate()` names which of three cases the change fell into**, because a ranking over an
all-zero score set is not a ranking — it is alphabetical order wearing a ranking's clothes. That
slice misses far more: **4.46% against 1.21% overall.** The product knows when its ranking is not
really ranking, and says so.

### The evidence

From `AGENTS.md`, and this is the claim the company rests on:

> **top-three-by-fix-history misses 1.21% of the changes a later fix returns to against
> alphabetical order's 3.12% — six repositories the method never saw, n = 2,400, p < 1e-6,
> 6 of 6 positive, 0.05 points from the original eight.**

*In simple words:* if you only read three files, which three? The ranker's three miss about 1 in 83
of the changes a later fix returns to. Alphabetical order's three miss about 1 in 32. Tested on six
repositories the method had never seen, and positive on all six.

**The counterweight, in the same file:** *"The founding correlation test returned NULL (RR 1.040),
killing the earlier product; this one inherits none of it."* An earlier version of this company had
a hypothesis that measured to nothing, and it was killed rather than defended.

### Whether to speak at all

`src/quantamind/rank/order.py` decides how much of the order gets funded and **whether we open our
mouth**. A wrong order misses defects; a wrong threshold buries the customer in noise or goes
silent for a month. Different failures, decided in different places.

**The firing rule is a percentile, not an absolute score.** An absolute threshold fired on 11% of
one repository and 53% of another — the same rule an order of magnitude apart in volume, because a
busy repository's ordinary file outscores a quiet repository's hottest one. Percentiles
self-calibrate to 10–12% across an 80× velocity range.

The module names its own weakness: the percentile is computed against *this change's own* scores,
which on a two-file change is nearly meaningless. A repository-wide distribution would be better,
so `fires()` takes the distribution as an argument rather than computing it, and can be given a
better one without changing the policy.

---

## 9 · The budget: how much of that order gets funded

`src/quantamind/allocate/depth.py` — `plan(ranking, changed)` returns a `Reading`: the paths the
model will be shown, the paths it will not, and **why**. `Depth` names which of three situations
produced the split.

The rule that matters: above the request ceiling, **the review still runs and still reports
coverage; only inference is withheld.**

*In simple words:* an enormous change does not get silently reviewed less. It gets reviewed as far
as the budget goes, and the comment says how far that was.

---

## 10 · The deterministic half: rules a parser decides

This is the half the evidence supports, and it runs on every review.

### The team writes their rules down

A repository declares its standards in `.quantamind/rules.toml`, read by
`src/quantamind/ingest/standards/rules_file.py`:

```toml
[[rule]]
id = "no-eval"
description = "eval turns data into code. A review is a bad place to find out something did."
severity = "high"
check = "forbid_call"
target = "eval"
paths = ["src/", "scripts/"]
```

TOML rather than YAML because `tomllib` is in the standard library and `pyproject.toml` declares
`dependencies = []` — this product installs nothing.

**A rule without a description is refused.** The description is what a developer reads next to a
violation; `no-console-log-in-prod` is a slug, not a reason, and a check nobody can act on is noise
wearing a standard's clothes.

**A rule without a scope is a rule in the wrong place.** "No pandas in the product" is true of
`src/` and false of `research/`. That was found by running these rules over this repository before
declaring them — the pandas rule flagged a research test, correctly by its own terms and wrongly by
the standard it came from.

### What a rule can be

From `src/quantamind/types/standards/rule.py`:

| kind | what it asks | decided by |
|---|---|---|
| `FORBID_CALL` | is this function called? | parser |
| `FORBID_IMPORT` | is this module imported? | parser |
| `NAMING_PATTERN` | do definitions match this pattern? | parser |
| `HARDCODED_SECRET` | does any line look like an issued credential? | parser |
| `MODEL_JUDGED` | anything a parser genuinely cannot answer | a model |

**Provenance is derived, never declared.** A rule cannot claim a parser verified it when a model
did — the field does not exist to be set. That distinction is the whole value of the audit trail: a
parser's verdict can be re-run on the same commit and shown to give the same answer, and a model's
cannot.

### Four outcomes, and three of them look like a pass from outside

`src/quantamind/types/standards/checked.py`:

- **`PASSED`** — the rule ran, the file is fine.
- **`VIOLATED`** — the rule ran and found something. Carries the name and the line.
- **`UNCHECKABLE`** — we could not decide. A TypeScript file against a Python-only check.
- **`DEFERRED`** — a model-judged rule; no parser decided it.

**Only `PASSED` and `VIOLATED` count toward a compliance rate.** If `UNCHECKABLE` counted as a pass,
a JavaScript repository would read as 100% compliant with checks that never ran. This codebase calls
that a *clean zero*, has found it four times, and `AGENTS.md` rule 14 exists because of it.

*In simple words:* "your code is fine" and "we could not check your code" must never print the same
number.

### The one check that is not Python-only

`HARDCODED_SECRET` — `src/quantamind/parse/secret_scan.py` — dispatches **before** the language
gate. Every other rule needs a Python syntax tree; a credential is just a string, so it is caught in
a `.env`, a `.tf`, a CI workflow or a notebook exactly as well as in a module. Those are the files
that leak one most often, and the files the language gate refuses.

**A provider prefix is evidence; entropy alone is a guess.** `AKIA…` is issued by one company in one
format and means one thing. A long random-looking string means nothing on its own — it is a hash, a
checksum, a base64 asset, a UUID, a minified line. So the generic rule needs **both** a
credential-shaped name (`api_key = "..."`) **and** enough entropy, and even then it is the weakest
kind reported.

The placeholder list is the precision: `xxx`, `your-key-here`, `<redacted>`, `changeme`, repeated
characters, and the example keys providers publish in their own documentation. **The first false
positive here costs more than anywhere else in the product** — telling a developer they committed a
credential when they did not is alarming, public, and takes a rotation to disprove.

**The secret never reaches the output.** Only the kind, the line, and a four-character prefix. A
`Checked` row reaches the audit trail, the comment and the customer's database; writing the
credential into any of those would move it somewhere new and make us the leak.

### Organisation-wide rules

`src/quantamind/ingest/standards/inherited.py`. An organisation puts rules in a `.quantamind`
repository it owns — the convention GitHub already uses for `.github` — and every repository
inherits them. A repository may:

- **tighten** a severity — allowed freely, and recorded;
- **loosen** one while still claiming to inherit it — **refused**; the organisation's severity
  stands and the refusal explains how to opt out properly;
- **drop** one entirely with `inherit = false` — allowed, explicit, and **recorded in the comment**.

*Why the asymmetry:* a team holding itself to more than the organisation asks needs nobody's
permission. A team quietly exempting itself is a different act. **A standard that can be disabled
invisibly is not a standard**, so the drop is allowed and made visible rather than forbidden and
worked around.

**A file we could not read inherits nothing, and says so** — which is different from an organisation
that declares nothing. Treating an unreachable file as an empty one would report a repository as
fully compliant at the moment its inherited standards stopped arriving.

---

## 11 · The AI half, and everything that tries to stop it

The part everyone asks about, and the part this product treats with the most suspicion.

### The measured problem

From `AGENTS.md`: **raw model findings are 66.7% to 82.1% wrong**, across four blind pools of
hand-rated findings. Not "sometimes wrong" — that is the measured rate at which a careful human
rater judged a finding not to be a real defect.

Worse: five separate attempts to improve it moved nothing — anchor repair, structured context, a
rejection filter, hunk expansion, and a full reviewer redesign. A sixth, showing the model the human
context behind a change, was run here and **withdrawn**:
`docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`. A control-vs-control replicate showed
two *identical* arms differing more than the treatment did — the result was the pipeline's own
noise.

**So the design question is not "how do we make the model better". It is "what do we let through".**

### What the model is asked

`src/quantamind/serve/review/deep_review.py` runs `src/quantamind/infer/` over the diff
**restricted to the files the ranker selected**. The model never sees the whole change — it sees the
few files history says are most likely to need a fix.

`src/quantamind/infer/vertex.py` is the transport (Gemini on Vertex AI), and it is defensive:

- **The finish reason is read, never inferred.** A reply cut off at the token limit and a reply that
  deliberately said little produce the same short output. This project has already published a
  number that was really eleven truncations.
- **The diff is capped** (`src/quantamind/infer/diff_cap.py`), and the cap is announced.

### Gate 1 — anchoring

`src/quantamind/verify/anchor.py` — `locate(finding, diff)`. Every finding must quote a line that
**actually appears in the added lines of the diff**. If the quote is not there, the finding is
dropped.

*In simple words:* if the model says "line 42 dereferences a null pointer" and no such line is in
what changed, it invented it. A finding the reader cannot locate is a finding they cannot check.

### Gate 2 — the external oracles

`src/quantamind/verify/publishable.py` — `gate(finding, diff)`. Anchoring is free and local; the
oracles cost a network call each, so they run second, over what survived:

- `src/quantamind/verify/external_facts.py` — does that commit SHA exist? What tags point at it?
  (asks GitHub)
- `src/quantamind/verify/releases.py` — was that package version ever published? (asks the package
  index)

**`UNRESOLVABLE` drops the finding.** A claim we could not check is not one we publish. Collapsing
"could not check" into "fine" is exactly what `CORRECTIONS.md` entry 8 records: a verifier that
defaulted the other way **confirmed every false claim it had been built to refute.**

### Gate 3 — the isolated judge, of a different family

The product principle, verbatim from `AGENTS.md`:

> **We do not build a better bug-finder — we build the judge.** Nothing publishes until an isolated
> judge of a DIFFERENT family clears it — a same-family one agreed with a careful rater on **34.9%**.

*In simple words:* asking a model to check its own work does not work. You need a second opinion
from a different model, judging each finding on its own, without knowing what the first concluded.

**An honest caveat.** On the research benchmark the judge is currently `gemini-2.5-pro` scoring
`gemini-2.5-pro` — same family — because the Anthropic publisher is not provisioned on our GCP
project. That is measured rather than glossed: `research/phase0/bench/d6b/judge_family.py` scores
the same candidates against a different family's published verdicts (34.7% theirs, 37.9% ours) and
finds two Gemini judges disagreeing with each other on about 10% of verdicts. The requirement is
**unmet, not unmeetable** — it is one Model Garden enablement away.

### Gate 4 — model-judged rules never touch the compliance rate

If a team writes a rule a parser cannot decide — *"every public function explains why it exists"* —
a model can judge it. But:

- the audit row stays `DEFERRED` **permanently**;
- the verdict becomes a separate type, `Judged`, in `src/quantamind/types/standards/judged.py`;
- it never reaches the database, the compliance rate, or the check-run annotations;
- it renders in its own section, under its own sentence saying a model decided it.

**Every failure path returns `UNDECIDED`, never "met."** Transport error, unparseable reply, or a
quote not in the file — all undecided. *"The model did not answer"* and *"the model said this is
fine"* must never be the same value.

### What actually survives

The comment prints the arithmetic: *"model: 1 finding(s) kept of 1 raw (0 unanchored, 0 refuted,
0 withdrawn)"*. The counts are printed **because** this is the weak half. A number you can check is
worth more than a number you must trust.

---

## 12 · Context: what the change is FOR

`src/quantamind/ingest/context/` reads the human context behind a change.

- `issue_refs.py` finds `#412`, `closes #88`, `owner/repo#5` in the pull request's text.
  **Code spans are blanked first** — a `#412` inside backticks is a code sample, not a reference.
  Found on a real pull request.
- `tickets.py` fetches each referenced issue, capped at 5. Distinguishes *"we could not read it"*
  (our failure) from *"the author named nothing"* (a fact about the change).
- `elsewhere.py` reaches Jira and Slack over plain `urllib` — REST and JSON over HTTPS, so
  `dependencies = []` still holds. Both take the customer's token; neither reads a credential from
  anywhere itself.

### Egress is a decision, not a detail

`src/quantamind/ingest/context/egress.py`. **Reading a Jira ticket and printing it into a GitHub
comment are two different acts.** The second moves the customer's data from a system with one access
list into a system with a different one. A private Slack thread quoted into a pull request is
visible to everyone who can read the repository — who are not the people who could read the channel.

So: **deny by default, per source, and only a literal `true` grants.** A repository opts in per
source in `.quantamind/context.toml`:

```toml
[context]
quote_jira = true
```

`"yes"`, `1`, and a misspelled key all grant nothing — a typo must not open an egress path.
Granting Jira says nothing about Slack. GitHub needs no consent, because the comment is posted to
GitHub quoting GitHub and nothing crosses a boundary.

**An unreadable consent file grants nothing** — the one place in this product where "we could not
tell" and "no" are deliberately the same answer, because the costs of the two mistakes are not
symmetric.

---

## 13 · Writing the comment

`src/quantamind/render/comment.py` assembles it in this order:

1. **The headline** (`render/blocks/headline.py`) — one of four openings. A refusal outranks
   everything: a review that could not run must never open with a verdict on code nobody read. A
   parser's violation outranks a model's finding, because one is reproducible.
2. **What this change says it is for** — the author's own words, quoted
   (`render/context/goal_block.py`).
3. **What changed / does it do what the PR says / will it break anything** — the model's summary.
4. **Things worth fixing** — findings that survived every gate.
5. **This change narrows what other code can use** — public API breaks (`parse/public_api.py`), and
   which registered consumer repositories import the broken symbol (`verify/consumers.py`).
6. **Organisation standards** — anything dropped, refused or tightened.
7. **Standards a parser cannot check** — model-judged rules, labelled as such.
8. **The same logic, already somewhere else** — duplicate function bodies found by
   alpha-equivalence (`parse/duplicate_bodies.py`: same structure, different variable names).
9. **The coverage table** — every file, how much changed, where to look, what was found.

### The rules the comment obeys

`docs/product/comment-golden-rules.md` holds nine, written after reading competitors and real
developer complaints. The ones that shape what you see:

- **Never mention our method.** Not "ranked", not "history", not "budget". A developer waiting to
  merge does not act on our firing rate. Enforced by
  `tests/unit/layers/render/test_never_our_method.py`.
- **A fold is not a cap.** When 66 files collapse into a `<details>` block, the count is stated. A
  truncated list that does not say it truncated reads as a complete one.
- **No diagrams.** A review comment is read in thirty seconds, often on a phone.

*A real correction from this file's history:* the comment once said *"3 of 56 file(s) reviewed; 53
not reviewed"*, which made developers panic — it reads as though 53 files are unreviewed landmines.
It now shows what was read closely, folds the quiet files by directory, and never implies the rest
are dangerous.

---

## 14 · Publishing: comment, status, check run

Three surfaces, deliberately different.

**1 · The comment** — `src/quantamind/ingest/publish/github_comments.py`. The prose review,
carrying the `quantamind:head=` marker so it is never posted twice.

**2 · The commit status** — `src/quantamind/ingest/publish/commit_status.py`, decided by
`src/quantamind/verify/blocking.py`. One line, one state. This is what can block a merge.

**3 · The check run** — `src/quantamind/ingest/publish/check_run.py`. The violations **on the
diff**, at the file and line, in GitHub's review interface.

### What may be annotated, and what may not

**Only a parser's verdict. Never a model's.**

*Why:* GitHub renders an annotation as a fact against a line. There is no room for "we think", and
raw model findings are 66.7–82.1% wrong. A `Judged` record has no path into that module at all.
**The surface where being wrong is loudest gets the half of the product that is reproducible.**

**Only violations.** `PASSED` on every checked line would train a reviewer to dismiss the column;
`UNCHECKABLE` is a statement about *our* coverage rather than their code.

**The customer's severity decides.** `HIGH` fails the check; `MEDIUM` and `LOW` do not. Deciding for
ourselves which of a team's standards blocks a merge would override the judgement their rules file
exists to record. A rule we cannot find is skipped rather than given a default level — inventing a
severity puts a level on somebody's diff that nobody chose.

**The 50-annotation cap is announced.** GitHub accepts fifty per request; a run with more says how
many were not shown.

**`POSTING_ENABLED=0` rehearses.** Every write path can run without writing, and reports what it
would have done.

---

## 15 · The store: the audit trail

`src/quantamind/store/` — SQLite, one database per tenant (`store/tenancy.py`). Tables in
`store/tables.py` include `repo`, `review`, `ranked_unit`, `rule_check`, `finding`, `claim`,
`unresolved`, `outcome`, `reaction`, `lifecycle`, `prod_signal`.

### Why it exists

A compliance team does not want to be told "you are compliant". They want **every check, with the
commit that lets them re-run it.** `rule_check` carries a `provenance` column, and that column is
what makes the trail worth reading: a `parser` row can be re-run on the same commit and shown to
give the same answer; a `model` row cannot.

### Applying a standard and recording it are one job

`enforce()` in `src/quantamind/verify/rule_check.py` does both. Separating them is how a trail comes
to hold fewer checks than ran: the recording half is easy to forget at a call site and impossible to
notice afterwards, because a missing row and a check that never happened look identical.

### The export

`quantamind compliance --repo owner/name --export trail.json`
(`src/quantamind/store/audit/export.py` + `src/quantamind/render/audit_export.py`).

JSON rather than CSV, and **the caveats are the reason**. A CSV opens more easily and cannot carry
the four sentences that make the document honest:

1. nothing is backfilled;
2. an absent row means the check did not run;
3. `uncheckable` and `deferred` are **not** passes;
4. only a `parser` row re-runs.

**`limits` comes first in the file**, so a reader who stops after the first object has read the part
that stops them over-reading the rest.

**The window is read from the rows, never assumed.** The trail begins when rule checking was
installed, not when the repository was created. An export implying otherwise would be the most
dangerous document this product can produce. An empty export is a document, not an error, and it
says it covers nothing.

### Cost

`src/quantamind/store/costs.py` — every review records requests and tokens; `quantamind cost` reads
them back. When part of a review's cost was never metered it says so, rather than writing a floor as
a total: *"cost not recorded — part of it was never metered, and a floor written as a total would be
priced from."*

---

## 16 · The dashboard and the reports

`src/quantamind/serve/web/` — sign in with GitHub OAuth (`routes.py`, `signin.py`), then read a
repository's report.

The dashboard answers the question the comment cannot: **did any of this matter?**

`src/quantamind/render/dashboard.py` renders `store/lifecycle.py` — for each thing we commented on:
did the pull request merge? Did a later fix come back to that file? `prod_signal` is where an
incident or a rollback attaches.

**It states when the numbers cannot yet be read as a rate.** A dashboard showing "100% accurate"
over four reviews is worse than one showing nothing.

Everything available from the command line today:

| command | what it answers |
|---|---|
| `quantamind review <clone>` | rank one change and print what we would say |
| `quantamind compliance --repo R` | every declared rule and what happened to it |
| `quantamind compliance --repo R --export F` | the whole trail as an auditable file |
| `quantamind cost --repo R` | what the reviews spent |
| `quantamind dashboard --repo R` | what we commented on, and what became of it |
| `quantamind standards --repo R --pulls N…` | what reviewers said more than once |
| `quantamind retrospective` | replay the ranker over a repository's own history |
| `quantamind serve` | the webhook endpoint |
| `quantamind config` | the resolved configuration |
| `quantamind migrate` | bring an existing store up to this build's schema |

---

## 17 · Deployment: three shapes, one image

`src/quantamind/types/deployment.py`, with operator documentation in
`docs/engineering/DEPLOYMENT.md`.

| shape | who runs it | may reach |
|---|---|---|
| `cloud` | us | everything |
| `on_prem` | you, inside your network | everything except Google's metadata server |
| `air_gapped` | you, with no egress | **the clone, and nothing else** |

**Air-gapped refuses; it does not merely fail to connect.** A deployment that simply has no route
produces timeouts and a late review, and the customer finds the attempt in their egress logs while
we never see it. **An outbound call that fails quietly in a bank is a finding against us, not a
bug.** So `permit(destination, shape)` is called *before* the socket opens and refuses by name,
saying what is permitted.

**The clone is the boundary, not an exception.** With no repository there is nothing to review, so
refusing it would be an off switch rather than an air gap.

**An unrecognised shape refuses rather than defaulting to `cloud`** — reading a typo as the
permissive shape is how a misconfigured air-gapped deployment starts reaching the network.

`scripts/guard/runtime/check_network_chokepoint.py` fails the build if any module opens a socket or
runs a networked git subcommand without asking first — nine call sites today, and nine chances to
forget one otherwise.

---

## 18 · The guards: what stops us lying to ourselves

**This is the part of the codebase people find strangest, and the part most worth understanding.**
A guard is a script that fails the build when a claim in the repository stops being true. Nearly
every one was added *after* something went wrong.

`just check` runs them all. If it is red, nothing else matters.

### Structure and convention

| guard | what it does |
|---|---|
| `check_structure.py` | ≤200 lines per source file, ≤15 files per directory |
| `check_conventions.py` | layering, module docstrings, banned name tokens, `FORBIDDEN` pairs |
| `check_module_identity.py` | no two files with one name; no unreferenced modules |
| `check_branch_name.py` | branch naming; `fix/` must name an issue |
| `check_work_on_main.py` | no uncommitted changes or unpushed commits on `main` |

**Why a 200-line cap:** a file you cannot read in one sitting is a file whose invariants live in
somebody's head.

**Why banned tokens** (`util`, `utils`, `helper`, `manager`, `common`, `misc`, `base`, `core`,
`data`, `stuff`): they hide missing abstractions. A file called `utils.py` is a file nobody decided
the purpose of.

**The layering rule** is `types → store → ingest → parse → rank → allocate → infer → verify →
render → serve`, imports going left only — plus a named pair the ordering cannot catch: **`verify`
may not import `infer`**, so the layer adjudicating the model's claims cannot call the layer that
makes them.

*That rule is a story worth telling.* For months `AGENTS.md` claimed the layer order "is what stops
`verify` importing `infer`". It did not — `infer` sits to the *left* of `verify`, so the import was
legal and the guard waved it through. The rule was true as an intention and false as a claim, with
a `→ guard` pointer beside it that made it look enforced and **stopped anyone checking**. It is now
enforced by `FORBIDDEN`, with a known-answer test in
`tests/unit/guards/test_forbidden_layer_pairs.py`.

### Tests and evidence

| guard | what it does |
|---|---|
| `check_assert_quality.py` | fails a test that asserts nothing, or only truthiness |
| `records/check_burned_corpora.py` | a repository used to measure something may not be reused |
| `records/check_schema_shape.py` | hashes the database DDL; a change must be deliberate |
| `records/check_plan_state.py` | the plan's module counts must match the filesystem |
| `records/check_stage_table.py` | three places recording progress must agree |

**`check_assert_quality` is the sharpest.** From `AGENTS.md` non-negotiable 1:

> **A green test is not a verified test.** A test that only proves "no exception was raised" is a
> silent failure waiting to ship.

*In simple words:* a test that calls a function and checks nothing passes forever, including after
the function starts returning garbage.

**Why burned corpora matter:** measure a method on the repositories you used to design it and you
measure your own memory. `check_burned_corpora` tracks which repositories have been spent.

### Documents and claims

| guard | what it does |
|---|---|
| `citations/resolve.py` | every citation in prose must point at something that exists |
| `citations/identity.py` | `docs/` may not hold two files with one name |
| `citations/freshness.py` | a figure marked `re-check <Month YYYY>` must be re-checked |
| `records/check_no_vague_refs.py` | a section number or a phase number is refused — name a file, function or heading  <!-- no-vague-refs:allow — the banned forms are spelled out below, marked, so the rule can show what it bans --> |
| `records/check_documented_commands.py` | a documented command must actually run |
| `records/check_documented_recipes.py` | every `just <recipe>` and `quantamind <subcommand>` in the docs must exist |
| `records/check_withdrawn_amendments.py` | a withdrawal must name the check that enforces it |
| `records/check_docs_sync.py` | a behaviour change must touch `docs/engineering/CODEBASE.md` |
| `check_enforcement_map.py` | every rule's `→ guard:` pointer must resolve, both directions |
| `records/check_decided_vocabulary.py` | once a decision is taken, the losing term stops appearing |

**Why `check_no_vague_refs` exists:** numbers break silently. Insert one heading and every citation
by section number points somewhere else, no test fails, and the sentence still reads correctly.
Eight such references were dangling when the rule was written. Both banned forms, with the marker
that lets the rule show what it bans:

    §7's gate  →  name the file and quote the heading text      no-vague-refs:allow
    Phase 0    →  name the experiment, not the period           no-vague-refs:allow

**The marker is counted and printed on every run**, so it is not a silent exemption — writing about
a banned form requires writing it, and the escape hatch is visible in the guard's own output.

**Why `citations/resolve` exists:** `CORRECTIONS.md` entry 1 — a protocol file was cited by path
*and section number* as established policy. The file had never been committed. Neither had the
section. **A citation to a document that was never written reads as established authority and gets
acted on.**

**Why `citations/identity` exists:** the corrections log itself ran as two files for eighteen days,
and the copy left behind declared the other's entries fabricated. Twenty-five citations resolved to
the wrong file, all green.

### Runtime behaviour

| guard | what it does |
|---|---|
| `runtime/check_no_partial_clone.py` | no `--filter` on a git clone |
| `runtime/check_subprocess_timeouts.py` | every subprocess declares a timeout |
| `runtime/check_constant_time_compare.py` | the webhook HMAC is compared in constant time |
| `runtime/check_network_chokepoint.py` | no outbound call without asking the deployment shape |

### And one rule with no mechanism, marked honestly

`AGENTS.md` rule 6 — "one public concern per module" — is tagged **ADVISORY**: *"no mechanism.
Judgement call, caught in review or not at all."*

**That honesty is the point.** A rule naming a guard that does not enforce it is worse than a rule
naming none, because the pointer is what stops anyone checking.

### Sabotage: how we know a guard works

A guard that has never fired might be working or might be broken — the output is identical. So
guards are tested by **deliberately breaking the thing they check** and confirming a *named* test
fails.

This is not theatre. In one session, of four new gates sabotaged, **two disabled cleanly with no
test failing.** `AGENTS.md` rule 14 puts it directly:

> **Ask what a check outputs when the thing it checks is broken. If the answer is "the same thing",
> it is not a check.**

---

## 19 · A worked example, start to finish

**Every path in this section is invented.** `acme/payments`, `billing/charge.py` and the rest are an
illustration, not files in this repository — which is why the lines naming them carry the citation
guard's marker. <!-- citation:allow — the example repository and its files are fictional by
construction; a citation guard resolving them is the guard working, and AGENTS.md marks its own
citation-shaped example the same way -->

A developer at Acme opens pull request #57 on `acme/payments`, changing 8 files.

**1 · Webhook.** GitHub POSTs to `/webhook`. The signature verifies in constant time. No existing
comment carries `quantamind:head=<this sha>`, so this is new work → `202 Accepted`.

**2 · Clone.** `acme/payments` is cloned with `--no-checkout` using an installation token that
expires in an hour.

**3 · Filter.** 8 files changed, 6 with a reviewable suffix. The 2 markdown files are out.

**4 · Rank.** History says the charge module has needed 14 later fixes, the refund module 6, the
routes module 2, and three files have never been fixed. Order: charge, refund, routes, then the
three zeros alphabetically.

**5 · Fire?** The top score sits in this change's top decile → yes, speak.

**6 · Budget.** The top three are funded for a deep read. The other three are named as not read.

**7 · Parser rules.** Acme declares four rules. Six files against four rules, minus rules scoped
elsewhere, gives 24 checks. `no-eval` fires at line 88 of the charge module — `HIGH`. All 24 rows go to
`rule_check` with `provenance = parser`.

**8 · Secrets.** `secret_scan` runs on all 6, including files a Python parser could not read.
Clean.

**9 · Model.** Gemini reads the diff of the three funded files and returns 5 findings.
Anchoring drops 2 — their quotes are not in the added lines. The SHA oracle refutes 1 — the commit
it names does not exist. The judge clears 2. The comment will say *"model: 2 finding(s) kept of 5
raw (2 unanchored, 1 refuted, 0 withdrawn)"*.

**10 · Context.** The body says `Closes #431`; that ticket's title is fetched. Acme has not granted
Jira egress, so a linked Jira ticket is **not** quoted.

**11 · Comment.** Headline: `⚠️ Needs a human. It breaks a rule you wrote down.` Then the goal, the
summary, the `no-eval` violation with its line, the two model findings labelled as a model's, and
the coverage table: 6 files touched, 24 checks decided, 3 read closely, 3 folded by directory.

**12 · Status and check run.** Commit status `failure`, because a `HIGH` rule was violated. The
check run posts one `failure` annotation on the charge module at line 88, visible on the diff. The
two model findings are **not** annotated.

**13 · Store.** One `review` row, 6 `ranked_unit` rows, 24 `rule_check` rows, 2 `finding` rows, and
the cost — 1 request, roughly 2,400 tokens out.

**14 · Later.** The developer removes the `eval` and pushes; we review the new head and post a
fresh comment. The pull request merges, and `lifecycle` records that. If a later fix returns to
the charge module in six weeks, the dashboard shows that we had pointed at it.

---

## 20 · What is not built, and what is not true

**Read this before quoting anything above to a customer.**

### Not built

- **Billing.** B3 and B7 are parked. Nobody can pay.
- **IDE integration, SSO.** Deferred until a deal asks.
- **SOC 2 Type II.** Months of external evidence collection; no code we write.
- **Scheduled exports.** The compliance artefact is produced by a command somebody runs; nothing
  produces one periodically.

### Measured and dropped — the honest ones

- **A stored dependency graph, blast radius, and architectural drift** — all measured, all failed
  their pre-registered bars, all dropped rather than shipped.
- **Human context as model input** — run, audited by two model families, and **withdrawn** when a
  replicate showed the pipeline's own noise exceeded the effect.

### Built but not proven in the wild

- **No check run has ever been posted to a real pull request.** The payload is asserted and
  rehearsal works; the write has not been exercised against GitHub.
- **Air-gapped has never run inside a real isolated network.** The refusals are tested and no module
  bypasses them, but "air-gapped works" is a claim about an environment we have not been in.
- **The audit trail's persistence in production is new.** Until 2026-09-01 the store lived on a
  container filesystem and was lost on every deploy. It now sits on a mounted bucket with a single
  writer — and a review has not yet been recorded, redeployed, and read back.

### The principles, if you remember nothing else

From `AGENTS.md`:

- **Honest beats complete.** A 78% coverage number we can defend is worth more than a 100% claim we
  cannot. Every competitor ships the second one.
- **Deterministic beats clever.** If a parser can answer it, a model must not.
- **The residual is the product.** What we cannot resolve is not our failure to hide; it is the
  thing the customer is paying us to find.
- **Assume the next reader knows nothing.**
