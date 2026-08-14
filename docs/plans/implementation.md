# Implementation plan

**Written 2026-08-13.** Filename deliberately does not start with `session-`, because the
session-end hook writes to that pattern and would overwrite this.

This is the plan for building the product, instrumenting it so we can tell whether it works,
and turning it into revenue. It assumes `docs/plans/product-skeleton.md` for structure and
`docs/QUANTAMIND.md` for evidence, and repeats neither.

**Stages are named, never numbered in cross-references.** Inserting a stage between two numbers
is how a build order silently stops matching the document describing it.

---

## What is already true

| | |
|---|---|
| `AGENTS.md` | rewritten for this product, committed |
| `LAYER_ORDER` | `types → store → ingest → parse → rank → allocate → infer → verify → render → serve`, enforced |
| Package | `src/quantamind/`, renamed by `git mv`, guards updated |
| Pass count | **one** at rank 1, three-request ceiling, specified in the build plan |
| Ranking evidence | top-1 **86.2%**, top-3 **95.4%** vs an 89.4% null on ≥4-file changes, cold-miss **4.6%**, 7,493 events, 25 repositories |
| Cost ceiling | **$0.140** per pull request, **$28** per repository per month at 200 pull requests |

**Nothing under `src/quantamind/` exists except the package root.** Every stage below starts
from an empty layer.

---

## The rule that governs every gate here

Each stage has a gate that can **fail**. A gate that cannot fail is decoration.

So each gate below is written with its **known-answer test**: what the check outputs when the
thing it checks is broken. If that answer is "the same thing", the gate is rewritten before the
stage begins. This is `AGENTS.md` rule 14 applied in advance rather than discovered afterwards,
and this project has already lost four measurements to skipping it.

---

# Stage — The skeleton

**Goal: every layer exists, is importable, and does nothing.** No business logic.

### Steps

1. Create the ten layer directories under `src/quantamind/`, each with `__init__.py` and a
   module docstring naming what it does, why it exists, what it imports, and who consumes it.
2. Write `types/settings.py` — one frozen settings object, populated from the environment,
   validated at import. **No other module reads `os.environ`.**
3. Write the core value objects in `types/`:
   - `change.py` — `ChangedUnit`, `Diff`, `Repo`, `PullRequest`
   - `ranking.py` — `Ranking`, `RankedUnit`, `Score`
   - `finding.py` — `Finding`, `Claim`, `ClaimKind`
   - `verdict.py` — `Confidence`, `Provenance`, `Unresolved`
   - `review.py` — `Review`, `CoverageLine`, `RequestLedger`
4. Every dataclass `frozen=True, slots=True`. Every enum exhaustive, checked by mypy.
5. `serve/app.py` returns healthy. `serve/cli.py` prints its version and exits 0.

### Output

A repository where `just check` passes and `uv run quantamind --version` works.

### Tests

- **Unit:** every type constructs, every enum round-trips through the store.
- **Property:** `Unresolved` cannot be constructed without a `reason` and a `construct`.
- **Guard:** `check_conventions.py` proves no layer imports rightward.

### Gate

`just check` green, and one end-to-end test posts a fake webhook and asserts a 200.

**Known-answer test:** delete the import-direction check from `check_conventions.py` and
introduce a `verify → infer` import. The suite must go red. If it stays green, the guard is
walking a directory it thinks is excluded — which has happened here before.

### What could silently fail

The layer guard walks `src/quantamind/` by name. Rename the package without updating
`PACKAGE` in the guard and it walks nothing, reports `ok`, and enforces no layering at all.
**Mitigation:** a test asserting the guard finds a non-zero number of files.

---

# Stage — The reader

**Goal: read a repository and a pull request into typed values. No ranking, no model.**

### Steps

1. `ingest/git_history.py` — walk history once per repository. **Assert the git exit code on
   every call**; raise a typed error, never return an empty list. This is the defect that
   voided four measurements and reproduced again on `apache_airflow` while writing this plan.
