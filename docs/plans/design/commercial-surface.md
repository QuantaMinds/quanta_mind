# The commercial surface — tracking, tiers, integrations, and what procurement requires

**Moved out of `docs/plans/implementation.md` unchanged.** None of it is scheduled, and mixing it
with the build phases made the plan read as though it were.

**Two things here are not currently true and must not be quoted.**

- **The tier table sells findings as a paid capability, and we do not ship them.** The reviewer
  half produces 0.013–0.037 correct findings per pull request across nine designs. Do not put that
  table in front of a customer until the published-findings bar has held twice, once with a rater
  who did not design the experiment.
- **Every tracking counter defined over published findings measures nothing today** — "reaction
  rate on published findings", "findings published per review". The ranking and coverage counters
  are the live ones.

Kept rather than deleted because the evidence could turn, and because the procurement and
identity work is real build work whenever a customer needs it.

---

# Tracking: what we count and what we refuse to

> **Every counter defined over published findings measures nothing today, because none are
> published.** The ranking and coverage counters are live and are the ones that matter now.

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

> **The tier table sells findings as a paid capability and we do not ship them.** Do not quote it
> to a customer until the published-findings bar has held twice, once with an independent rater.

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

   **Two numbers, not one, because the failure is asymmetric.** A model producing fewer parseable
   structural claims raises the drop rate **visibly**. A model producing claims that *pass the
   parser while being semantically wrong* raises **nothing at all** — and the defects this
   product exists for are semantic, which is why the verifier cannot judge them. The parser
   confirms *"line 71 precedes line 88"* and publishes a finding whose reasoning is wrong.

   | | What it measures | Visible? |
   |---|---|---|
   | **Drop rate by claim class** | what the verifier rejects | yes, automatically |
   | **Published-and-wrong rate** | findings that passed verification and were judged incorrect | **only if measured** |

   **The second decides the model, and price says nothing about it.**

   **Get it cheaply by running both candidates on the same pull requests and adjudicating only
   where they disagree.** Where they agree there is little to learn; the disagreements are a
   small set worth human judgement, and concentrating effort there is the same logic as McNemar
   using only discordant pairs.

   **And this procedure applies to our own default, not only to a customer's model.**

   ### Pre-specified now, before `infer/` exists, so early results cannot shape it

   **The certification run cannot be improvised.** It needs the real prompt, the real schema and
   the real verifier — a standalone two-model script would measure two models on an ad-hoc
   prompt, not this reviewer, and the number would be discarded once the pipeline exists.
   **Worse, the disagreement events are scarce**: hand-adjudication is expensive and there is
   one clean read before the prompt starts being shaped by what was seen.

   | | Fixed now |
   |---|---|
   | **Population** | 100 pull requests drawn from the 8 full-object clones, seeded, drawn before the run |
   | **What counts as a disagreement** | **both models publish a finding on the same unit with incompatible claims.** One publishing while the other is silent is a *different* case — informative about coverage, not adjudicable head-to-head, and counted separately |
   | **Adjudication** | blind to which model produced which finding |
   | **Sample** | 100 adjudicable disagreements, or the whole set if fewer |
   | **The decision rule** | **superseded — the provider question was decided by direction, not by measurement** |

   **Gemini only. Decided 2026-08-14, and recorded as a decision rather than dressed up as a
   result.** Claude on Vertex was probed the same day: `claude-sonnet-4-5` is offered in
   `us-east5` but returns `NOT_FOUND` for this project, which is a Model Garden subscription
   gate rather than an availability one. It will not be opened. Everything runs on Gemini.

   **What that retires.** The Claude-versus-Gemini adjudication does not need running, and the
   `$15 per repository per month` saving it was meant to arbitrate is no longer a live trade.
   Two providers were also the only justification for keeping the render path provider-neutral
   at cost to its clarity; that justification is gone, and the constraint should be dropped
   deliberately rather than left standing as a cost nobody remembers paying for.

   **What survives, because the arithmetic was about the instrument and not about Anthropic.**
   The threshold was mismatched to its sample by an order of magnitude — the rule said *"within
   2 percentage points"* while an exact binomial on adjudicated disagreements resolves this:

   | adjudicated disagreements | smallest skew resolvable at p < 0.05 |
   |---|---|
   | 50 | 32 points |
   | **100** | **22 points** |
   | 200 | 15 points |
   | 400 | 10 points |

   **At n=100 the instrument resolves 22 points. It was being asked to adjudicate 2.** Any
   future two-way model comparison inherits that table, and any rule written against it must
   state the skew it can actually see.

   **And there is still a live comparison, now within one provider: `gemini-2.5-pro` versus
   `gemini-2.5-flash`.** Unlike the retired one it is runnable today — both answered on this
   project — and it matters more, because the probe showed pro spending **204 thinking tokens
   to answer a one-word prompt** against flash's 20, and thinking bills at the output rate. The
   same rule applies with the same arithmetic: *pro is retained only if it wins ≥61 of 100
   adjudicated disagreements, an exact-binomial rejection of 50/50 at p < 0.05.* If it finds
   nothing, that is not evidence of equivalence — it is evidence this instrument cannot tell,
   and the choice then falls to measured cost, which is now available rather than estimated.

   **The reasoning behind wanting a tight threshold is kept**: a wrong published finding costs
   more here than at a competitor, because what is sold is that the review can be trusted at its
   edges. What does not survive is the pretence that 100 hand-adjudications measure it to two
   points.

   ### How much weight can drop rate carry? Measured on real reviews, and the instrument failed

   **Fetched live: 1,213 inline review comments on `.py` files across eight public
   repositories** — the closest public analogue to what this reviewer emits, attached to a file
   and about specific code. Classified into *not a finding*, *structural*, *semantic*.

   **The classifier is not trustworthy and the number it produced should not be quoted.** 56.5%
   fell into the residual bucket, which means the patterns did not cover most of the content.
   Reading the printed samples, every bucket contains obvious errors: *"Can you add type
   annotation for the returns?"* was filed as not-a-finding because it ends in a question mark;
   *"It creates it if it doesn't exist"* was filed structural on the phrase "doesn't exist";
   *"i think the return type is a dictionary"* — a genuinely structural claim — landed in the
   residual.

   **The residual is not only a defect — it is the result.** A keyword classifier failing to
   cover 56.5% of review content is evidence the content **is not keyword-shaped**. The samples
   say the same from the other side: *"i think the return type is a dictionary"* is a structural
   claim carried entirely by hedged natural language, with no token a pattern could key on.

   **So the survivable statement is stronger than "structural claims are a minority". It is that
   structural claims are not reliably identifiable from surface form at all.**

   **And that is a design consequence, not a measurement gap.** Stage four can only adjudicate
   the fields **the schema forces into structural shape** — not claims a model happens to make.
   If `infer/schemas.py` requires `claim_type`, `file`, `line_a`, `line_b`, `relation`, then
   **every finding is structurally checkable by construction**, and the surface form of natural
   language stops mattering.

   **Which replaces the question.** It is no longer *"what fraction of review claims are
   checkable"* — it is **"what fraction of USEFUL findings can be expressed in that form without
   distortion"**. That is answerable from the worked example and the schema, before any model
   runs, and it is the question `infer/schemas.py` has to be designed against.

   **So drop rate is a weak signal for choosing between models**, because it can only speak to
   the minority of findings a parser can touch. **The hand-adjudicated published-and-wrong rate
   is not one number of two — it is close to the whole test.**

   **A trustworthy version needs a real classifier**, which means hand-labelling or a model from
   another family — the instrument this project used before for exactly this reason, and cannot
   use now because no key is configured. Recorded as unmeasured rather than approximated.

   **It was re-run, and it found something bigger than the sampling bias.**

   A uniform draw across each repository's full page range — fixed seed, 3,812 comments,
   spanning 2019-03 to 2026-07 against the recent draw's narrow window — moved the structural
   share by a mean of 12.5 points per repository and 61 points at the extreme. But the largest
   mover, browser-use at 5.0% → 62.9%, was too large to be review-content drift, and inspecting
   it showed why:

   **A third of the inline review comments in this corpus are written by other AI review bots.**

   | repository | comments | bot | share | principal bot authors |
   |---|---|---|---|---|
   | browser-use/browser-use | 636 | 585 | **92.0%** | cubic-dev-ai, cursor |
   | Skyvern-AI/skyvern | 536 | 463 | **86.4%** | github-advanced-security, ellipsis-dev |
   | cartography-cncf/cartography | 724 | 270 | 37.3% | cubic-dev-ai |
   | vllm-project/vllm | 684 | 171 | 25.0% | gemini-code-assist, cursor |
   | langchain-ai/langchain | 668 | 96 | 14.4% | open-swe, corridor-security |
   | bespokelabsai/curator | 653 | 54 | 8.3% | cursor |
   | apache/airflow | 583 | 0 | 0.0% | — |
   | huggingface/transformers | 711 | 0 | 0.0% | — |
   | **all** | **5,195** | **1,639** | **31.5%** | |

   **The contamination pointed the same way as the thing being measured**, which is why it was
   invisible: of comments that assert anything, **bot output is 52.9% structural against a
   human's 5.9% — nine times the rate.** A templated `### Bug: … **Medium Severity**` block
   matches structural patterns almost by construction. Neither earlier fetch stored the author,
   so neither could subtract it. **Fourth instance of the same defect class: a machine artefact
   wearing a corpus label.**

   **On human comments only, the sampling objection survives but changes character.** Mean
   absolute shift 12.5 points, maximum 61 — the scheme moves the answer a lot — but 6 of 8
   repositories moved *down* and the sign test is p = 0.29. **Recency is a noise source, not a
   directional bias**: it does not inflate or deflate the figure predictably, it makes any single
   draw unreliable. Both affected numbers were already discarded, so nothing published moves.
   The corrected reader is `research/phase0/corpus/fetch.py`.

   **The bot detector was then given a known-answer test, and passed one it could have failed.**
   It is a login-and-marker match; it is never shown a date. If it is really detecting AI
   reviewers, its rate must collapse to zero before those tools existed:

   | year | comments | bot share | human structural |
   |---|---|---|---|
   | 2019 | 234 | **0.0%** | 9.9% |
   | 2020 | 301 | **0.0%** | 4.2% |
   | 2023 | 573 | **0.0%** | 3.0% |
   | 2024 | 468 | 8.1% | 4.3% |
   | 2025 | 1,352 | 38.4% | 4.2% |
   | 2026 | 2,267 | **47.7%** | 7.8% |

   **Zero through 2023, then a monotone climb tracking the adoption curve of the tools by name.**
   A detector matching something else — verbosity, templating, length — would not respect a
   boundary it was never told about.

   **And the same table answers the era question the sampling objection implied.** Only three
   repositories predate 2022, so era is confounded with repository; comparing *within* repository
   across the boundary: pre-2022 **6.7%** (25/374) against 2023+ **6.5%** (55/850), **p = 0.889**.
   Airflow moved +5.9 points and transformers −5.3, in opposite directions. **The human
   structural rate does not depend on the era**, which means the figure is not an artefact of the
   AI-reviewer period or of the bot subtraction — it is what human review has looked like for
   seven years.

   **Two things are worth keeping.** The human structural rate lands at **5.9%** (132/2,241) —
   computed on a seven-year window with bots removed, and pointing the same way as the discarded
   figure: **structural claims are rare in human review, so a verifier that waits for a model to
   volunteer one will mostly wait.** That is the argument for forcing structure through the
   schema rather than detecting it in prose. And separately: **on repositories that have adopted
   an AI reviewer, the AI writes most of the inline comments** — 92.0% and 86.4% at the top.
   That is a statement about volume and nothing else. It is not evidence about quality and must
   not be published as if it were.

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

