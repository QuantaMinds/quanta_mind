# QuantaMind

> **Canonical document.** Every measurement in this repository is defined here. Other
> documents copy from it and carry a reconciliation date; where they disagree, this file
> wins. Vendor figures below are dated at the point of use and re-checked quarterly.

**Written 2026-08-13. Self-contained — nothing here cites another document.**

**Two kinds of number appear.** Ones **we measured**, each stated with its method. Ones taken from
**external sources** — vendor documentation, published benchmarks, industry studies — each listed
with its source and verification status in the appendix. Where a claim is unproven it says so.

Nothing described here is shipped. Where a claim is unproven it says so.

---

# 1. What QuantaMind is

> **QuantaMind — Focus: a model-free pass ranks where to look first in a large change, by which
> files a later fix has returned to; the model reads only there, one isolated judge adjudicates
> every claim before it is published, and a coverage line names what was not analysed.**

That is the one-line thesis, in the form the category states its own. **Every other line in that
category ends in "…and reviews your code." Ours reviews a tenth of it, on purpose, and says which
tenth and why.** The bet is not that we skip the model — it is that deciding *where* to point it,
and refusing to publish what an isolated judge cannot confirm, beats reading everything at one
depth.

**Every AI code reviewer reads the whole diff at the same depth. QuantaMind decides where to
look first, and only reads hard there.**

## The problem, in plain words

**Agents write most of the pull requests now. The people reviewing them did not multiply.**

A team that opened twenty pull requests a week opens sixty. The same two or three senior
engineers still have to read them, and they are the same people you least want spending their
day on line-by-line review. Industry figures put senior engineers at **8–12 hours a week**
reviewing. At a $150K salary that is **roughly $28,000–$42,000 a year of senior engineering time
per engineer**, and **44% of teams** name slow review as their single biggest delivery
bottleneck.
AI-authored pull requests merge at **32.7%** against roughly **84.5%** for human-authored ones, and the
largest single reason they are rejected is **inactivity — 17.3%**, auto-closed after a week
because nobody got to them.

**Then the review tools arrived and made it worse.** They comment on nearly every pull request,
and a third of what they write is not worth reading — an independent audit of the market leader
found **36% of comments were noise or nitpicking**. So the reviewer's queue went from twenty
pull requests to sixty, each one now carrying a wall of bot comments they have to wade through
before finding anything real.

**The bottleneck was never detection. It is attention.** Every incumbent responds to the flood
by generating more text into a queue that is already unreadable. Adding volume to a volume
problem does not help, and the only way to shorten a queue is to take things out of it.

**QuantaMind is quiet on purpose.** It comments on about one change in ten, and when it does it
names the **file** worth reading first — and says which files it did not read. The unit is the
file everywhere allocation happens; a function name appears in the routing sentence only, to give
a human a place to start inside the file we ranked.

## The problem with reviewers as they exist today

**They comment on nearly everything, and a third of it is not worth reading.** An independent
audit of one market leader — 28 pull requests, 32,784 lines, 693 files — found **15% useless and
21% nitpicking: 36% noise**. Stated fairly, the same audit found **35% genuine quality
improvements and 3% security-critical findings**, so this is not a claim that these tools are
worthless. It is a claim that **a third of what lands in the reviewer's queue is not worth the
reading time**, which at sixty pull requests a week is the difference between a queue that gets
read and one that does not.

The field's precision on **the benchmark's ONLINE layer** — did a developer change the code —
spans roughly **49% to 76%**: the top tool converts about three comments in four into an actual
code change, the market leader about one in two. **That is a behavioural measure, not a truth
measure, and `publishing-rules.md` bars it from standing beside our own numbers.** It is quoted
here to describe the market's own claims about itself, and nothing below compares to it. On the
benchmark's *offline* layer, scored against human-verified issues, the same market leader is at
**36.5%**. One vendor
keeps its noise low by commenting rarely, and publishes a **sub-3% false-positive rate** — a
measure of how often it is wrong, not of how much it finds.

**They cannot tell you what they failed to read.** We checked seven shipping reviewers against
their own documentation. **Not one can emit "I could not analyse this."** One vendor documents
the collapse in its own words: its `neutral` result means *"found issues, the run was cancelled,
or hit an internal error"* — three unrelated situations, one signal — and states outright that
it emits no `skipped` conclusion. Another filters *"anything low-confidence before it reaches
the pull request"*: uncertainty is deleted rather than reported. The single tool that typed
absence correctly is dead — 8 stars, last code push December 2023.

The consequence is that **silence from a reviewer is indistinguishable from safety**, and every
buyer currently reads one as the other.

**They cost what they cost because they read uniformly.** Feeding an entire diff to a large
model at full depth is simultaneously the source of the token bill and the source of the noise.

## ~~Our measurement of the reviewers' actual catch rate~~ — WITHDRAWN

**We measured a leading reviewer at 10 of 65 pull requests that later required a symbol-level
fix, against 23.9% of those that did not, and this document previously carried it with caveats.
It is withdrawn, and the caveats were not enough.**

**The interval settles it.** 10/65 is 15.4% with a Wilson 95% interval of **8.6% to 26.1%** —
and **the 23.9% comparison figure sits inside that interval.** So the measurement cannot separate
that reviewer's finding rate on changes that later broke from its rate on changes that did not.
It demonstrates no targeting deficiency in either direction. A number that cannot distinguish the
two things it is quoted to contrast is not a weak finding; it is not a finding.

**And the denominator is worse than 65.** By the blind labelling further down this document,
roughly 86% of symbol-overlap pairs are not genuine repairs — so the real base is somewhere near
nine observations, where no interval is informative.

**Why it is withdrawn rather than caveated.** Every version of it named a company. A claim about
a named competitor that its own confidence interval cannot support is a liability before it is a
methodological error, and a caveat does not travel with a number once the number is quoted. **A
claim we have withdrawn is not a claim.**

What survives is the weaker statement, which needs no measurement of ours: **nobody in this
market publishes their own miss rate.** That is verifiable by looking, and it is the argument
this section was reaching for.

## What we do differently

A free pass that runs **no model** ranks the **files** a change touches by how often each has
needed a follow-up fix before. **That ranking then decides where the model reads** — deep on rank
one, shallow on two and three, not at all on a cold file — and every claim it returns goes to an
isolated judge before anyone sees it. What ships is the surviving findings plus a line saying what
was not analysed and why.

**FILES, NOT FUNCTIONS, AND THE DIFFERENCE IS THE RESULT.** At a three-unit budget, file-level
ranking misses **1.22%** of the changes a later fix returns to; function-level misses **8.84%** on
the same events, and **+2.29 points** even at matched coverage. The file arm is the one that
replicated out-of-sample. `rank/order.py` emits `Site(path, line=0)` — the zero is what says the
unit is the whole file — and earlier drafts of this document described the arm that measured
worse. **Functions appear in one place only: the routing line's prose, which names a function to
say where to start reading. Allocation is file-level everywhere.**

**THE MODEL READS ONLY WHERE THE RANKER SENDS IT, AND ONE ISOLATED JUDGE DECIDES WHAT IS
PUBLISHED.** The reviewer half is part of the product. It runs on **Gemini**, over the files the
model-free ranker selected, and nothing it produces reaches a pull request until `verify/` clears
it. `infer/` and `verify/` are empty today and `quantamind review` exits 2 — that is a build state,
not the product.

**THE JUDGE IS THE RELIABILITY MECHANISM, AND IT IS ISOLATED BY CONSTRUCTION.** Raw model findings
are bad: two corpora and four blind rater pools put them **66.7–82.1% wrong** at **0.013–0.037
correct findings per pull request**, and nine designs of prompt engineering moved that nothing.
**So raw findings are not what ships.** `verify/` adjudicates every claim, and the architecture
forbids it from importing `infer/` — the layer judging the model's claims cannot start trusting
them.

**AND THE JUDGE MUST NOT BE THE REVIEWER'S OWN FAMILY. THAT IS MEASURED, NOT ASSUMED.** On
2026-08-20 a judge sharing the subject's model family was run against a pool a careful rater had
already graded. It agreed with that rater **34.9% of the time**, and it did not fail randomly — it
**ratified the reviewer's own hallucinations**, accepting invented claims about which tag a pinned
SHA carries, and repeating the reviewer's belief that 2026 lay in the future while itself running in
2026. **A judge sharing the subject's blind spots certifies them.** Twelve of twelve planted
sabotage findings were caught while that was happening, so the sabotage control did not detect it
either. The isolated judge is a different family, and this is why.

Four properties follow. **Two are now measured out-of-sample, one is billed, one is verified —
and a fifth that this document used to claim has been measured and withdrawn.** See
`docs/product/evidence-ledger.md` for the full accounting, including what failed.

| | |
|---|---|
| **Quiet** — *measured at file level for the first time* | **Six of seven repositories sit at 8–13% on their most recent window**, measured 2026-08-20 on repositories the rule was not built from and spanning 2,007 to 38,217 commits. `angular/angular`, the largest, is the steadiest at **11%**. **Within a repository the rate DRIFTS** — `sveltejs/svelte` from 23% down to 11%, `facebook/react` from 3% up to 13% — so it is a direction, not a constant. **`gin-gonic/gin` sits near 30% and that is a stable property of a 236-file surface, not an error.** The product does not quote a band: `rank/firing.py` replays the customer's own history and prints their rate before they install |
| **Honest** | Reports its own blind spots — verified as unavailable to all seven competitors |
| **Right about where to look** | **Replicated out-of-sample.** Ranking the changed files by prior touch count and reading the top three misses **1.21%** of the changes a later fix returns to, against **3.12%** for an alphabetical ordering — on **six repositories the method was never developed against**, n = 2,400, McNemar **p < 0.000001**, positive in **6 of 6**. The original eight gave **1.44% vs 3.31%**. The two lifts differ by **0.05 points**. **Leave scrapy out and the lift is +0.90 rather than +1.92** — `publishing-rules.md` requires the smaller number wherever one figure is quoted, because a caveat does not travel with a number into someone else's deck |
| **Honest about what cannot be decided** | A claim needing a fact outside the diff is labelled, not published. **A MODEL gate separated at Fisher p = 0.0007 on n = 29** — an inference call, not a rule, with wide intervals and a rater whose reasoning correlated with the gate's own criterion. **The free keyword rule that approximates it was tested out-of-sample and INVERTED: D/L 1.40 against chance 3.64.** The largest failure class is a confident claim the diff cannot settle |
| **Cheaper** — *billed, not estimated* | **$0.119 per pull request** on real diffs through Vertex, against a $0.140 derived estimate — but the estimate was right by luck: input is 5.2% of the bill and **thinking is 91.3%** |


## Correction — "Quiet" is not a measured property of the shipped product

**A client will ask how that number was obtained. This is the answer, written before they ask.**

**The 10–12% is real.** `docs/findings/RETROSPECTIVE_SWEEP_2026-08.md`, eight repositories spanning
an 80× velocity range, fire rates of 10, 10, 11, 11, 12, 12%. Nobody invented it.

**It describes a different unit.** That sweep ranks **functions**. This product ranks **files** —
deliberately, because file-level misses **1.22%** of the changes a later fix returns to against
function-level's **8.84%**, and the file arm is the one that replicated out-of-sample. **The
file-level firing rate had never been measured anywhere.**

**And the mechanism was never built.** The sweep's own heading is *"The firing rule that works: a
percentile, not a threshold"*; `rank/order.py` shipped the absolute threshold that sweep rejected,
and `types/ranking.py` already recorded that `threshold_percentile` "governs nothing".

**Measured 2026-08-20**, four repositories the rule was not built from — `sveltejs/svelte`,
`vuejs/core`, `gin-gonic/gin`, `nestjs/nest`, 1,200 changes:

| firing rule | pooled rate | **spread across the four repositories** |
|---|---|---|
| absolute threshold, **as previously shipped** | **91.3%** | 83.0–97.0% |
| top decile of this repository's **files** | **62.2%** | 42.7–79.7% |
| top decile of this repository's **changes**, calibrated IN-SAMPLE | ~11% | 10.0–12.3% |
| **top decile of changes, calibrated out-of-sample — WHAT SHIPS** | **8–14% on six of seven repositories** | gin-gonic/gin, alone, at 31% |

**Seven repositories, none of which the rule was built from, spanning 2,007 to 38,217 commits:**

| repository | commits | files ever | earlier windows, each vs **its own** floor | **current** |
|---|---|---|---|---|
| `angular/angular` | 38,217 | 30,108 | 12 11 11 10 | **11%** |
| `facebook/react` | 21,640 | 13,323 | 14 8 11 15 | **12%** |
| `nestjs/nest` | 21,639 | 4,541 | 10 12 14 12 | **8%** |
| `sveltejs/svelte` | 11,326 | 17,236 | 14 10 18 28 | **14%** |
| `vuejs/core` | 7,157 | 957 | 12 18 7 12 | **13%** |
| `trpc/trpc` | 4,902 | 2,542 | 14 6 9 11 | **12%** |
| `gin-gonic/gin` | 2,007 | **236** | 32 24 24 32 | **31%** |

