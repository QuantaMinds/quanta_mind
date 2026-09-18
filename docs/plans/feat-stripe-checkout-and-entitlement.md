# Checkout, a signed subscription webhook, and the first `payment_verified: true`

**Branch:** `feat/stripe-checkout-and-entitlement`. **Status: PLAN.** Written first because it
changes `verify/tier_request.py`, which `AGENTS.md` "Working rules" requires, and because the
field it changes is a tripwire somebody installed on purpose.

## What is being asked for

Build row **B3** of `docs/plans/roadmap/product-build.md` — Stripe checkout and subscription
webhooks — parked by decision 2026-08-27, unparked 2026-09-17 by the owner of the account.

Three things, in dependency order:

1. A checkout session a signed-in account can be sent to.
2. A Stripe webhook that authenticates, refuses a replay, and records what the subscription IS.
3. `payment_verified` stops being a constant.

## The tripwire this removes, and why it must not be removed carelessly

`verify/tier_request.py:Verdict.__post_init__` **raises** if anybody sets `payment_verified=True`:

> *"payment_verified cannot be True: B3 is parked and nothing here reads a payment processor. The
> field exists to carry that fact, not to be set."*

That is the correct shape for a field that must never be set by accident, and the change here is
**not** to delete the check. It becomes: `payment_verified=True` is admissible **only when the
verdict was built from a subscription row this product wrote from an authenticated Stripe
delivery.** A caller who merely passes a `payment_ref` string still gets the refusal it gets today.

**The distinction is the whole point of the row.** `payment_ref` is what a caller SENT.
A subscription row is what Stripe TOLD US over a signed channel. Collapsing them would give the
endpoint the appearance of verification and none of it, which is worse than today's honest false.

## What already exists and is not rebuilt

| | where | what it gives this change |
|---|---|---|
| HMAC webhook verification | `serve/webhook_github.py` | the shape: verify bytes before parse, constant-time compare, an unset secret RAISES |
| replay refusal | `store/deliveries.py` | `begin()`/`complete()` keyed on a delivery id, already used by the listener |
| POST dispatch | `serve/listener.py:_post` | a prefix branch, added for `serve/web/provision_route.py` |
| tier admission | `verify/tier_request.py` | every rule except the one about money |
| entitlement at review time | `store/installations.py:Entitlement.may_review` | the thing a lapsed subscription has to be able to close |
| outbound-call permission | `types/deployment.py:permit` | air-gapped must REFUSE Stripe, not merely fail to reach it |

## The dependency decision, stated rather than assumed

**No Stripe SDK. `pyproject.toml` declares `dependencies = []` and it stays that way.**

What this needs from Stripe is: form-encoded POSTs to two endpoints, and an HMAC-SHA256 compare.
`serve/listener.py` already argues this for the HTTP server — *"a framework would be paid for on
every install to save perhaps forty lines"* — and the argument is stronger here, because the SDK
would arrive with its own HTTP client, its own retry policy and its own telemetry in a product
whose deployment story includes air-gapped.

**The cost is named:** we hand-write the signature check and the form encoding, and we do not get
the SDK's API-version pinning for free. The version is therefore pinned explicitly in a header by
`ingest/payments/stripe_api.py`, which the SDK would otherwise have done.

## Pricing, as decided 2026-09-17 and as it disagrees with what is live

**One paid tier. $29/month, recurring.** Decided by the account owner.

**The live account disagrees, and nothing in this branch touches live to fix it.**
`prod_V9YxGzPjNwa8vQ` carries `price_1U9FpWGwi83EhBSFIbuj2gSP` at **$39.00/month**. That price is
stale against this decision and against `docs/product/pricing.md`, which sells $29. Archiving it is
an act against a live payment account and is the owner's to make, not this branch's.

**Enterprise gets no checkout session, and that is a decision rather than an omission.**
`verify/tier_request.py` already refuses Enterprise without an `org`, and the tier's distinguishing
terms — SSO, a DPA, residency, an SLA — are contract terms signed before money moves.
`POST /billing/checkout` therefore serves `Tier.TEAM` and refuses the other two by name:
Free needs no payment, Enterprise is invoiced.

## The modules

Layer order is `types → store → ingest → parse → rank → allocate → infer → verify → render →
serve`. Every import below is leftward.