2. `ingest/git_diff.py` — the diff for one pull request, as hunks with file and line ranges.
3. `ingest/github_pulls.py` — pull request metadata. Timeout 30s, declared.
4. `ingest/github_comments.py` — post one comment, idempotently, keyed on head SHA.
5. `parse/languages.py` — which languages we parse, and to what depth. **Public, and printed in
   the coverage line.**
6. `parse/units.py` — map diff hunks to the functions they touch. Two passes: git's funcname
   diff drivers as the cheap first pass, tree-sitter as the exact one.
7. `parse/signatures.py`, `parse/references.py` — signatures and call sites.
8. Everything unparseable emits `Unresolved(site, reason, construct)`. **Never nothing.**

### Output

`uv run quantamind read <repo> <pr>` prints the changed units, the signatures, and the
unresolved list, as JSON.

### Live verification

Against the pinned submodules in `tests/live/fixtures/repos/`, plus five repositories from the
research corpus, run `read` and diff against a checked-in golden file **reviewed by a human**.

### Gate

**Conservation:** for every diff, `parsed units + unresolved sites == total sites`. Nothing
vanishes.

**Known-answer test:** feed a file in a language we do not parse. It must appear in
`unresolved` with a reason, not be absent from both lists. **Sabotage the whole mechanism, not
the entry point** — disable the tree-sitter path *and* the funcname path; a previous sabotage
here disabled only the entry point and left the suite green, reading as coverage.

### What could silently fail

A blobless clone. 27 of 35 clones in the research corpus are `blob:none`, and a cold read
lazily fetches trees over the network — non-deterministic until warm, and a network failure
looks like a small repository. **Mitigation:** `ingest` records clone filter and object count
per read, and the review record carries both.

---

# Stage — The ranker

**This is the stage that decides whether the research is the product.**

### Steps

1. `rank/touch_index.py` — the index built from history. Bounded strictly by the parent commit;
   **no data from after the change may enter the ranking of that change.**
2. `rank/percentile.py` — the percentile threshold. Absolute thresholds fired at 11% on one
   repository and 53% on another; percentiles self-calibrate to 10–12% across an 80× velocity
   range.
3. `rank/ranker.py` — the ranking itself, global across the diff, never file-then-function.
4. A `NullRanker` shipped **in the test tree, not in `src/`** — alphabetical, non-informative,
   run on every gate.

### Output

`uv run quantamind rank <repo> <pr>` prints the ranked units with scores and the fire decision.

### Gate — the hard one

**The productionised ranker reproduces the research figures on the corpus already collected:**

| Metric | Research value | Tolerance |
|---|---|---|
| Top-1, pooled | 86.2% | ±2 points |
| Top-3, changes touching ≥4 files | 95.4% | ±2 points |
| Cold miss, ≥4 files | 4.6% | must not exceed 7% |
| Fire rate | 10–12% | must not exceed 15% |
| Alphabetical null, top-1 | 72.0% | ranker must beat it by ≥8 points |

**If it does not reproduce, stop.** The research measured something the product cannot, and
that must be understood before anything is built on top of it.

**Known-answer test, and it is the important one here.** A ranker returning a constant scores
above 70% on top-1 because the null is 72%. So the gate is not "the number is high" — it is
**"the number is high AND the null ranker, run through the identical harness, is not."** Three
sabotages, all required to go red:

1. Replace the score with a constant → top-1 must fall to the null.
2. Reverse the ranking → top-1 must fall below the null.
3. Let post-change history into the index → top-1 must rise implausibly. **A rise is a failure
   here**, and the only sabotage in this plan whose failure signal is an improvement.

### Live verification

Re-run against all 25 repositories with the skip ledger printed. **Any failed read refuses to
report.** Compare per-repository against `research/phase0/results/top3_recall.json`.

### What could silently fail

