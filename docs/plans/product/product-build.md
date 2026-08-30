# The product build — phase by phase, ticked as it lands

**How to read this.** One line per deliverable. `[ ]` not built, `[x]` built AND verified by
`just verify`, `[~]` in progress. A line is only ticked when the gate the definition of done names
is green — not `just check`. Design reasoning lives in `docs/plans/delivered/feat-review-every-pr.md`; this
file is the state.

## THE BUILD ORDER — do these in this number order

**Read this first. Each number says what to build and why it comes before the next one.** The
order is by dependency and by what would be wasted work if done later. An item marked ⏸ is parked
by decision, not by difficulty.

| # | item | why it is here and not later |
|---|---|---|
| **1** | **A5** record depth, cost and gate outcomes | Nothing measures what a review costs or how often the gate fires. Everything after this is decided on numbers we do not have yet, so it comes first and is small. |
| ~~2~~ | ~~**A6** read those numbers~~ **DONE** | 0.686 published per change, gate rejection 14.3%, 6,321 output tokens each. **The model half was not ruled out.** The correctness rate behind that 0.686 was the 2024 figure; **it was re-measured 2026-08-29 at 25.0%** — 6 of 24 published findings correct, 95% interval **12.0–44.9%** against a raw band of 17.9–33.3%. **The published interval contains the whole raw band, so there is no evidence the gate raises correctness.** `docs/findings/A6_WHAT_A_REVIEW_PRODUCES_2026-08.md`. This changes what the numbers below are worth — see the note under the table. |
| **3** | **E2** `--json` output | Small, and the only thing standing between E1 and a coding agent that can act on a review. A human re-typing prose is not an integration. |
| **4** | **E3** `/qm-review` editor command | A thin wrapper over E1+E2. Last of Phase E on purpose: a wrapper over a weak answer is a faster way to be unhelpful. |
| **5** | **D2a/D2b** import edges, stored | The deterministic half of "without disturbing anything else". `parse/importers.py` already answers it per file; this makes it a graph that persists. |
| **6** | **D2d** blast radius in the review | The payoff of 5. Testable against the same fix-return outcome the touch index uses. |
| **7** | **D5** per-repo compliance dashboard | A view over `rule_check`, which exists and has real rows. Cheap now, and it is what a buyer asks to see. |
| **8** | **B1** background warm-up worker | The cold start is a full clone plus ~31s index build, and Cloud Run's ephemeral disk means every instance pays it. Needed before real traffic, not after. |
| **9** | **B8** free-tier qualification checks | The traffic path, and **it needs no payment rail** — a free tier is free. Every rule is a GitHub API check that can be enforced rather than advertised. |
| **10** | **B2/B4/B5** accounts, installation→customer, entitlement | Only meaningful once there is traffic to attribute. |
| **11** | **D1f** blocking status check | Requires the confidence that only 2 can give. Only reproducible checks may ever block. |
| **12** | **D6a** the ticket and discussion behind the change | Retrieval for the reader; worth something whatever the model does. |
| **13** | **C1** web dashboard | A surface over 7. |
| **14** | **D2c/D2e** duplicate logic, architectural drift | Real, and neither blocks anything else. |
| **15** | **D3a/D3b** cross-repo by declaration | **Not before a design partner has more than one repository that matters.** |
| ⏸ | **B3/B7** Stripe, BYOK | Parked by decision 2026-08-27: product and traffic first. |
| ⏸ | **D7e** SOC 2 Type II | External, months, and no code substitutes for it. |

**When picking up work: take the lowest number that is not ticked.** If it is blocked, say why in
the plan rather than skipping silently — a number jumped without a reason is how a checklist stops
describing the product.

**5 and 6 are parked, 2026-08-29.** D2d's blast-radius claim came back **INCONCLUSIVE against its
own registered bar** — 10 discordant pairs against a floor of 20, so the test could not decide
either way rather than deciding against. D2b exists to feed D2d, so it is parked with it, with
recommend-drop pending a corpus large enough to reach the floor. Written here because the rule
above requires it: the next person would otherwise read 5 and 6 as simply not started.

**And what row 2 now means for everything under it.** Phase A opens by saying *everything after
this is packaging, and is worth nothing until A produces a review worth selling*. Three of four
published findings are wrong and the gate does not measurably improve that. **7 onward — the
dashboard, the warm-up worker, the free tier — is packaging by this plan's own definition.** The
one item the evidence positively supports is not on this list: **findings are emitted at a 17.3%
redundancy rate against Qodo's 1.0%**, and we emit 194 comments covering 81 goldens where Qodo
emits 152 covering 98. That is model-free and unbuilt — no finding-level dedup exists anywhere in
`src/`. See `docs/plans/preregistrations/reviewer/dedup-preregistration.md`.

