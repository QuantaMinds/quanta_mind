# QuantaMind

**Written 2026-08-13. Self-contained: every number below was measured by this project, and the
method is stated beside it. Nothing here cites another document.**

Nothing described here is shipped. Where a claim is unproven it says so.

---

# 1. What QuantaMind is

**Every AI code reviewer reads the whole diff at the same depth. QuantaMind decides where to
look first, and only reads hard there.**

## The problem, in plain words

**Agents write most of the pull requests now. The people reviewing them did not multiply.**

A team that opened twenty pull requests a week opens sixty. The same two or three senior
engineers still have to read them, and they are the same people you least want spending their
day on line-by-line review. Industry figures put senior engineers at **8–12 hours a week**
reviewing — roughly **$9,600 a year per engineer** at a $150K salary — and **44% of teams** name
slow review as their single biggest delivery bottleneck.
AI-authored pull requests merge at **32.7%** against **84.4%** for human-authored ones, and the
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
names the one function worth reading first.

## The problem with reviewers as they exist today

**They comment on nearly everything, and a third of it is not worth reading.** An independent
audit of one market leader — 28 pull requests, 32,784 lines, 693 files — found **15% useless and
21% nitpicking: 36% noise**. Stated fairly, the same audit found **35% genuine quality
improvements and 3% security-critical findings**, so this is not a claim that these tools are
worthless. It is a claim that **a third of what lands in the reviewer's queue is not worth the
reading time**, which at sixty pull requests a week is the difference between a queue that gets
read and one that does not.

The field's precision, measured by an independent benchmark on real pull requests, spans
roughly **49% to 76%** — the top tool converts about three comments in four into an actual code
change, the market leader about one in two. One vendor
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

## Our measurement of the reviewers' actual catch rate

On 337 AI-authored pull requests across 14 repositories, using an attribution rule we corrected
(described in the next section), **one leading reviewer left an actionable inline finding on
10 of 65 pull requests that later required a symbol-level fix** — and flagged 23.9% of the ones
that did not. Its silence is the normal case: roughly three quarters of pull requests received
a walkthrough with no inline finding at all.

That number is not an indictment of that vendor. It is the state of the art.

## What we do differently

A free pass that runs no model ranks the functions a change touches by how often each has
needed a follow-up fix before. **That ranking then decides where inference is spent** — deep
reading on the one or two functions history says changes come back to, nothing at all on the
cold ones. Structural claims the model makes are checked by a parser before publication. And
every pull request carries a line saying what could not be analysed and why.

Four properties follow, and each is measured or verified rather than asserted:

| | |
|---|---|
| **Quiet** | Fires on 10–12% of changes, held steady across repositories differing 80× in velocity |
| **Honest** | Reports its own blind spots — verified as unavailable to all seven competitors |
| **Right about where to look** | Names the function a later fix returns to, +22 points above its rate on non-repairs, p = 0.015 |
| **Cheaper** | Inference on a fraction of the diff instead of all of it |

---

# 2. How it works

```
  a pull request opens
        │
  ┌─────▼───────────────────────────────────────────────────┐
  │ 1. RANK        no model, no key, ~zero marginal cost     │
  │                every changed function, by how often it   │
  │                has been touched in the prior year        │
  ├──────────────────────────────────────────────────────────┤
  │ 2. ALLOCATE    the ranking decides the inference budget   │
  │                rank 1  → deep read, high effort           │
  │                rank 2–3 → shallow read                    │
  │                cold    → no model call at all             │
  ├──────────────────────────────────────────────────────────┤
  │ 3. READ        the model, on those functions only,        │
  │                returning structured findings              │
  ├──────────────────────────────────────────────────────────┤
  │ 4. VERIFY      the parser checks every structural claim   │
  │                confirmed → publish · contradicted → drop  │
  ├──────────────────────────────────────────────────────────┤
  │ 5. SAY         one comment, or silence                    │
  │                plus the coverage line, always             │
  └──────────────────────────────────────────────────────────┘
```

