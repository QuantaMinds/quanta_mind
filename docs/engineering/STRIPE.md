# Stripe, end to end

**What this document is.** Every call this product makes to Stripe, every delivery it accepts from
Stripe, the exact syntax of both, what comes back, and what each piece is for. It is written for
somebody who joined this morning and has never seen the code.

**Status.** Build row **B3** of `docs/plans/roadmap/product-build.md`, parked by decision
2026-08-27 and unparked 2026-09-17. The design record, including what was deliberately left out,
is `docs/plans/feat-stripe-checkout-and-entitlement.md`. The codebase map is the
"Billing — Stripe checkout, subscription deliveries, and what they entitle" section of
`docs/engineering/CODEBASE.md`.

---

## 1. The shape of it in one picture

```
  a signed-in browser                    Stripe                      our endpoint
  ───────────────────                    ──────                      ────────────
  POST /billing/checkout  ──────────────────────────────────────────────►
        (cookie: qm_session)                                      checkout_route.answer
                                                                        │
                            ◄── POST /v1/checkout/sessions ─────────────┘
                                   stripe_api.call
                            ─── { id, url } ──────────────────────────► 200 {"url": ...}
  redirect to url  ─────────►  Stripe's hosted page
                               customer pays
                                     │
                                     ├── customer.subscription.created ──► POST /billing/webhook
                                     │      (signed: t=…,v1=…)              stripe_hook.answer
                                     │                                            │
                                     │                                   webhook_stripe.verify
                                     │                                   deliveries.begin
                                     │                                   stripe_event.interpret
                                     │                                   subscriptions.record
                                     │                                   deliveries.complete
                                     │                                            │
                                     │                              ◄─────── 200 {"applied": true}
                                     │
                                     └── .updated / .deleted, for the life of the subscription
```

**Two halves, two different proofs of who is calling.** Checkout is authenticated by a session
cookie — a human is asking to buy something. The webhook is authenticated by an HMAC over the
request body — Stripe is telling us something happened. They share a URL prefix and nothing else,
which is why `serve/web/post_routes.py` matches each path exactly instead of guarding `/billing/`
once. One guard would necessarily be the wrong guard for one of them.

---

## 2. The account, the product, and one number that disagrees

| | value |
|---|---|
| Live account | `acct_1U9FQIGwi83EhBSF` — "QuantaMind" |
| Sandbox | `acct_1U9FQPGY5MuBVWoy` — "QuantaMind sandbox", test mode |
| API version | `2026-08-26.dahlia` — read off a real `Stripe-Version` response header, not chosen |
| Sandbox price | `price_1UGfiCGY5MuBVWoyiOyqLh6G` — **$29.00/month recurring**, `licensed` per-unit, on `prod_VHEAhvZFFjtj5Y` |

**The live account still carries a $39.00/month price** — `price_1U9FpWGwi83EhBSFIbuj2gSP` on
`prod_V9YxGzPjNwa8vQ`. The decision of 2026-09-17 is **one paid tier at $29/month**, which is also
what `docs/product/pricing.md` sells. **Nothing in this codebase touches the live account**, so
archiving that price is a deliberate act somebody has to perform in the Dashboard. Until then, the
live account and the published price page disagree, and this paragraph is the record of it.

**The price is per-unit `licensed`, so the quantity IS the seat count.** Selling per-seat later
needs no new price — only a quantity above 1, which `POST /billing/checkout` already sends.

---

## 3. Configuration: every variable, what reads it, and what happens when it is unset

**All five are read from the process environment first and the repository `.env` second**, the
same precedence `types/settings.load()` uses. An exported variable always wins, so nothing a
deployment sets can be overridden by a file in a working tree.

