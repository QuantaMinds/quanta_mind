# Restructure for building the product

**Written 2026-08-13**, branch `feat/product-skeleton`. Filename deliberately does not start
with `session-`, because the session-end hook writes its record to that pattern and overwrites
whatever is there.

This is the plan for turning a research repository into one that can carry a product, without
discarding the research that justifies it.

---

## Two things must change before a single folder moves

Both are constitutional. Neither is optional, and skipping them means the pre-commit guards
fight every commit.

### The repository's own rules describe a product that was falsified

`AGENTS.md` currently opens with *"We build the layer that tells a coding agent what it does not
know about a repository"*, and states:

> **The correlation test is not done.** The founding correlation is unmeasured, so no product
> code is written yet. If you are asked to implement a layer, check that file has a filled
> Results section first. If it does not, say so.

That test has since run and returned **null** — relative risk 1.040, cluster-robust interval
[0.598, 1.890], against a preregistered stop threshold of 1.5. It falsified the product those
rules describe. **So the gate is satisfied and the answer it gave was "stop"** — for that
product. The product now being built is a different one, justified by different measurements.

**`AGENTS.md` must be rewritten first**, or every agent and every contributor reading it will
correctly refuse to write product code. What survives the rewrite is all of the discipline —
the guards, the typed-silence rule, the assertion-quality rule, rule 14 — and what changes is
the description of what we are building and why.

### The enforced layer order belongs to the dead product

`scripts/guard/discovery.py` declares, and the pre-commit hook enforces:

```
types → discover → ingest → resolve → probe → label → store → serve
```

That is the pipeline of a static-analysis tool producing labelled edges. **The product's pipeline
is a different shape**: receive a webhook, read history, parse the diff into units, rank them,
decide a budget, call a model, adjudicate its claims, post one comment.

Proposed replacement, left-to-right imports only:

```
types → store → ingest → parse → rank → allocate → infer → verify → render → serve
```

| Layer | One concern | Imports from |
|---|---|---|
| `types` | value objects, enums, protocols. Frozen dataclasses. | nothing |
| `store` | persistence of those types; schema and migrations | types |
| `ingest` | git reads and GitHub API reads — diffs, history, pull-request metadata | types, store |
| `parse` | changed units from a diff; signatures; references. Tree-sitter lives here | ← left |
| `rank` | the prior-touch index and the percentile threshold | ← left |
| `allocate` | budget decisions derived from the ranking | ← left |
| `infer` | model calls: structured output, prompt caching, refusal handling | ← left |
| `verify` | adjudication of the model's structural claims against the parse | ← left |
| `render` | the comment body and the coverage line | ← left |
| `serve` | HTTP: webhook in, comment out, configuration, health | everything |

**Why this ordering and not the enterprise default.** A conventional `controllers / services /
repositories` split groups code by *technical role*. This groups by *stage in one pipeline*, and
the guard mechanically prevents a later stage leaking into an earlier one. The practical effect
is the one that matters here: **`verify` cannot import `infer`**, so the layer that adjudicates
the model's claims cannot quietly start trusting them.

---

## Where the enterprise concerns live

The request was for controllers, DTOs and the structure a real company uses. Each maps onto the
above rather than sitting beside it.

**Controllers → `serve/`.** FastAPI routers are controllers. They are named for what they serve,
one concern per file, because `AGENTS.md` bans a module that needs "and" to describe it:

```
serve/webhook_github.py     receives pull-request events, verifies the signature, enqueues
serve/review_status.py      read-only status of a review
serve/health.py             liveness and readiness
serve/admin_policy.py       per-repository configuration
serve/app.py                the FastAPI application object and router registration
```

**DTOs → deliberately two kinds, never one.**

```
types/                      internal domain objects. Frozen dataclasses, slots, no I/O.
serve/contracts/            HTTP request and response models. Pydantic, validated at the edge.
```

They are separate on purpose. **A domain object used as an API contract couples the wire format
to the internals**, so the first refactor becomes a breaking API change. The mapping between them
is explicit and lives in `serve/`.

**Persistence → `store/`.** Repository-pattern modules, one aggregate per file, plus a versioned
schema. Migrations under `migrations/` at the repository root, applied by a command, never
implicit at startup.

**Configuration → `types/settings.py`.** One frozen settings object, populated from the
environment, validated at import. No module reads `os.environ` directly; that is how a service
acquires undocumented configuration.

**Observability → `serve/` middleware plus structured logging from every layer.** Every log line
carries the repository, the pull request, and the review identifier, because a review that
misbehaves must be reconstructable from logs alone.

---

## What the product is: a GitHub App, proven by a CLI, with no dashboard

The plan assumed a webhook service without ever stating the product's shape. Three surfaces,
and they are not equal.

**The product is a GitHub App.** The finding is a pull-request comment, because that is where
the reviewer already is. One click to install, read-only on code, write-only on a comment, no
key to provision. Nobody opens a dashboard to review a pull request, and a tool that asks them
to is beside the workflow rather than in it.

**The CLI is built first and is permanent.** It is not a developer convenience; it does three
jobs nothing else can.