**Six of seven are STEADY across their own history, and that is the finding.** Each earlier window
is scored against **its own contemporaneous floor**, which is the only comparison that isolates
selectivity from activity. Six sit at 8–15% throughout; `gin-gonic/gin` sits at 24–32% throughout,
which is a stable property of a **236-file** surface against angular's 30,108, not an error.

**A SELF-CALIBRATING RULE HAS LITTLE TREND BY CONSTRUCTION, AND THAT IS THE POINT.** If the bar
moves with the repository, each period fires at roughly its own target whatever the activity did.
**So the rate is a per-repository constant that can be measured once, at install, and relied on.**

> **THIS MEASUREMENT WAS WRONG TWICE BEFORE IT WAS RIGHT, BOTH TIMES LOOKING PLAUSIBLE.**
> First the earlier windows were sliced out of the calibration set itself — in-sample, so the newest
> slice shared a period with the bar and could agree for that reason. Then they were made disjoint
> but scored against **today's** floor, which compares a top counted in one era against a bar
> derived from another: `trpc/trpc` read **70%, 68%, 62%, 54%** on periods when it was simply
> busier, against 12% now. **That is the same defect that silenced svelte and gin, in a third
> costume**, and it produced a confident trend in five of seven repositories that does not exist.
> A fourth instance would have been reported as a finding.
>
> **And an earlier report of these windows was printed newest-first and read as oldest-first**,
> which inverted the direction for two repositories. The SQL had no `ORDER BY`: a trend read off an
> unordered list is noise wearing a direction.


**Six of seven land at 8–14%, and the largest repository is the tightest.** The documented band
substantially holds at file level — which was not knowable before, because it had only ever been
measured at function level.

**The one outlier is a small-surface repository, and the product detects it.** `gin-gonic/gin` has
**236 files ever** against angular's 30,108 — a 128-fold difference. On a surface that small the
touch-count distribution is coarse, a decile lands where many changes tie, and the rate lands at
31% with a 17-point range. **`rank/firing.py` reports that range and marks the estimate unreliable
rather than quoting the headline.**

**A MINIMUM CALIBRATION SIZE WAS PROPOSED AND THE MEASUREMENT REFUSED IT.** Sample size does not
predict stability: `sveltejs/svelte` calibrates on **703** changes and swings 9 points, `vuejs/core`
on **243** and swings 7. `gin` calibrates on 184 — more than vue — and is the unreliable one. **The
driver is the file surface, not the sample.** A size floor would have been a rule with nothing
behind it, and the variability report is what it was reaching for.

**An average is still not what any individual customer gets.** So the product computes it from the
customer's own history instead of quoting a band: `rank/firing.py` replays their recent changes
through the real gate and prints *"on your last 400 changes this would have spoken 88 times — 22%"*
before anything is installed.

**Three bugs were found getting here, each by a number that did not close:**

1. Calibrating over "the last 400 changes" reached about **1.5 years back** on an active repository,
   so the floor described a busier era than the change being judged.
2. Each calibration change's top was counted in **its own** prior year and compared against a top
   counted in **today's** year — two different quantities. On a cooling repository the floor sat
   above everything the present could produce: **`sveltejs/svelte` fired on 0.0% of 300 changes.**
   Counting both sides in the same window took it to **13.0%**.
3. On integer counts the decile lands on a value many changes share. On `gin-gonic/gin` **every one
   of the 87 firings was an exact tie at the floor** — `>=` fired on 29.0% and `>` on **0.0%**. The
   rule was deciding a quarter of the corpus on which comparison operator was written. The cut is
   chosen by realised share now, not by index.

**A third typed state exists because of the second bug.** Beside `NO_HISTORY` and `FLAT_NONZERO`
there is now `CONCENTRATED`: a repository whose few dominant files put the decile beyond reach, so
the gate would be structurally silent. **That silence is not legible from a coverage line** — the
review would truthfully report that nothing was skipped, because nothing was. It is named and
reported at install rather than discovered in week three.

**The in-sample row is why this needed measuring twice.** Calibrating the decile on the same
changes it is tested against gives 10–12% *by construction* — it is a tenth of a tenth. Calibrated
on changes it has not seen, the same rule gives 0.0–25.0%. **This project has hit that collapse
before: the word-list filter was beautiful in-sample and inverted on fresh data.**

**A prediction was written down first and it was WRONG.** Files were expected to fire *less* than
functions — a pull request holds fewer files than functions, so fewer units get a chance to clear
the bar. They fire *more*, because the top-ranked file of a change is the most-touched among the
changed files, and changed files are heavily selected relative to the repository as a whole.

**Only the IN-SAMPLE change-calibrated rule reproduces 10–12%, and it is definitional.** A top
decile of changes fires on a tenth of changes because that is what a top decile is. Out-of-sample
the same rule ranges 0.0–25.0%.

**"10–12% everywhere across an 80× velocity range" DOES NOT HOLD AT FILE LEVEL.** It was measured
at function level and it does not transfer to the unit this product ships. **The transferable
finding was never the rate — it is the contrast: 11% against 53% for an absolute threshold, which
is the evidence that a percentile travels between codebases better than an absolute number.** Even
that is weaker than it reads: the percentile's own spread here is 0.0–25.0%.

**What ships is still a large improvement and is not the claim.** 91.3% to 9.5% pooled is the
difference between commenting on nearly every pull request and commenting on roughly one in ten.
**The per-repository stability that would let us call the product "quiet" has not been
demonstrated**, and until it is, that word does not belong in a table of proven properties.

---

# 2. How it works

> **STAGES 3 AND 4 — READ and VERIFY — ARE THE PRODUCT AND ARE NOT YET BUILT IN CODE.** `infer/`
> and `verify/` are empty today and `quantamind review` exits 2; what runs in production right now
> is RANK, ALLOCATE and the coverage line. **The measurement that used to close them is now the
> specification for stage 4.** Nine designs of prompting could not make raw findings safe to
> publish — 66.7–82.1% wrong — so the answer is not a better prompt, it is that nothing is
> published until an isolated judge confirms it.

```
  a pull request opens
        │
  ┌─────▼───────────────────────────────────────────────────┐
  │ 1. RANK        no model, no key, ~zero marginal cost     │
  │     BUILT      every changed FILE, by how often it has    │
  │                been touched in the prior year             │
  │                (file-level: function-level missed 8.84%   │
  │                 against the file arm's 1.22%)             │
  ├──────────────────────────────────────────────────────────┤
  │ 2. ALLOCATE    the ranking decides the inference budget   │
  │     BUILT      rank 1  → deep read, high effort           │
  │                rank 2–3 → shallow read                    │
  │                cold    → no model call at all             │
  │                this is what bounds the bill: the model    │
  │                never sees a file the ranker did not pick  │
  ├──────────────────────────────────────────────────────────┤
  │ 3. READ        NOT BUILT YET — Gemini, on those files     │
  │                only, returning structured findings        │
  │                raw findings are 66.7–82.1% wrong and      │
  │                NONE is published unverified               │
  ├──────────────────────────────────────────────────────────┤
  │ 4. VERIFY      NOT BUILT YET — ONE ISOLATED JUDGE         │
  │                a DIFFERENT model family from stage 3,     │
  │                plus the parser on structural claims:      │
  │                confirmed → publish, else drop             │
  │                THIS is what makes stage 3 shippable       │
  ├──────────────────────────────────────────────────────────┤
  │ 5. SAY         one comment, or silence                    │
  │                plus the coverage line, always             │
  └──────────────────────────────────────────────────────────┘
```

**That symmetry is the design, and stage 4 is not built yet, so it is an argument rather than a
property today.** The deterministic layer that allocates the budget is the same layer that
adjudicates the model's output, which is what makes verification cheap. Nothing adjudicates
anything at present: `verify/` contains an `__init__.py`, and until it does not, `quantamind review`
exits 2 rather than publishing unverified findings.

**THE JUDGE IS ONE, AND IT IS ISOLATED.** Not an ensemble, not a second pass by the reviewer, not a
reflection step in the same context — one judge, in a different model family from stage 3, that
never sees the reviewer's reasoning. `AGENTS.md` rule 7 enforces the isolation in code: `verify/`
may not import `infer/`. The measurement behind that constraint is in section 1 — a same-family
judge agreed with a careful rater on 34.9% of findings and certified the reviewer's own invented
facts.

## The day you install it

**Twenty minutes.** One GitHub App, read-only on code, write-only on a comment. No merge
rights, no customer model key.

It reads the repository's history once and builds a single index: for every **file**, how often
changing it has required a follow-up, and which files those follow-ups touched.

**The same pipeline runs backwards over your merged pull requests and hands you the answer BEFORE
you install anything** — how many of your changes came back, how many we would have commented on,
and on how many of those we would have named the **file** the fix returned to.

**That is a different motion from the install, and the distinction matters.** The retrospective is
`uv run quantamind retrospective <clone>`: a clone on your own machine, no App, no token, no code
leaving it. The install above is the App watching new pull requests. **You can have the number
without granting anything**, which is the point — a reviewer that runs a model over every diff
cannot open that way, because replaying 340 pull requests costs it 340 pull requests of
inference.

## What ramps is breadth, not time

It comments from day one, narrowly, and widens only on evidence:

| Tier | Fires when | Volume |
|---|---|---|
| Start | the top-ranked **file** is in this repository's top decile of **changes** | **8–13% on six of seven**; computed per repository at install |
| Widen | top two ranked **files** | untested |

Widening requires **two signals moving together**: the acceptance rate of findings climbing,
**and** the post-merge defect rate flat or falling. One without the other is a red flag —
acceptance can climb simply because the tool got timid.

---

# 3. How it works technically, end to end

## The worked example

A payments service. An agent opens a pull request for ticket PAY-3318, *"Refund fails when a
partial capture exists."* It changes **three functions across two files**:

```
refunds/service.py    process_refund()
refunds/service.py    _build_refund_payload()
notifications/mail.py send_refund_email()
```

> **STEPS 1 TO 4 ARE BUILT. STEPS 5 TO 7 DESCRIBE A PIPELINE THAT DOES NOT RUN.** `infer/` and
> `verify/` contain an `__init__.py` each and `quantamind review` exits 2, so the model call, the
> structural verification and the published finding below are a record of what was designed and
> measured — not of what happens when a pull request opens. Each step says which it is. What runs
> in production is the ranking, the allocation labels and the coverage line.

### Step 1 — extract the changed units — **BUILT**

We do **not** diff whole files. We read the diff at zero context and take the function each
hunk sits in:

```
$ git diff -U0 <base>..<head> -- '*.py'

+++ b/refunds/service.py
@@ -71,0 +72,6 @@ def process_refund(order, amount):     ← unit: refunds/service.py::process_refund
@@ -140,2 +146,3 @@ def _build_refund_payload(order):      ← unit: refunds/service.py::_build_refund_payload
+++ b/notifications/mail.py
@@ -22,1 +22,4 @@ def send_refund_email(order):          ← unit: notifications/mail.py::send_refund_email
```

Git's hunk headers name the enclosing function directly. A parser gives the same answer more
precisely, and is what handles languages whose hunk headers are unreliable.

**Why functions and not files or lines.** This is measured, not preferred — **and it was
superseded by a later measurement that this document now follows.** The argument below is about
which unit *localises a defect*; the decision that governs the product is about which unit *ranks
best at a three-unit budget*, and there file-level wins: **1.22% miss against function-level's
8.84%** on identical events, **+2.29 points** even at matched coverage, and the file arm is the
one that replicated out-of-sample on six unseen repositories. `rank/order.py` emits
`Site(path, line=0)`. **Both measurements are real and they answer different questions; the
second is the one the allocator obeys.** The bullets are kept because the symbol-level lift they
report is what makes the *routing sentence* name a function inside the ranked file:

- **Files are too coarse.** Of 1,316 follow-up fixes we examined, **989 touched only the same
  file at different lines** — that is continued development, not a repair. File-level signal
  measures *traffic*.
- **Lines are unusable.** Every later commit renumbers a file. With a median 26 hours between a
  change and its follow-up in an active repository, intervening edits are near-certain, so line
  ranges no longer line up.
- **Functions survive both.** `process_refund` is the same function at line 71 or line 340.

Measured across four repositories, ranking lift over a random pick: **symbol +46, +36, +28,
+17 points. File overlap erratic (+50 to −1). Line overlap dead (+7 to −5).**

### Step 2 — build the ranking index, bounded by the past — **BUILT**

For each changed unit, count the commits that touched it in the **year before this pull
request** — and nothing after:

```
  unit                                        prior-year touches
  refunds/service.py::process_refund                        34
  refunds/service.py::_build_refund_payload                  6
  notifications/mail.py::send_refund_email                   2
```

**The bound is not a date filter, it is an ancestry filter.** History is walked from the pull
request's parent commit, so nothing after the change can leak in. This is asserted rather than
assumed — `git merge-base --is-ancestor` is run per pull request — and a deliberate
future-leaking run must move the score, or the harness is measuring lookahead rather than
history. On our corpus, leaking the future moved the top-1 rate from 50.0% to 37.5%, confirming
the bound is load-bearing.

### Step 3 — decide whether to speak, using a percentile — **BUILT**

**An absolute threshold does not transfer between repositories.** "Twelve prior touches" is rare
in a slow repository and unremarkable in a fast one; the same rule fired on 11% of one
repository and 53% of another.