| variable | read by | absent means |
|---|---|---|
| `QUANTAMIND_STRIPE_API_KEY` | `serve/commands/run_endpoint.py` via `types/dotenv.credential`, passed to `build(billing=…)` | `POST /billing/checkout` answers **503** naming the variable |
| `QUANTAMIND_STRIPE_WEBHOOK_SECRET` | same | `POST /billing/webhook` answers **503**; no delivery can be authenticated |
| `QUANTAMIND_STRIPE_PRICE_ID` | `types/settings.py` → `Settings.stripe_price_id` | checkout answers **503** |
| `QUANTAMIND_BILLING_SUCCESS_URL` | `Settings.billing_success_url` | Stripe returns the browser to an empty URL — set it |
| `QUANTAMIND_BILLING_CANCEL_URL` | `Settings.billing_cancel_url` | as above |

**The two credentials are NOT on `Settings` and that is not an oversight.** `types/settings.py`
states the rule for the GitHub webhook secret — *"a credential in a settings object reaches a log
or a config dump the first time anybody prints one"* — and `quantamind config` prints that object.
They are read in `serve/commands/run_endpoint.py`, beside `QUANTAMIND_WEBHOOK_SECRET`, and passed
down as parameters.

**They are read through `types/dotenv.credential` rather than `os.environ`, and that is a repair.**
Until 2026-09-18 `run_endpoint.py` read the process environment directly while
`types/dotenv.from_file` deliberately never writes to it — so **a `.env` holding
`QUANTAMIND_WEBHOOK_SECRET` produced "no webhook secret: refusing to bind"**. Three credentials in
that file were read by nothing, and no test could see it because every test that exercised the
endpoint supplied the value some other way. Found by running the command with nothing exported.

**The price id IS on `Settings`, deliberately.** It is public the moment a customer sees a checkout
page, and the whole point of holding it there is that `quantamind config` can show an operator what
is being sold before a customer finds out.

**Unset refuses; it never opens.** "Not configured" and "no payment required" are the same code
path in most handlers and must not be in this one. The startup banner reports which of the two
states each route is in, computed from the values rather than written as a claim:

```
[serve] POST /billing/checkout — creates a Stripe session against price_1UGfiCGY5MuBVWoyiOyqLh6G
[serve] POST /billing/webhook  — verifies Stripe's signature and a 300s timestamp, then records …
```

---

## 4. `ingest/payments/stripe_api.py` — the one outbound call

### `call(path, *, api_key, method="POST", params=None, idempotency_key=None) -> dict`

```python
from quantamind.ingest.payments.stripe_api import call

session = call(
    "v1/checkout/sessions",
    api_key=key,                     # sk_test_… or sk_live_…
    method="POST",                   # default
    params={"mode": "subscription", "line_items": [{"price": PRICE, "quantity": 3}]},
    idempotency_key="a-stable-hash", # optional; same key replays the first response
)
```

**What it sends.** `POST https://api.stripe.com/v1/checkout/sessions` with these headers:

| header | value | why |
|---|---|---|
| `Authorization` | `Bearer <api_key>` | |
| `Stripe-Version` | `2026-08-26.dahlia` | **pinned.** Without it the account default applies, and Stripe changing that default silently changes the shape of every object we read — a breakage with no deploy behind it |
| `Content-Type` | `application/x-www-form-urlencoded` | Stripe's v1 API accepts **no JSON request bodies** |
| `User-Agent` | `quantamind` | |
| `Idempotency-Key` | caller's, when given | the same key replays the first response instead of creating a second subscription |

**What it returns.** The parsed JSON object, as a `dict[str, Any]`. Stripe's objects are
heterogeneous; narrowing further here would be inventing a schema we do not own.

**What it raises.** `PaymentsFailed(method, path, reason)` on:

| case | `reason` |
|---|---|
| empty `api_key` | refuses before the socket — an unauthenticated call to a payments API is never right |
| any non-2xx | `HTTP 400: No such price: 'price_x' [resource_missing]` — **Stripe's own sentence**, because collapsing it to "payment failed" throws away the only text saying whether the fault is our code or their configuration |
| unreachable | `could not reach Stripe: <urllib reason>` |
| no answer in 30s | `Stripe did not answer within 30s` |
| 2xx with a non-JSON body | named, rather than returned as an empty object |

