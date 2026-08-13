# Build plan — the reviewer that ranks first, then reads

**Written 2026-08-12**, branch `feat/gravity-reviewer`. Product argument and evidence are in
`docs/PRODUCT_BLUEPRINT_2026-08.md`; the measurements behind it are in
`docs/findings/SIGNAL_SEARCH_LOG_2026-08.md` and
`docs/findings/HISTORY_SIGNAL_BACKTEST_2026-08.md`.

**Filename note:** this file deliberately does **not** start with `session-`. The session-end
hook writes its record to `docs/plans/session-<branch>.md` and overwrote an earlier copy of
this plan at that path. Anything written by hand belongs outside that naming pattern.

Inference is now in scope. This plan says what to build, in what order, with which model, and
what each stage costs.

---

## The measurements this plan is built on

Nothing below is designed around a hypothesis when a measurement exists — and a measurement
that turns out to be unsound is marked, not deleted.

| Measurement | Value | Status | What it decides |
|---|---|---|---|
| Attention ranking, top-1 | **85.3%** vs a 72.0% null, 4,293 events, 17 of 17 repositories | SOUND | Where inference is spent |
| Language generalisation | six languages, lift **+8.9 to +26.0** over each null | SOUND | Addressable surface |
| Breakage localisation by co-change | **0 of 8** | SOUND | Why we do not ship a "missing file" finding |
| Fix lands inside files already changed | **11 of 11** | SOUND | Why the deterministic layer cannot find the defect alone |
| Outcome rule granularity | symbol lift **+46/+36/+28/+17**; file erratic; line dead | SOUND (rerun) | **Files give traffic, symbols give the problem** |

**A measurement defect, recorded rather than quietly redone.** Every result above marked SOUND
was produced with `git log --name-only` or `--numstat`, which read no file contents. Every
symbol-level result was produced with `git log -U0 -p`, which **fails outright on a
blob-filtered clone**:

```
fatal: You are attempting to fetch 27f89abbd669d6351d66f9c49b6842ab49e71eb9,
which is in the commit graph file but not in the object database.
```

It emits a partial patch stream, exits non-zero, and the harness did not check the return code
— so every symbol-level run silently analysed a truncated prefix of history, of varying length
between runs. Two runs of the identical command on one repository returned 710 and 918 commits.
The repository actually holds 3,313.

**Voided by this: the symbol-versus-file comparison, the nested-versus-global comparison, and
every retrospective figure produced against these clones.** The file-level core is unaffected.

**Rule for the branch: any harness reading patch content must assert the git exit code, and any
clone used for symbol-level work must carry full objects.** The blob-filtered clone is correct
for `--name-only` work and wrong for anything that reads a diff body.

**Fix lands inside files already changed** is the reason inference is in the design at all: the
defects are semantic, so a parser cannot judge them. **Attention ranking** is the reason
inference is affordable: we know which part of the diff to spend it on. Both survive the
defect above, so the architecture does.

---

## Architecture — the allocator and the reader

```
pull_request
   │
   ├─ 1. deterministic pass   (no model, no key, ~zero marginal cost)
   │       git-history ranking of changed units
   │       parsed signatures and references
   │       what could not be resolved, and why
   │
   ├─ 2. allocation           the ranking decides the inference budget
   │       rank 1        → deep read, high effort, multi-pass
   │       rank 2-3      → single shallow read
   │       cold units    → no model call at all
   │
   ├─ 3. inference            structured findings only
   │
   ├─ 4. verification         parser checks every structural claim the model made
   │       claim confirmed → publish · claim contradicted → drop silently
   │
   └─ 5. one comment, or silence, plus the coverage line
```

**The verification pass** is the pillar no competitor can state, and it is cheap: the
deterministic layer that allocated the budget is the same layer that adjudicates the output.

---

## Model and API decisions

**Model: `claude-opus-5`** at $5 per million input tokens and $25 per million output. 1M
context, 128K max output. Cheaper tiers exist and are a real lever, but that is a decision to
make against measured quality on our own corpus, not a default to assume.