- **It runs the retrospective.** Replaying six months of a prospect's history is a batch job
  over a clone — no webhook, no hosting, no OAuth. The strongest sales act in this product is a
  command.
- **It is how a sceptic verifies us before granting repository access.** A platform engineer who
  will not install an app on their monorepo will run a command against a checkout. That barrier
  matters more here than for most products, because the entire pitch is honesty.
- **It answers the gate below.** *"Does the productionised ranker reproduce 85.3%?"* is settled
  by a command over the collected corpus, before any hosting exists.

So the App is the CLI plus a webhook, a signature check and idempotency — not a separate system.

**No dashboard, deliberately.** A web interface means authentication, sessions, a front end, and
a place users must remember to visit. This product argues that its thin visible surface is a
feature; a dashboard contradicts that and is the most expensive item available. The two non-pull
-request outputs already have cheaper homes: the weekly digest goes to Slack, and the quarterly
audit is a generated report — delivered, not browsed. If the audit becomes the revenue product
and buyers ask for it live, that is when an interface earns its place, and its shape should be
decided by what they ask for rather than guessed now.

**Consequence for the layer order:** `serve/` carries two thin adapters over identical layers.

```
serve/app.py     FastAPI — the webhook surface
serve/cli.py     the same pipeline invoked locally, posting nothing
```

**The pipeline must not know which one called it.** If the two paths can diverge, the thing a
customer verified with the CLI is not the thing the App runs, and the CLI stops being evidence.

---

## The proposed tree

```
src/quantamind/
  types/        settings.py  change.py  ranking.py  finding.py  review.py  verdict.py
  store/        schema.py  reviews.py  index.py  migrations_check.py
  ingest/       git_history.py  git_diff.py  github_pulls.py  github_comments.py
  parse/        units.py  signatures.py  references.py  languages.py
  rank/         touch_index.py  percentile.py  ranker.py
  allocate/     budget.py  tiers.py
  infer/        client.py  prompts.py  schemas.py  caching.py
  verify/       claims.py  adjudicate.py
  render/       comment.py  coverage_line.py  digest.py
  serve/        app.py  webhook_github.py  review_status.py  health.py  admin_policy.py
                contracts/  webhook.py  review.py  policy.py
migrations/     versioned SQL, applied by command
deploy/         Dockerfile, compose, runtime configuration
tests/          unit/  integration/  live/  property/
research/       UNCHANGED — the evidence base, see below
docs/           unchanged
scripts/guard/  unchanged except LAYER_ORDER
```

Every directory stays under the fifteen-file cap; every file stays under two hundred lines. Both
are enforced, so a directory approaching the cap is a signal to split a concern, not to raise a
threshold.

---

## What happens to the research

**Nothing moves and nothing is deleted.** `research/` becomes the product's evidence base rather
than its origin, and gains one file — `research/README.md` — stating which product claim each
result supports, so a new engineer can trace any assertion in the product documentation back to
the run that produced it.

The reason to keep it inside the repository rather than archiving it: **every quantitative claim
the product makes in front of a customer is defensible only while the measurement behind it is
reachable.** Four measurements were withdrawn during this work — the blobless-clone truncation,
the dead hotspot check, the vacuous revert test, the void'd symbol comparison. A reader who
cannot see those withdrawals has no way to calibrate the results that survived.

`research/` keeps its separate interpreter and its own dependency set. **Rule 11 stands: nothing
in `src/` may import pandas, scipy, statsmodels, gitpython, pyyaml, pycg or tree-sitter's
research bindings.** The product's own tree-sitter dependency is a product dependency, declared
in `pyproject.toml`, and the guard's import list needs re-reading against that distinction
before `parse/` is written.

---

## Order of work

**One — the constitution.** Rewrite `AGENTS.md` for the product being built; change `LAYER_ORDER`
in the guard; update the layer-order property test. Nothing else in the same commit, because a
constitutional change reviewed alongside feature code gets waved through.

**Two — the skeleton.** Empty layers with module docstrings, `types/` populated, settings, the
FastAPI app returning healthy, one end-to-end test that posts a fake webhook and asserts a 200.
No business logic.

**Three — the deterministic engine**, in dependency order: `ingest` → `parse` → `rank`. **Gate:
the productionised ranker reproduces the 85.3% top-1 figure on the corpus already collected.**
If it does not, the research is not the product and that must be understood before anything is
built on top.

**Four — allocate, infer, verify, render.** `verify` ships in the same change as `infer`, never
after it, with the sabotage test that injects a false structural claim and requires it to be
dropped.

**Five — serve.** Webhook, signature verification, idempotency, the comment.

---

## What this plan does not do

**It does not write business logic.** Everything above is structure, and structure is cheap to
get right now and expensive later.

**It does not resolve whether anyone will buy this.** That is unchanged by any amount of
scaffolding, and it remains the largest open risk.

**It does not assume the ranking transfers to production.** The gate in step three exists because
a productionised ranker that fails to reproduce the research number would mean the research was
measuring something the product cannot.