**It never returns a value on failure.** Returning one is how a broken call becomes a quiet no-op,
which this project has already paid for four times.

**`permit(Destination.PAYMENTS)` runs before the socket opens.** An air-gapped deployment refuses
Stripe rather than timing out against it, and `scripts/guard/runtime/check_network_chokepoint.py`
fails the build if that line is removed. On-prem is permitted; air-gapped is not.

### `encode(params, prefix="") -> list[tuple[str, str]]`

Stripe's bracket form encoding, flattened to pairs. This exists because there is no SDK doing it.

| input | output |
|---|---|
| `{"mode": "subscription"}` | `mode=subscription` |
| `{"line_items": [{"price": "p", "quantity": 3}]}` | `line_items[0][price]=p&line_items[0][quantity]=3` |
| `{"subscription_data": {"metadata": {"account": "octocat"}}}` | `subscription_data[metadata][account]=octocat` |
| `{"expand": ["a", "b"]}` | `expand[0]=a&expand[1]=b` |
| `{"x": None}` | *dropped* |
| `{"x": False}` | `x=false` |

**`None` is dropped and `False` is not.** `str(None)` is the four characters `None`, which Stripe
would read as a value. An omitted optional and a deliberate false cannot share a branch.

**A wrongly flattened structure does not error.** Stripe ignores parameters it does not recognise,
so a subscription would be created against no price or at the wrong quantity, and the first symptom
is an invoice. That is why `tests/unit/layers/ingest/test_stripe_encoding.py` compares the whole
encoded body rather than checking keys individually.

---

## 5. `ingest/payments/checkout.py` — creating a session

### `open_session(*, api_key, account, price_id, seats, success_url, cancel_url, idempotency_key=None) -> Session`

**Every argument is required and nothing is defaulted.** A default `seats=1` or a fallback price id
would each be a number this module invented appearing on somebody's card statement.

The body it sends:

```
mode=subscription
line_items[0][price]=price_1UGfiCGY5MuBVWoyiOyqLh6G
line_items[0][quantity]=3
client_reference_id=octocat
subscription_data[metadata][account]=octocat
success_url=https://quantamind.co/thanks
cancel_url=https://quantamind.co/pricing
```

**The account is carried TWICE, and that is not belt-and-braces — it is two different events.**

- `client_reference_id` appears on `checkout.session.completed` **and on nothing else**.
- Every later event — the renewal, the failed card, the cancellation — is about the SUBSCRIPTION,
  which has no reference id at all. So the account also goes into
  `subscription_data[metadata][account]`, where it lands on the subscription object itself and
  travels with every event for the life of it.

Setting only the first would attribute the signup and lose every event after it — **and the gap
would open a month later, on the first renewal, not on the day this ships.**

**Returns** `Session(session_id, url, account, price_id, seats)`. `url` is Stripe's hosted page.

**Raises** `PaymentsFailed` for an empty account, `seats < 1`, an empty price id, anything
`call()` raises, and **a 2xx that carries no `url`** — returning that would send a caller to
redirect a browser to `""`, which renders as the caller's own page and looks like the customer
changed their mind.

---

## 6. `POST /billing/checkout` — `serve/web/checkout_route.py`

**Request**

```
POST /billing/checkout
Cookie: qm_session=<token>
Content-Type: application/json

{"seats": 3}
```

**Response 200**

```json
{
  "url": "https://checkout.stripe.com/c/pay/cs_test_…",
  "session_id": "cs_test_…",
  "account": "octocat",
  "seats": 3,
  "paid": false,
  "note": "a session was created. Nothing is charged until the customer completes it, and entitlement changes only when the subscription webhook arrives."
}
```

**`paid: false` ships in every reply.** A caller that treated a created session as a completed
payment would grant access to a customer who closed the tab.

**Every other answer**