The research harness ranks **files**; the product ranks **functions**. These are different
units and the file-level number may not transfer. **This is the single largest technical risk
in the plan.** Mitigation: the gate runs at both granularities and reports both; a function-level
number materially below the file-level one is a finding, not a rounding error.

---

# Stage — The free tier

**Goal: something shippable that runs no model at all.** First public release.

### Steps

1. `render/coverage_line.py` — what we checked, what we did not, and why.
2. `render/comment.py` — the comment body. Coverage first, findings second.
3. `serve/cli.py` — `quantamind review <pr> --no-post` runs the whole path locally.
4. `render/digest.py` — the weekly Slack message.

### Output

A real comment on a real pull request, containing a ranking and a coverage line and **no model
output**.

### Gate

Install on our own repository. **For ten consecutive pull requests, the coverage line must be
accurate when checked by hand.** Not "plausible" — checked, unit by unit, by a person.

**Known-answer test:** a coverage line that always prints 100% looks identical to a correct one
on a well-parsed repository. So the gate includes a repository with a deliberately unparseable
file, where the correct answer is **not** 100%.

### Why ship this first

It is the tier a sceptic runs before granting repository access, it is what the retrospective
prints, and it costs us compute rather than inference. It is also the only part of the product
we can give away without giving away margin.

---

# Stage — The retrospective

**Goal: the sales motion.** Replays history and shows where we would have pointed.

### Steps

1. `serve/cli.py` gains `quantamind retrospective <repo> --since 180d`.
2. For each merged pull request in the window, in ancestral order: rank it using only history
   before it, record the top-ranked unit, then look forward for a later fix touching it.
3. `render/report.py` — the customer-facing document.

### Output

An HTML and Markdown report: every merged pull request, what we would have pointed at, whether
a later fix went there, and what we could not read.

### Gate

Runs end to end on three repositories of different sizes, and **the numbers it prints match a
hand audit of twenty randomly selected pull requests.**

**Known-answer test:** the lookahead must be bounded by `git merge-base --is-ancestor`. Remove
the bound and the report's hit rate must rise — an unbounded lookahead scores better and is
wrong. **A report that improves when the bound is removed is the failure signal.**

### What could silently fail

Time-travel. A ranking that sees any commit after the change is not a prediction, it is a
lookup. **Mitigation:** the ranker takes an explicit `as_of` commit and the store refuses reads
beyond it. Not a convention — a refusal.

---

# Stage — Allocate, infer, verify

**`verify` ships in the same change as `infer`, never after it.** A reviewer publishing
unchecked model claims for even one release is the failure this product exists to prevent.

### Steps

1. `allocate/budget.py` — emits a `Budget` carrying a **maximum request count**. Exceeding it
   raises; it never silently degrades.
2. `allocate/tiers.py` — deep for rank 1 at one pass, shallow for ranks 2–3, nothing for cold.
3. `infer/client.py` — `claude-opus-5`. Check `stop_reason` before `content[0]`; a refusal is
   an HTTP 200. Stream anything above roughly 16K.
4. `infer/prompts.py`, `infer/schemas.py` — structured output only. **The verifier can only
   check a claim it can parse**, so free-text review output would make verification impossible.
5. `infer/caching.py` — repository prefix cached; **no clock, no request id, nothing volatile in
   the prefix.** A clock there makes every request a cache miss with no error.
6. `verify/claims.py` — extract the structural claims from a finding.
7. `verify/adjudicate.py` — check each against the parse. Confirmed publishes; contradicted
   drops; **undecidable is labelled, not silently published.**

### Output

A review with findings, each carrying a verdict and a provenance.

### Gates

| Gate | Passes when |
|---|---|
| **Request ceiling** | observed request count ≤ 3 on 100 consecutive reviews, read from the ledger, not from the config |
| **Cost** | observed cost per pull request within 20% of $0.140 |
| **Cache** | `usage.cache_read_input_tokens` non-zero on the second request of every review |
| **Sabotage** | an injected false structural claim is dropped |
| **Drop rate** | the live counter reports a non-zero, non-100% drop rate by claim class |

