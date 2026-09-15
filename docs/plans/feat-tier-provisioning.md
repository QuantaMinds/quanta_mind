# Three provisioning routes, one per tier — and the thing that must not be built carelessly

**Branch:** `feat/tier-provisioning`. **Status: PLAN.** Written first because it touches `verify/`,
which `AGENTS.md` "Working rules" requires, and because the obvious implementation of this endpoint
is a way for anybody on the internet to grant themselves a paid tier.

## What is being asked for

Three routes, called after a payment completes, that validate a tier's criteria and then provision:
link the account, admit the repositories, and warm them.

```
POST /provision/free
POST /provision/team
POST /provision/enterprise
```

## The security problem, stated before the design

**THERE IS NO PAYMENT SYSTEM.** `docs/plans/roadmap/product-build.md` rows **B3** (Stripe checkout
and subscription webhooks) and **B7** (BYOK) are **parked by decision, 2026-08-27**. Nothing in
`src/` talks to Stripe.

So "once the payment is done" describes a caller that does not exist, and this endpoint cannot
verify a payment against anything. **A `payment_ref` field is a string we record, not a fact we
check** — and an unauthenticated POST that grants `tier=enterprise` on a made-up reference is not a
provisioning endpoint, it is a free upgrade for anyone who can reach the port.

**Two consequences, both non-negotiable:**

1. **The routes authenticate with a shared secret**, `QUANTAMIND_PROVISION_SECRET`, compared with
   `hmac.compare_digest`. Same reasoning as the webhook's HMAC: `scripts/guard/runtime/
   check_constant_time_compare.py` exists because a `==` on a secret leaks it one byte at a time.
   **A missing or empty secret refuses the route entirely** rather than defaulting to open — the
   `permit()` pattern, not the "no route configured" pattern.
2. **The response says what was verified and what was only recorded.** `payment_verified: false`
   ships in every paid-tier reply until B3 exists. A field that silently means "we took your word
   for it" is the shape this project refuses everywhere else.

## What each tier actually validates — and two of them are thinner than they sound

| | Free | Team | Enterprise |
|---|---|---|---|
| Repository eligibility (`verify/qualification.qualifies`) | **yes** | no | no |
| Global cap — `FREE_REPOS_TOTAL` = 40 | **yes** | no | no |
| One free repository per account | **yes** | no | no |
| Seats declared | no | **yes** | **yes** |
| Payment reference present | no | **yes** | **yes** |
| An organisation named | no | no | **yes** |

**Free is the only tier with a real gate, and that is not an accident.** The eligibility rules exist
because we give it away: stars, contributors, history length, recent activity, and a cap of forty
places. A paying customer has already answered the only question those rules were asking.

**Team and Enterprise differ in almost nothing a program can check.** SSO, a DPA, residency and an
SLA are contract terms, not validations. **The one genuine difference is `org`**: Enterprise sells
"define a standard once; every repository is held to it", and `ingest/standards/inherited.py` reads
those from an organisation's `.quantamind` repository. **Without an organisation named, the feature
that distinguishes the tier has nowhere to read from**, so the route refuses.

**Three routes that mostly agree is honest here, and pretending otherwise would not be.** The
alternative — inventing per-tier checks so the table looks full — is how a validation comes to exist
for the shape of the documentation rather than for anything it protects.

## Shared validation, every tier

- The account is named and non-empty.
- Every repository is `owner/name`. `store/installations.record` already refuses otherwise, and
  `store/tenancy._segment` refuses `..` and separators — **the path is derived, never taken from the
  payload**.
- Nothing is provisioned unless **every** repository passes. A partial provision leaves a customer
  paying for repositories that were not admitted, and no reply shape makes that legible.

## What it does after validating

1. `store/installations.record(conn, account, repo, at, tier, eligible, reasons)` — one row per
   repository, carrying the tier and, for Free, the verdict's reasons.
2. `tenancy.provision()` for the store files.
3. **Warming is not inline.** A clone plus an index is ~31 seconds on a large repository and no
   caller waits that long. `serve/onboarding.admit()` already does this after the response, which is
   the same acknowledge-then-work shape the webhook uses for the same reason.

So the route answers **202** with what it accepted, not **200** with work it has not done.

## The listener has no seam for this, and making one is most of the change

`serve/listener.py` delegates every non-health GET to `routes.get`, which returns a `Reply` rather
than writing to a socket. **`do_POST` has no equivalent** — it handles `/webhook` inline and 404s
everything else — and the file is **at the 200-line cap**, so the branch cannot simply be added.

**The `Installed` branch moves to `serve/onboarding.py`, where it belongs anyway.** It provisions
store files, prints two lines and calls `admit()` — installation work sitting in the socket layer.
Moving it frees the lines the dispatch needs and puts the code beside the function it already calls.

## What could silently fail

- **The secret is unset and the route is reachable.** Refused by construction, and a test must
  assert the refusal rather than assert a 200 on a configured one — the configured path passing
  says nothing about the unconfigured one.
- **A paid tier is granted on an unverified reference.** True today and unavoidable until B3. It is
  in the response as `payment_verified: false` so it cannot be forgotten, and this plan is the
  record that it was a decision.
- **A repository is admitted twice at different tiers.** `record()` is idempotent per
  `(account, repo)` and upserts the tier, so the last write wins. **That is correct for an upgrade
  and wrong for a downgrade nobody intended**, and nothing currently distinguishes them.
- **Warming fails after a 202.** The installation row exists and the index does not, which
  `GET /scan` already reports as `scanned: false` — a named state rather than an empty one.

## Sabotage, before any of it is believed

1. **Unset the secret** → every provisioning route must refuse. A green suite here means the check
   runs only where it cannot fail.
2. **Post a valid Team body to `/provision/free`** → must be refused by the eligibility gate, not
   quietly admitted because the fields happened to parse.
3. **Post one good and one malformed repository** → nothing provisioned, both named in the refusal.
4. **Post Enterprise with no `org`** → refused, because the tier's one distinguishing feature has
   nowhere to read from.