| status | when |
|---|---|
| 503 | `QUANTAMIND_STRIPE_API_KEY` and/or `QUANTAMIND_STRIPE_PRICE_ID` unset — **checked before the session is read**, so an unconfigured deployment answers the same to everyone rather than leaking that billing exists |
| 401 | not signed in, or a forged/expired token. **The reason is not given**: "expired" and "no such session" differ to us and not to a visitor |
| 400 | `seats` missing, not an integer, a JSON `true` (Python says `True == 1`; a boolean must not quietly buy one seat), `< 1`, or `> 5000` |
| 502 | Stripe refused. **Stripe's sentence goes to the log, not to the browser** — it can name a price id and an account, and this response is reachable by anyone who can sign in |

**The account comes from the session and never from the body.** A route that billed whichever
account the request named would attach a subscription to the wrong login, and the repair is a human
reading two dashboards side by side.

**The seat count DOES come from the body.** `docs/product/pricing.md` bills per developer who opened
a pull request, and nothing in this product measures that at checkout time. A number we derived
would put a claim about their team on their card statement.

**The idempotency key is `sha256(session_token : price_id : seats)`.** A double-clicked upgrade
button is one request repeated, and a key invented per call would differ each time — which is the
same as having none. Changing the seat count is a different intent and gets a different key.

---

## 7. The webhook signature — `serve/webhook_stripe.py`

### The scheme

Stripe sends:

```
Stripe-Signature: t=1789691888,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
```

The signed payload is `f"{t}."` followed by **the exact request bytes**, HMAC-SHA256 with the
signing secret (`whsec_…`), hex-encoded.

### `verify(secret, body, signature, *, at) -> Refusal | None`

Returns `None` when the delivery is authentic. Otherwise a `Refusal(reason, detail)`:

| `Reason` | when |
|---|---|
| `NO_SIGNATURE` | no header |
| `MALFORMED_SIGNATURE` | not `t=<int>`, no `v1`, or a `v1` that is not 64 hex characters |
| `TIMESTAMP_OUTSIDE_TOLERANCE` | `abs(at - t) > 300` |
| `BAD_SIGNATURE` | no `v1` matched |

**An empty secret raises `SecretMissing`. It does not skip verification.** "No secret configured,
so accept everything" is how a webhook becomes an open command channel, and it is the default that
passes every test that supplies a secret.

### Four properties worth knowing

**1. Stripe signs a timestamp and GitHub does not.** `serve/webhook_github.py` says so about itself:
*"a captured delivery stays valid forever… there is no timestamp in it, unlike Stripe's."* This path
can expire a captured delivery. That is the one security property it has that the GitHub path
cannot have.

**2. The comparison is on the ABSOLUTE skew.** `at - t < 300` is true for every timestamp in the
future, however far — a signature generated with a forward-set clock would pass forever. The check
is `abs(skew) > TOLERANCE_S`.

**3. A breach names the measured skew**, because a bad clock and a bad secret look identical:

```json
{"error": "the signed timestamp is outside the tolerance",
 "detail": "signed at 1000000000, our clock says 1789692067 -- 789692067s old, tolerance is 300s.
            A clock this far out refuses every genuine delivery and looks exactly like a wrong
            secret, so check NTP before rotating anything"}
```

Without that sentence an operator rotates the secret, changes nothing, and is still down.

**4. Every `v1` is compared, not the first.** Stripe sends two during a secret rotation. Reading
only the first breaks rotation silently, and only for the customer who rotates — which is to say,
only in production.

**What is NOT covered, stated rather than implied.** The compare is `hmac.compare_digest`, and
replacing it with `==` leaves every test passing — the same admission `serve/webhook_github.py`
makes about itself. `scripts/guard/runtime/check_constant_time_compare.py` is what holds it.

**Verification is not replay protection.** The tolerance bounds the window; inside it a delivery can
arrive twice, and Stripe legitimately retries one event for three days. `store/deliveries.py`,
keyed on the event id, is what makes a retry a retry.

### `sign(secret, body, *, at) -> str`