**Effort.** Start at `xhigh` for the deep read — the documented starting point for coding and
agentic work — then sweep down. On this model `low` and `medium` are unusually strong, and the
sweep is the primary cost lever. The shallow pass starts at `low`.

**Thinking is on by default on this model**, and `max_tokens` caps thinking plus response
together. Two consequences: size `max_tokens` with headroom (start at 64K at `xhigh`), and
**stream anything above roughly 16K** or the request risks an HTTP timeout. Disabling thinking
is only legal at effort `high` or below and brings two failure modes — tool calls written as
plain text, and internal tags leaking into output — so we leave it on.

**Structured outputs, not prose.** Findings come back through `output_config.format` with a
JSON schema. The verification pass can only check a claim it can parse, so free-text review
output would make that pillar impossible.

**Refusal handling is not optional.** This model's safety classifiers can decline a request —
HTTP 200 with `stop_reason: "refusal"` — and code that reads `content[0]` unconditionally
breaks. Check `stop_reason` first, and opt into server-side fallbacks in `"default"` mode
rather than pinning a substitute model, so the routing stays correct as models change.

### Prompt caching is the cost architecture, not an optimisation

Caching is a **prefix match**: any byte change invalidates everything after it, and the render
order is tools, then system, then messages. That maps onto this product exactly:

| Position | Content | Volatility |
|---|---|---|
| Prefix, cached | repository conventions, resolved signatures, the ranking index summary | per repository |
| Suffix, uncached | this pull request's diff and the ranked unit | per request |

Cache reads cost about a tenth of base input; writes cost 1.25× at the five-minute window and
2× at the hour. **The five-minute window breaks even at two requests**, which a busy repository
clears easily; the hour window needs three and suits repositories with bursty traffic.

Two rules the implementation must not violate, because both are silent failures:

- **Nothing volatile in the prefix.** No timestamp, no request identifier, no per-user string
  in the system prompt. A clock in the prefix makes every request a cache miss with no error.
- **Tools and model are frozen for a conversation.** Both render at the very front.

Verify with `usage.cache_read_input_tokens` in tests — a persistent zero means an invalidator
is live. The minimum cacheable prefix on this model is 512 tokens, half what earlier models
required, so even a small repository summary caches.

### The Batch API is for the audit, not the review

Batches run at **half price**, accept up to 100,000 requests, and mostly finish within an
hour. Pull-request review is latency-sensitive and cannot use them. **The attribution audit
is the opposite** — a backfill across a customer's history, run once, read the next day. That
is the revenue product, and it runs at 50% off with the same cached prefix.

---

## What a review costs

Illustrative, at list prices, for a pull request touching six files with a repository summary
of about 20,000 tokens.

| Component | Tokens | Cost |
|---|---|---|
| Repository prefix, cache read | 20,000 at 0.1× | $0.010 |
| Ranked unit and its neighbours, uncached | 3,000 | $0.015 |
| Output including thinking | 2,000 | $0.050 |
| **Per pull request** | | **≈ $0.075** |

Against reading the whole diff at uniform depth — call it 15,000 input tokens and 4,000 output
— roughly **$0.175**, so allocation saves on the order of **2×**, not 10×. Say two, and be
right.

At 200 pull requests a month that is **about $15 of inference per repository per month**,
against a free tier that costs only compute. That number is the floor under any price we set,
and it is the first thing to re-measure once real diffs are flowing.

---

## Build order, with a gate on each stage

Stages are named, not numbered, and each one names the stage it follows. Inserting a stage
between two numbers is how a build order silently stops matching the document that describes
it — the same failure the citation rule in `AGENTS.md` exists to prevent.

**The deterministic engine.** First. Ranking, signatures, coverage line. Offline command, no
hosting, no model. **Gate: reproduces the 85.3% top-1 figure on the corpus already collected.**
If the productionised ranker does not match the research ranker, the research is not the
product and the difference must be explained before anything is built on it.