**Known-answer test on the ceiling:** a ceiling never hit and a ceiling never wired up print
the same thing. So the test sets the ceiling to 1 and asserts the run **raises**. If it does
not, the ceiling is decoration.

**Known-answer test on the verifier:** the sabotage gate proves it can reject **once, on the
planted case**. It cannot distinguish "rejecting correctly" from "rejected that one and nothing
since". The drop-rate counter is what proves it still works — and a drop rate that falls to zero
and stays there is either a flawless model or a dead verifier. **Those must not look the same on
the wire**, so zero for seven consecutive days raises an alert.

### What could silently fail

**The verifier is a parser, so it cannot adjudicate semantic claims** — and semantic defects are
the reason a model runs at all. A wrong semantic finding publishes. This is not fixable within
this stage; it is bounded by labelling every published finding with whether it was verified or
merely suggested, and never claiming more.

---

# Stage — Serve

### Steps

1. `serve/webhook_github.py` — signature verification, then enqueue. **Verify before parse.**
2. Idempotency keyed on `(repo, pr, head_sha)`. A redelivered webhook must not double-post.
3. `serve/review_status.py`, `serve/health.py`, `serve/admin_policy.py`.
4. `serve/contracts/` — Pydantic models at the edge, mapped explicitly to `types/`.
5. GitHub App: read on code, write on pull request comments. **Nothing else requested.**

### Gate

Replay 100 real webhook deliveries including duplicates and out-of-order arrivals. **Exactly one
comment per head SHA.**

**Known-answer test:** send the same delivery twice. Two comments is a fail. Then send with a
bad signature — a 401 and no queue entry. A handler that parses before verifying accepts
attacker-controlled JSON, and its happy path looks identical.

---

# Memory: what we store, and why it is not a graph

The question this section answers: **when the product is wrong, how do we find out, and how do
we improve it?**

### The shape of the problem

The label arrives late. We rank a change today; whether the fix returns to that unit is knowable
in two to eight weeks. **So the store must be append-only with late-arriving outcomes**, and
nothing may be overwritten when the truth turns up.

### Why not a graph database

There is a graph in this product — changes, follow-up fixes, and the edges between them. But the
queries are relational: *count reviews where the ranked unit matched a later fix, grouped by
repository and month.* A graph store buys traversal we do not need and costs an operational
dependency. **SQLite per install, Postgres for cloud. The graph is a table of edges.**

We reconsider only if a query needs traversal deeper than two hops, which none currently does.

### The tables

```
repo            id, host, name, clone_filter, first_seen, languages_parsed
review          id, repo_id, pr_number, head_sha, created_at,
                fire_decision, coverage_pct, request_count, tokens_in,
                tokens_out, cost_cents, latency_ms, tier
ranked_unit     review_id, unit_path, unit_name, rank, score,
                percentile, allocation          -- deep | shallow | cold
finding         id, review_id, unit_path, kind, body, published,
                confidence, provenance
claim           id, finding_id, claim_kind, verdict, reason
                                                -- confirmed | contradicted | undecidable
unresolved      review_id, site, reason, construct
outcome         review_id, unit_path, fix_sha, fix_at, source, matched_rank
                                                -- git | datadog | manual
reaction        review_id, finding_id, kind, actor_hash, at
                                                -- resolved | dismissed | replied | emoji
shadow_pick     review_id, ranker_name, unit_path, rank
```

**`outcome` is the table the product is built to fill.** Everything else describes what we did;
this one says whether it was right.

### The two rules on this store

**Append-only, and no destructive migration.** The schema is versioned; changing
`store/schema.py` requires a migration and a `SCHEMA_VERSION` bump. There is no
delete-and-reindex path in production, because the outcome history *is* the asset.

**Never store source code.** `finding.body` quotes at most a few lines. `unit_path` and
`unit_name` are identifiers. A telemetry table that accumulates customer source is a breach
waiting for a date.