The deterministic layer that allocates the budget is the same layer that adjudicates the
model's output. That is what makes the verification step cheap.

## The day you install it

**Twenty minutes.** One GitHub App, read-only on code, write-only on a comment. No merge
rights, no customer model key.

It reads the repository's history once and builds a single index: for every function, how often
changing it has required a follow-up, and which functions those follow-ups touched.

**Then it runs the pipeline backwards over your merged pull requests and hands you the answer
before you have committed to anything** — how many of your changes came back, how many we would
have commented on, and on how many of those we would have named the function the fix returned
to. Your repository, your number, in the install. A reviewer that runs a model over every diff
cannot open that way: replaying 340 pull requests costs it 340 pull requests of inference.

## What ramps is breadth, not time

It comments from day one, narrowly, and widens only on evidence:

| Tier | Fires when | Volume |
|---|---|---|
| Start | the top-ranked function is in this repository's top decile of prior touch counts | 10–12% |
| Widen | top two ranked functions | untested |

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

### Step 1 — extract the changed units

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

**Why functions and not files or lines.** This is measured, not preferred:

- **Files are too coarse.** Of 1,316 follow-up fixes we examined, **989 touched only the same
  file at different lines** — that is continued development, not a repair. File-level signal
  measures *traffic*.
- **Lines are unusable.** Every later commit renumbers a file. With a median 26 hours between a
  change and its follow-up in an active repository, intervening edits are near-certain, so line
  ranges no longer line up.
- **Functions survive both.** `process_refund` is the same function at line 71 or line 340.

Measured across four repositories, ranking lift over a random pick: **symbol +46, +36, +28,
+17 points. File overlap erratic (+50 to −1). Line overlap dead (+7 to −5).**

### Step 2 — build the ranking index, bounded by the past

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

### Step 3 — decide whether to speak, using a percentile

**An absolute threshold does not transfer between repositories.** "Twelve prior touches" is rare
in a slow repository and unremarkable in a fast one; the same rule fired on 11% of one
repository and 53% of another.

So the threshold is a **percentile of this repository's own distribution**. Fire when the
top-ranked unit sits in the top decile. Measured across repositories spanning an 80× range in
velocity, this holds the comment rate at **10–12% everywhere**.

Here `process_refund` at 34 touches is in this service's top decile. **We speak.**

### Step 4 — allocate the inference budget

```
  process_refund            rank 1  →  deep read, high effort, full surrounding context
  _build_refund_payload     rank 2  →  shallow read
  send_refund_email         cold    →  no model call
```

The model receives the ranked function and its immediate context, not the whole diff.

### Step 5 — read, with the repository cached

Prompt caching is a **prefix match**: the render order is tools, then system, then messages, and
any byte change invalidates everything after it. That maps onto this product exactly:

| Position | Content | Changes |
|---|---|---|
| Prefix — cached | repository conventions, resolved signatures, index summary | per repository |
| Suffix — uncached | this diff and the ranked function | per request |

Two rules the implementation cannot break, because both fail silently: **nothing volatile in the
prefix** (a timestamp there makes every request a cache miss with no error), and **tools and
model frozen for a conversation** (both render at the very front).

Findings come back as **structured JSON against a schema**, never prose — the verification step
can only check a claim it can parse.

### Step 6 — verify the model's structural claims

The model returns:

> *The partial-capture branch returns before the ledger entry is written. On a full refund the
> entry is written at line 88; on the new partial path the early return at line 71 skips it.*

The parser then checks the structural parts of that claim against the parsed code: do both
return paths exist, does the early return precede the write. **Confirmed claims are published.
Contradicted claims are dropped silently, before any human sees them.**

A verifier that never rejects anything is not a verifier, so this ships with a sabotage test: a
deliberately false structural claim is injected and must be dropped.

### Step 7 — emit, with the coverage line first

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