Builds the header Stripe would send. **For tests only** — and a suite that only ever verifies what
this function produced has tested itself, which is why
`tests/fixtures/stripe_subscription_created.json` is a delivery captured from Stripe.

---

## 8. `serve/stripe_event.py` — reading an authenticated delivery

### `interpret(body) -> Subscription | Ignore`

**Acts on exactly three event types:**

```
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
```

**`checkout.session.completed` is deliberately not one of them.** It fires once, at signup, and
Stripe emits `customer.subscription.created` for the same moment carrying the full state — status,
price, quantity, period. Acting on both would write one row from two shapes, and the session object
does not carry a status at all, so it could only ever produce a guess.

### The payload, with real values from the sandbox

```jsonc
{
  "id": "evt_1UGpoaGY5MuBVWoyam3A9ay7",
  "type": "customer.subscription.created",
  "created": 1789691888,                     // → Subscription.event_at   (ORDERING)
  "data": { "object": {
    "id": "sub_1UGpoYGY5MuBVWoyoH6gtWwV",    // → subscription_id
    "customer": "cus_VHObXYYaL5p3z2",        // → customer_id
    "status": "active",                      // → standing
    "currency": "usd",                       // → currency
    "metadata": { "account": "octocat" },    // → account   ← OUR KEY
    "items": { "data": [ {
        "quantity": 3,                       // → seats
        "current_period_end": 1792283886,    // → current_period_end   ← SEE BELOW
        "price": {
          "id": "price_1UGfiCGY5MuBVWoyiOyqLh6G",   // → price_id
          "unit_amount": 2900                        // → amount_cents
    } } ] }
  } }
}
```

### **`current_period_end` is not where the documentation examples put it**

Under `2026-08-26.dahlia` it is **absent from the subscription object entirely** and present only on
the subscription ITEM. This was confirmed against a real delivery, not assumed:
`tests/unit/layers/serve/test_stripe_event.py` asserts `subscription.get("current_period_end") is
None` on the captured fixture, and fails loudly if Stripe ever puts it back.

A reader written against the top-level field — which is what every older example shows — records
`0` for every subscription, and `verify/paid_access.py` then reports every paying customer as
having no period. **Nothing else in the suite would have caught it.** `_period_end()` reads the item
first, falls back to the top level, and records 0 rather than guessing a date.

### The `Ignore` cases, all of them normal traffic

| reason | what it means |
|---|---|
| `event 'invoice.paid' does not change what an account is entitled to` | a healthy account emits dozens of these an hour |
| `subscription sub_… carries no metadata.account…` | **unmatched** — created by hand in the Dashboard, not through checkout |
| `Stripe sent subscription status 'x', which this build does not know…` | refused rather than read as unpaid; a new Stripe status must not cut off a paying customer on the day it ships |
| `body is not JSON: …` | a gateway's HTML error page |
| `customer.subscription.updated carried no data.object` | malformed |

---

## 9. `POST /billing/webhook` — `serve/web/stripe_hook.py`

**The order is: authenticate → claim → read → write → complete.** Nothing treats the body as a
document until the HMAC has passed on the exact bytes.

| status | body | when |
|---|---|---|
| 503 | `{"error": "…QUANTAMIND_STRIPE_WEBHOOK_SECRET is unset…"}` | not configured |
| 401 | `{"error": "…", "detail": "…"}` | any `Refusal` from `verify()` |
| 400 | `{"error": "the delivery authenticated but carries no event id"}` | nothing to key the ledger on |
| 200 | `{"replay": "evt_…", "note": "already completed, not applied twice"}` | the ledger already has it completed |
| 200 | `{"ignored": "<reason>", "event": "evt_…"}` | an `Ignore`, including an unmatched subscription |
| 200 | `{"event": …, "account": …, "applied": false, "reason": "event at X is older than the stored Y (active), so it was not applied"}` | out of order |
| 200 | `{"event": …, "account": …, "applied": true, "standing": "active", "paid": true, "paid_through": 1792283886}` | recorded |

