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

- [x] **A1 `allocate/depth.py`** — `just check` AND `just verify` green, **42 passed, 0 skipped**
      with `QUANTAMIND_PUBLIC_READ_TOKEN` set. The first fully-verified green: the same gate read
      34 passed / 8 skipped without the token, and was green BECAUSE eight tests did not run.
      `plan(ranking, changed) -> Reading(depth, paths, unread, why)` with three depths —
      `FULL` / `FOCUSED` / `UNRANKED` — and the conservation invariant `paths + unread == changed`
      asserted on the value. 12 tests, three sabotages caught (dropping `unread`, relabelling
      `UNRANKED` as `FOCUSED`, restoring the small-change mute). Nothing consumes it yet.
      Those eight included `tests/live/test_delivery_live.py` — the test covering the path A2
      changes — so A2 now lands verified rather than assumed.
- [x] **A2 Wire the model into the webhook.** `just verify` green, **42 passed, 0 skipped** —
      including `test_delivery_live.py`, which covers the changed path. `deliver()` builds a
      `Reading` and hands it to `deep_review.examine()`. **Nothing costs money by default:**
      `runs_model` now requires `inference_enabled` AND `inference_project`, two deliberate acts,
      and `config` reports it truthfully rather than claiming a model will run with nothing to
      bill. Never-asked / unreachable / asked-and-silent are three distinguishable values
      (`None`, `consulted=False`, empty `anchored`). Cost bounded by `FULL_CEILING` and
      `max_requests`. Three sabotages caught; the weak `is None` assertions were replaced with a
      spy proving no billed call happens.
- [x] **A3 Wire `verify/publishable.gate()`** — **already done, and a docstring hid it.**
      `deep_review.deep()` has called `gate()` since `978bbda`; `verify/publishable.py` went on
      claiming the oracles were "never wired in" for several commits after the gap closed, and
      this checklist item was written from that stale claim. The docstring now records both.
      No code change was needed; the false statement was the defect.
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
| ~~now~~ | ~~GitHub public-read token~~ — **DONE.** In the gitignored root `.env`; limit is
5,000/hour and `just verify` runs 42/42 with none skipped. `config` reports it `set`, never its
value. Used only where the App is not installed, so it can never touch a customer repository. |
| **A6** | **One design partner.** Tier 0 item 1 — minutes-per-file on binding changes — is still the item that decides whether any of this is worth building. |