### How outcomes get filled

| Source | Mechanism | Latency |
|---|---|---|
| **git** | a later commit whose subject looks like a fix touches a ranked unit | days to weeks |
| **Datadog** | Error Tracking suspect commits, consumed as configuration | hours |
| **manual** | a reviewer marks a finding as real | immediate, rare |

The git path is the one we control and the one the research validated. **Datadog is the faster
signal and we consume rather than rebuild it** — see the integrations section.

### Shadow ranking: how the product improves without shipping regressions

Every review runs the live ranker **and** every candidate ranker, recording all picks in
`shadow_pick`. Only the live ranker's output is published.

Weeks later, when `outcome` fills, we can ask: *which ranker would have been right?* — on real
customer traffic, with no experiment, no traffic split, and no risk.

**A candidate is promoted only when it beats the live ranker on outcomes across at least three
repositories and does not lose on any.** The alphabetical null runs in shadow permanently: if it
ever draws level with the live ranker, something has broken upstream and the whole ranking is
measuring nothing. **That is the single most valuable row in this table** — it is the check that
tells a working ranker from a dead one, and without it both print a plausible number.

### The analysis queries we commit to running monthly

1. Top-1 and top-3 against outcomes, per repository, per month. Trend, not a point.
2. Cold-miss rate — outcomes landing on a unit we gave no model call.
3. Drop rate by claim kind. Zero for a week is an alarm, not a success.
4. Fire rate per repository. Drift away from 10–12% means the percentile is mis-calibrated.
5. Coverage percentage distribution. A rise without a parser change means we stopped noticing
   what we cannot read.
6. Reaction rate on published findings. The only direct human signal we get.
7. Live ranker versus every shadow ranker, including the null.

**Each has a number that means "broken" as well as one that means "good".** A query with only
the second is not a check.

---

# Tracking: what we count and what we refuse to

### The one number

**Weekly active repositories with at least one acted-on finding.**

Not installs, not reviews posted, not comments. A repository where reviews go out and nobody
ever reacts is churn that has not happened yet, and counting it as usage hides that.

### The counters

| Group | Metric |
|---|---|
| **Adoption** | installs, active repositories, active developers (opened a PR this period), reviews posted |
| **Frequency** | daily and weekly active repositories, daily and weekly active developers, reviews per repository per week |
| **Volume seen** | commits observed, pull requests observed, pull requests reviewed, pull requests skipped **and why** |
| **Behaviour** | fire rate, coverage percentage distribution, unresolved sites per review, languages encountered vs parsed |
| **Quality** | drop rate by claim kind, findings published per review, reaction rate, dismissal rate |
| **Cost** | requests per review, tokens in and out, cost per review, cost per repository per month |
| **Service** | time to first comment, webhook-to-comment latency, error rate, queue depth |
| **Money** | free-to-paid conversion, seats billed, expansion, day-30/60/90 retention |

**"Pull requests skipped and why" is not a vanity metric.** If we silently skip 40% of traffic,
every other number is computed on a population nobody chose.

### How it is collected

- Every review writes one row. **Telemetry is a query over the store, not a parallel pipeline**
  — a second pipeline drifts from the first and then both are wrong.
- Cloud aggregates by repository, hashed. **We never see repository names for customers who
  have not asked us to.**
- Self-hosted telemetry is **opt-in**, documented on the security page, and refuses to send
  anything but counts.
- A weekly digest email to us. **No dashboard**, for the same reason the product has none.

### What we refuse to collect

Source code. File contents. Commit messages beyond a fix/not-fix classification. Individual
developer identity — `actor_hash` is salted per install and cannot be reversed to a person.

**A tool that measures where code needs rework must never become a tool that measures which
developer causes it.** That is the fastest way to be uninstalled, and it deserves to be.

---

# Free tier to revenue

### The path