**Everything that is not a refusal is 200, and the BODY carries the outcome.** Answering non-2xx for
an unmatched or stale delivery would make Stripe retry for three days something that can never
succeed. So the status code cannot carry that information and the body must.

**Every outcome is also printed.** The response body goes to Stripe, which discards it. An operator
watching the log must be able to tell a refused replay from an applied delivery — a gap that was
reintroduced here and found by resending a real event.

**`deliveries.complete()` runs only after the row is written.** If the write raises, the ledger row
has no `completed_at` and Stripe's retry is a legitimate second attempt rather than a replay.

---

## 10. `store/billing/subscriptions.py` — the row

```sql
CREATE TABLE subscription (
    account TEXT NOT NULL, subscription_id TEXT NOT NULL, customer_id TEXT NOT NULL,
    price_id TEXT NOT NULL, standing TEXT NOT NULL, seats INTEGER NOT NULL DEFAULT 1,
    amount_cents INTEGER NOT NULL DEFAULT 0, currency TEXT NOT NULL DEFAULT 'usd',
    current_period_end INTEGER NOT NULL DEFAULT 0, event_at INTEGER NOT NULL,
    PRIMARY KEY (account, subscription_id))
```

Added at `SCHEMA_VERSION` 8 by `store/migrations.py:_to_8`. **Nothing is backfilled: a backfilled
row is an invented payment.**

### `record(conn, subscription) -> Recorded`

The upsert carries `WHERE excluded.event_at >= subscription.event_at`. **This is the load-bearing
line of the whole integration.**

Stripe does not guarantee delivery order. A `customer.subscription.updated` carrying `canceled` can
arrive *after* the `active` that superseded it — a retry of an older event, or two deliveries racing
through the same socket. A plain upsert takes the last one to arrive and **switches off a live
customer**, and nothing downstream can tell that from a real cancellation.

`Recorded(stored, reason)` — **the refusal is returned, never silent.** If a stale write and a fresh
one both returned nothing, a deleted ordering guard would be indistinguishable from a working one.

`>=` rather than `>` so a redelivery repairs a row somebody edited by hand, which is the only way
the two can disagree.

### `current(conn, account) -> Subscription | None`

The newest by `event_at`. **`None` means "never had one", not "cancelled"** — a cancelled
subscription is a row with `Standing.CANCELED` and a visible date, and returning `None` for both
would make an account that left indistinguishable from one that never arrived.

The key is `(account, subscription_id)`, not `account`: one account can hold more than one
subscription over time — they cancel, they come back — and a key of `account` alone would erase the
record that they were ever a customer.

### `paid(conn, account) -> tuple[bool, str]`

Never a bare bool. `past_due` is named separately because it is the one state a human should look
at: everything else is settled, and that one is a card being retried right now.

---

## 11. `verify/paid_access.py` — whether the paid product is open

### `decide(subscription, *, at, grace_days=7) -> Access`

`at` is a parameter and not a `time.time()` call. Every boundary in this function is a comparison
against it, and a clock read inside would make all of them unreachable from a test.

| `Verdict` | open? | when |
|---|---|---|
| `PAID` | ✅ | `active` or `trialing`, and `at <= current_period_end` |
| `IN_GRACE` | ✅ | `past_due`, within `grace_days` of the period end |
| `STALE_RECORD` | ✅ | `active`, period ended, within the grace window — **our missed webhook** |
| `EXPIRED` | ❌ | grace closed, or `unpaid` (every retry failed) |
| `CANCELED` | ❌ | they chose to leave |
| `NEVER_PAID` | ❌ | `incomplete` / `incomplete_expired` — the first payment never completed |
| `PAUSED` | ❌ | collection paused |
| `NO_SUBSCRIPTION` | ❌ | no row — **this is the free tier, not a refusal** |

### Three things this gets right that a boolean cannot