## The golden rule every item is judged against

**Did this pull request achieve the goal it set out to achieve, WITHOUT disturbing anything else?**

That is the question a review exists to answer, and everything the product gathers is an input to
it: the changed lines, how many files were touched, **how often those files have changed before**,
the context a human wrote (previous comments, Jira, Slack), and the stated goal of the change.
Anything that does not feed that question does not belong in the comment — which is why the body
no longer explains how we rank.

**Delivery is INLINE, on the lines.** Line-level correctness is what a linter already covers; the
goal-versus-collateral question is the one a human currently has to hold in their head, and it is
what the touch index and the cross-file relationships are actually evidence for.

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
- [x] **A5 Record what it cost.** `types/spend.py` + `store/reviews.record_spend()`. The four
      cost columns had existed since the schema was written and **nothing ever wrote them**.
      `tokens_out` includes the model's own reasoning, which Vertex bills and reports separately —
      one real summary measured **422 in, 1,631 out, 16s**, the output four times the input and
      almost all of it thinking. `Spend.complete` marks a total as a FLOOR when part of the review
      went unmetered, and an incomplete spend is **refused rather than rounded down**, because an
      undercount on a dashboard gets priced from. *Depth is derivable from `ranked_unit`; the gate
      outcome is already `review.fire_decision`.* ~~Depth, cost and gate outcomes into the store; Depth, cost and gate outcomes into the store; surfaced by
      `render/dashboard.py`.
- [x] **A6 Read the numbers.** Run 2026-08-28 on `pallets/flask`, 35 changes, model on —
      `docs/findings/A6_WHAT_A_REVIEW_PRODUCES_2026-08.md`. **Coverage 100%: PASS.
      Gate rejection 14.3%: PASS** (the bar was strictly between 0 and 100). Reported without a
      bar: **0.686 findings published per change**, 77% of changes ≤3 files, and **6,321 output
      tokens and 60s per change** — the first cost figure this product has ever had.
      **0.686 is PUBLISHED, not CORRECT**, and must not be compared to the 0.013–0.037 in
      AGENTS.md until the error rate is re-measured on this pipeline. One repository,
      unreplicated. ~~Coverage 100%, gate rejection strictly between 0% and 100%, Coverage 100%, gate rejection strictly between 0% and 100%,
      FULL/FOCUSED split, and **published findings per pull request** — the number that decides
      whether coverage is sellable. Comparable today: 0.013–0.037 correct findings per PR.

## Phase G — GCP integration (the container cannot run `gcloud`)

**Direction 2026-08-27: product and traffic first, payments later.** This is the gap that actually
blocks Half B in production, and it was invisible until the deep half ran for the first time.

- [x] **G1 A Vertex token with no `gcloud` and NO KEY.** `ingest/google_auth.py`. `just verify`
      green, 42 passed, 0 skipped. **The org policy refused to issue a service-account key**
      (`constraints/iam.disableServiceAccountKeyCreation`) and that produced a better design than
      the plan: metadata server first, so a container on GCP holds no credential on disk at all;
      `gcloud` only for laptop development. Probe bounded at 1s — a test that was VACUOUS in its
      first form until sabotage caught it. Service account `quantamind-reviewer` created with
      `roles/aiplatform.user` only. Real Vertex call verified through the new path. ~~Original
      plan: `infer/gemini.py`
      shells out to `gcloud auth print-access-token`. There is no `gcloud` in the container and
      there should never be — a 200 MB SDK to fetch a bearer token is the dependency this product
      refuses. **The machinery already exists:** `ingest/app_auth.py` signs an RS256 JWT with
      `openssl` and exchanges it for a GitHub installation token, and a Google service account is
      the SAME pattern — sign a JWT with the SA key, POST to `oauth2.googleapis.com/token`,
      receive an access token. One sibling module, zero new dependencies; `gcloud_path` stays for
      laptop development.~~
- [x] **G2 Half B proven from a container on GCP.** Deployed to Cloud Run as
      `quantamind-reviewer`; PR #85 reviewed end to end with `[infer] access token from metadata`
      — no credential on disk. **Found: Cloud Run's default CPU throttling silently starves the
      background review**, returning a 202 GitHub accepts while nothing runs — indistinguishable
      from working. Also: the filesystem is ephemeral so the touch index dies with the instance,
      which makes Cloud Run the wrong long-term home and a queue plus worker (B1) the real answer.
      ~~Original: It has run exactly once, by hand, through the
      CLI on a laptop. Never from a webhook delivery, never in Docker, never with a service
      account. Until that runs, "the endpoint reviews with a model" is a claim about a code path
      rather than an observation.