```
free report          →  free tier        →  Team           →  Business        →  Enterprise
retrospective,          ranking and         findings on       org-wide report,   own model,
no install              coverage line,      pull requests,    SSO, own key       self-host
                        no model            unlimited
```

### Where the wall sits

**The free tier runs no model.** That is not a limit we invented to force upgrades — it is what
makes the free tier free. Ranking and the coverage line cost compute. Findings cost inference.
The wall sits exactly where our cost begins, and saying so is more persuasive than a feature
grid.

### The conversion event

Not a trial expiry. **The retrospective report.** A team that has seen where we would have
pointed across their own six months has already tested the claim. The upgrade question is then
"do you want it on the next one" rather than "do you believe us".

### Triggers to watch

| Trigger | Move |
|---|---|
| Free tier active 14 days, coverage line read | offer the retrospective |
| Retrospective delivered | offer Team, two-week trial with findings on |
| Third repository connected | offer Business — the org-wide view is the reason |
| Someone asks about SSO | Business |
| A security questionnaire arrives | Enterprise, and start the process immediately |
| PR volume above the fair-use ceiling | Enterprise with their own key. **Not a cap — an upgrade** |

### Billing

**Seats = developers who opened a pull request in the period.** Reviewers and managers are free.
This matches how CodeRabbit bills, so the comparison is honest, and it removes the
"but we only have four people who actually push" objection before it is made.

Stripe. Monthly and annual. **Usage is metered in the store from day one even while every plan
is unlimited**, because we cannot price what we never measured — and the $28 per repository
figure is a ceiling derived from a specification, not from traffic.

### The separate line

**The quarterly coverage audit, $8,000–15,000 per engagement.** Different buyer, different
budget, no seat maths. Plausibly the larger business, and the reason `render/report.py` is built
during the retrospective stage rather than later.

---

# Integrations

### Slack — one message a week

`render/digest.py` posts a weekly summary: where rework concentrated, coverage trend, what we
could not read.

**Not an alert stream.** An alert per finding trains people to mute the channel, and a muted
channel is worse than no channel because it looks like a working integration.

### Jira — read, never write

**We read the linked issue to give the model intent.** A change whose ticket says *"customers
are being double-charged on partial refunds"* is a different review from the same diff with no
context.

**We do not create tickets, and we do not assign blame.** Datadog already creates tickets from
issue panels; duplicating it puts us in an occupied position with a worse product, and a tool
that files tickets naming people gets switched off within a quarter.

Scope: OAuth, read the issue linked in the branch name or PR title, pass summary and description
into the prompt prefix. **Feature-flagged per repository, off by default**, because sending
ticket text to a model is a decision a customer must make deliberately.

### Datadog — consumed as an instrument

This is the integration that closes the loop in the memory section.

Datadog Error Tracking already ships **suspect commits**, on four stated criteria: the commit
modifies a line in the stack trace, was authored before the first error occurrence, no more than
90 days before, and is the most recent commit meeting those criteria.

**So the incident-to-commit link is a configuration, not a build.** We consume it to fill
`outcome` faster than git history can — hours instead of weeks.

Two things their documentation does **not** claim, and we must not either: automatic
pull-request linking and auto-assignment. Commit-to-pull-request is a GitHub API lookup — a thin
gap, not a moat.

**What we add is the denominator.** The standard file-overlap attribution rule is wrong on 67.9%
of its verdicts. Their webhook plus our corrected rule is the measurement, and that is the whole
of our contribution here.

**Out of scope, deliberately:** reimplementing their attribution, and emitting per-incident blame
tickets.

---

# The commercial surface, which the pricing table sells and this plan did not build

**Audited against the four-tier table. Every row below was being sold with no stage, no gate and
no test.** Listing them as monetisation prose was not the same as planning them, and the gap was
only visible by reading the price list next to the build order.

