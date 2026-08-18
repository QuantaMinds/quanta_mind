# Storage — what we keep, why it is not a graph, and what the database enforces

**Moved out of `docs/plans/implementation.md` unchanged.** It is the design `store/` is built
against, and at four hundred lines it was burying the build steps it supports.

**Read it before writing `store/schema.py`.** The schema is versioned and append-only: a column
this document says must exist from the first row cannot be backfilled later.

**Two warnings carried over.** The `finding` and `claim` tables assume a reviewer that publishes,
and it does not — **create the tables, because adding them later is a migration, but build nothing
that writes to them.** The retention windows for findings and comment bodies are governed by the
same fact.

---

# Memory: what we store, and why it is not a graph

> **The `finding` and `claim` tables below assume a reviewer that publishes. It does not — see
> "How far this document is safe to follow". Create the tables anyway: the schema is versioned and
> append-only, so adding them after the fact is a migration. Do not build anything that WRITES to
> them.**

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
                tokens_out, latency_ms, tier
                -- CORRECTED: this listing carried `cost_cents`, which the rule three
                -- sections below explicitly forbids. `store/schema.py` omits it and
                -- derives cost from the `request` table's token counts. The listing was
                -- the stale half; the reasoned rule is the one that survived.
ranked_unit     review_id, unit_path, unit_name, rank, score,
                percentile, allocation          -- deep | shallow | cold
                -- EVERY changed unit, including cold ones. Not the funded subset.
                -- Cold rows are the coverage line's content and shadow evaluation's
                -- denominator; dropping them silently removes both.
finding         id, review_id, unit_path, kind, body, published,
                confidence, provenance
claim           id, finding_id, claim_kind, verdict, reason
                                                -- confirmed | contradicted | undecidable
unresolved      review_id, site, reason, construct
outcome         review_id, unit_path, fix_sha, fix_at, source, matched_rank
                                                -- git | datadog | manual
reaction        review_id, finding_id, kind, actor_hash, at
                                                -- resolved | dismissed | replied | emoji
shadow_pick     review_id, ranker_name, unit_path, rank, score, percentile
                -- ranks 1..k for k >= 3, NOT the top pick only
request         id, review_id, ordinal, model, model_version, effort,
                tokens_in, tokens_out, cache_read_tokens, cache_creation_tokens,
                latency_ms, stop_reason