So the threshold is a **percentile of this repository's own distribution**. Fire when the
top-ranked unit sits in the top decile. Measured across repositories spanning an 80× range in
velocity, this holds the comment rate at **10–12% everywhere**.

Here `process_refund` at 34 touches is in this service's top decile. **We speak.**

### Step 4 — allocate the inference budget — **BUILT — labels only, nothing consumes them**

```
  process_refund            rank 1  →  deep read, xhigh effort, ONE pass
  _build_refund_payload     rank 2  →  shallow read
  send_refund_email         cold    →  no model call
  ceiling                           →  three requests. A limit, not a target.
```

The model would receive the ranked **file** and its immediate context, not the whole diff.

**One pass at rank 1, and the number matters more than it looks.** This read *multi-pass* until
the arithmetic was checked: at one pass allocation is 1.25× cheaper than reading everything, at
two it is 1.29× **more expensive**, so an unspecified pass count left the sign of the product's
cost argument blank. It is one, for reasons that are not about cost — reasoning is already on by
default at `xhigh`, so a second *request* re-pays the cache read to buy deliberation the first
request already performs internally; and a model-based triage pass would duplicate the ranker,
whose entire claim is that it needs no model. The ceiling is enforced and **observable**: each
review records its actual request count and token spend, because a ceiling never hit and a
ceiling never wired up otherwise print the same thing.

### Step 5 — read, with the repository cached — **NOT BUILT**

Prompt caching is a **prefix match**: the render order is tools, then system, then messages, and
any byte change invalidates everything after it. That maps onto this product exactly:

| Position | Content | Changes |
|---|---|---|
| Prefix — cached | repository conventions, resolved signatures, index summary | per repository |
| Suffix — uncached | this diff and the ranked file | per request |

Two rules the implementation cannot break, because both fail silently: **nothing volatile in the
prefix** (a timestamp there makes every request a cache miss with no error), and **tools and
model frozen for a conversation** (both render at the very front).

Findings come back as **structured JSON against a schema**, never prose — the verification step
can only check a claim it can parse.

### Step 6 — verify the model's structural claims — **NOT BUILT**

The model returns:

> *The partial-capture branch returns before the ledger entry is written. On a full refund the
> entry is written at line 88; on the new partial path the early return at line 71 skips it.*

The parser then checks the structural parts of that claim against the parsed code: do both
return paths exist, does the early return precede the write. **Confirmed claims are published.
Contradicted claims are dropped silently, before any human sees them.**

**What this can and cannot adjudicate, stated before a customer states it for us.** The verifier
is a parser. It decides claims a parser can decide — a symbol exists, a signature has that
arity, a return precedes a write, a reference resolves. **It cannot adjudicate a semantic
claim**: that logic is wrong, that an edge case is unhandled, that a lock is held. And semantic
defects are precisely why a model runs at all. So the verifier is structurally unable to check
the claim class the model exists to produce, and **a wrong semantic finding publishes.**

The honest claim is therefore *typed silence on structural claims*, not *verified findings*. It
is still a claim no competitor makes. It is narrower than it first sounds, and saying so
ourselves is worth more than being corrected.

A verifier that never rejects anything is not a verifier, so this ships with a sabotage test: a
deliberately false structural claim is injected and must be dropped. **That gate proves the
verifier can reject once, on the planted case — not that it still does.** So it ships alongside
a live drop-rate counter: claims received and claims dropped, by claim class, per review. A drop
rate that falls to zero and stays there is either a flawless model or a dead verifier, and those
two must never look the same on the wire.

### Step 7 — emit, with the coverage line first — **NOT BUILT as written — the coverage line ships, the finding does not**

```
QuantaMind

Checked      2 files · 3 functions · 38 call sites resolved
Could not    dynamic dispatch in handlers/registry.py — 1 file unresolved
Found        1 finding

  process_refund()  ·  refunds/service.py
  Read closely: changed 34 times this year, the most of the 3 functions here.

  The partial-capture branch returns before the ledger entry is written.
  On a full refund the entry is written at line 88; on the new partial
  path the early return at line 71 skips it.

  Verified against the parsed control flow — both return paths confirmed.
```

When nothing fires, the comment is the coverage line alone. When most of a change cannot be
analysed, it says so plainly and warns that absence of findings is absence of analysis, not a
clean bill of health.

## The corrected attribution rule underneath all of it

Everything above depends on knowing which later fix belongs to which earlier change. **The
standard rule used across the industry is file overlap: a fix touching a file the change touched
counts against it.** We measured that rule against symbol-level ground truth:

**36 of 53 verdicts — 67.9% — blamed a change that shares no symbol with the fix.** Reproduced
at 36.1% and 35.7% survival on two further corpora. **Roughly two thirds of what every AI-code
dashboard currently attributes is pointing at the wrong change.**

## Does the ranking track risk, or just activity?

This is the question the whole design rests on, and it was open until we labelled the outcome by
intent rather than by geometry.

Three hundred change pairs were labelled **blind** — the ranker's verdict withheld — by a model
from a different family, reading both changes, both diffs, and any pull-request discussion. It
classified each as a repair of the earlier change, continued work on the same feature, unrelated,
or unclear.

| | Hand labels, 60 pairs | Independent model, 300 pairs |
|---|---|---|
| Ranker named the symbol on **repairs** | 70% | **69%** |
| Ranker named it on **non-repairs** | 48% | **47%** |
| Difference | +22 points | **+22 points** |
| Fisher exact two-sided | p = 0.298 | **p = 0.0151** |

**Two raters — one with every incentive to find the effect, one with no stake — produced the
same effect size to within a point.** Agreement on the binary decision was 92%, Cohen's kappa
0.66, and the rater who wanted the effect was the *more liberal* one, so the stricter independent
rater should have shrunk it and did not.

**The ranking tracks repairs, not traffic.**

## What we measured and rejected

Ideas that looked good and are not in the product, because they failed:

| Idea | Result |
|---|---|
| Gate merges on static-analysis coverage | **Null** — relative risk 0.916; held changes broke at the same rate as passed ones, while firing on 45% of pull requests |
| "You forgot to change file X" from co-change history | **Dead** — fired on genuinely broken changes but named the right file **0 times out of 8** |
| Warn when a change touches a historically buggy file | **Null** — relative risk 1.56, p = 0.334, firing on 36% of clean changes |
| Flag changes that add no test | **Null**, and backwards — changes with no test broke slightly *less* |
| Ten pull-request metadata signals | **Nothing survived correction for multiple testing**; only diff size replicated, and every competitor already gates on it |
| Rank the top file, then the top function inside it | **Worse than an alphabetical null ranker** |

## Languages

Measured at file level, lift over each language's own null ranker:

| TypeScript | Java | Python | C++ | Go | JavaScript |
|---|---|---|---|---|---|
| +26.0 | +17.1 | +14.5 | +14.3 | +9.2 | +8.9 |

**Positive in all six, and Python is in the middle rather than at the top.** Function-level
extraction still needs a parser per language, and the non-Python samples are small.

## What it costs to run

Per pull request, at list prices, for a change touching six files with a 20,000-token
repository summary:

The budget funds rank 1 deep and ranks 2 and 3 shallow, so the worked example is **three
calls**, and every call pays its own cache read at one tenth.

| | Tokens | Cost |
|---|---|---|
| Deep call — prefix cache read | 20,000 at one tenth | $0.010 |
| Deep call — ranked file and neighbours | 3,000 | $0.015 |
| Deep call — output including reasoning, `xhigh` | 2,000 | $0.050 |
| Two shallow calls — prefix cache read, once each | 2 × 20,000 at one tenth | $0.020 |
| Two shallow calls — the function, low effort | 2 × 1,500 in | $0.015 |
| Two shallow calls — output | 2 × 600 out | $0.030 |
| **Total, three calls** | | **≈ $0.140** |

Reading the whole diff at uniform depth costs roughly **$0.175**, so this is a **1.25×** saving
— not the 2× an earlier single-call version of this table implied, and not the 1.5× the
two-call version implied.

**One thing could erase it, and one is settled.** ~~The allocator specifies rank 1 as
*multi-pass*~~ — **it does not, and step 4 above is the decision: ONE pass.** A second pass
re-sends the first pass's output as input and pays another cache read, roughly $0.085, taking the
total to **$0.225 — worse than reading everything**, which is precisely why the single pass was
chosen. This paragraph described the abandoned option as though it were current, two sections
after the section that abandoned it. What remains open is that
half of the remaining saving is the assumption that the model writes 2,000 output tokens
instead of 4,000, which is unsourced and pushed the wrong way by `xhigh`, since reasoning bills
as output. **Allocation is argued as an input-side saving; the arithmetic is currently carried
by an output ratio that may point the other way.**

**This whole table prices the CLOSED reviewer and is not what anyone pays.** At 200 pull requests
a month it would be **$28 of inference per repository** at the single pass the
allocator actually specifies. **Treat it as a derived ceiling rather than a floor** — and note
that a real run has since billed **$0.119 per pull request** against this table's $0.140, so the
derived figure is an over-estimate, not a boundary that has been tested from below. The
free tier runs no model at all and costs only compute — that part is structural, not an
estimate. **Every paid tier now carries two model calls per fired change, not one**: the reviewer
and the judge. The $0.119 figure above is the reviewer alone and is therefore a FLOOR for a tier
that verifies, which is every tier that publishes a finding.

## What is still unproven

**The full ledger is `docs/product/evidence-ledger.md`** — every measurement run, against the
claim it carries, and the rows where argument is currently covering for a gap. Its summary:
**the ranking rests on two datasets and the review was measured and failed its own
pre-registered bar** — 66.7% and 74.2% of findings wrong under two blind raters. The asymmetry
is structural: the ranker is model-free and could be checked against seven years of history,
while the review did not exist until a model ran. The paragraphs below are the sharpest cases;
the ledger is the list.

**Whether a reviewer shown the routing line before the defect exists catches anything they
would otherwise miss.** Every number above is retrospective. This is a field measurement, and
no amount of history substitutes for it.

**And a limit on what the outcome rule can support:** only **14%** of the change pairs it admits
are genuine repairs — the rest are continued work or coincidence. That caps the *firing*
precision of anything gated on the rule alone: fire on an admitted event and you are right about
it being a repair roughly one time in seven.

**It does not discount the ranking accuracy**, which is measured separately and conditionally:
given a genuine repair, the ranker names the repaired function **69%** of the time. Multiplying
85.3% by 0.14 yields the *joint* probability of naming the right unit **and** the event being a
real repair — a different quantity, and one that assumes the ranker performs equally on repairs
and non-repairs when it measurably does not.

---

# 4. The competition, and why they cannot simply copy this

> **THE SIX HERE ARE NOT THE SIX IN THE TABLE BELOW.** This list covers CodeRabbit, Graphite,
> Greptile, Bugbot, Qodo and CodeScene — chosen for what they *do*. The category table further
> down covers CodeRabbit, Greptile, Graphite, Macroscope, Qodo and Aikido — chosen for what their
> output *asserts*. Four overlap. Neither set is "the competition"; each answers a different
> question, and reading them as one list produces a competitor count that is wrong either way.

## What each of them actually does

**CodeRabbit** — the market leader. Raised $143M at a **$1.5B valuation on 12 August 2026**, and reports **over 2 million code reviews a week across 17,000 customers**, plus 150,000 open-source projects.
$24–48 per seat; enterprise from $15,000/month at 500+ seats. Its strength is presentation:
ten-section walkthroughs, sequence diagrams, grouped file tables, one-click fix, chat, an IDE
plugin. It **does** use history — its own engineering writing describes scanning commit history
for *"files that frequently change together"* to build a dependency map — but at **file**
granularity, as hidden background context for the model, never as an explicit finding.

**Graphite** — $52M raised. Primarily workflow, not review: stacked pull requests and a
merge queue, with an AI reviewer folded in. $20–40 per seat, unlimited AI reviews on the
team plan. Markets a low negative-comment rate, which it buys by commenting rarely.

**Greptile** — confidence 0–5 and P0/P1/P2 severities. Its `Failed` state means the run broke,
not that analysis was incomplete.

**Cursor Bugbot** — emits `success`, `neutral`, `failure`. Supports hand-written rules that can
express companion-change checks, but a human must write and maintain each one.

**Qodo** — severity-ranked findings, with a judge agent that filters low-confidence findings
before they reach the pull request.

**CodeScene** — file-level change coupling as an analysis dashboard, not a pull-request comment.
The underlying technique is old: mining version histories to guide software changes dates to
2004.

## What the category sells, and what we sell instead

Six tools, one sentence each, in their own framing:

| | what it sells | what its output asserts |
|---|---|---|
| **CodeRabbit** | line-by-line feedback with deep repository context | *this line is wrong* |
| **Greptile** | codebase-wide review with architectural awareness | *this change is wrong architecturally* |
| **Graphite** | stacked pull requests, workflow speed, AI review | *ship faster — also, this is wrong* |
| **Macroscope** | high-signal, low-noise automated review | *this is wrong, and we mean it* |
| **Qodo** | quality-first generation with test/review verification | *this is wrong, here is a test* |
| **Aikido** | developer-first application security guardrails | *this is insecure* |
| **QuantaMind** | **where to look, and what we could not see** | ***nothing about correctness*** |