| Sold on | Row | Was it planned? |
|---|---|---|
| Business | cross-repository aggregation | **No** |
| Business | quarterly coverage audit | named once, never built |
| Business | SSO / SAML / SCIM | SSO named, SAML and SCIM absent |
| Business | verifier drop-rate telemetry | covered by the telemetry section |
| Business | bring your own key, allowlisted model | mentioned, no mechanism |
| Enterprise | bring your own **model**, uncertified | **No**, and it implies a recurring process |
| Enterprise | self-host, audit logs, residency, SLA | self-host named; audit logs and residency absent |
| Team+ | token budget, fair use per repository | **No** — and it is load-bearing for margin |

Four stages follow. **None may start before the ranker gate**, because all of them are worthless
if the ranking does not reproduce.

---

## Stage — The budget ceiling

**First of the four, because it is not a feature. It is what keeps the price honest.**

At twenty developers and 400 pull requests a month, inference runs about $56 against $380 of
revenue — 85% margin. At 2,000 pull requests it is $280 against $380, or **26%**. "Unlimited
reviews" is a promise the `allocate` layer has to keep.

### Steps

1. `store/quota.py` — spend per repository per billing period, written by the same review record
   that already carries request count and token spend. **A query over the existing store, never
   a second counter.**
2. `allocate/ceiling.py` — a per-repository budget read at allocation time. Above it, the review
   still runs and still posts the coverage line; **only inference is withheld, and the comment
   says so.**
3. Threshold configurable per plan, defaulting to the fair-use figure on the price list.

### Gate

Drive a repository past its ceiling on real traffic. **Reviews keep arriving, coverage lines keep
appearing, inference stops, and the comment states that it stopped.**

**Known-answer test:** set the ceiling to zero. Every review must degrade to coverage-only and
none may fail. A ceiling that errors instead of degrading turns a billing limit into an outage.

### What could silently fail

A ceiling never reached and a ceiling never wired up look identical. The monthly analysis already
required for cost includes **spend against ceiling per repository**; a column of zeroes across
every repository means the ceiling is not connected, not that nobody is heavy.

---

## Stage — Identity and the organisation view

**What actually separates Team from Business.** Not a bigger quota — a different buyer, who has
more than one repository and someone above them asking about all of them.

### Steps

1. `serve/auth_sso.py` — SAML and OIDC. **SCIM last**, and only when a customer asks: it is user
   provisioning, it is where identity integrations rot, and nobody has ever bought because of it.
2. `types/org.py`, `store/org.py` — an organisation owning repositories. **This is a schema
   change and needs a migration**, which is why it lands before any Business customer, not after.
3. `render/org_report.py` — rework concentration across repositories, quarter over quarter.
4. `serve/admin_org.py` — role-based access. Three roles, not nine.

### Gate

Two repositories, one organisation, one report whose numbers **equal the sum of the per-repository
records** when checked by hand.

**Known-answer test:** put a repository in the organisation with no reviews. It must appear with
zeroes rather than be omitted — a silently dropped repository is how an org-wide report becomes
quietly wrong, and it looks like a clean report.

---

## Stage — Bring your own key, and the certification that follows

**Two features, deliberately split, and the split is the pricing line.** Business gets a key for
a model we have already evaluated. Enterprise gets a model we have not.

### Steps

1. `infer/providers/` — one module per provider: direct, Bedrock, Vertex, Azure. **They differ on
   cache semantics, structured-output shape and refusal handling**, and each is a maintained
   integration rather than a configuration flag.
2. `store/credentials.py` — customer keys encrypted at rest, never logged, never in a review
   record. **A key in a log is a breach with a date on it.**
3. `infer/allowlist.py` — the models certified for Business. Anything outside it is Enterprise.
4. **`scripts/certify_model.py` — the recurring process this plan had no place for.** For a model
   we have not evaluated: run the verifier against it on the corpus and record the drop rate by
   claim class. **We publish a coverage number under our name; publishing one for a model we
   never measured is the failure this product exists to prevent.**

### Gate

The same pull request reviewed through two providers produces **the same structural claims**.
Where it does not, the difference is recorded in the certification, not averaged away.