```

### Three things the schema must record from the first row, because append-only cannot backfill

**`shadow_pick` stores a ranked LIST, not a top pick.** The allocator funds ranks 1–3 and
top-3 recall is the metric that decides whether allocation loses defects — and **top-3 for a
candidate ranker cannot be computed from a top-1 record.** Scores and percentiles go in too, or
the firing threshold cannot be re-derived either. This is the most consequential line in the
design: shadow evaluation on free-tier traffic is the strongest asset here, and a top-1 schema
silently halves it.

**Token counts per request, and cost derived from them — never a stored `cost_cents`.** Prices
change and token counts do not. Cents cannot separate a cache read from fresh input, and they
round away shallow calls that cost fractions of a cent. **Gate 3b is measured against uniform
review, and a cents column cannot produce that measurement.** `requests=3` on the review row is
a summary; the `request` table is the data.

**`outcome` carries a `rule_version` and the inputs to re-derive it.** The attribution rule has
already been corrected once — file overlap to symbol overlap, which changed 67.9% of verdicts.
Correct it again and every stored outcome needs re-deriving, and without a version stamp nobody
can tell which rule labelled which row. The rule also assumes English fix-keywords in commit
subjects, so the subject is stored rather than just the verdict.

**`outcome` is the table the product is built to fill.** Everything else describes what we did;
this one says whether it was right.

### The cache monitor lives in the data, not in a test

The build plan verifies `cache_read_tokens` in tests, where a persistent zero means an
invalidator is in the cached prefix. **On Cloud Run that becomes a production concern**: many
short-lived instances, and any per-instance value that reaches the prefix — an instance id, a
boot timestamp, a request id threaded through the system prompt — is a **total cache miss with
no error and no failing test.**

Because `request` stores cache-read tokens per call, a persistent zero is visible as data.
**Alert on it.** A test that passed once cannot see a regression that arrives with a deploy.

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

## Routing inference through Vertex — checked, 2026-08-14

**Gemini only.** The project is `quantamind-oss`, billing is enabled, `aiplatform.googleapis.com`
is on, and `gemini-2.5-pro`, `gemini-2.5-flash` and `gemini-2.5-flash-lite` all answered live.
Claude on Vertex was probed at the same time: `claude-sonnet-4-5` is offered in `us-east5` but
returns `NOT_FOUND` for this project — a Model Garden subscription gate — and it will not be
opened.

**That settles the first of the three checks by removing it.** The partner-model question was
whether GCP credits apply to marketplace models. Gemini is first-party Google, billed as ordinary
Vertex usage, so the credits apply on the same terms as any other Vertex spend. **The other two
remain open and neither is a formality:**

1. ~~Do the credits apply to partner models?~~ **Moot.** First-party model, ordinary Vertex
   billing. This was the largest single risk to the $16,000-of-credits arithmetic and it is gone.
2. **Does prompt caching behave identically?** Gemini's context caching is a *different
   mechanism* from Anthropic's prefix caching — explicit cached-content objects with their own
   minimum token count and TTL, not an automatic prefix match. **The entire cost architecture
   rests on this**, the design in the render step was written against prefix semantics, and this
   is now the top open question rather than a checkbox.
3. **Is structured output the same?** The verification pillar requires findings to arrive as
   parseable structure. Free-text output makes adjudication impossible, so a gap here is not a
   degradation — it removes a layer.

## C3 — the cost, billed rather than priced

**68 requests over 23 merged pull requests, live against `gemini-2.5-pro` on Vertex, 2026-08-14.**
The prompt is the one the architecture specifies: repository prefix, the funded function's full
source, its file's diff, and the schema a finding must satisfy. Unit of record is the **request**,
because aggregating three calls into one line is the defect that inverted this table's sign once.

| | measured |
|---|---|
| mean per pull request | **$0.1193** |
| median | $0.1247 |
| p90 | $0.1310 |
| max | $0.1452 |
| the derived estimate it replaces | $0.140 — ratio **0.85×** |

**The estimate was right in magnitude and wrong in structure.** It modelled a large prompt made
cheap by caching. The bill has the opposite shape: **input 5.2%, thinking 91.3%, answer 3.5%.**
The prompt is far smaller than assumed — 1,674 tokens mean, because one function and one diff is
not much text — and thinking, which the estimate did not model at all, is nine tenths of the cost.
Two errors that partly cancelled.

**Which makes the consequence architectural rather than financial. Prompt caching would save 4.7%
of this bill** — the whole of the "read, with the repository cached" design, optimising a term
that a dial beside it dominates twenty to one. That verdict depends on prefix size, and the prefix
measured here is a ~150-token stub rather than the conventions-and-signatures block specified:

| cached prefix | input share of cost | caching saves |
|---|---|---|
| stub, as measured | 5.2% | **4.7%** |
| 2,000 tokens | 10.7% | 9.6% |
| 10,000 tokens | 27.6% | 24.8% |
| 40,000 tokens | 57.6% | 51.9% |

**Caching is worth building only if the prefix is deliberately made large, and nobody has decided
that.** It cannot be inherited from the Anthropic-era plan where prefix caching was automatic.

**And the headline is a parameter, not a property of the workload.** Thinking was capped at 4,096
by the harness and **46% of requests pinned the cap**. The first run set no budget and observed a
mean of 5,744, maximum 13,108 — **1.51×, or $0.183 per pull request**. The price of a review is
currently set by a dial that has never been tuned against output quality.

**Three things this run cannot say**, recorded beside the number so they travel with it:

1. **No cached content was declared**, so this is the uncached figure. Given the table above that
   matters less than it would have.
2. **Nothing here evaluates whether a finding is any good.** 68 requests emitted 66 findings and
   all 68 responses parsed as a JSON array, with 8 returning the empty array. Near-total schema
   conformance is the *expected* outcome of forcing the schema — it says the schema works, not
   that the findings are right. Published-and-wrong remains untested and needs hands.
3. **Population**: 24 merged pull requests from the same 8 repositories, median 20-line units.
   Whether that resembles a customer's diff is unestablished, exactly as with everything else
   measured on these 8.

**One defect found by running it.** The first attempt died at request 66 of 72 on a 401 — the
`gcloud` token expires after about an hour and the serial run took fifty minutes — and wrote
nothing. Worse, **11 of its 39 recorded answers were one token long** behind six to thirteen
thousand thinking tokens: a `MAX_TOKENS` truncation that, reported without the finish reason,
would have read as *"the model found nothing."* The reader now returns `finishReason` rather than
letting a caller infer it, re-mints the token on a 401, and appends each row as it lands.

**Any headline built on the old figure — "$16,000 of credits is roughly 114,000 reviews" — should
be recomputed against $0.1193, and should carry the thinking-budget dial with it.**

## Which database runs, and when

**The split is not free versus paid. It is local versus hosted.** Both engines run the same
schema and the same migrations, and the store layer is written to SQL both accept.

| Where the product runs | Engine | Whose machine |
|---|---|---|
| `quantamind review` / `retrospective` on a laptop | **SQLite**, one file | theirs |
| The GitHub App, **any tier including free** | **Postgres**, one shared database | ours |
| Enterprise self-host | **Postgres** in their VPC | theirs |

### Walking one customer through it

**They run the retrospective first.** `uv run quantamind retrospective` against a clone. That
writes `quantamind.db`, a SQLite file in their working directory. **No account, no upload, and
we never see it.** This is the whole point of the CLI existing: a sceptic can check the claim
before granting anything.

**They install the App on the free tier.** Now reviews run on our infrastructure, so rows land
in our Postgres — one row in `repo`, then a `review` row per pull request with its
`ranked_unit` and `unresolved` children. **`finding` and `claim` stay empty**, because the free
tier runs no model. Their SQLite file stays on their laptop; nothing is imported, because a
retrospective is a report rather than state worth migrating.

**They upgrade to Team.** *No data moves and no database changes.* It is a plan column on their
organisation row. From the next pull request, `allocate` permits inference, so `finding` and
`claim` rows start appearing beside the ones already there. **The upgrade is visible in the
data as the moment those tables start filling** — which is exactly how it should read, because
that is what they started paying for.

**They upgrade to Business.** Again no migration. The `org` row gains their second and third
repositories, and the cross-repository report becomes a query over rows that were already being
written. **Everything the org view needs has been collected since the free tier**, which is why
the schema change for `org` lands before the first Business customer rather than after.

**They go Enterprise and self-host.** A container plus a Postgres they operate. Same schema,
same migrations, run by command. **We hold nothing.** Telemetry from that install is opt-in and
sends counts only.

### Why one shared Postgres rather than a database per customer

A database per customer means a migration is a fleet operation and a schema bug is discovered
customer by customer. One database with rows keyed by organisation means one migration, run
once, verified once. **The cost is that isolation is now a query predicate rather than a
boundary**, so every read is scoped by organisation at the repository layer and that scoping is
what the tests target — a missing `WHERE org_id` is the failure mode this trade buys, and it
must be tested for directly rather than assumed.

### The constraint that keeps both engines possible

**No engine-specific features in `store/`.** No Postgres arrays or `JSONB`-only queries, no
SQLite pragmas doing anything but performance. The moment one appears, self-hosting on SQLite
stops working and the CLI stops being able to run the same code as the App — and the CLI's
whole value is that it runs *the same pipeline*.

**Gate, and it is a CI job rather than a note.** `.github/workflows/ci.yml` gains a `store`
job that runs the `store/` suite twice — once against SQLite, once against a Postgres service
container — and asserts identical results. A written rule that nothing can fail is a wish; this
is the same argument the sabotage test rests on, applied to a rule this plan had left as prose.

**Row-level security is worth an hour before the first Business customer.** Postgres RLS turns
the `org_id` predicate back into a boundary without giving up the single-migration benefit, and
it is far harder to retrofit once queries exist that assume it is absent.

### Retention

**Retention is set on the measurement, not on the table**, and the earlier version of this
policy got it wrong in a way that would have destroyed the asset it meant to protect.

An `outcome` row on its own is unusable. `review=8801, unit=process_refund, fix_sha=b71e` says a
fix happened — it does not say what rank we gave that unit, or what any candidate ranker would
have picked. **The `ranked_unit` and `shadow_pick` rows are what turn an outcome into a
measurement.** Expiring those at 90 days while keeping outcomes forever would retain the truth
and delete the belief it exists to adjudicate.

| What | Kept |
|---|---|
| An `outcome`, **and the `ranked_unit` and `shadow_pick` rows it adjudicates** | **indefinitely, together, at every tier** |
| Reviews with no outcome, findings, claims, comment bodies | 90 days free · 2 years paid |
| Enterprise | their policy, and they hold it |

**This matters most on the free tier**, which is where shadow data accumulates at zero inference
cost — the counterfactual evaluation a model-per-diff competitor cannot replicate at any tier.

### Enforced by the database, not by the deletion job

A retention job written against table names deletes exactly the rows this policy exists to keep,
**and produces no error**: the tables still exist, queries still return, and the loss surfaces
months later when someone asks a question the deleted rows would have answered. That is the
signature of every instrumentation failure this project has recorded — plausible output, nothing
detectable from the output alone.

**So it is a constraint, not a comment.** `outcome` holds foreign keys to the `ranked_unit` and
`shadow_pick` rows it adjudicates, `ON DELETE RESTRICT`. The wrong deletion aborts. A job that
has to be written around a constraint is one somebody thinks about; a job that silently satisfies
a policy paragraph is not.

**The application role has no DELETE on `ranked_unit` or `shadow_pick`.** The constraint above
cannot express "keep this until we know whether it matters", because that is a fact about the
future and there is no row to point at yet. So it is expressed as an **absence of capability**
rather than a rule: a retention job that tries to delete these fails loudly at runtime, and
nobody has to remember the policy. Pruning later goes through a separate migration role with a
deliberate grant — a decision somebody makes, not a job that runs.

**`ranked_unit` is not deleted at all.** Adjudication arrives two to eight weeks late and
retention runs on a schedule, so a row at day 89 with no outcome yet is indistinguishable from
one that will never get an outcome. The rows are small and they are the belief half of the only
comparison this product sells. Keeping them is cheaper than being wrong about which ones matter.

**And the job reports both numbers**: rows deleted, and rows retained *because* they adjudicate
an outcome. A retention job that never retains anything is not retaining.

### Before `store/` is written: one pass asking what the database could enforce

**Four gaps in this plan have had the same shape** — a correctness rule living in prose while
the schema permits the violation, failing silently while every test passes:

| Gap | Prose said | Now enforced by |
|---|---|---|
| Retention | "outcomes are kept forever" | foreign keys, `ON DELETE RESTRICT` |
| Cold units missing | "the coverage line reports what was skipped" | a required field in the type |
| Cold units counted | "name what was skipped" | a list, with a residual that cannot stand alone |
| Cold units as strings | "the names match the ranking" | a reference to `ranked_unit` |

Each was caught one at a time, immediately after the fix that created it. **The cheaper rule is
general: anything the schema permits will eventually happen, so a rule that matters belongs in
the type or the constraint rather than the docstring.**

**So `store/` gets one pass before it is written, not after**: for every rule currently stated in
a comment, ask whether the database could refuse the violation instead. Where it can, it does.
Where it cannot — "keep this until we know whether it matters" is a fact about the future —
express it as an **absence of capability**, which is what revoking DELETE on `ranked_unit` does.

**The residue after that pass is the list of rules genuinely enforced by nothing**, and that list
should be short enough to read in one sitting. A rule on it is a rule someone has to remember,
and this plan has now demonstrated four times that nobody does.

**Keep the residue visible, not the enforced set.** The enforced rules take care of themselves;
the unenforced ones are what a new engineer needs on day one. **It is the internal equivalent of
the coverage line** — a short list saying *here is what nothing stops* — and it is written in the
same form:

| The rule | Why the database cannot hold it | What catches a violation instead |
|---|---|---|
| *(example)* a review must be posted before its outcome arrives | ordering across weeks, no row exists yet | nothing — **live risk** |

**Where the third column says "nothing", that is the live-risk list**, and it should be read
aloud at the start of the stage that touches it. A residue that never gets shorter is a design
that has stopped absorbing its own rules.

### The house rule these three share

Three mechanisms in this plan exist because a check that cannot report having fired is
indistinguishable from one that was never connected:

| Mechanism | What its silence would otherwise mean |
|---|---|
| The verifier's **drop-rate counter** | a flawless model, or a dead verifier |
| The **alphabetical ranker running in shadow forever** | a working ranker, or one measuring nothing |
| The **retention counter** | nothing needed keeping, or the constraint is not wired |

A fourth is already in the research: a dead hotspot check reported zero at every threshold until
a sanity counter reported in-window commits found — **0 before the fix, 1,298 after.**

**Rule: every check reports what it did, not only what it found.** Ask what a mechanism outputs
when the thing it protects is broken; if the answer is "the same thing", it is not a mechanism.

---

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