**`NO_SUBSCRIPTION` is not "blocked".** `docs/product/pricing.md` sells a free tier that *"does not
expire and it does not degrade"*. This function answers *did they pay*, and the caller is the only
thing that knows whether it was asking about the paid product. Collapsing the two would turn every
free-tier customer off with one import.

**`STALE_RECORD` is our bug, named.** Stripe moves a subscription out of `active` when it stops
being paid. So `active` with a period that ended weeks ago means we MISSED A DELIVERY — the webhook
was down, the secret was wrong, the endpoint 500ed. Reading it as paid grants free service forever
on a stale row; reading it as unpaid cuts off a customer who has paid. It stays open through the
grace window and then blocks with a reason pointing at our webhook:

> *Stripe last said active but the period ended at 1792283886, 9d ago. **That means we missed a
> delivery, not that they stopped paying** — access is held open for 7d. Check the webhook endpoint
> and the signing secret before touching this account.*

**A clean "still active" months after a period ended is exactly the shape `AGENTS.md` rule 14 is
about:** the same output whether the mechanism works or not.

**`past_due` keeps access for `GRACE_DAYS` = 7.** Stripe retries a failed card for days; cutting off
at the first failure means a bank's fraud hold takes down their CI. The window is measured **from
the period end, not from now** — a window measured from the moment we ask never closes, because
every call restarts it.

---

## 12. What this does to entitlement — and the one wire that is deliberately not connected

### `verify/tier_request.py`

`admissible(tier, request, *, free_verdicts=None, access=None)`.

**`payment_verified` is True only when `access` is an open subscription.** There is no branch in
that function that reads `request.payment_ref` when setting the field.

| the caller sent | result |
|---|---|
| `payment_ref: "sub_123"`, no subscription on record | **admitted**, `payment_verified: false`, note explains it was recorded and not verified |
| an open subscription on record | **admitted**, `payment_verified: true`, note names the standing |
| a lapsed subscription on record | **refused**, carrying `access.reason` |

Until 2026-09-17 the type refused `payment_verified=True` outright. That tripwire was **narrowed,
not deleted**: a refused verdict still may not claim a payment, and the only path to True runs
through an HMAC over Stripe's bytes.

### `store/installations.py:Entitlement.may_review` is UNCHANGED

**The subscription state is recorded and reported and does not yet gate a review.**

This is a decision, not an omission. The gate is one line and its blast radius is every paying
customer. The honest order is: record the state, watch it agree with Stripe's dashboard across real
deliveries, then close the gate in a change that can be reverted on its own. It is written here so
it cannot be read as something that was forgotten.

---

## 13. Running it end to end, locally

**One-time.** Install the CLI and point it at the sandbox:

```bash
npm i -g @stripe/cli
stripe login                                   # browser; pairs the CLI
stripe switch acct_1U9FQPGY5MuBVWoy            # the sandbox. --live would be live mode
```

**Terminal 1 — the forwarder.** It prints the signing secret to use:

```bash
stripe listen --forward-to localhost:7391/billing/webhook \
  --events customer.subscription.created,customer.subscription.updated,customer.subscription.deleted
# → Ready! … Your webhook signing secret is whsec_…
```

**Terminal 2 — the endpoint:**

```bash
QUANTAMIND_WEBHOOK_SECRET=any-value-for-the-github-route \
QUANTAMIND_DATABASE_PATH=/tmp/qm-store \
QUANTAMIND_STRIPE_API_KEY=sk_test_… \
QUANTAMIND_STRIPE_WEBHOOK_SECRET=whsec_…              \
QUANTAMIND_STRIPE_PRICE_ID=price_1UGfiCGY5MuBVWoyiOyqLh6G \
QUANTAMIND_BILLING_SUCCESS_URL=https://quantamind.co/thanks \
QUANTAMIND_BILLING_CANCEL_URL=https://quantamind.co/pricing \
uv run quantamind serve --port 7391
```

**Terminal 3 — make something happen:**

