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
- [x] **A4 Open the gate.** `just verify` green, 42 passed, 0 skipped. `render/comment.py`
      returned `None` on `fired=False`; it now always renders and states salience in a sentence
      (`LOUD` / `QUIET`), because the objection recorded when it muted was right — commenting on
      everything WITHOUT marking the loud ones would delete the signal rather than move it.
      `fired` survives as the signal; only the muting is gone. Four tests rewritten, none deleted,
      each recording what it used to assert and why that changed. Proven on real data: PRs #58 and
      #78 returned "no file stood out enough to be worth a comment" this morning and now both
      render a body. **Found on that real output:** the coverage line still read "below the
      threshold **to comment on**" — while commenting — so the golden was regenerated and reviewed
      by hand for that one line.
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

## Phase D — the gaps a competitor demo makes obvious

From Qodo's own enterprise pitch: deep codebase context, a centralised rules engine, specialised
agents, and a compliance dashboard. What we already have, what we do not, and what is cheap.

- [ ] **D1 Deterministic blast radius.** An import graph over the changed files: "this module is
      imported by 14 others, two of them entry points." Python's `ast` is **stdlib**, so this costs
      no dependency and no model — which is the "breaking changes" and "duplicate code" claim
      answered the way this codebase prefers: *deterministic beats clever*. It is also a new
      ranking signal, testable against the same fix-return outcome the touch index uses.
- [ ] **D2 A rules file, enforced.** `.quantamind/rules.yml` in the customer's repo: their
      standards, versioned with their code, checked on every pull request, with the violation and
      the rule that fired both named. This is the "manage rules like code" claim, and it is the
      one that produces an audit trail a buyer can show a regulator.
- [ ] **D3 Cross-repository index.** The expensive one. Requires org-wide indexing and a place to
      keep it. **Not before a design partner has more than one repository that matters.**
- [ ] **D4 Specialised passes** (bugs / security / duplication / breaking changes) instead of one
      generic reviewer. **Pre-register a bar first.** Five prompt levers have now moved nothing,
      and shape-context went PASS → NULL under McNemar and a same-arm replicate. "More context
      improves findings" is not an assumption we are entitled to — it is the hypothesis our own
      experiment failed to confirm.

**What we already have that the pitch charges for:** "past pull requests indexed" IS the touch
index, and it is the half that replicated out-of-sample. What we do not have is "code
relationships mapped" or multi-repo — D1 is the cheap first bite of that.

**A note on the compliance dashboard.** Theirs measures rule compliance per developer, by name.
Ours (`render/dashboard.py`) measures what we commented on, whether it merged, and what production
said. Theirs is more legible to a manager; ours is harder to fake and is the only one of the two
that can be wrong in public. A per-developer scoreboard is also a cultural decision, not just a
feature — worth deciding deliberately rather than by copying a screenshot.

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