**The retrospective report**, after the engine. The same pipeline run **backwards** over a repository's
merged pull requests, delivered during install. This replaces a forward shadow-mode period:
waiting a month for a number the history already contains is how a tool gets uninstalled before
it is judged, and only a history-based product can avoid it — replaying hundreds of pull
requests costs an inference-per-diff reviewer hundreds of diffs of tokens, and costs us compute.
**Gate: the lookahead bound is asserted per pull request with `git merge-base --is-ancestor`,
and a deliberate future-leaking run moves the score.** If leaking the future changes nothing,
the report is measuring lookahead and is void — this failure has already occurred once in this
repository's own harness.

**The free tier**, live on day one and narrow, alongside the retrospective. GitHub App, read-only on code, write-only
on a comment. Coverage line, structural findings, one routing line. No model, no key. **What
ramps is breadth, not time**: start at top-ranked function *and* high prior rework rate (~3–5%
of pull requests), widen to top-ranked function alone (~10%), then top two (~15%). **Gate for
each widening: acceptance rate climbing *and* post-merge defect rate flat or falling.** Both are
measurable from the first week precisely because the tool is live.

**The allocator and the deep read**, after the free tier is trusted. Inference on the ranked unit only, structured
output, streamed. **Gate: measured token cost per pull request is below uniform review of the
same diffs on the same corpus.** This is the claim the pricing rests on and it is currently
UNVERIFIED.

**Parser verification**, shipped with the deep read and never after it. Every structural claim checked before publication. **Gate: a
sabotage test in which a deliberately false structural claim is injected and dropped.** A
verifier that never rejects anything is not a verifier — that failure has already occurred
twice in this repository.

**The audit, on batches**, last. The attribution report over a customer's history.

---

## What must be measured before any of it is sold

1. **Does a human act on the routing line?** Top-1 accuracy against historical fixes is 85.3%.
   Whether a reviewer reading that hint before the bug exists catches something they otherwise
   would not is **UNVERIFIED**, and it is the whole commercial risk. One month of shadow mode
   on three repositories.

   **Measure two signals, and require both.** Acceptance rate alone can climb simply because
   the tool became timid, so it is paired with the outcome it is supposed to improve:

   | Signal | Direction required |
   |---|---|
   | Acceptance rate — findings a reviewer acts on | climbing |
   | Post-merge defect rate, under the corrected attribution rule | flat or falling |

   **One moving without the other is a red flag, not a result.** A practitioner report puts
   first-pilot acceptance at 35–40%, climbing past 60% as context improves — useful as a
   target to beat, and **REPORTED**, with no method we can check.

   **The defect-rate half needs an incident-to-pull-request link, and we consume rather than
   build it.** Datadog's Error Tracking already ships suspect commits, VERIFIED from its own
   documentation, on four stated criteria — the commit *"modifies one of the lines in the stack
   trace"*, was *"authored before the first error occurrence"* and *"no more than 90 days
   before"*, and is *"the most recent commit that meets the above criteria"* — plus ticket
   creation from the issue panel and automation rules that open tickets when issues match. So
   the incident-to-commit half, the ticket, and the routing are all a configuration, not a
   build.

   Two things their documentation does **not** claim, and we should not either: **automatic
   pull-request linking and auto-assignment.** Commit-to-pull-request is a GitHub API lookup —
   a thin gap, not a moat.

   What no vendor supplies is a defensible **denominator**: the standard file-overlap rule is
   wrong on 67.9% of its verdicts. Their webhook plus our corrected rule is the measurement.
   Re-implementing their attribution, or emitting a per-incident blame ticket, is out of scope —
   it is an occupied position and the artifact gets disabled.
2. **The token saving from allocation**, against uniform review. Asserted above, unmeasured.
3. ~~**Symbol against file granularity.**~~ **Settled — see below.**

### Language coverage: the signal is not Python-specific

File-level ranking, same code path, pathspec swapped, across the repositories already cloned:

| Language | Events | Ranker | Null ranker | Random | **Lift over null** |
|---|---|---|---|---|---|
| TypeScript | 400 | 80.8% | 54.8% | 59.2% | **+26.0** |
| Java | 41 | 90.2% | 73.2% | 59.4% | **+17.1** |
| Python | 5,242 | 85.4% | 70.9% | 67.4% | **+14.5** |
| C++ | 63 | 82.5% | 68.3% | 72.0% | **+14.3** |
| Go | 185 | 85.4% | 76.2% | 64.3% | **+9.2** |
| JavaScript | 168 | 77.4% | 68.5% | 58.8% | **+8.9** |