**We measured the thing all six sell.** Two corpora, four blind rater pools: **66.7%, 74.2% and
82.1% of findings wrong, zero correct of 39 off-corpus, 0.013–0.037 correct findings per pull
request.** Nine designs; anchor repair, structured context, a rejection filter, hunk expansion and
a conventions file each moved the headline nothing.

**That is not a claim we are better at it.** On Martian's offline layer we are **level with
CodeRabbit and behind Greptile**. It is a claim about the category — and we are the only ones who
ran the experiment, published what it said, and then **built the judge the result demanded instead
of shipping the findings raw.** Every competitor above publishes its model's claims directly. Ours
do not reach a pull request unless a judge in a different model family confirms them, and what the
judge dropped is reported as a number.

**These figures are internal.** `docs/product/publishing-rules.md` governs the public form: our
own precision, recall and miss rate do not go on a page, and a competitor's ONLINE precision is
never a backdrop for one of our numbers. The offline-layer comparison above is permitted because we
entered that layer and it measures the same quantity — that exception is written into the rules,
not assumed here.

### Where this survives, and where it does not

**The ranker is not the moat.** Counting prior fixes per file is a couple of hundred lines; any
platform could ship it in a sprint. What cannot be retrofitted is **typed silence**: every layer
emits `Unresolved(site, reason, construct)` rather than nothing, so the coverage line is a
computation and not a claim. A tool that did not do that from its first row cannot state what it
missed, because it does not know.

**Distribution is where this is weakest, and it is not close.** There are no customers. The only
bottom-up motion available is the retrospective — it runs against a clone, needs no install and no
permissions, and shows what the ranking would have said on closed history. It is unbuilt.

**Noise is the strongest ground, and the rate is now measured on the unit we ship.** Six of seven repositories fire at **8–13%** on their most recent window; the largest, `angular/angular`, at 11%. **We do not quote a band to a customer** — the rate is computed from their own history before they install, which is a stronger thing to say than any fixed figure.
But Macroscope positions on low noise too, so the distinction is narrower than it sounds: theirs is
low-noise *claims*, ours is *no claims*.

**And the pitch this evidence forbids** is "an autonomous senior engineer". The best configuration
across nine designs produced **one useful comment per 27 to 77 pull requests**. Any strategy that
requires that capability is a strategy this project has already measured and failed. What is left
is smaller and duller: **be the layer that decides where attention goes and admits its blind
spots** — one replicated result at p < 1e-6 on six unseen repositories, one half closed on
evidence, and no customers yet.

## Differentiation

| | CodeRabbit | Graphite | Greptile | **QuantaMind** |
|---|---|---|---|---|
| Question it answers | Is this change **wrong**? | Is this change **slow to ship**? | Is this change **wrong**? | **Where in this change should a human look first** |
| Reads | whole diff + code graph, 40+ linters, microVM | whole diff | whole diff + semantic code graph, agentic multi-hop | **git history first, then the model on the top-ranked files only** |
| Uses history | files that change together, as hidden context | codebase-aware model | **yes — git history is a tool its v3 agent calls** | **fix history is the entire ranking** |
| Says what it could not analyse | **no** | **no** | **no** | **yes, on every pull request** |
| Publishes model claims about correctness | yes | yes | yes | **only what an isolated judge in a different model family confirmed** |
| Fires on | nearly every change | nearly every change | nearly every change | **8–13% on six of seven repositories, and computed on yours before you install** |
| Marginal cost per pull request | tokens, scaling with lines read | tokens | tokens | **tokens on 10–12% of changes, and only on the ranked files — the ranker is the budget** |
| Priced | per seat | per seat | per seat | **per repository** |
| Separates *undecidable* from *clean* | **no** | **no** | **no** | **a MODEL gate did, `p = 0.0007`, n = 29, never out-of-sample. The free rule inverted** |

**Three rows in this table were wrong until the benchmark run and are corrected above.** Greptile
was listed as not using history; its v3 agent calls git history as a tool. We were listed as
reading "the ranked function, deeply" and as publishing "parser-verified" claims; **`infer/` and
`verify/` are not built and not planned**, so we read nothing with a model and publish no claims at
all. A differentiation table that credits us with a capability we deleted is the drift this
project's publishing rules exist to catch.

**The last row is the newest axis, and it is the one the reviewer-half work bought.** A finding
whose truth depends on a fact the diff cannot supply — whether a commit hash exists, whether a tag
was released, what today's date is — is not a finding a diff-scoped reviewer can make. **We can
label those; nobody else does.** The label separates: findings the model itself called "decidable
from the diff" were **0 of 14 wrong**, against **9 of 15 wrong** for "needs a deeper look", Fisher
**p = 0.0007**. And the same principle, applied to file kinds rather than single findings, is what
explains the reviewer half's failure: **CI-config findings are 66.7% wrong and 23 of 24 of those
are undecidable by construction.**

**This is a differentiator precisely because it is not a better bug-finder.** Every rival ships the
claim that their findings are right. Ours is that we can tell you which of ours cannot be checked —
and that is the residual the customer is paying to see.

**The cost-driver row is a claim about *structure*, not a measured saving, and it must not be
read as one.** The arithmetic puts allocation at **1.25×** cheaper than uniform review at one
pass — and that figure is derived from a specification rather than observed on real diffs. It is
listed as unproven at the end of this document and gated in the build plan. **What is
structural, and does not depend on that number, is that the ranking stage runs without
inference at all.**

> **THIS ROW AND THE PRICING TABLE NOW AGREE, AND THEY DID NOT BEFORE.** The pricing table charged
> **$19–55 per developer per month** while this row claimed per-repository pricing as a
> differentiator. The row was right about where our costs sit; the table had not caught up.
>
> **The swing that made it urgent is gone with it.** The old arithmetic ran from 85% margin at 400
> pull requests a month to 26% at 2,000, because revenue tracked seats while cost tracked
> pull-request volume through inference. **The shipped product runs no inference**, so a
> repository that doubles its merge rate costs us the same `git log` it cost before. Revenue and
> cost now sit on the same axis.
>
> **Verified against the market:** no competitor prices per repository — CodeRabbit per developer,
> Greptile per seat plus per review, Qodo per user — because all of them pay per token. It is
> available to us precisely because we do not.

## We entered their benchmark. This is what came back.

**Every competitor comparison here was previously refused on the grounds that their precision is
behavioural — did a developer change the code — and ours was truth.** That was correct about the
public leaderboard and wrong as a permanent position. Martian's benchmark also has an **offline
layer**: 50 pull requests, five repositories, human-verified issue lists, an open judge and an
open pipeline. Both kinds of reviewer can be scored on it, so we ran ours through.

→ `docs/plans/preregistrations/reviewer/martian-comparison-preregistration.md`, bars fixed before the run.

| arm | precision | 95% CI | recall | F1 |
|---|---|---|---|---|
| greptile-v4-1 | **56.5%** | 48.8–63.9% | 52.6% | **54.5%** |
| coderabbit | 36.5% | 31.1–42.2% | **60.7%** | 45.6% |
| **QuantaMind** | **43.6%** | 36.6–50.9% | 45.7% | 44.6% |

**Read this the careful way.** We are **at level with CodeRabbit and behind Greptile.** The +7.2
points over CodeRabbit is **not significant** (Fisher p = 0.145); Greptile's +12.9 over us **is**
(p = 0.0228). And our arm was judged by its own model family — a blind out-of-family adjudication
put our over-match rate at 15.0% against the rivals' 5.0%, which at the point estimate would move
us to **37.1%**, level with CodeRabbit rather than above it.

**The number that mattered most was the one about the industry, not us.** The precision figures
the market quotes — Greptile 76.2%, CodeRabbit 49.2% — are from the **online** layer, which asks
whether a developer changed the code. On the offline layer, against human-verified issues,
**CodeRabbit is at 36.5%.** Our 65.2%-wrong figure had been compared against an assumed field
floor near 49% correct for months. **The real comparison was never as bad as we told ourselves.**

**And no tool of the 48 exceeds roughly 63% recall.** Nobody has solved this.

**On 48 against 49:** Martian's leaderboard lists **49 tools**; **48** of them carry the
evaluations this comparison is computed from, per
`docs/plans/preregistrations/reviewer/martian-comparison-preregistration.md` — "48 tools, 50 pull
requests, two judges". The leaderboard count is the one to use when naming Qodo's position; the
scored count is the one to use for any statement about what tools achieved. **They are two
denominators, not a disagreement.**

## The experiment that decided our configuration

The gap to Greptile is not architecture. **Two-thirds of it is Low-severity issues, and splitting
the golden set by whether our own prompt banned the category gives a −21% deficit rate inside the
ban against −2% outside.** So we removed the ban and re-ran.

| arm | comments | precision | recall | F1 | gap to Greptile |
|---|---|---|---|---|---|
| strict | 194 | 43.6% | 45.7% | 44.6% | −9 |
| **nits on** | **464** | **22.7%** | **57.8%** | **32.6%** | **+14** |

**The gap did not close, it reversed — our recall passed Greptile's.** And the price:

> **The 270 comments we added contained 21 real findings and 238 false ones. Marginal precision:
> 8.1%.** Noise per pull request went from 2.0 to 6.8, against Greptile's 1.4.

**Greptile leads this benchmark emitting one fifth of what that arm does.** They win on selection,
not volume — and their own published quality programme is a filter that deletes comments
resembling ones developers downvoted, taking their address rate from 19% to 55%.

> **Benchmark position and product quality are opposed on this gold set, and the exchange rate is
> 8.1%. Benchmark rank is therefore not a product target.**

→ `docs/product/greptile-gap-analysis.md`

## Should the product be a mandatory gate? The data says no — and it says why

**Checked against GitHub, not assumed.** Six merged pull requests from the design-nine corpus,
queried through the check-runs API:

| pull request | checks at merge |
|---|---|
| bokeh#15342, #15346, #15348 | green |
| **bokeh#15337** | **2 failures** |
| **bokeh#15353** | **1 failure** |
| **huggingface/datasets#8363** | **3 failures, 8 cancelled** |

**Half of them merged over a red build.** Branch protection overridden, a flaky job waved through,
an unrelated failure shipped anyway. **"Merged" is not a fact about correctness. It is an
assumption about how teams use GitHub, and it is wrong half the time.**

### What that implies about being a gate

**A team that overrides its own CI will override ours.** A blocking check on top of checks they
already bypass is not a safety mechanism; it is another thing to click through, and it converts the
product into the noise it was built to reduce.

**So gate on the measured thing and never on the unmeasured one:**

| gate on | evidence | verdict |
|---|---|---|
| **routing** — "this change lands in the top risk band; it needs a human read" | ranker, 1.53% against 2.97%, **p = 1.3 × 10⁻¹⁴**, 20 repositories | **defensible as a gate** |
| **correctness** — "this change contains a bug" | 30–35% of published findings wrong | **never a gate** |

**The first is a claim about where attention should go and it is measured. The second is a claim
about whether code is wrong and it is not.** Blocking a merge on the second would be selling a
certainty nobody in this industry has — QA teams exist and production still breaks.

### The four labels, and the one word that must not drift

| label | meaning | evidence |
|---|---|---|
| **"look here first"** | this file has needed fixes before | ranker, p = 1.3 × 10⁻¹⁴ |
| **"decidable from the diff"** | **nothing external is involved.** NOT "this is correct" | the gate |
| **"needs a deeper look"** | depends on a registry, a test run, or a file we were not shown | the gate |
| **"we did not read these"** | honest coverage | `CoverageLine` |

**The rejected findings are the product, not the waste.** A finding the gate drops is not "wrong",
it is **"we cannot verify this from what we saw"** — which is a true and useful thing to tell a
developer, and nobody else says it.

**"Decidable from the diff" must never become "settled by the diff".** A claim can involve nothing
external and still be false, because the model failed to trace its own input — measured directly:
on `bokeh#15337` both the test and the implementation it depended on were in the diff, and the
model still got it backwards. **Decidability is a statement about the input, never about the
answer.**

### The label separates, and this is the measurement

**Design ten's findings, split by the label the product would print. THE LABEL IS PRODUCED BY A
MODEL — `decidable.judge_one()`, one inference call per finding. It is not a rule and it is not
free.** The distinction is written here because it was lost once: the figure below was cited as
evidence that a *rule* separates, and the rule it was credited to inverted on the first corpus it
was tested against.

| label | n | WRONG | rate | 95% CI |
|---|---|---|---|---|
| **"decidable from the diff"** | 14 | **0** | **0.0%** | 0.0–21.5% |
| **"needs a deeper look"** | 15 | **9** | **60.0%** | 35.7–80.2% |

**Fisher exact p = 0.0007** — `research/phase0/quote/results/quote10_run.json` against
`adj10/verdicts.json`, the `decidable` field, which `run10.py` fills from the model.

**The free keyword approximation was measured separately and FAILED.** On design ten's own corpus it
also separates (kept 20 at 10.0% wrong against dropped 12 at 75.0%, Fisher p = 0.0003). On the
Martian corpus it **inverts**: 24 findings dropped, **14 false and 10 true, D/L 1.40 against a
chance value of 3.64** — discarding true findings faster than random deletion would. **The word list
learned design ten's corpus, not the property.**

