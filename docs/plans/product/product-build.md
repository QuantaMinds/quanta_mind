# The product build — phase by phase, ticked as it lands

**How to read this.** One line per deliverable. `[ ]` not built, `[x]` built AND verified by
`just verify`, `[~]` in progress. A line is only ticked when the gate the definition of done names
is green — not `just check`. Design reasoning lives in `docs/plans/feat-review-every-pr.md`; this
file is the state.

**Nothing below is ticked on a promise.** Each tick names the evidence next to it.

---

## Phase A — make it a reviewer

The product. Everything after this is packaging, and is worth nothing until A produces a review
worth selling.

- [x] **A1 `allocate/depth.py`** — `just check` AND `just verify` green (34 passed, 8 skipped,
      1 deselected). **The 8 skips do not bear on A1**: nothing imports `allocate.depth` yet, and
      the skipped tests read PUBLIC repositories through the API, where the unauthenticated limit
      is 60/hour. A1's own 12 unit tests all ran.
      `plan(ranking, changed) -> Reading(depth, paths, unread, why)` with three depths —
      `FULL` / `FOCUSED` / `UNRANKED` — and the conservation invariant `paths + unread == changed`
      asserted on the value. 12 tests, three sabotages caught (dropping `unread`, relabelling
      `UNRANKED` as `FOCUSED`, restoring the small-change mute). Nothing consumes it yet.
      **From A2 onward those skips DO matter**: `tests/live/test_delivery_live.py` is one of the
      eight, and it is the test that covers the path A2 changes. The token stops being a
      convenience there and becomes the difference between verifying and assuming.
- [ ] **A2 Wire the model into the webhook.** `deep_review.deep()` is CLI-only today
      (`--deep`, `argparse.SUPPRESS`); `serve/review_delivery.py` never calls it. Behind the
      allocation, with a hard per-pull-request cost cap.
- [ ] **A3 Wire `verify/publishable.gate()`** before anything publishes. Built and measured, never
      connected — today a finding ships if a parser can place its quote and nothing else.
- [ ] **A4 Open the gate.** Replace the mute with depth so every reviewable pull request gets a
      comment. Rewrite — never delete — the tests that encode the old ~11% decision.
- [ ] **A5 Record it.** Depth, cost and gate outcomes into the store; surfaced by
      `render/dashboard.py`.
- [ ] **A6 Read the numbers.** Coverage 100%, gate rejection strictly between 0% and 100%,
      FULL/FOCUSED split, and **published findings per pull request** — the number that decides
      whether coverage is sellable. Comparable today: 0.013–0.037 correct findings per PR.

## Phase B — make it buyable

- [ ] **B1 Background warm-up worker.** Kills the cold start: full clone + ~31s index build on a
      115k-commit repository. Cannot be inline — GitHub needs a prompt 2xx.
- [ ] **B2 Accounts + sign in with GitHub.** No user model exists today.
- [ ] **B3 Stripe checkout + subscription webhooks.** 🔑 *needs your Stripe account*
- [ ] **B4 Installation → customer mapping.** The App install flow already provisions a store; it
      does not know whose it is.
- [ ] **B5 Entitlement check at delivery.** Today any installation is reviewed, paid or not.
- [ ] **B6 Per-tenant posting switch + turn posting ON.** `POSTING_ENABLED` is off by default and
      the webhook path has never posted to a real pull request.

## Phase C — make it comparable

- [ ] **C1 Web dashboard.** `render/dashboard.py` renders the business table as TEXT today.
- [ ] **C2 CI integration.**
- [ ] **C3 IDE integration.** Only when a deal asks.
- [ ] **C4 SSO.** Procurement gate — only when a deal asks.

---

## What I need from you, and when

| when | what |
|---|---|
| **B3** | A **Stripe account** (test-mode keys are enough to build against): publishable key, secret key, and a webhook signing secret. Say the word and I'll list the exact steps. |
| **B2/C1** | A **domain** and somewhere to host — the endpoint is a container today, reachable only through a temporary tunnel. |
| **now** | A **GitHub token with public read access** (a fine-grained PAT with no scopes is
enough) for `QUANTAMIND_PUBLIC_READ_TOKEN`. Unauthenticated reads are 60/hour and one `just verify`
run exhausts them, so the live suite skips rather than verifies. This token is used ONLY where the
App is not installed — never on a customer repository. |
| **A6** | **One design partner.** Tier 0 item 1 — minutes-per-file on binding changes — is still the item that decides whether any of this is worth building. |