| new | layer | one concern |
|---|---|---|
| `types/billing.py` | types | `Lapse`, `Subscription` — what a subscription IS, with no way to spell "probably paid" |
| `store/subscriptions.py` | store | write one subscription row, read the current one for an account |
| `ingest/payments/stripe_api.py` | ingest | one authenticated form-encoded call to Stripe; `permit()` first; raises on every non-2xx |
| `ingest/payments/checkout.py` | ingest | build one Checkout Session for one account and price |
| `serve/webhook_stripe.py` | serve | `verify()` over bytes, `interpret()` over an authenticated payload — pure functions, no socket |
| `serve/web/billing_route.py` | serve | `POST /billing/checkout` and `POST /billing/webhook` |

`ingest/payments/` is a new directory because `ingest/` holds thirteen files and
`scripts/guard/check_structure.py` caps a directory at fifteen.

| changed | why |
|---|---|
| `types/deployment.py` | `Destination.PAYMENTS`. Air-gapped refuses it; `check_network_chokepoint.py` fails the build if `stripe_api.py` opens a socket without asking |
| `types/settings.py` | `stripe_price_id`, `billing_return_url`. **No secret** — see below |
| `store/tables.py`, `store/schema.py`, `store/migrations.py` | the `subscription` table, `SCHEMA_VERSION` 7 → 8, and `_to_8` |
| `store/installations.py` | `Entitlement` learns that a lapsed paid subscription is not the same as an unassessed one |
| `verify/tier_request.py` | the tripwire above |
| `serve/listener.py` | one prefix branch |
| `serve/commands/run_endpoint.py` | reads the two Stripe secrets from the environment and refuses to serve the billing routes without them |

**Neither Stripe secret goes into `Settings`.** `types/settings.py` states the rule for the webhook
secret — *"a credential in a settings object reaches a log or a config dump the first time anybody
prints one"* — and `quantamind config` prints that object. The API key and the webhook signing
secret are read in `run_endpoint.py` beside `QUANTAMIND_WEBHOOK_SECRET`, which already does exactly
this, and are passed down as parameters.

## Stripe's signature is not GitHub's, and the difference is worth having

`serve/webhook_github.py` says it plainly:

> *"VERIFICATION IS NOT REPLAY PROTECTION, and GitHub does not close that gap for us. Its signature
> covers the body and nothing else — there is no timestamp in it, unlike Stripe's."*

Stripe sends `Stripe-Signature: t=<unix>,v1=<hex>,v1=<hex>` and signs `f"{t}.{body}"`. So:

- **The timestamp is inside the MAC**, and a delivery older than the tolerance is refused. A
  captured GitHub delivery stays valid forever; a captured Stripe one does not.
- **There can be more than one `v1`**, during a secret rotation. Every one is compared, all in
  constant time, and a match on any is a pass. Reading only the first breaks rotation — silently,
  and only for the customer who rotates.
- **`store/deliveries.py` is still used**, keyed on the event id. The timestamp bounds the window;
  it does not make a delivery single-use, and Stripe retries with the same id for three days.

**The tolerance is 300 seconds and it is a CEILING on clock skew, not a guess.** A container with
a clock five minutes out rejects every real delivery, which looks exactly like a bad secret. The
refusal therefore names the skew it measured rather than saying "bad signature".

## What is recorded, and the three states it must be able to tell apart

`subscription`, one row per `(account, subscription_id)`, written only from an authenticated
delivery:

- **`lapse` is a named state, never a boolean.** `ACTIVE`, `PAST_DUE`, `CANCELED`, `UNPAID`. A
  boolean `active` cannot tell "they cancelled" from "their card failed on Tuesday", and those need
  different answers from us and different emails to them.
- **`current_period_end` is stored**, so entitlement can answer *"paid through the 3rd"* rather than
  *"not active"* on the day a renewal is retrying.
- **Nothing is backfilled by the migration.** No account had a subscription before this table, so
  there is nothing to write, and writing one would be inventing a payment.

## What this does to `may_review`, which is the part that can cut off a paying customer

`store/installations.py:Entitlement.may_review` today returns `self.eligible is not False`, and its
docstring records the last time that rule changed and why.

**This branch does not change `may_review`.** The subscription state is recorded and reported and
does NOT yet gate a review. That is deliberate: the gate is one line and the blast radius is every
paying customer, and the honest order is to record the state, watch it agree with Stripe's
dashboard for real deliveries, and close the gate in a second change that can be reverted alone.