**Checked against what the competition already holds, because this is the one area where being
behind loses a deal before anyone sees the product.** Greptile lists SOC 2 Type II, self-hosted
deployment, SSO/SAML, GitHub Enterprise compatibility and a custom DPA. CodeRabbit lists SOC 2
Type II, GDPR, SSO, audit logs, zero-retention options and self-hosting. **Both hold SOC 2
Type II today.**

### The item that cannot be triggered on demand

**SOC 2 Type II is the gate, and it has a lead time that breaks the trigger below if ignored.**

A Type II report needs an *observation window* — typically three to six months for a first
audit — on top of readiness work and fieldwork. **Roughly six to nine months from kickoff to a
report**, and the auditor cannot compress the window, because the window is the evidence. Budget
in the region of $20,000–$60,000 all in for a company this size. *(Figures from published
guidance; confirm with an auditor before planning against them.)*

**So it cannot start when the first questionnaire arrives.** Starting then means losing that deal
and the two behind it. **It starts when enterprise becomes a target, not when it becomes
urgent** — and a Type I report is what covers the gap, since it needs no observation window and
demonstrates the controls exist.

### Steps

1. **Begin SOC 2 readiness on the decision to sell to enterprise.** Everything else here is
   evidence that feeds it.
2. `serve/audit_log.py` — append-only: who changed configuration, when, from where. **Separate
   from application logs**, because the first question in an audit is whether the log could have
   been edited.
3. Data residency — region-pinned storage, chosen at install and not migratable afterwards.
4. **Zero-retention mode** — asked for by name by regulated buyers, and a competitor already
   offers it. Nothing but the review record persists; no diff content at rest.
5. Self-hosted deployment: container, migrations run by command, an offline licence check that
   **fails open**. A licence check that fails closed takes a customer's reviews down over our
   billing problem.
6. **GitHub Enterprise Server**, which is not github.com — a different API surface, self-hosted by
   the customer, and a real engineering item rather than a configuration flag. A competitor lists
   it; assume it will be asked for.
7. Retention controls, and contractual no-training in writing. **A custom DPA has legal lead
   time** and is not an engineering task.
8. SLA measurement before an SLA is offered. **We do not have latency numbers**, and the rule
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
| Procurement surface | **SOC 2 readiness on the decision to target enterprise; the rest on the first questionnaire** | The report needs a three-to-six-month observation window, so triggering on the questionnaire loses that deal |

**Only the budget ceiling is unconditional.** The rest are sold on the price list and built when
someone tries to buy them — which is the honest way to run a four-tier table with no customers
yet, provided the table does not promise a delivery date.

---