| | Tokens | Cost |
|---|---|---|
| Repository prefix, cache read | 20,000 at one tenth | $0.010 |
| Ranked function and neighbours | 3,000 | $0.015 |
| Output including reasoning | 2,000 | $0.050 |
| **Total** | | **≈ $0.075** |

Reading the whole diff at uniform depth costs roughly **$0.175**. **Allocation saves about 2×,
not 10×.** At 200 pull requests a month that is about **$15 of inference per repository**. The
free tier runs no model at all and costs only compute.

## What is still unproven

**Whether a reviewer shown the routing line before the defect exists catches anything they
would otherwise miss.** Every number above is retrospective. This is a field measurement, and
no amount of history substitutes for it.

**And a correction that applies to every precision figure:** only **14%** of the change pairs
our outcome rule admits are genuine repairs — the rest are continued work or coincidence. Any
precision number stated against that rule must be multiplied by roughly 0.14 to become
precision against real repairs.

---

# 4. The competition, and why they cannot simply copy this

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

## Differentiation

| | CodeRabbit | Graphite | Greptile / Bugbot / Qodo | **QuantaMind** |
|---|---|---|---|---|
| Question it answers | Is this change **wrong**? | Is this change **slow to ship**? | Is this change **wrong**? | Is this change **incomplete or risky, and where** |
| Reads | whole diff, uniform depth | whole diff | whole diff | **the ranked function, deeply** |
| Uses history | files that change together, as hidden context | codebase-aware model | no | **functions that come back, as the allocation decision** |
| Says what it could not analyse | **no** | **no** | **no** | **yes, on every pull request** |
| Checks its model's own claims | no | no | no | **yes, parser-verified before publication** |
| Fires on | nearly every change | nearly every change | nearly every change | **10–12%** |
| Cost driver | tokens, scaling with lines read | tokens | tokens | **compute; inference only where ranked** |
| Priced | per seat | per seat | per seat / credits | **per repository** |

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
showing what we would have caught, before they commit to anything.

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

### Where we are genuinely exposed, stated plainly

- **The ranking is not defensible.** A week of work for anyone who reads this description.
- **CodeRabbit already scans co-change history.** Moving from file to function granularity and
  surfacing it as a finding is incremental for them, not a rebuild.
- **They have 17,000 customers and we have none.** Distribution beats mechanism, and it beats it
  quickly.
- **Our visible surface is a tenth of theirs.** Next to walkthroughs, diagrams and one-click
  fixes, a coverage line and one finding looks thin until somebody measures the noise.
- **We are not better at finding bugs.** Same model class, same precision ceiling. Nothing
  measured here says otherwise, and claiming it in a room would be false.

**The honest position: better on noise, honesty, targeting, verification and cost — not better
at bug-finding.** The moat is not the ranking. It is that the incumbents cannot measure
themselves, cannot afford to prove value on a prospect's own history, and cannot report coverage
without first building a layer whose output embarrasses them.

## The investor question: "if you are not better at finding bugs, why should we invest?"

The answer, in the order it should be given.

### "You're right. We're not. Neither is anyone else — and that is the point."

The independent benchmark puts the entire field between **49% and 76% precision**. We measured
the market leader against real breakages: it left an actionable finding on **10 of 65 changes
that came back**. Everyone runs the same model class against the same diffs, so detection
converges. **Any company whose plan is "we detect slightly better" is one model release from
parity, in either direction.** That is not a business worth funding, and we are not proposing it.

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
  we can prove value on a prospect's own history — replay their last six months and show what we
  would have caught. **That costs a model-per-diff reviewer a full inference pass per historical
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
same file at different lines**, 327 touched the modified lines, and 105 were explicit reverts.

**Lines are unusable.** Every later commit renumbers a file; with a median 26 hours to the
follow-up, intervening edits are near-certain. The rule under-counts real repairs by an
unmeasured amount.

**Symbols survive both.** A function keeps its identity when line numbers move.