**Said here so it cannot be read as an oversight**, and so the follow-up is a row rather than a
memory.

## Emails are not in this branch

Receipts and dunning are their own change, and the decision taken 2026-09-17 is that the sender is
built behind an interface that **records and prints** rather than sends, switching to a real
provider with one environment variable. Nothing here sends anything.

## What could still silently fail

- **The webhook secret is unset and the route is reachable.** Same failure the provisioning route
  was designed against. `verify()` raises on an empty secret the way `serve/webhook_github.verify`
  does, and `build()` refuses to serve the billing routes without one — belt and braces, because
  the two have different reachability and a test of the configured path says nothing about the
  unconfigured one.
- **A delivery arrives for an account we do not have.** Stripe knows a customer id; we know a
  GitHub login. The link is `client_reference_id`, set at checkout. A delivery whose reference
  names no account is **recorded as unmatched and answered 200** — answering non-2xx would make
  Stripe retry for three days something that will never match, and dropping it silently would lose
  a payment we took.
- **Two deliveries for one subscription arrive out of order.** Stripe does not guarantee order.
  The row carries the event's `created` timestamp and an older event does not overwrite a newer
  one. **This is the defect most likely to survive review**, because in every test written by hand
  the events arrive in order.
- **The price id in the environment names a product that is not the $29 one.** Nothing in this
  product can tell. It is configuration, and the checkout session reflects whatever it is given.
  The session's returned amount is recorded so a wrong price is visible in the row afterwards
  rather than only on an invoice.
- **A `Verdict` is built with `payment_verified=True` from a subscription that has since lapsed.**
  The verdict is a statement about the instant it was made, and provisioning acts on it
  immediately. Nothing here re-checks it later — that is the `may_review` gate above, deferred.

## Sabotage, before any of it is believed

`AGENTS.md` rule 14, and the memory that a same-length edit inside one second can reuse a stale
`.pyc` — every item below deletes `__pycache__` first and breaks the **mechanism**, not the entry
point.

1. **Replace `hmac.compare_digest` with `==`** in `serve/webhook_stripe.py` → nothing will fail,
   the same way it does not in `serve/webhook_github.py`. **Recorded as uncovered rather than
   claimed**, and `scripts/guard/runtime/check_constant_time_compare.py` is what actually holds it.
2. **Return `None` unconditionally from `verify()`** → the forged-signature test must fail. If it
   passes, the test is asserting on a shape rather than on a decision.
3. **Unset the webhook secret** → every billing route must refuse, and the refusal must be asserted
   directly rather than inferred from a configured route returning 200.
4. **Make the timestamp tolerance infinite** → the replay test must fail. A tolerance nothing tests
   is a constant, and `test-the-value` says 95 of 130 product constants could be changed green.
5. **Hand `interpret()` a payload with `v1` matching and `t` in the future** → must refuse. A
   forward clock is the case a naive `now - t < 300` admits.
6. **Delete the `created`-ordering guard in `store/subscriptions.record`** → the out-of-order test
   must fail. This is the one I expect to survive, so it is written first.

## Definition of done for this branch

The seven in `AGENTS.md`, and one more that is specific to it: **a real Stripe delivery, from a
sandbox, verified by this code** — recorded in the live test, not asserted from a hand-built
payload. A signature checker that has only ever seen payloads its own `sign()` produced has been
tested against itself.

---

# What actually happened — written after the build, 2026-09-17

**Status: BUILT.** `just check` green. The plan above is left unedited; this section records where
it was wrong, what the build found, and what is still not done.

## Two things the plan did not anticipate, both found by running it

**`current_period_end` does not exist on the subscription object.** The plan said it would be read
"off the ITEM first… the top level is read as a fallback", which turned out to be understated: under
`2026-08-26.dahlia` the field is **absent from the subscription entirely**. A reader written against
the top level — which is what every older example shows — would have recorded 0 for every
subscription and made every paying customer look period-less. Confirmed against a captured delivery,
now pinned by `tests/fixtures/stripe_subscription_created.json` and asserted in
`tests/unit/layers/serve/test_stripe_event.py`.

**Reading the subscription created a database on refused requests.** The first version of
`serve/web/provision_route.py` opened the accounts store to look up the subscription before
validating. `open_store` CREATES the file, so every refused provisioning request left one behind —
breaking an invariant a test had been asserting for weeks, and which caught it on the first run. The
read moved into `serve/web/provision_payment.access_for`, which refuses to open a store that does
not exist. `serve/web/routes.py` already makes this exact argument about `/`; it was not applied
here until the test said so.