**This is the only number from the review-half work that is about the PRODUCT rather than about a
benchmark.** Eleven designs chased a wrong-rate; what they produced instead is a label that sorts
findings into two piles a developer can act on differently.

**Three things it does NOT say.** The intervals are wide at n = 29. The rater graded WRONG using
reasoning correlated with the gate's rule, so the separation is partly structural. And nothing here
shows that acting on the label prevents anything — that is the pilot.

**What it does say:** we can print *"we cannot verify this from what we saw"* and have it mean
something measurable. **No competitor prints that sentence at all.**

### And the label is not calibrated yet

**We have the label. We do not have the calibration.** Saying "merge with confidence" requires
showing that when we say it, things do not break. The chain runs: we rank the risky file
(**measured**) → the reviewer reads it (**unmeasured**) → they find the defect (**unmeasured**) →
it never reaches production (**unmeasured**). **Only the first link has evidence.**

**That is thirty days with a real team, not another experiment.**

## Why they cannot kill this in one update

**Start with what they can copy, because the argument is worthless without it.**

| What | How long it takes a funded competitor |
|---|---|
| Rank changed files by prior-year commit count | **A week.** It is `git log` counted and sorted |
| Move that ranking from files to functions | **Two weeks.** Hunk headers or a parser |
| Spend more model budget on the top-ranked unit | **A month.** It is a prompt-assembly change |
| Emit a coverage line saying what it could not analyse | **Two to three months, and it makes their headline number worse** |
| Credibly publish their own miss rate | **Never** |
| Give away a six-month retrospective to every prospect | **Never at their cost structure** |

**The first three are not a moat and we should never claim they are.** If the product is only
the ranking, a competitor ships it in a month and we are finished. The bottom three are the
business.

### One: an LLM reviewer does not know what it failed to read

This is the argument that matters, and it is architectural rather than a matter of will.

Their pipeline is: index the repository, retrieve context, prompt a model, post what comes back.
**Nowhere in that pipeline is a step that produces a coverage number**, because a model does not
report what it failed to resolve — it produces text either way. Ask it what it missed and you
get a plausible sentence, not a measurement.

To emit *"41 of 43 call sites resolved; 2 unresolved, dynamic dispatch in `registry.py`"* you
need a parser that enumerates the call sites in a diff, a resolver that attempts each one, and a
typed record of every failure. **That is a different layer of software from a retrieval-plus-prompt
pipeline**, and it is the layer this project spent six weeks building before writing a line of
product code.

So the honest form of the claim is not *"they won't ship typed silence because of marketing."*
Marketing positions reverse in a quarter. It is: **they cannot ship it without building a
resolution layer they do not have, and when they do, the first thing it will tell their
customers is how much of each diff their reviewer never actually understood.** That is a
capability they must build in order to publish a number that damages them.

**Verified, not assumed: none of seven shipping reviewers can express it today**, and one
documents in its own manual that it emits no `skipped` conclusion.

### Two: the auditor cannot be the vendor — and this one is permanent

A reviewer cannot credibly report its own miss rate. Not because it would refuse to, but
because **no buyer would believe the number**, in the same way no company audits its own books.
Bond ratings, financial audit and clinical trials all separate the measurer from the measured
for this reason, and no amount of engineering closes it.

Concretely, we can say a sentence they can never say:

> *"Of the changes in your repository that came back with a fix this quarter, your reviewer
> commented on this many. Here are the ones nobody caught."*

Every dashboard a buyer has today attributes rework using a **file-overlap rule that is wrong on
67.9% of its verdicts** — measured here, reproduced three times. **Being the party that owns a
correct denominator, while selling no reviewer of your own, is a position, not a feature.**
Positions do not get shipped in an update.

### Three: they cannot give away the proof, because it costs them what it saves us

The single strongest sales act in this product is replaying a prospect's last six months and
showing **where we would have pointed** — before they commit to anything.

**Stated precisely, because the distinction is the whole argument:** a model-free replay can show
which changes came back, how often we would have spoken, and whether we named the function the
fix returned to. It **cannot** show what a reviewer would have *found*, because finding requires
inference over historical diffs — and that costs us exactly what it costs them.

**For a model-per-diff reviewer, doing that costs a full inference pass over every historical
pull request.** A thousand pull requests is a thousand reviews of compute spend, per prospect,
before a dollar of revenue — so they can demo on a toy repository and we can demo on the
customer's actual history. Our deterministic pass costs CPU.

The same asymmetry runs through the product: their cost of goods scales with lines read, ours
does not. **That is why our free tier can be genuinely free and theirs cannot**, and price is a
real weapon against two venture-funded companies carrying token bills.

### Four: the data position compounds, and only we can collect it

Every install yields four things joined together: the repository's history, **the corrected
attribution of which change actually caused which fix**, what the customer's existing reviewer
said about each change, and what came back anyway.

**That is a labelled dataset of which review findings mattered, across many organisations, and
nobody else is accumulating it** — not because it is secret, but because collecting it requires
the corrected outcome rule, and building that means first publishing that the industry-standard
rule is broken. A vendor whose own dashboards use the broken rule is poorly placed to lead with
that.

It compounds in the ordinary way: more repositories, better thresholds, better calibration per
service type, and eventually a defensible per-language answer to *"where does review time
actually pay."*

### Five: per-seat pricing forces volume, and volume is now priced at 8.1%

**This is the one the benchmark measured, and it is a business-model constraint rather than an
engineering one.**

A reviewer sold **per seat** has to look present. A developer paying monthly for a bot that stays
quiet on two changes in three cancels it, so the incumbent's incentive is to comment — and every
one of them fires on nearly every change. **We measured what that costs on their own benchmark by
doing it ourselves:** removing one sentence of suppression took us from 194 comments to 464, and
**the 270 we added contained 21 real findings and 238 false ones.**

**Marginal precision of visible presence: 8.1%.**

They know it. Greptile's published quality programme is a vector filter that blocks a comment
resembling three previously downvoted ones — **built specifically to delete the comments per-seat
economics push them to emit**, and worth going from a 19% to a 55% address rate. **CodeRabbit ships
288 comments across 50 pull requests where Greptile ships 161 and scores 20 points higher.**

**Priced per repository, silence costs us nothing.** Firing on 10–12% of changes is a feature of
the invoice rather than a threat to it. **That inversion is not something a competitor ships in an
update; it is something they change by repricing, which breaks the model their revenue is built
on.**

### Where we are genuinely exposed, stated plainly

- **The ranking is not defensible.** A week of work for anyone who reads this description.
- **Greptile is better at review than we are, and it is significant.** 56.5% precision against our
  43.6%, p = 0.0228, on a benchmark we chose to enter. If what the market wants is a reviewer, we
  lose that contest on the evidence.
- **CodeRabbit already scans co-change history**, and **Greptile's agent calls git history as a
  tool.** The signal we rank on is already inside both products; what differs is what they do with
  it. Surfacing it as an ordering is incremental for them, not a rebuild.
- **They have 17,000 customers and we have none.** Distribution beats mechanism, and it beats it
  quickly.
- **Our visible surface is a tenth of theirs.** Next to walkthroughs, diagrams and one-click
  fixes, a coverage line looks thin until somebody measures the noise.
- **We are not better at finding bugs, and we no longer try.** `infer/` is not built. Nothing
  measured here says we would win that contest, and claiming it in a room would be false.

**The honest position: better on noise, honesty, targeting and cost — not better at bug-finding,
and no longer competing on it.** The moat is not the ranking. **It is that the incumbents cannot
measure themselves, cannot afford to prove value on a prospect's own history, cannot report
coverage without building a layer whose output embarrasses them, and cannot go quiet without
breaking the per-seat model they are priced on.**

## The investor question: "if you are not better at finding bugs, why should we invest?"

The answer, in the order it should be given.

### "You're right. We're not. Neither is anyone else — and now we have run their benchmark to prove it."

**We entered Martian's offline layer rather than asserting this.** Against human-verified issues on
50 pull requests, scored by one judge: **Greptile 56.5%, us 43.6%, CodeRabbit 36.5%.** We are level
with CodeRabbit and behind Greptile, and **no tool of the 48 scored exceeds roughly 63% recall**
(48 scored of the 49 listed — see the note above).

**The 49–76% band the market quotes is the ONLINE layer** — did a developer change the code — and
it is a different measurement on a different population. The same CodeRabbit that reports 49.2%
there is at **36.5%** against verified issues. **The field is materially worse than its own
marketing, and the benchmark's authors say their gold set is incomplete on top of that.**

An earlier measurement of the market leader against real breakages **is withdrawn** — its Wilson
interval spans the comparison figure, so it distinguishes nothing. See the withdrawal near the top
of this document. **The benchmark run replaces it, and it was pre-registered.**

### The bottleneck was never detection. It is attention.

Agents write most pull requests now. A team that opened twenty a week opens sixty. The two
senior engineers reading them did not become six. Then the review tools arrived and put a wall
of comments on every one, a third of it noise. Review did not get faster — it stopped happening.
**The largest single reason AI pull requests are rejected is inactivity: 17.3%**, auto-closed
because nobody got to them.

Every incumbent answers that flood by generating more text into it. **We are the only entrant
whose goal is to say less** — one change in ten — and to be right about the one thing it says.
It is: the function we point at is the one the fix returns to, **22 points above its rate on
everything else, replicated by an independent rater with no stake in the result**.

### The company is not the reviewer. It is the measurement layer.

Every buyer of AI coding tools now has a board question they cannot answer: *is the code our
agents write getting worse?* They cannot answer it because every dashboard they own attributes
rework with a rule that is **wrong on 67.9% of its verdicts** — measured here, reproduced three
times on separate corpora.

We corrected that rule, and we sell no reviewer of our own, so we are the only party who can
answer the question and be believed. **The auditor cannot be the vendor.** No incumbent can
credibly publish its own miss rate, for the same reason no company audits its own books.

### Three properties that make it fundable rather than merely true

- **Cost structure inverted.** Their marginal cost scales with lines read; ours is compute. So
  we can prove value on a prospect's own history — replay their last six months and show **where
  we would have pointed.** Not what we would have caught: the replay runs the ranking, which is
  deterministic, and it produces no findings at all. **That costs a model-per-diff reviewer a full inference pass per historical
  pull request. It costs us CPU.** They demo on a toy repository; we demo on the customer's
  actual code.
- **Quiet enough to survive developers.** Firing on 10% of changes is an adoption strategy, not
  a limitation. Noisy tools get muted in week three.
- **Falsifiable next month for the price of a pilot**, not a round.

### The risk, handed over before they find it

> *"The routing feature on its own is a feature, not a company — it is a shell one-liner plus
> packaging, and a competitor ships it in a month. This is a company only if the measurement
> position holds: if engineering leaders will pay an independent party to tell them whether
> their AI tooling works. **That demand is unproven.** It is the biggest risk in this plan, and
> five conversations answer it faster than five months of building."*

An investor who finds that objection unaided discounts everything said before it. An investor
handed it starts weighing the actual bet.

### If there is time for only one sentence

**"We are not selling better bug-finding — that is capped and commoditised. We are selling the
only trustworthy answer to 'is this working', in a market where every existing answer is two
thirds wrong."**

---

## What we charge, and why the tiers split where they do

> **PRICING STAYS PER REPOSITORY, AND THE REASON HAS CHANGED.** An earlier draft priced per
> repository because the shipped product ran no inference and its only cost was a clone and an
> index. **Inference is part of the product**, so tokens are a real cost again — but a BOUNDED
> one, and that is the argument: the ranker fires on **10–12%** of changes and the allocation
> budget caps the read to three files, so the bill tracks the repository's history rather than its
> headcount. **Per-seat pricing stays rejected**, because a seat consumes nothing here — a
> repository does.

**What the shipped product actually costs is a clone and an index, per repository.** Measured:
`pallets/flask` is **15 MB of history and a 393 KB index** holding 4,281 touches. A run is one
`git log` and a handful of SQLite queries — CPU seconds, no network, no tokens. **Cost scales
with the number of repositories and the size of their history. It does not scale with pull-request
volume, team size, or lines read.**

**So the price is per repository, and the differentiation table is now telling the truth.** It
claimed per-repository pricing as a differentiator against per-seat incumbents while the pricing
table charged per developer; the claim was right about where our costs sit and the table had not
caught up.

**Verified against the market, August 2026:** CodeRabbit is about **$24 per developer per month**
annually, Greptile **$30 per seat with 50 reviews included** and per-review charges beyond it,
Qodo **$30 per user** (Qodo Merge free self-hosted, or $19 per seat). **None of them price per
repository**, because all of them pay per token and tokens track reviews. We do not, so we can
price the axis our costs actually sit on — and it is the axis a customer can predict, because
they know how many repositories they have and cannot know how many pull requests next quarter
brings.

**This is a smaller number than a per-seat line would produce, and that is correct.** Twenty
developers on four repositories pay four repository fees, not twenty seats. We ship a ranker and
a coverage line, not a reviewer; charging reviewer prices for it would be the overclaim this whole
document exists to avoid.