## 6.3 The ranking itself

**File level, the largest sample:** top-1 accuracy **85.3%** against a **72.0%** alphabetical
null ranker and a 67.5% random baseline — **4,293 events across 17 repositories, positive in 17
of 17.** Sign test on direction, p ≈ 1.5 × 10⁻⁵.

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

**Thresholds must be percentiles, not constants.** "Twelve prior touches" fired on 11% of one
repository and 53% of another. A top-decile threshold holds the firing rate at **10–12% across
an 80× range in repository velocity**.

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

**Two raters — one with every incentive to find the effect, one with none — produced the same
effect size to within a point.** Agreement on the binary decision: **92%, Cohen's kappa 0.66**.
The biased rater was the *more liberal* one (17% repairs against 12%), so the stricter
independent rater should have shrunk the effect and did not.

**And the correction this forces on every other number here:** the independent labels found
**39 genuine repairs in 300 pairs — 14%**. Symbol overlap is therefore **~86% noise**, and any
precision figure stated against it must be multiplied by roughly 0.14 to become precision
against real repairs.

## 6.5 Signals tested and rejected

Sixteen candidate pre-merge signals were tested. These failed, and are recorded so nobody
rebuilds them.

| Signal | Result |
|---|---|
| Gate merges on static-analysis coverage | **Null.** Relative risk 0.916, 95% CI [0.557, 1.505], Fisher p = 0.746. Held changes broke at 22.1%, passed ones at 24.1% — while the gate fired on **45% of pull requests** |
| Exposure to unresolvable call sites predicts breakage | **Null.** RR 1.040, cluster-robust CI [0.598, 1.890], 310 pull requests. Correcting the outcome rule moved it to 1.251 — *"the null survives the correction that would have helped it"* |
| "You forgot to change file X", from co-change history | **Dead.** Fired on genuine breakages but named the right file **0 times out of 8** |
| Fix-history hotspot warning | **Null.** RR 1.56, p = 0.334, firing on 36% of clean changes |
| Test-coverage gap | **Null and reversed.** Changes touching no test broke *less* (RR 0.91 and 0.76) |
| Ten pull-request metadata signals | **Nothing survived Bonferroni correction.** Only diff size replicated, at RR ≈ 2.1 — and every competitor already gates on it |
| Nested file-then-function ranking | **Below its own null ranker** |
| Structural callers as a localiser | **1 of 5**, while flagging 19% of the repository |

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

Four instrumentation failures occurred during this work. All produced plausible numbers. None
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

**Whether allocation actually reduces token cost** against uniform review of the same diffs. The
2× figure is arithmetic, not measurement.

**Whether the productionised ranker reproduces these numbers.** If it does not, the research is
not the product.

**Whether anyone will pay an independent party to measure their AI tooling.** The largest risk in
the plan, and the one that no further engineering resolves.

---

# Appendix — verification of every external claim

Checked against primary sources on 2026-08-13. Our own measurements are described with their
method in the body; this covers only claims about the outside world.

| Claim | Status | Source checked |
|---|---|---|
| CodeRabbit $1.5B valuation, $143M round, 12 Aug 2026 | **VERIFIED** | Bloomberg, BusinessWire, PYMNTS |
| 2M code reviews/week, 17,000 customers, 150,000 OSS projects | **VERIFIED** | Company announcement |
| 36% noise: 15% useless, 21% nitpicking, 28 PRs / 32,784 lines / 693 files | **VERIFIED** | Independent audit by the Lychee project |
| Same audit: 35% genuine improvements, 3% security-critical, 72% relevant | **VERIFIED** | Same audit |
| Reviewer precision spans ~49–76% | **VERIFIED** | Martian Code Review Bench — top tool 76.2%, market leader 49.2% |
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
4. **"$10,000+ per engineer per year"** — rounded up. The underlying figure is ~$9,600 at a
   $150K salary. Corrected.