## One thing built that the plan deliberately excluded

**`verify/paid_access.py`** — asked for mid-build. It decides open-or-blocked from a subscription
and a clock, with a named verdict per case. It is wired into `verify/tier_request.py` and
`serve/web/provision_route.py` and **is still not wired to `store/installations.py:
Entitlement.may_review`**, for the reason the plan gives.

**`NO_SUBSCRIPTION` is not "blocked", and that conflict was raised rather than resolved silently.**
`docs/product/pricing.md` sells a free tier that does not expire. A module that answered "blocked"
for an account with no subscription would turn the free tier off with one import.

## Four files the plan did not predict, all from the 200-line cap

`serve/web/post_routes.py`, `serve/web/get_reply.py`, `serve/web/provision_payment.py` and
`serve/web/provision_request.py`. The plan said *"the listener has no seam for this, and making one
is most of the change"* and was right about the shape and wrong about the count.

**`get_reply.py` is the one worth reading.** Folding `/health` into it was not a line count: health
was the single GET that wrote itself through the handler instead of returning a `Reply`, so the only
way to exercise it was to bind a port. The bytes are unchanged.

## The schema golden found a hole that predates this branch

`tests/unit/layers/store/test_schema_golden.py` derived its "version 2" store by removing only what
version 3 added. Every migration step creates with `CREATE TABLE IF NOT EXISTS`, so steps 4 through
7 ran against a store that already had their tables, created nothing, and passed — **four migration
steps that were green whether they worked or not**, for five schema versions. Found because adding
step 8 was about to widen it. `ADDED_AFTER_2` now names every table per version, and a new test
asserts the starting state genuinely lacks them.

## Sabotage, as promised — every item run, `__pycache__` deleted first

| mechanism broken | result |
|---|---|
| period boundary `<=` → `<` | 2 failed |
| grace window made effectively infinite | 4 failed |
| stale record reported as `PAID` | 2 failed |
| every verdict declared open | 10 failed |
| ordering guard deleted from the upsert | 8 failed |
| redelivery repair turned off (`>=` → `>`) | 1 failed |
| every write reported as stored | 2 failed |
| period read from the subscription only | 1 failed |
| unmatched subscription given a fake account | 1 failed |
| unknown-status reason emptied | 1 failed |
| seat count hardcoded to 1 | 1 failed |

Each file was restored and confirmed byte-identical afterwards. **Item 1 of the plan's sabotage list
— replacing `compare_digest` with `==` — is still uncovered by any test**, as predicted;
`scripts/guard/runtime/check_constant_time_compare.py` holds it.

## The live exercise the definition of done asked for

Against sandbox `acct_1U9FQPGY5MuBVWoy`, with `stripe listen` forwarding real deliveries:

- `customer.subscription.created` → verified, recorded whole: `octocat`, 3 seats, $29.00, period
  ending 2026-10-18
- `customer.subscription.deleted` → `canceled`, and `paid_access.decide` → `CANCELED / blocked`
- a resent event → refused by the delivery ledger
- forged / absent / stale signatures → 401, each with its own reason
- `POST /billing/checkout` with no session → 401

**This is a manual procedure, not a test.** `tests/live/` does not cover Stripe, because a path
needing a Stripe key and outbound network would fail `just verify` on any machine without one. That
is weaker than the definition of done asks for and is not being presented as anything else.

## Still not done

1. **`may_review` is not gated.** Deliberate; see above.
2. **The live account's $39 price** contradicts the $29 decision and `docs/product/pricing.md`.
3. **Receipts and dunning.** Decided 2026-09-17: a sender behind an interface that records and
   prints, switching to a real provider with one environment variable. Nothing is built.
4. **`.env` holds four Stripe names that nothing reads** — `STRIPE_Publishable_key`,
   `STRIPE_Secret_key`, `STRIPE_LIVE_SECRET_KEY`, `STRIPE_LIVE_PUBLISHABLE_KEY`. The code reads
   `QUANTAMIND_STRIPE_API_KEY` and `QUANTAMIND_STRIPE_WEBHOOK_SECRET`. A variable nothing reads is
   worse than an absent one, because it looks configured.