**Known-answer test:** a deliberately weak model must produce a **higher** drop rate, and
certification must refuse to pass it. If every model certifies, the certification measures
nothing — and this is the one gate whose failure is silent, because a bad certification still
prints a number.

### What could silently fail

Certification is **not one-off**. A provider updating a model silently invalidates it. Record the
model version in every review, and treat an unrecognised version as uncertified rather than
assuming continuity.

---

## Stage — What procurement requires

**Bought by security review, not by engineers.** None of it improves the product and all of it is
mandatory above a company size.

### Steps

1. `serve/audit_log.py` — append-only: who changed configuration, when, from where. **Separate
   from application logs**, because the first question in an audit is whether the log could have
   been edited.
2. Data residency — region-pinned storage, chosen at install and not migratable afterwards.
3. Self-hosted deployment: container, migrations run by command, an offline licence check that
   **fails open**. A licence check that fails closed takes a customer's reviews down over our
   billing problem.
4. Retention controls, and contractual no-training in writing.
5. SLA measurement before an SLA is offered. **We do not have latency numbers**, and the rule
   against performance claims without measurement applies hardest in a contract.

### Gate

A full security questionnaire answered **from the running system**, not from a document. Every
answer demonstrable.

**Known-answer test:** attempt to modify an audit-log entry through any application path. It must
be impossible, and the attempt must itself be logged.

---

## Where these sit in the order

**All four are gated behind the ranker**, and three of the four should wait for a customer who is
actually blocked on them:

| Stage | Trigger | Why not sooner |
|---|---|---|
| **Budget ceiling** | **before the first paid seat** | It is not a feature, it is what makes the price true |
| Identity and org view | first Business prospect with two repositories | The schema change wants doing before there is data to migrate |
| BYO key and certification | first prospect blocked on compliance | Each provider is a maintained integration; build them one customer at a time |
| Procurement surface | first security questionnaire | It never makes the product better and it always takes longer than estimated |

**Only the budget ceiling is unconditional.** The rest are sold on the price list and built when
someone tries to buy them — which is the honest way to run a four-tier table with no customers
yet, provided the table does not promise a delivery date.

---

# Order, and what would make us stop

| Stage | Ships | Stop condition |
|---|---|---|
| Skeleton | week 1 | — |
| Reader | weeks 2–3 | conservation invariant cannot be made to hold |
| **Ranker** | weeks 4–5 | **does not reproduce within tolerance — stop and re-examine the research** |
| Free tier | week 6 | coverage line cannot be made accurate by hand audit |
| Retrospective | weeks 7–8 | report contradicts the hand audit |
| Allocate/infer/verify | weeks 9–11 | cost exceeds uniform review, or drop rate is 0% or 100% |
| Serve | week 12 | duplicate comments cannot be eliminated |
| Telemetry | with each stage | — |
| **Budget ceiling** | **before the first paid seat** | **degrades to an outage instead of coverage-only** |
| Billing and integrations | after ten paying repositories | — |
| Identity and org view | first two-repository prospect | org report disagrees with the per-repository sum |
| BYO key and certification | first compliance-blocked prospect | every model certifies, so certification measures nothing |
| Procurement surface | first security questionnaire | audit log is modifiable through any application path |

**The ranker gate is the one that can end the project**, and it is deliberately placed before
any hosting, any billing, and any model spend. If the productionised ranker does not reproduce,
everything after it is built on a number that did not survive contact with the product.

---

# What this plan does not resolve

**Whether anyone will pay.** Unchanged by any amount of building, and still the largest risk.

**Whether a reviewer shown the routing line before the defect exists catches anything they
would otherwise miss.** Every number here is retrospective. This is a field measurement and no
amount of history substitutes for it. It is the first thing to measure once real traffic flows,
and it is not gated on anything above.

**Whether function-level ranking transfers from the file-level research.** Named as the largest
technical risk, measured at the ranker gate, and it has no mitigation beyond measuring it early.