```bash
CUS=$(stripe customers create --email dev@quantamind.co --source tok_visa | jq -r .id)
stripe subscriptions create --customer "$CUS" \
  -d "items[0][price]=price_1UGfiCGY5MuBVWoyiOyqLh6G" \
  -d "items[0][quantity]=3" \
  -d "metadata[account]=octocat"
```

**`metadata[account]` is what makes it ours.** Without it the delivery is correctly reported as
unmatched, which is the right answer and not what you want while testing.

What terminal 2 prints:

```
[billing] evt_1UGpoaGY5MuBVWoyam3A9ay7: octocat: active, 3 seat(s) at 29.00 USD, subscription sub_1UGpoYGY5MuBVWoyoH6gtWwV
```

**Cancel it** — the CLI's `cancel` prompts, so go through the raw API:

```bash
stripe delete /v1/subscriptions/sub_… --confirm
# [billing] evt_…: octocat: canceled, 3 seat(s) at 29.00 USD, subscription sub_…
```

**Prove the refusals** without any Stripe involvement at all:

```bash
curl -i -X POST localhost:7391/billing/webhook \
  -H "Stripe-Signature: t=$(date +%s),v1=$(python3 -c 'print("a"*64)')" \
  -d '{"id":"evt_forged","type":"customer.subscription.deleted"}'
# 401 {"error": "no v1 signature matches the body", "detail": "1 v1 signature(s) offered, none matched"}
```

---

## 14. What was verified against real Stripe, and what was not

**Verified against the sandbox on 2026-09-17**, not asserted from a hand-built payload:

- a real `customer.subscription.created` verified by `webhook_stripe.verify` and recorded whole —
  account, seats 3, $29.00, period end 2026-10-18
- `current_period_end` read off the item, which is the **only** place it exists on this API version
- a real `customer.subscription.deleted` moving the row to `canceled` and `paid_access.decide` to
  `CANCELED / allowed = False`
- a resent event refused by the delivery ledger
- forged, absent and stale signatures each refused 401 with their own reason
- `POST /billing/checkout` answering 401 without a session

**Not verified, and named rather than left to be discovered:**

- **`tests/live/` does not cover Stripe.** It runs the real pipeline against real repositories;
  adding a path that needs a Stripe key and outbound network would make `just verify` fail on any
  machine without one. The live exercise above is a manual procedure, and this section is its
  record — which is weaker than a test and is not being presented as one.
- **The checkout happy path has no unit test.** Creating a session is one HTTPS POST; asserting it
  against a stub would assert our own stub. What is unit-tested is the exact body Stripe receives.
- **The constant-time compare is unobservable to any test**, as above.
- **Nothing validates that `QUANTAMIND_STRIPE_PRICE_ID` names the $29 price.** It is configuration.
  `amount_cents` is recorded so a wrong price shows up in the row rather than only on an invoice.
- **Out-of-order deliveries have never been observed in the wild**, only constructed. The guard is
  tested; the scenario is inferred from Stripe's own documentation saying order is not guaranteed.

---

## 15. Before this touches the live account

1. **Archive `price_1U9FpWGwi83EhBSFIbuj2gSP`** ($39) or accept it as the real price and correct
   `docs/product/pricing.md`. They currently disagree and the page is published.
2. **Create the $29 price on the live account** and set `QUANTAMIND_STRIPE_PRICE_ID` to it.
3. **Register the webhook endpoint** in the live Dashboard against the deployed URL, subscribed to
   the three `customer.subscription.*` events, and set `QUANTAMIND_STRIPE_WEBHOOK_SECRET` to the
   signing secret it issues. **This is not the `whsec_` that `stripe listen` prints** — that one is
   for local forwarding only.
4. **Terminate TLS in front of the endpoint.** `serve/listener.py` says it plainly: `http.server` is
   not a hardened edge.
5. **Check the clock.** A container more than 300 seconds out rejects every genuine delivery, and
   the log will tell you so in as many words.
6. **Watch the first real deliveries** before anything is wired to `may_review`. See
   "What this does to entitlement — and the one wire that is deliberately not connected" above.