- [ ] **G3 Cost per review, measured.** Every delivery that consults a model records what it
      spent. Without it, BYOK pricing and the free-tier cap are both guesses.

## Phase B — make it buyable  ⏸ **PAYMENTS PARKED 2026-08-27**

**Parked:** B3 (Stripe), B7 (BYOK billing). **Not parked:** the items below that produce TRAFFIC,
which need no payment rail — a free tier is free, so onboarding real repositories does not wait on
Stripe.

- [x] **B1 Background warm-up worker.** `serve/warm.py`. On an installation event the handler
      answers **200 first**, then clones and indexes each provisioned repository — the same
      acknowledge-then-work shape the module docstring already documents for deliveries, because a
      clone will not finish inside GitHub's ten seconds. 5 tests against a REAL git repository and
      a REAL store with only the network clone stubbed; sabotaging the index call fails two of
      them by name.
      **The line it replaces was a false claim.** `listener.py` said "Provisioned here so a first
      review pays no cold index", but `tenancy.provision` creates the store FILE and nothing else
      — no clone, no touches, no watermark. It was true of nothing until this existed.
      **A failed warm-up is not a failed installation**: `warm_all` collects failures per
      repository and prints them, because an install that 500s over a slow clone is worse than a
      slow first review. Idempotent by construction — `index_repository` reads the watermark and
      appends `<watermark>..HEAD`, asserted by warming twice and getting the same count.
      **Making room for it moved `pin_check` to `verify/`**, where it always belonged: it
      adjudicates a claim about a pinned SHA and imports `verify.pin_mismatch`, and `serve/` was
      at its fifteen-file cap.
- [x] **B2 Accounts + sign in with GitHub.** `store/accounts.py` at schema v7, `serve/web/`
      for the surface: `/login` redirects, `/callback` signs in, anything else 404s. 26 tests,
      four security sabotages caught.
      **The session token is never stored, only its SHA-256** — `issue()` returns it once, so a
      stolen database yields no live session, and a test asserts the raw token appears nowhere in
      the file on disk. **Expired and unknown are different answers.** Sessions last two weeks,
      written at issue.
      **`state` is checked, and before the code is spent.** Without it anyone can hand a victim's
      browser a callback carrying THEIR code and log the victim into the attacker's account. Two
      copies — URL and a short-lived `HttpOnly` cookie — cleared on use, because a replayed
      callback is what an attacker keeps. Cookies carry `HttpOnly`, `Secure` and `SameSite=Lax`,
      and the error page never echoes the callback.
      **NOT DONE HERE:** nothing is shown to a signed-in user yet. `whose()` answers who a cookie
      belongs to and no page consumes it — the dashboards from 7 and 13 are what would.
- [ ] **B3 Stripe checkout + subscription webhooks.** ⏸ PARKED. 🔑 *needs `claude mcp login plugin:stripe:stripe` run in a REAL terminal (my Bash tool has no tty), and a `STRIPE_WEBHOOK_SECRET`, absent from `.env`. Present: `STRIPE_Publishable_key`, `STRIPE_Secret_key`, `STRIPE_LIVE_SECRET_KEY`, `STRIPE_LIVE_PUBLISHABLE_KEY`.*
- [ ] **B7 BYOK — the customer brings their own model key.** ⏸ PARKED with B3. Inference cost moves to them, which
      makes per-review cost somebody else's ceiling rather than our margin. Needs per-tenant
      credentials rather than one `inference_project`, and a stored key is a liability: it belongs
      encrypted at rest and must never reach `quantamind config`, a log, or a comment.