**Six languages, every one positive, and Python sits in the middle rather than at the top.**
The prediction that one-unit-per-file languages would collapse toward the null did not hold:
Java shows the second-highest lift, on the smallest sample.

Four limits, stated rather than implied:

- **This is file-level ranking only.** It establishes that the history signal exists in these
  languages. It does **not** establish that symbol extraction works in them — that is a separate
  build, using git's funcname diff drivers as the cheap first pass and tree-sitter as the
  precise one.
- **The non-Python samples are small** — 41 to 400 events against Python's 5,242. Java's
  +17.1 rests on 41 events and should not be quoted as a headline.
- **Kotlin returned no result at all**, despite being the largest non-Python corpus available
  (2,344 files in one repository). Unexplained, and recorded rather than dropped.
- **The outcome rule assumes English fix-keywords in commit messages.** That is a natural-language
  assumption, not a programming-language one, and it travels differently.

### Granularity: files give traffic, symbols give the problem

Resolved, on blob-complete clones with the exit code asserted, superseding the void'd runs.

**Rank and judge at symbol level; use files for coverage, not for judgement.** Symbol-overlap
lift over a random pick is **+46, +36, +28, +17** across four repositories; file overlap is
erratic (+50 to −1) and line overlap is dead (+7 to −5). Full table and the reasoning in
`docs/findings/RETROSPECTIVE_SWEEP_2026-08.md`.

File-level ranking remains the fallback where no symbol can be resolved, and remains what the
4,293-event result was measured on — but it measures **which file is busy**, not which change
came back.

---|---|---|---|---|---|
| **Symbol** | 75.9% | 59.1% | 55.4% | **+16.8 points** | 340 |
| **File** | 87.8% | 77.5% | 71.5% | +10.3 points | 809 |

**Read the lift column, not the accuracy column.** Symbol accuracy is lower because there are
more candidate units per change and therefore a lower random baseline — 55.4% against 71.5%.
Against its own null, the symbol ranker does substantially better.

**The design follows directly: rank at symbol level where a symbol is extractable, fall back
to file level otherwise.** There is no need to choose — the fallback is strictly better than
silence, and both tiers are independently validated.

**The coverage gap is an instrument limitation, not a property of symbols.** The symbol ranker
produced 340 events against the file ranker's 809 — **42%** — because changed units were
extracted from diff hunk headers, which only name a unit when the hunk begins at a `def`. A
real parser over the changed ranges should close much of that gap, and closing it is a task on
the branch, not an open research question.

**This is also the differentiator claim, and it survives.** CodeScene and CodeRabbit both
operate at file granularity; the tier that carries the most information is the one neither
ships.

---

## Where this would and would not beat the incumbents

Stated plainly so the plan cannot be read as claiming more than it earns.

**Better, and defensible:** noise (fires on roughly a tenth of pull requests against their
near-total coverage); typed silence (verified uncontested across seven tools); attention
routing (85.3% against a 72.0% null across 4,293 events); structural claims verified before
publication; and cost, both per review and as a free tier with no marginal cost.

**Not better, and no measurement says otherwise:** finding bugs in the diff. Same model class,
same field precision ceiling of 50–76%. Nothing measured here is about *what is wrong* — only
about *where to look*. Also not better on visible surface area, on the stacked-pull-request and
merge-queue product, or on distribution.

**The whole position therefore rests on buyers valuing honest coverage and targeting over
visible output volume.** That has been UNVERIFIED since the first market file and no amount of
building resolves it.

---

## What would falsify this plan

- Reviewers ignore the routing line in shadow mode.
- Allocation does not measurably reduce cost against uniform review — the cost pillar is then
  marketing, not architecture.
- The verification stage never rejects a model claim, meaning it is not verifying.
- The free tier fails to convert to audit revenue, leaving adoption with no business model.
- A competitor ships typed silence. It is the cheapest pillar to build and the only one they
  structurally cannot answer, which makes it the one to ship first.