| | **Free** | **Team** | **Business** | **Enterprise** |
|---|---|---|---|---|
| Price | $0 | **$12**/repo/mo annual · $15 monthly | **$10**/repo/mo annual, **10 repo minimum** | from **$2.5K**/mo, unlimited repositories |
| | | | *At exactly 10 repositories Business is $100 against Team's $120 for a superset — Team is dominated from 10 up, deliberately. The minimum is the crossover, and it is set where pooling starts being worth buying.* | |
| **Priced on** | — | **repository** | **repository** | contract |
| Seats | unlimited | **unlimited** | **unlimited** | unlimited |
| Buyer | anyone | team lead | Director or VP Engineering | procurement and security |
| What is being bought | the proof | **the routing** | **the org-wide report** | the contract |
| Bought with | nothing | credit card | light purchase order | MSA, DPA, security review |
| Ranking, coverage line, retrospective | ✓ | ✓ | ✓ | ✓ |
| **Coverage line names every skipped unit** | ✓ | ✓ | ✓ | ✓ |
| **Model findings in the pull request** | — | ✓ | ✓ | ✓ | 
| **Review depth** | 3 files | 3 files | **5 files** | 5 files + org policy | 
| **Pooled retrospective across repositories** | single repo | single repo | **✓ org-wide** | ✓ org-wide |
| Cross-repository aggregation, quarterly audit, SSO | — | — | ✓ | ✓ |
| Verifier drop-rate telemetry | — | — | ✓ | ✓ |
| **Bring your own key** / **Bring your own model** | — | — | — | **✓** — the reviewer runs on Gemini by default and Enterprise may supply its own key. **The judge stays ours and stays a different family from the reviewer**: a customer pointing both halves at one model would remove the mechanism they are paying for |
| Self-hosting, audit logs, residency, SLA | — | — | — | ✓ |
| **Token budget** | capped, free tier | capped | higher cap | **org-wide pooled cap** |
| **Our cost of goods** | storage + CPU | **a clone and an index per repository** — 15 MB and 393 KB for flask — **plus tokens on the 10–12% of changes that fire**, twice: once to read, once to judge |||

> **REVIEW DEPTH IS THE TIER LEVER AGAIN, AND THE MEASUREMENT BEHIND IT IS NARROWER THAN THE ROW
> SUGGESTS.** Three units against five is measured — 8.84% against 3.50%, paired, McNemar
> p < 0.0001 — but both are **function-level** figures, and allocation ships at **file** level.
> The direction holds; those magnitudes do not transfer to the shipped unit and must not be quoted
> as if they did. **Depth multiplies the judge's bill as well as the reviewer's** — every extra
> file read is a file to adjudicate.

**The lever that survives is POOLING, and it is the one a customer actually hits.** A single
repository rarely reaches the pre-registered floors — measured on repositories nobody had seen,
`requests` gave 551 events, `fastapi` 257 and `click` 414, all three INCONCLUSIVE against floors
of 500 events and 20 discordant pairs. Pooled across the three: 1,222 events, p < 1e-5,
**+14.79 points against chance** on the informative stratum, 3 of 3 positive. **The org-wide
answer is the one that exists, and a single repository often cannot be given one.**

That is an honest upsell because the constraint is arithmetic rather than artificial: we are not
withholding a number at the lower tier, the lower tier's data cannot support one.

~~**And the margin improves at the deeper tier**~~ — **that arithmetic priced per-seat revenue
against per-unit inference cost, and both are retired.** Depth is not a tier lever, the row is
struck through above, and there is no per-unit cost to improve on. What replaces it is simpler:
**four repositories cost four clones and four indexes whichever tier they sit on**, so the margin
difference between tiers is entirely the price.

**Which means the margin is WORSE at Business, not better** — $10 per repository against Team's
$12, on identical cost. That is ordinary volume pricing and it is the opposite of what the retired
paragraph claimed, so it is said here rather than left for someone to derive: **the higher tier
buys pooling and an org-wide report at a lower unit price, and we take a thinner margin per
repository to get more of them.**

**The quarterly coverage audit is a separate line, $8,000–15,000 per engagement**, sold to an
engineering leader out of a different budget than seats. It is plausibly the larger business.

**SEATS ARE UNLIMITED AT EVERY TIER, INCLUDING FREE, AND THAT IS NOT GENEROSITY.** A seat costs
us nothing: the ranking is computed once per repository and read by everyone. Charging per seat
would mean charging for a resource we do not consume, and it is the reason every competitor's
price rises when a team grows while their cost does not.

**The margin no longer swings with volume, because the thing that swung it is gone.** The old
arithmetic went from 85% at 400 pull requests a month to 26% at 2,000 — driven entirely by
per-pull-request inference. A repository that doubles its merge rate now costs us the same
`git log` it cost before. **Revenue and cost sit on the same axis for the first time.**

**The tiers split by who signs, not by how much you get.** Team is a credit card and a team
lead buying routing for their repositories. Business is a light purchase order and a director buying an org-wide
report — which is why SSO becomes mandatory there and not before. Enterprise is procurement
buying a contract: it runs where legal permits, with a number we will defend to their auditor.
**A tier whose only distinction is a bigger quota is anchoring, not a tier.**

> **SELLABLE, AND WITH ONE LIMIT THAT IS NOT NEGOTIABLE.** A customer may bring a key or a model
> for the REVIEWER. **The judge stays ours and stays a different family from whatever the reviewer
> runs.** A customer who pointed both halves at one model would delete the mechanism this product
> sells: a same-family judge agreed with a careful rater on 34.9% of findings and certified the
> reviewer's own invented facts. That is a support burden and a correctness claim we cannot make on
> their behalf, so it is a product limit rather than a preference.

**Bring your own *key* at Business; bring your own *model* at Enterprise.** The line would be
one sentence — *we have certified that model, or we have not.* An allowlisted model costs us nothing
because the evaluation is already amortised across every customer. An uncertified model means
publishing a coverage number under our name for a configuration we never measured, which is the
one failure this product cannot survive, so it requires a per-model evaluation run and therefore
a contract. **Neither reduces the repository price**, and both are moot until `infer/` ships: there is no
model call to bring a key for. They are kept here as the shape the Enterprise tier would take if
the reviewer ever reopened, and bring-your-own-key would be bought for compliance rather than
cost even then.

**~~Where this is fragile~~ — the fragility was a property of the reviewer, and it left with it.**
The arithmetic here ran from **85% gross margin** at 400 pull requests a month to **26%** at
2,000, on twenty developers and four repositories. Every dollar of that swing was inference:
revenue tracked seats, cost tracked pull requests. **The shipped product runs no inference**, so
the same four repositories cost the same whether they merge 400 changes a month or 2,000, and the
price is now charged on repositories too.

**What is fragile instead, and it is a different shape.** Cost tracks repository SIZE — a clone
and an index. `pallets/flask` is 15 MB and a 393 KB index; a monorepo with fifteen years of
history is not, and a per-repository price flat across both is a per-repository price that loses
money on the largest customer. **That is the number to re-derive in the first week of real
traffic**, and it is a storage question rather than a token one.

**And the old ceiling should not be quoted at all.** "$28 per repository" was derived from a
specification for three model requests that no longer run. It is not a floor, a ceiling, or a
measurement of anything we ship.

# 5. Slack and Datadog

**We integrate with both. We rebuild neither.**

## Datadog — consumed as an instrument, not reimplemented

Datadog's Error Tracking already ships suspect commits, on four criteria stated in its own
documentation: the commit *"modifies one of the lines in the stack trace"*, was *"authored
before the first error occurrence"*, *"no more than 90 days before"*, and is *"the most recent
commit that meets the above criteria."* It also creates tickets from the issue panel and
supports rules that open tickets automatically when issues match. Sentry ships an equivalent.

**So incident-to-commit is a configuration, not a build. We consume the webhook.**

What no vendor supplies is a **defensible denominator**. Their attribution — and every dashboard
built on it — uses the file-overlap rule that is wrong on 67.9% of its verdicts. Our corrected
rule turns their incident feed into a post-merge defect rate you can actually act on, which is
one half of the widening gate described earlier.

**What we deliberately do not build:** a per-incident blame ticket naming an author or an agent.
It is an occupied position, it adds nothing at three in the morning when the engineer wants the
fix, and tools that generate blame artefacts get disabled within a quarter.

Two things Datadog's documentation does **not** claim, so we should not either: automatic
pull-request linking and auto-assignment. Commit-to-pull-request is a GitHub API lookup — a thin
gap, not a moat.

## Slack — one weekly digest, no alert stream

Not an alert per finding. **One short message a week to the team channel**, naming the few
functions where rework concentrates:

```
Where this service reworks itself, this week

  process_refund()    7 follow-up fixes in 9 changes
  apply_promotion()   5 in 8
  sync_ledger()       4 in 11

  These three account for a third of the follow-up fixes here.
  They are where human review is worth the most.
```

The index that drives the comments also tells a lead where to spend the review attention they
have. Not *"your code is bad"* — *"these functions have cost you the most rework, and here are
the commits."*

**And an anti-requirement:** no per-pull-request Slack alerts. A tool that pings a channel on
every change is muted in week three, and the whole design is built on firing rarely.

---

# 6. The evidence, in full

Everything this project measured, including what failed. A reader who only wants the conclusion
can stop at the previous section; this exists so the conclusions can be checked.

## 6.1 The corrected attribution rule

**The problem.** To know whether any review signal works, you need to know which later fix
belongs to which earlier change. The industry-standard rule is **file overlap**: a fix touching
a file the change touched counts against it.

**The measurement.** 53 breakage verdicts were re-derived at symbol level. **36 of 53 — 67.9% —
blamed a change sharing no symbol with the fix.** Broken out: 65.6% on one arm, 71.4% on the
other. Survival under correction: **32.1%**, reproduced at **36.1%** and **35.7%** on two further
corpora.

**Why it matters.** Every AI-code-quality dashboard a buyer reads today runs on this rule, so
roughly two thirds of what it attributes points at the wrong change.

## 6.2 What the ranking is measured against

Three candidate outcome rules, run on **one population per repository** so they cannot be
confounded. "Lift" is precision at a 10% firing rate minus the precision a random pick of the
same changed units would achieve.

| Repository | Units | file lift | **symbol lift** | line lift |
|---|---|---|---|---|
| Skyvern | 1,022 | +50 | **+46** | +7 |
| browser-use | 186 | +20 | **+36** | −4 |
| cartography | 251 | +1 | **+28** | −5 |
| opendbc | 17 | −1 | **+17** | +0 |

Base rates tell the same story more plainly. Under the file rule: **90%, 83%, 44%, 33%** —
implausible as defect rates. Under the symbol rule: **62%, 42%, 27%, 29%**.

**Files measure traffic.** Of 1,316 follow-up fixes examined directly, **989 touched only the
same file at different lines** and 327 touched the modified lines — those two are exhaustive and
sum to 1,316. Separately, **105 of the 1,316 were explicit reverts**; that is an overlapping
count, not a third category.

**Lines are unusable.** Every later commit renumbers a file; with a median 26 hours to the
follow-up, intervening edits are near-certain. The rule under-counts real repairs by an
unmeasured amount.

**Symbols survive both.** A function keeps its identity when line numbers move.

## 6.3 The ranking itself

**File level:** top-1 accuracy **85.3%** against a **72.0%** alphabetical null ranker and a
67.5% random baseline — **4,293 events across 17 repositories, positive in 17 of 17.** Sign test
on direction, p ≈ 1.5 × 10⁻⁵.

**Top-3, which is the number the budget actually depends on.** Top-1 answers *is the spend well
aimed*; it does not answer *does allocation lose defects*. The budget funds ranks 1–3 and gives
cold units no call at all, so a defect in a cold unit yields no finding and no error — silence
indistinguishable from a clean review. Measured on the same corpus, stratified, because for a
change touching three files or fewer "in the top 3" is **true by construction**:

| Changed files | n | Top-1 | **Top-3** | Alphabetical null, top-3 | Random top-3 | **Cold miss** |
|---|---|---|---|---|---|---|
| **Four or more** — the informative stratum | 2,893 | 80.5% | **95.4%** | 89.4% | 89.0% | **4.6%** |
| Three or fewer — 100% by construction | 4,600 | 89.8% | 100% | 100% | 100% | 0% |
| Pooled | 7,493 | 86.2% | 98.2% | 95.9% | 95.7% | 1.8% |

**25 repositories, every exclusion printed with its reason and no failed read** — the harness
refuses to publish a table at all if a history read did not complete, which is how the airflow
defect recorded further below was caught rather than absorbed.

**This run ranks FILES, and so does the allocator, so it validates exactly the policy we operate.**
The harness reads history with `--name-only`, every unit above is a file, and `rank/order.py`
emits `Site(path, line=0)` — the zero says the unit is the whole file. The file-level table
therefore describes the shipped policy, and it is the arm that replicated out-of-sample on six
unseen repositories. The nested strategy — top file, then top function inside it — scored
**54.2%, below its own 61.0% null** in the table further up this section, which is part of why
functions were not chosen.

**The operational number is the pooled row, not the ≥4 row** — and this is the ONE operational
number, now that the function-level arm is documented as the road not taken rather than as "the
number the product has". Production sees every change, and
61.4% of them touch three files or fewer where a three-unit budget is not binding. So the figure
that describes the policy's cost is the pooled one:

| | n | misses | rate | 95% CI (Wilson) |
|---|---|---|---|---|
| Four or more files | 2,893 | 133 | 4.60% | 3.89% – 5.42% |
| Three or fewer | 4,600 | 0 | 0% | 0% – 0.08% |
| **Pooled** | **7,493** | **133** | **1.77%** | **1.50% – 2.10%** |

At 200 pull requests a month that is **3.5 changes, and between 3.0 and 4.2**, where the defect
unit would receive no model call and produce no error.

> **This paragraph and the subsection below it were written when the plan was to allocate over
> functions.** They said the run "does not validate the allocation policy" and that the
> function-level figure was "unmeasured" — the second contradicted by the subsection immediately
> below, which is titled *measured* and is.

## The function-level figure, measured — this is the arm we did NOT ship

**The table above ranks FILES, and so does the allocator.** This figure is kept because it is the
measurement that decided the unit, not because it describes the product: paired on identical
events across the 8 clones with complete objects, function-level loses to file-level by enough
that the choice was not close.

| arm | top-3 miss | 95% CI |
|---|---|---|
| file-level | 24/1,969 = 1.22% | 0.82–1.81% |
| **function-level, three-unit budget** | **174/1,969 = 8.84%** | **7.66–10.17%** |
| function-level, five-unit budget | 69/1,969 = 3.50% | 2.78–4.41% |

**At 200 pull requests a month, 8.84% is roughly eighteen changes where the defect sits in a unit
that received no model call.** That is the honest cost of allocation, and it is far above the
1.77% the file-level analogue suggested.

**Most of the apparent gap was the budget, not the unit.** Three functions is not three files —
with 1.64 functions per file, three functions covers about half what three files does. At
**matched coverage** (top-3 files against top-5 functions, 3.05 file-equivalents) the gap is
**+2.29 points**, not +7.62. McNemar exact p < 0.0001 on both.

**So two earlier measurements that looked contradictory both hold.** Function *ordering* is
better — 75.0% top-1 against 58.9% for any-function-in-the-top-file. Function *allocation at
equal budget* is slightly worse. **Granularity costs about two points; the rest was the smaller
net.**

**Every figure here is an upper bound.** Three biases push the same way and none is corrected:
the 8 clones are a convenience sample carrying larger changes than the other 17; git credits a
hunk between two functions to the nearest preceding one; and 14.6% of hunks yield no function at
all. Each puts a defect's true function outside the index, inflating the function arm alone. **So
"at most 8.84%", not "8.84%".**

**And the budget stays at three.** Five units would halve the miss for about +$13 per repository
per month — defensible, and unnecessary, because **naming the cold units in the coverage line
removes what makes a cold miss expensive.** The cost is not the miss; it is that nobody knew.

**Two claims about this were made before it was measured, and both were wrong.** They are kept
because the pattern is instructive.

**The first said 1.77% was a floor** — reasoning from partition fineness alone: functions are a
finer partition, so a three-unit budget covers less and the miss rate should rise. Real effect,
and it turned out to dominate — but the reasoning ignored the second term, better aim, which
pulls the other way. **Asserting a net from one of two opposing terms is the error, even when the
sign happens to come out right.**

**The second said the direction was unknown.** Correct at the time and superseded by the
measurement above: function-level loses, by about 2.3 points at matched coverage.

**The lesson kept from both:** the file figure was never a floor *or* an unknown. It was a
different arm, and only a paired run on identical events could say how the two related.

**And a same-number result would be a warning, not a confirmation.** If a symbol-level re-run
returns 1.77% again, the likeliest explanation is that the extraction did not actually change
units — this harness has already once read truncated history as complete. That run asserts the
git exit code and reports the unit count so a reader can see the partition got finer.

**61.4% of events sit in the vacuous stratum**, where a three-unit budget is not binding — so a
pooled top-3 of 98.2% is mostly arithmetic and the four-or-more row is the real answer. Read off
it: the top-3 lift over the null is **+6.0 points, not the +13.3 that top-1 earns**, because
top-3 is a much easier task and the null already sits at 89.4%.

**The trade is now statable in one line: allocation buys 1.25× on cost and pays 1.8% of
fix-localisable defects in silence.** If the pass count had stayed unspecified and landed at
two, it would have paid that 1.8% *and* cost more than reading everything.

**An unplanned replication, and the reason to distrust the first two attempts at it.** This run
returns top-1 of **86.2%** against the documented 85.3%, on 7,493 events across 25 repositories.
Overlapping data, so not an independent replication. It is quoted from the third run because the
first two were measured on **19 and 22 repositories** without saying so — the harness silently
dropped repositories whose history read failed, and only a skip ledger made the population
visible. The three runs returned top-3 of 95.3%, 95.8% and 95.4% on the informative stratum, so
the finding was stable throughout; **the population was not, and nothing in the output said so.**

**A note on counts, because two figures here look contradictory and are not.** This run and the
language run further below are separate passes over different repository sets — the language pass
ran later, after more repositories had been cloned, which is why its Python arm alone reports
5,242 events against this run's 4,293 total. Same method, different populations; neither is a
subset of the other.

**Rank globally, never hierarchically.** Ranking the top file and then the top function inside
it performs *below* the null ranker:

| Strategy | Top-1, 236 events |
|---|---|
| **Rank all changed functions globally** | **75.0%** |
| Alphabetical null ranker | 61.0% |
| Any function in the top-ranked file | 58.9% |
| Top file, then top function inside it | 54.2% |

The highest-history file is usually not where the highest-history function lives, so filtering
by file first discards better candidates elsewhere in the diff.

**Thresholds must be percentiles, not constants.** This is the finding, and the contrast is
where it lives: **"twelve prior touches" fired on 11% of one repository and 53% of another** —
the same rule, an order of magnitude apart in volume, which is what makes an absolute threshold
unusable across a customer base.

A top-decile threshold then fires at **10–12%** everywhere. **That number is close to definitional
and should not be presented as a discovery** — a top-decile rule selects a tenth of units by
construction, and landing at 10–12% of *pull requests* rather than units is a mild fact about
pull-request size distributions. The evidence is the 11%-versus-53% contrast, not the constancy.

## 6.4 Does the ranking track risk, or activity?

The question everything else depended on. Answered by labelling the outcome by **intent** rather
than geometry: 300 change pairs labelled **blind**, ranker verdict withheld and order shuffled by
content hash, by a model from a **different family** with no stake in the result.

| | Hand labels, 60 pairs | Independent model, 300 pairs |
|---|---|---|
| Ranker named the symbol on **repairs** | 70% (7/10) | **69% (27/39)** |
| Ranker named it on **non-repairs** | 48% (21/44) | **47% (117/247)** |
| Difference | +22 points | **+22 points** |
| Fisher exact two-sided | p = 0.298 | **p = 0.0151** |
| 95% confidence interval | — | **+6.1 to +37.6 points** |

**The interval matters more than the point estimate.** The effect rests on 39 genuine repairs,
so the honest claim is *"+22 points, 95% CI +6 to +38"*. A six-point product is a materially
different product from a thirty-eight-point one, and this document's own standard is to quote
the range rather than the midpoint.

**Two raters — one with every incentive to find the effect, one with none — produced the same
effect size to within a point.** Agreement on the binary decision: **92%, Cohen's kappa 0.66**.
The biased rater was the *more liberal* one (17% repairs against 12%), so the stricter
independent rater should have shrunk the effect and did not.

**And the correction this forces on every other number here:** the independent labels found
**39 genuine repairs in 300 pairs — 14%**. Symbol overlap is therefore **~86% noise as a
trigger**: gate on it alone and six of seven firings are not repairs. **This is a cap on firing
precision, not a discount on ranking accuracy** — the 69% above is already conditional on a
genuine repair and needs no correction. Multiplying a conditional by a base rate produces a
joint probability, not a corrected conditional.

## 6.5 Signals tested and rejected

Sixteen candidate pre-merge signals were tested. These failed, and are recorded so nobody
rebuilds them.

| Signal | Result |
|---|---|
| Gate merges on static-analysis coverage | **Null.** Relative risk 0.916, 95% CI [0.557, 1.505], Fisher p = 0.746. Held changes broke at 22.1%, passed ones at 24.1% — while the gate fired on **45% of pull requests** |
| Exposure to unresolvable call sites predicts breakage | **Null.** RR 1.040, cluster-robust CI [0.598, 1.890], 310 pull requests. Correcting the outcome rule moved it to 1.251 — *"the null survives the correction that would have helped it"* |
| "You forgot to change file X", from co-change history | **Dead.** Fired on 8 genuine breakages and named the right file **0 times**. The 8 are the subset it fired on; the 11 in the paragraph below are the breakages whose fix commits were retrievable, a different denominator |
| Fix-history hotspot warning | **Null.** RR 1.56, p = 0.334, firing on 36% of clean changes |
| Test-coverage gap | **Null and reversed.** Changes touching no test broke *less* (RR 0.91 and 0.76) |
| Ten pull-request metadata signals | **Nothing survived Bonferroni correction.** Only diff size replicated, at RR ≈ 2.1 — and every competitor already gates on it |
| Nested file-then-function ranking | **Below its own null ranker** |
| Structural callers as a localiser | **1 of 5**, while flagging 19% of the repository |

**Two of these rows are n ≤ 11, and that must be read off the page rather than inferred.**
`0 of 8` has a 95% upper bound of roughly **37%** — it supports *"not enough signal to ship a
missing-file finding"* and does **not** support *"co-change carries no signal"*; the first is a
decision under uncertainty, the second is a claim we have not bought. `1 of 5` is weaker still.
And `11 of 11` below puts the true rate above roughly **72%** — enough to point inference at
already-changed files, not enough to quote as a percentage. **Directional evidence, and it
happens to point where the architecture already goes, which is exactly when a small n is most
dangerous.** They do not belong in the same register as the 4,293-event ranking result, and
neither belongs on a slide.

**Why the localisers all failed, measured rather than assumed.** For every genuine breakage, the
fix commit's files were split into those the change had already touched and those it had not:
**5 of 11 SELF** (the fix only re-touched changed files), **6 of 11 MIXED**, **0 of 11
COMPANION**. Every breakage required re-editing a file the change had already touched. **These
are not incomplete changes; they are wrong changes** — which is why no signal about *which files
are involved* can localise them, and why inference is in the design at all. Published work
agrees: semantic errors account for over 60% of faults in model-generated code.

## 6.6 Language coverage

File-level ranking, same code path, pathspec swapped:

| Language | Events | Ranker | Null | **Lift** |
|---|---|---|---|---|
| TypeScript | 400 | 80.8% | 54.8% | **+26.0** |
| Java | 41 | 90.2% | 73.2% | **+17.1** |
| Python | 5,242 | 85.4% | 70.9% | **+14.5** |
| C++ | 63 | 82.5% | 68.3% | **+14.3** |
| Go | 185 | 85.4% | 76.2% | **+9.2** |
| JavaScript | 168 | 77.4% | 68.5% | **+8.9** |

**Positive in all six, with Python in the middle rather than at the top.** Limits: this is
file-level only, so it establishes the signal exists in these languages and not that
function-level extraction works in them; the non-Python samples are small; Kotlin returned no
result despite being the largest non-Python corpus available; and the outcome rule assumes
English fix-keywords in commit messages, which is a natural-language assumption travelling under
a programming-language result.

## 6.7 Measurement defects found and corrected

Eight instrumentation findings came out of this work. All produced plausible numbers. None
was detectable from the output alone. They are recorded because a document that never reports
its own errors gives a reader no way to calibrate the rest of it.

**A dead check that could not fail.** A hotspot signal returned zero at every threshold, which
looked like a clean null. Its window was expressed relative to today while the history it walked
was ancestral to a 2025 commit, so no commit could satisfy both. A sanity counter now reports
in-window commits found: **0 before the fix, 1,298 after.**

**Truncated history read as complete.** `git log -p` **exits non-zero on a blob-filtered clone**
and emits a partial patch stream. The harness did not check the return code, so runs analysed
**710 and 918 commits on two invocations of an identical command**, against the 3,313 the
repository holds. **Voided:** the first symbol-versus-file comparison, the nested-ranking
comparison, and the first retrospective figures — all rerun on full objects. **Unaffected:**
everything produced with `--name-only`, which reads no file contents.

**A test that could not fail.** Reverts are a repair by definition and need no rater, which made
them the obvious escape from self-labelling bias. The pooled result looked decisive — ranker
12/12 on reverted changes against 51% elsewhere, **+49 points, p = 0.0005**. The control killed
it: **the alphabetical non-informative pick also scored 12/12**, because a revert touches **94%
of the change's symbols** and 75% of them touch all. Any pick scores. **Withdrawn.** Caught
before publication, by asking what a broken ranker would score.

**The same defect again, on a different repository, and the documented repair did not fix
it.** Measuring top-3 surfaced `apache_airflow` failing with the identical fatal — *"in the
commit graph file but not in the object database"* — and emitting **9.1, 9.9 and 10.3 MB of
output on three invocations of one command** before exiting 128. `git fetch --refetch`, the
repair adopted last time, did **not** clear it: the corrupt artefact was the commit-graph file,
which named the clone's previous `main` tip after the refetch had removed that object. Ignoring
the commit-graph for that clone produced **11.4 MB and exit 0**. Two lessons kept: *byte counts
that differ between runs of an identical command are the signature*, and **the largest truncated
read still looks exactly like a complete one** — only the exit code separates them.