- [x] **B8 Free tier — the decision, made and recorded; enforcement is B5's.** `verify/qualification.py`
      reads the facts and `qualifies()` returns a `Verdict` naming EVERY failing rule, not the
      first — a prospect told "no" repeatedly learns the list by attrition. 18 tests; three
      sabotages caught (dropping a rule, making a bound exclusive, returning one reason).
      `serve/onboarding.admit()` runs it on installation and **skips warming a repository that
      does not qualify**, which is the part that costs a clone and a ~31s index build.
      **It does NOT refuse the installation, deliberately.** B5 is "entitlement check at delivery
      — today any installation is reviewed, paid or not", and refusing to provision here with no
      entitlement system to say "but this one is a customer" turns every non-qualifying install
      into a dead end with no override. **An unreadable repository is warmed, not refused**: an
      outage at GitHub must not quietly downgrade somebody's installation.
      **TWO NUMBERS THE PLAN LEFT OPEN ARE NOW EXPLICIT RATHER THAN IMPLICIT.** `STAR_CEILING`
      ships as `None` — the question below was never answered, and this section's own reasoning
      argues against a ceiling since the criteria exist to select repositories the ranker can
      serve. If one is wanted it is a COST control, a different rule with a different reason.
      `MAX_PUSHED_DAYS_AGO` is 30, because "recent" was undefined and a number in a constant is
      arguable where a number in nobody's head is not.
      Every rule below is checkable from the GitHub API at install time:

      | rule | check |
      |---|---|
      | public only | `repo.private is False` |
      | 1,000–5,000+ stars | `stargazers_count` — **is 5K a ceiling or just "and above"? unresolved** |
      | 50+ contributors | contributors API, counted not estimated |
      | 6+ months of recent activity | commits spanning ≥180 days AND `pushed_at` recent — both, because either alone passes for a repo that was busy once |
      | one free repo per account | keyed on the owner, not the installation, which changes when somebody ticks a box |
      | until 40 unique repos | a global counter, and the offer closes on it |

      **THESE CRITERIA ALSO SELECT FOR REPOSITORIES WHERE THE PRODUCT WORKS.** The ranker needs
      fix history; 50 contributors over six months is exactly what produces it. A repository that
      fails these would likely have got a weak review, so the qualification is honest rather than
      arbitrary.

      **AND WE CAN ALREADY TELL A PROSPECT BEFORE THEY INSTALL.** `rank/firing.estimate()` returns
      `NO_HISTORY` ("this repository cannot be ranked yet") and `CONCENTRATED` ("a few files
      dominate; almost nothing will be flagged"). Running it during onboarding turns eligibility
      into a measured answer about their repository instead of a sales rule — and refusing a
      repository we would serve badly is worth more than the install.
- [x] **B4 Installation → customer mapping.** `store/installations.py`, schema v6. `admit()`
      writes one row per repository at install time carrying the account, the tier, and the B8
      verdict flattened — `store/` sits left of `verify/` and cannot import a `Verdict`.
      **`eligible` IS NULLABLE AND THAT IS THE WHOLE DESIGN**: NULL is "never assessed", 0 is
      "assessed and refused". Nothing is backfilled, so every repository installed before the
      table reads UNKNOWN rather than as one we turned down. An uninstall sets `removed_at` and
      keeps the row — "never a customer" and "left" are different answers to an auditor.
- [x] **B5 Entitlement check at delivery.** `review_delivery.deliver()` reads the seat before
      reviewing and returns a SEVENTH outcome, `NOT_ENTITLED`, rather than a flag on an existing
      one: folding "we chose not to review" into "there was nothing to review" would hide a
      withdrawn customer among unreadable pull requests.
      **ONLY `REMOVED` REFUSES.** `UNKNOWN` reviews, because refusing it would silence every
      installation predating the mapping to enforce a rule they were never told about. An
      INELIGIBLE repository reviews too: the free-tier verdict is information for a human, and a
      gate with no paid tier to fall back on is a dead end with no override. 10 tests; three
      sabotages caught — UNKNOWN refusing, ineligible refusing, and a no-op withdrawal claiming
      it removed one.
- [x] **B6 Posting ON.** Default in the Dockerfile, still False in `Settings`, so building the image is the act of asking while a test or CLI run can never write to a pull request. Real comments and an inline review posted to PRs #85 and #86 as `quanminds[bot]`. *Per-tenant switch still absent.* ~~`POSTING_ENABLED` is off by default and `POSTING_ENABLED` is off by default and
      the webhook path has never posted to a real pull request.

## Phase C — make it comparable

- [x] **C1 Web dashboard.** `serve/web/pages.py` over `render/page.py`. Signed out, `/` offers
      sign-in; signed in, it lists the account's repositories and `/r/<owner>/<name>` shows that
      repository's compliance table and outcome board. 15 tests, three sabotages caught.
      **AN ACCOUNT SEES ONLY ITS OWN, CHECKED PER REQUEST.** A path is a claim, not a permission:
      `mine()` answers from the installation rows, never from the URL. "Not yours" and "does not
      exist" return the SAME answer, and the test compares the two to each other rather than each
      to None — a difference would confirm the repository is there.
      **THE TWO REPORTS ARE THE CLI'S, SHOWN NOT REBUILT.** A second rendering of the same
      judgement is the one that drifts, so they go inside `<pre>`, escaped.
      **No dependency, no script.** `dependencies = []` holds; a page with no script is one where
      a missed escape cannot execute. A repository name carrying markup never reaches the page at
      all — `store/tenancy.py` refuses it at the storage boundary, which the test asserts instead
      of asserting an escape that path cannot exercise.
- [ ] **C2 CI integration.**
- [ ] **C3 IDE integration.** Only when a deal asks.
- [ ] **C4 SSO.** Procurement gate — only when a deal asks.

## Phase D — relationships, linked repos, audit, and the context a human wrote

Direction set 2026-08-27. **This is the codebase's founding design, unbuilt.** `types/verdict.py`
already carries `Confidence` (where `RESOLVED` requires two independent resolvers agreeing),
`Provenance.PARSER`, and a closed `Reason` set with `DYNAMIC_DISPATCH`, `EXTERNAL_SYMBOL` and
`UNPARSEABLE_SYNTAX`. Non-negotiables 2 and 3 in `AGENTS.md` are ABOUT edges. Nothing has ever
emitted one.

### D1 — the rules engine (the spine: audit and dashboard are views over it)

A compliance rate cannot be reported without rules to be compliant with. Built first because D4
and D5 read what it records.

- [x] **D1a Rules as code, in the customer's repository.** `types/rule.py` +
      `ingest/standards/rules_file.py`. **No rules and unreadable rules return different answers** — the
      failure that would report a customer compliant at the moment enforcement stopped. Malformed
      declarations come back as `Unresolved`, never dropped; provenance is DERIVED from the check
      so a model-judged rule cannot claim a parser verified it; duplicate ids refused. 10 tests,
      4 sabotages caught. ~~`.quantamind/rules.toml` — `tomllib` is
      stdlib and rule 11 bans `pyyaml` from `src/`. Versioned with their code, reviewed like their
      code, diffable.~~ Documentation is what this replaces: standards nobody reads and every
      reviewer interprets differently.
- [x] **D1b Deterministic checks FIRST, and most rules are.** `parse/python_names.py` +
      `verify/rule_check.py` + `types/checked.py`. `just verify` green, 42 passed, 0 skipped.
      One `Checked` per rule per file, **four outcomes** because three of them look like a pass
      from outside: PASSED / VIOLATED / UNCHECKABLE / DEFERRED. A TypeScript file is UNCHECKABLE,
      never passed — otherwise a JS repository reads 100% compliant with checks that never ran.
      `counts_toward_compliance` excludes undecided rows so a rate moves with the customer's code,
      not our parser coverage. 9 tests, 4 sabotages caught. ~~From the competitor's own examples: From the competitor's own examples:
      `async-error-handling`, `typed-catch-block`, `no-console-log-in-prod`,
      `input-validation-required`. **Every one is an AST pattern, not a semantic judgement.** A
      parser can answer them, so a model must not — and a deterministic check is the only kind
      that can be re-run later to prove an audit entry was right.~~
- [ ] **D1c Model-checked rules, clearly separated.** For rules a parser genuinely cannot answer.
      Each result carries `Provenance.PARSER` or `Provenance.MODEL` so an auditor can see which
      claims are reproducible. **They must never render alike.**
- [x] **D1g The team's OWN written standards, read and enforced.** `ingest/conventions.py` reads
      `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `CONVENTIONS.md`  <!-- citation:allow — these are filenames `ingest/standards/conventions.py` SEARCHES FOR in a customer's repository, not documents in this one -->
      and `CONTRIBUTING.md` from git at the commit under review, and the review names any rule the
      change contradicts — quoting the customer's own sentence. **A team that wrote its rules down
      should not have to write them again for us**, and `.quantamind/rules.toml` asking them to
      restate the same standards creates two documents that drift.
      **Context, not enforcement:** prose cannot be re-run on a commit and shown to give the same
      verdict, so nothing read here becomes a `Checked` row or enters the audit trail — that stays
      the parser's territory. Known-answer tested: a diff with a bare `except` and no docstring was
      caught against this repository's own rule 8. **A local-only file this repo never pushes is
      invisible to it**, because the reviewer reads the clone.
- [ ] **D1d Mine rules from past review comments.** Senior engineers repeat themselves, and the
      repetition IS the standard. **This is the one model use where being wrong is cheap:** the
      output is a PROPOSED rule a human approves, not a published finding — a different risk
      profile entirely from the path that measured 66.7-82.1% wrong.

- [ ] **D1e One definition, every repository.** "Define a standard once and it is checked on every
      pull request across all repositories" is the actual enterprise claim, and a per-repo
      `rules.toml` does not make it. Org-level rules live in a `.quantamind` repository the
      installation owns; a repository's own file EXTENDS them and may tighten a severity, never
      silently drop an inherited rule. **A dropped inheritance must appear in the audit trail**,
      because a standard that can be disabled invisibly is not a standard.
- [ ] **D1f Blocking, not just commenting.** The claim is that code meets standards *before a human
      reviewer sees the pull request*. That requires a **required status check that fails**, not a
      comment somebody may scroll past. **Only reproducible checks may block** — a `Provenance.MODEL`
      verdict at our measured error rate must never hold somebody's merge, and the split already
      exists on `Rule.reproducible`.

**OPEN DECISION — which languages.** Python checks are free: `ast` is stdlib. JS/TS are not, and
`AGENTS.md` states plainly that **tree-sitter is NOT a dependency** while `pyproject.toml` declares
`dependencies = []`. Either the rules engine ships Python-only at first, or that constraint is
spent deliberately. It must not be spent by accident.

### D2 — code relationships, deterministically

- [x] **D2a Labelled import edges.** `parse/imports.py`. Base rate measured before shipping —
      **~44% of import statements resolve in-tree**, see `docs/findings/graph/D2A_IMPORT_EDGE_BASE_RATE_2026-08.md`. `parse/imports.py` over stdlib `ast`: no dependency, no
      model. Every edge carries `Confidence` and `Provenance`; an unresolvable import emits
      `Unresolved(site, reason, construct)` and never nothing — `importlib` is `DYNAMIC_DISPATCH`,
      a third-party name `EXTERNAL_SYMBOL`, a broken file `UNPARSEABLE_SYNTAX`. `RESOLVED` only
      where two independent resolvers agree: the syntax says the import exists AND the target is a
      file in the tree.
- [ ] **D2b The graph, stored.** **ON HOLD, recommend DROP.** Six unseen repositories, 1,301 non-degenerate events:
      in-degree gives the same top three as alphabetical on 99.2% of changes, and loses to the
      shipped fix-history signal 65-13 at p < 0.0001. See
      `docs/findings/graph/D2D_BLAST_RADIUS_SIX_REPOS_2026-08.md`. A whole-repo pass into a `dependency` table, incremental against
      the same commit watermark the touch index uses.
- [ ] **D2c Duplicated logic, without a model.** Normalised AST hashing of function bodies —
      rename-insensitive, comment-insensitive, stdlib only. "The same logic is written in multiple
      places, and a fix to one leaves the others wrong" is a real cost, and it is a structural
      question a parser answers exactly rather than a judgement a model guesses at.
- [ ] **D2d Blast radius in the review.** **ON HOLD**, same reason as D2b. "This module is imported by 14 others, two of them entry
      points." A new signal, testable against the same fix-return outcome the touch index uses.

- [ ] **D2e Architectural drift, measured rather than asserted.** "Team members implement parts of
      the system differently from the original design" is a claim about DIVERGENCE, and divergence
      is measurable: the import graph plus rule violations over time, per module. We have the
      history to do it retrospectively — `retrospective` already replays the ranker over a clone's
      own past, which is the instrument for showing drift happened rather than saying it does.

### D3 — cross-repo, by declaration rather than discovery

- [ ] **D3a The business declares its links.** `.quantamind/links.toml`. **Declared beats
      discovered:** no org-wide crawl, no broad permissions, and a link a customer stated is
      provenance an auditor can be shown, where an inferred one is our guess about their
      architecture.
- [ ] **D3b Edges that cross a repository boundary.** A changed exported symbol against the linked
      repositories that import it.

### D4 — audit trail

- [x] **D4a Wired into the delivery.** `deliver()` reads `.quantamind/rules.toml` via
      `verify/rule_check.enforce()`, checks every changed file (`git show <sha>:<path>`, so the
      code is read AS THE CHANGE LEAVES IT), and renders the result with the denominator printed.
      **Proven on PR #86: "60 declared rule(s) checked".** The per-tenant posting switch that was
      once listed here belongs to B6 and is recorded there; it was never part of this item.
- [x] **D4b Append-only, exportable.** `rule_check` at schema v5, `store/rule_checks.py`. All four outcomes stored so the denominator is real; `provenance` derived from the rule; nothing backfilled. **Proven on a real delivery: PR #86 reported "60 declared rule(s) checked".** ~~Every check on
      every pull request: which rule, the outcome, the commit, the provenance, whether it posted.~~ **This is the artefact a compliance team buys**, and it is
      worth more when the checks behind it are reproducible, which is why D1b precedes D1c.

### D5 — compliance dashboard, PER REPOSITORY

- [x] **D5 Per repo, not per developer.** `quantamind compliance --repo owner/name` —
      `store/compliance.py` reads every `rule_check` row for one repository, `render/compliance_table.py`
      renders it. **Proven end to end on a seeded tenant store**: three rules over three reviews,
      "9 check(s) decided, 3 not", `src/pay/ledger.py` named as the hotspot. 14 tests.
      **All four outcomes are separate columns and the rate is over DECIDED checks only** — a rule
      nobody could evaluate renders `-`, never `0%`, because zero per cent violated reads as
      compliance and is actually silence. **Deliberately not a per-developer scoreboard**: the
      competitor screenshot ranks named engineers, which is a cultural decision rather than a
      feature, and a test asserts no such word appears in the output.
      **Building it found `quantamind dashboard` broken**: `database_path` is the tenancy ROOT to
      `review_delivery` and `health`, and `run_dashboard` still opened it as a single file, so on
      any real deployment it raised `sqlite3.OperationalError` instead of reporting. Both commands
      now resolve tenants through `store/tenancy.py`.

### D6 — the context a human wrote

Pulled in as **two separate uses**, because they succeed or fail independently:

- [ ] **D6a Retrieval for the READER.** The ticket and discussion behind the files being changed,
      shown in the comment. Deterministic, and worth something whatever the model does.
- [ ] **D6b The same text as MODEL input.** **Pre-register a bar.** Shape-context went
      PASS to NULL under McNemar and a same-arm replicate, and five prompt levers moved nothing.
      Human context is a DIFFERENT variable — it carries why a change exists, which no diff shape
      contains — so the null does not condemn it. It does mean measuring rather than assuming.
- [ ] **D6c Sources, cheapest first.** GitHub PR and issue comments need no new credential and no
      new dependency. Jira and Slack are REST and JSON over HTTPS, so `urllib` reaches both and
      `dependencies = []` holds; what they need is the customer's auth. **Egress is a decision,
      not a detail:** quoting a private Slack thread into a GitHub comment moves their data
      between systems, and that must be opt-in per source.

### D7 — the three questions a security team asks

Their answers, given our thesis: say what is true, prove it where we can, and refuse the claim
where we cannot.

- [ ] **D7a "What does it catch?"** AI-written code carries more hardcoded secrets, and a
      hardcoded key is **deterministically** detectable — pattern plus entropy, no model, no
      judgement. It ships as a `CheckKind`, high precision, reproducible in the audit trail.
      **What we must NOT claim is general vulnerability detection.** Our raw findings measure
      66.7-82.1% wrong across four blind pools. "We catch hardcoded credentials, exactly, and we
      do not claim to catch injection" is a weaker sentence and a defensible one.
- [x] **D7b "What do you do with our code?" — answerable, and provable.** `assert_no_source_in_pack.py` runs inside `just verify`: the store holds paths and counts, never contents. A customer can run that test themselves. ~~We can already prove more than a policy statement **We can already prove more than a policy statement
      can.** `scripts/verify/assert_no_source_in_pack.py` runs in `just verify` and asserts the
      store holds NO SOURCE — it keeps paths and counts, never file contents. That is a test a
      customer can run themselves, not a certification we bought.
      Precision required: the CLONE is on disk (bounded by `sweep`, 8 kept) and with inference ON
      the diff IS sent to a model. "The store holds no source" is true and provable; "your code
      never leaves" is only true with inference off. **Both must be said, not one.**
- [x] **D7c "Where is it allowed to run?" — answerable.** Half A needs a git clone and nothing else, and E1 strengthened it: the local path makes no network call at all. ~~Half A is air-gap-capable by construction: the **Half A is air-gap-capable by construction**: the
      ranker needs a git clone and nothing else — no API, no model, no network. That is not a
      roadmap item, it is what the model-free half already is, and it is the strongest answer we
      have for banking and defence. Half B cannot be air-gapped without a local model. Cloud and
      on-prem are the same container; the difference is who runs it.

- [x] **D7d "Do you train on our code?" — No, structurally.** ~~We fine-tune nothing We fine-tune nothing
      and there is no training pipeline to disable. With BYOK the call goes to the customer's own
      model account under their terms, so the question stops being about our promises. **This is a
      commitment we can keep because there is nothing to give up.**
- [ ] **D7e SOC 2 Type II.** External, expensive, months of evidence collection, and no code we
      can write substitutes for it. Recorded so nobody plans around its absence. **Until it
      exists, say so** — a buyer discovering it mid-procurement costs more than the deal.
- [ ] **D7f Three deployment shapes, one container.** Cloud (we run it), on-prem (they run the
      same image), air-gapped (Half A only, no network beyond the clone). The image already
      exists; what is missing is on-prem installation docs and an air-gapped mode that REFUSES to
      make a network call rather than merely not making one — an outbound call that fails quietly
      in a bank is a finding against us, not a bug.

**The framing for all of Phase D:** build what the competitor sells, but with the thesis —
deterministic where a parser can answer, provenance on every verdict, refusals returned rather
than dropped, and no claim published that we cannot defend when someone checks it.

### Traceability — every competitor claim, and where it is answered

| their claim | ours |
|---|---|
| Centralised rules engine, defined once | D1a ✅, D1e (org-wide) |
| Enforced on every PR, identically | D1b (deterministic), D1f (blocking) |
| Learns rules from senior reviewers | D1d — the one model use where being wrong is cheap |
| Evidence and audit trail | D4, and `Rule.reproducible` is what makes it worth reading |
| Standards met before a human reviewer sees it | D1f + E1 (pre-PR, local) |
| Duplicated code | D2c — normalised AST hashing, exact not guessed |
| Breaking changes | D2b/D2d (blast radius), D3b (cross-repo) |
| Harder maintenance / architectural drift | D2e — measured with `retrospective`, not asserted |
| Deep codebase context, multi-repo | D2, D3 — **declared** links, not an org-wide crawl |
| Catches hardcoded keys and passwords | D7a — deterministic. General vuln detection: **refused** |
| Does not retain source | D7b — already PROVEN by `just verify`, not a policy |
| Does not train on client code | D7d — structurally true; nothing to train |
| SOC 2 Type II | D7e — absent, and said out loud |
| Cloud / on-prem / air-gapped | D7f — Half A is air-gap-capable by construction |
| IDE / shift left | Phase E |

**What we deliberately do NOT copy:** the per-developer compliance scoreboard (D5), and any claim
to general vulnerability detection (D7a). Both are things we could ship and could not defend.

## Phase E — shift left: review before the pull request exists

`quantamind review <clone> --sha <sha>` already runs Half A locally and prints the same comment
the webhook would post — verified on this repository. What it cannot do is review work that has
no commit yet, and it prints prose for a human rather than something a coding agent can act on.

**And it enforces standards the endpoint cannot.** `ingest/standards/conventions.py` reads an
uncommitted `CLAUDE.md` from disk; the webhook never can, because its clones have no working tree.
A developer's own rules are checked here or nowhere.

- [x] **E1 Review before the pull request exists.** `ingest/worktree.py`; `--sha` optional. Uncommitted work first, then commits not on the default branch. **Untracked files included** — `git diff` omits them and they are usually the new code. Nothing leaves the machine. ~~`--sha` requires a commit; a `--sha` requires a commit; a
      developer about to open a pull request has uncommitted edits, or commits not yet pushed.
      Diff against the merge-base with the default branch, and against the index for uncommitted
      work. **Nothing leaves the machine on this path**, which is also the honest answer to
      "can we run it in an air-gapped environment".
- [x] **E2 Machine-readable output.** `--json`: the ranking, the allocation with `unread` named,
      and any findings with their provenance. This is what makes `/qm-review` useful inside
      Cursor, Claude Code or Copilot — the agent reads it and fixes, rather than a human
      re-typing prose.
- [x] **E3 `/qm-review` as an editor command.** `.claude/commands/qm-review.md`. Building it
      found `--json` emitting prose on two of three paths; see `CODEBASE.md` “`/qm-review` — E3”.
      A thin wrapper over E1 and E2. It is last on
      purpose: the value is entirely in what E1 and E2 return, and a wrapper over a weak answer
      is a faster way to be unhelpful.

**Why this is worth building before the enterprise surface:** it is the only path where a
developer sees output before anyone else does, so a wrong finding costs them ten seconds instead
of a public comment on their pull request. It is the cheapest place to be wrong, which makes it
the right place to find out whether the findings are worth anything.

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