**A silent drop that wore the same clothes as a clean skip.** The first top-3 harness returned
`None` when a history read failed, and its caller could not tell that from *"this repository has
too few commits to qualify"*. Three of the largest repositories in the corpus vanished from one
run and returned in the next, and both runs printed a confident table. The cause underneath:
**27 of 35 clones are `blob:none`**, so a cold read lazily fetches trees from the promisor
remote over the network and is not deterministic until the object store is warm. The reader now
raises rather than returning, and the harness prints a per-repository skip ledger with reasons
and **refuses to report at all** if any read failed — which is what caught the airflow defect
above. Ask what a check prints when the thing it checks is broken; the honest answer here was
*the same table*.

**A control beaten by fourteen points, by a policy that was catastrophically worse.** This is
the quantitative version of the revert lesson above, and it is the more useful half.

Testing allocation policies, a score-gap stopping rule beat its alphabetical control by **+14.3
points — the widest margin of any arm measured** — while missing **17.76%** of events against
1.44% for the incumbent. It is the worst policy tested and it has the best lift.

**The mechanism: it reads about two units instead of three, so it selects a small, hard
population where alphabetical does terribly.** Both numbers move together. Neither says the
policy is good.

**The rule, and it generalises past this project: a control establishes that a result is not
noise. It says nothing about whether the policy is good. Both require the absolute number.**
Every lift figure in this document should be read beside its absolute, and a lift quoted alone
is uninterpretable in a direction that flatters.

**A split that reproduced its own pooled figure.** Partitioning the corpus into train and
holdout, the function-level arm scored 128 misses on one side and 46 on the other — **174/1,969
= 8.84%, landing exactly on the pre-split pooled value.** Nothing forced that. It is the same
class of assertion as the bin-sum check: against a quantity known from elsewhere, not internal
consistency. **Adopted as a rule — any future split must reproduce the pre-split pooled figure,
and a mismatch means the partition is doing something.**

**A guard firing correctly.** A wrapper timeout later killed a run mid-stream and the new
exit-code assertion refused to report from the partial read.

**The rule adopted:** any harness reading patch content asserts the git exit code, any clone used
for symbol-level work carries full objects, and any precision figure is reported beside a
non-informative control. **A precision number without a control is not a finding** — two
repositories produced figures the ranking had not earned.

## 6.8 What remains unproven

**Whether a reviewer shown the routing line before the defect exists catches anything they would
otherwise miss.** Every measurement above is retrospective. This is a field question — one month
of shadow mode on three repositories — and no quantity of history substitutes for it.

**~~Whether allocation actually reduces token cost~~ — PARTLY ANSWERED, and the figure moved.**
A real run through Vertex billed **$0.119 per pull request** against the $0.140 the table derived.
The saving against uniform reading is **1.25×**, not the 2× this row used to quote — an earlier
single-call version of the table implied 2×, a two-call version implied 1.5×. What is still open
is the multi-pass case, which the allocator specifies for rank 1 and which the arithmetic puts at
**$0.225, worse than reading everything.**

**~~Whether the productionised ranker reproduces these numbers~~ — ANSWERED. Gate 2b is met on
`main`.** `rank/` reproduces `research/phase0/external/defect_return_external.json` **event for
event** across the six pinned repositories: 2,400 events, miss **1.21%** against alphabetical's
**3.12%**, zero ordering mismatches. `just gate-2b` re-proves it on every run, and
`just verify-pack-vs-git` recomputes every stored row from git per path rather than trusting our
own read. **The research is the product, and it is checked rather than asserted.**

**Whether anyone will pay an independent party to measure their AI tooling.** The largest risk in
the plan, and the one that no further engineering resolves.

---

## 6.9 The two mechanisms taken from Qodo, and what each one bought

> **THE 67.9% HERE IS NOT THE 67.9% ELSEWHERE IN THIS DOCUMENT.** This one is Qodo's *precision*
> on Martian's offline layer — a behavioural measure of their output. The other, under "The
> corrected attribution rule",
> is the share of file-overlap attribution *verdicts* that blame a change sharing no symbol with
> the fix. Two unrelated quantities that happen to share two digits, and a reader meeting both
> will assume a relationship. `publishing-rules.md` bars mixing their behavioural numbers with
> ours at all; this is the same hazard arriving by coincidence rather than by argument.

Qodo leads Martian's offline layer at **67.9% precision** across **49 tools on the leaderboard** and does two cheap things
this project did not. Both were built, sabotage-tested, and run against **80 merged pull requests
from six repositories verified unused**, three arms, blind adjudication, bars fixed in advance,
**10 of 10 sabotaged controls caught**.

### Expansion removed the failure class it was built for

Git writes the enclosing declaration into every hunk header — `@@ -266,17 +269,12 @@ def
get_dumper(self, obj: Any, format: PyFormat) -> abc.Dumper:` — and we discarded it, so the model
saw `+ if order.refunded:` with three lines of context and no idea what function it was in.

**Wrong findings caused by not following code that was shown fell from 73.3% to 18.8% — a 54.6
point move**, against a 15-point bar. **The mechanism is visible in individual findings:** two
claims that falcon's URI decoder held an infinite loop died once the model could see ten lines
further back, where `for pos in range(...)` sits — a range loop advances every iteration, so the
`continue` it objected to cannot spin.

Expansion fired on **50.8% of 453 real hunks** and **moved an added line zero times across 664
hunks** — the invariant that decides everything, because every anchor we publish derives from where
an added line sits.

| pre-registered bar | | result | |
|---|---|---|---|
| **H1** wrong findings that failed to follow shown code | ≥ 15 point fall | 73.3% → **18.8%** | **PASS** |
| **H2** wrong-rate with expansion | ≤ 30% | **59.3%** [40.7, 75.5] | **FAIL** |
| **H3** conventions file makes convention-policing worse | ≤ +10 points | **−12.6 points** | **PASS** |
| **H4** yield | ≥ 0.30/PR | 0.41 / 0.40 / 0.46 | **PASS** |

### The overall rate did not move because a second class dominates — a different fact

Cross-tabulating cause against file kind separates them completely.

| file kind | n | wrong | rate | causes |
|---|---|---|---|---|
| **CI config** (`.github/`, `*.yml`) | 36 | 24 | **66.7%** [50.3, 79.8] | **EXTERNAL 23**, TRACE 1 |
| tests | 20 | 10 | 50.0% | TRACE 8, EXTERNAL 2 |
| source code | 29 | 11 | 37.9% | TRACE 8, EXTERNAL 3 |

**Every EXTERNAL claim checked against GitHub was false.** `actions/setup-python@5fda3b95` is
tagged exactly `v7.0.0`; `actions/checkout` `v7.0.1`, `astral-sh/setup-uv` `v9.0.0`,
`pre-commit/mirrors-mypy` `v2.3.0` and `PyCQA/isort` `9.0.0b2` all exist;
`hynek/build-and-inspect-python-package` was never renamed.

**The dates it called "in the future" read Aug 14–17 2026, against a run on Aug 18 2026 — three
days in the PAST.** That is not a training-cutoff artefact. It is a model with no reliable notion
of the present, and it will recur wherever dates appear. It also partly retires the registry-lookup
arm before it is built: an API lookup answers *does this tag exist* and never answers *what is
today*, while excluding the file kind is free and covers both.

**This is the third application of the decidability rule, not a new discovery.** Lockfiles,
manifests and documentation were already excluded on it. `.github/` was kept **deliberately and on
evidence** — it produced CORRECT findings at roughly one in four when the filter was written. It is
now 66.7% wrong at n = 36. The principle did not change; the evidence did.

### H3 inverted, and the reason is not the good news it looks like

| arm | n | CORRECT | WRONG | UNFALSIFIABLE | TRIVIAL |
|---|---|---|---|---|---|
| A | 29 | 2 | 15 | 4 | 8 |
| B | 27 | 2 | 16 | 4 | 5 |
| C | 30 | **3** | **14** | **8** | 5 |

From B to C, WRONG fell by 2 while **UNFALSIFIABLE rose by 4 and CORRECT rose by 1**. The
CORRECT-rate barely moves — **6.9% → 7.4% → 10.0%**, intervals overlapping almost entirely. **The
conventions file made the model more cautious, not more accurate**, and the CORRECT-rate is quoted
beside the wrong-rate every time for that reason.

### The off-CI subgroup is not the headline

Off CI config the wrong-rate runs 52.2% → 38.5% → **28.6%** across the arms. **Post-hoc, not
pre-registered, and the Wilson intervals — [33.0, 70.8], [17.7, 64.5], [11.7, 54.6] — overlap
almost completely.** A clean monotone ordering across three arms is exactly what noise looks like
at n = 13 and n = 14. It is the next pre-registration, not a result.

### What this does not license

The rater designed the run, so **none of it counts toward replication** — four designs now owe an
independent grader. Design 11's arm R, the clean design-nine replication, **cleared its yield bar
at 0.40/PR but is unadjudicated, so the replication count stays at two**; arm E failed yield at
0.22/PR before adjudication ran. **`infer/` stays closed.**


# Appendix — verification of every external claim

**Every vendor figure carries the date it was read, and a re-check date.** This document now
rests entirely on what vendors publish about themselves, so a reader has to be able to tell how
stale a number is without asking. **The Martian leaderboard turned over once in five months** —
CodeRabbit's January–February lead was superseded by Greptile's on 30 July 2026 — so a citation
without a date is a claim that quietly expires.

**Cadence: quarterly. Next re-check due November 2026.**


Checked against primary sources on 2026-08-13. Our own measurements are described with their
method in the body; this covers only claims about the outside world.

| Claim | Status | Source checked |
|---|---|---|
| CodeRabbit $1.5B valuation, $143M round, 12 Aug 2026 | **VERIFIED** | Bloomberg, BusinessWire, PYMNTS |
| 2M code reviews/week, 17,000 customers, 150,000 OSS projects | **VERIFIED** | Company announcement |
| 36% noise: 15% useless, 21% nitpicking, 28 PRs / 32,784 lines / 693 files | **VERIFIED** | Independent audit by the Lychee project |
| Same audit: 35% genuine improvements, 3% security-critical, 72% relevant | **VERIFIED** | Same audit |
| Reviewer precision spans ~49–76% | **VERIFIED, dated** | Martian Code Review Bench. Greptile 76.2% precision / 50.6% recall, **leaderboard 30 July 2026**; CodeRabbit 49.2% / 53.5%, **data Jan–Feb 2026**. **Rolling leaderboard — re-check quarterly, next due Nov 2026** |
| Cursor Bugbot: `neutral` conflates three states; emits no `skipped` | **VERIFIED verbatim** | Cursor's own documentation |
| Qodo: judge agent filters low-confidence findings before the pull request | **VERIFIED verbatim** | Qodo's own documentation |
| BreakBot: 8 stars, last push 2023-12-16, ISC licence | **VERIFIED** | GitHub API, queried directly |
| Graphite raised $52M Series B (Accel-led, Anthropic participating; $81M total) | **VERIFIED** | Funding coverage and company blog |
| Graphite $20–40 per seat; CodeRabbit $24–48, enterprise from $15,000/month | **VERIFIED** | Vendor pricing pages |
| CodeRabbit scans commit history for files that frequently change together | **VERIFIED verbatim** | CodeRabbit engineering blog |
| AI pull requests merge at 32.7% vs ~84.5% human; 8.1M PRs, ~4,800 teams | **VERIFIED** | LinearB 2026 Engineering Benchmarks |
| Inactivity is the largest single rejection cause at 17.3% | **VERIFIED** | MSR 2026 paper on the AIDev dataset; 3,225 fix PRs, 46.4% rejected |
| Senior engineers 8–12 hrs/week reviewing; 44% call review the top bottleneck | **VERIFIED** | Multiple industry analyses |
| Datadog suspect commits: four stated criteria, ticket automation | **VERIFIED verbatim** | Datadog documentation |
| Method-level change prediction wins when few recommendations are acceptable | **VERIFIED** | Peer-reviewed comparative evaluation, 15 open-source projects |
| Change coupling from version histories dates to 2004 | **VERIFIED** | Zimmermann et al., ICSE 2004 |

## Claims corrected during this verification pass

Recorded rather than silently fixed, because a document that never reports its own errors gives
a reader no way to calibrate the rest of it.

1. **"Over 2 million connected repositories"** — wrong metric. CodeRabbit reports 2 million code
   *reviews per week* across 17,000 customers. Corrected.
2. **"Reportedly catches about 6% of bugs"** — could not be substantiated from any primary
   source. What that vendor actually publishes is a **sub-3% false-positive rate**, which
   measures the opposite property. **Claim removed.**
3. **"36% noise"** stated alone — accurate but one-sided. The same audit reports 35% genuine
   quality improvements and 3% security-critical findings. Both halves now appear, because a
   competitor or investor will find the second half in ten minutes and the argument does not
   need the omission.
4. ~~**"$10,000+ per engineer per year"** — rounded up. The underlying figure is ~$9,600 at a
   $150K salary.~~ **This correction is itself superseded and is kept only as a record of the
   process.** "What QuantaMind is" now carries **$28,000–$42,000**, derived differently. An appendix that documents
   a correction to a number nobody quotes any more reads as current guidance; it is not.
