# What to say when someone asks

> **Derived document.** Measurements here are copied from `QUANTAMIND.md`, which is canonical.
> Reconciled against it on 2026-09-09. If the two disagree, that one wins and this is the
> bug.
>
> **THIS FILE WAS THE BUG FOR THREE WEEKS.** It opened "Nothing is built yet — `src/quantamind/`
> holds a package root and nothing else" while nine layers shipped and the webhook reviewed real
> pull requests, and it told the reader to answer every question in future tense on that basis. A
> derived document that is not re-derived does not decay into vagueness; it states the opposite of
> the truth in confident prose, and this one was handing that to a room.

Six questions, in the order they get asked. Say the bold line, then stop — the paragraphs under
it are what to reach for **if** they push, not a script to recite.

---

## The one line, if there is time for nothing else

> **We check every code change against the rules your team already wrote down. If a change breaks
> one, it doesn't get in.**

If they ask what makes that different: **every other tool in this category tells you what is
wrong. We do not — we measured that half and it did not survive.** Then stop. The numbers behind
it are in `QUANTAMIND.md` and most of them do not belong in print; `publishing-rules.md` says which.

**THE OPENING CHANGED ON 2026-08-31 AND THE OLD ONE IS STILL RIGHT — JUST NOT FIRST.** This line
used to be *"we decide where to look first, and we tell you what we did not look at."* Routing is
still true, still replicated, and still the hardest thing here to copy. It stopped being the
opening because leading with it invites *"and are the findings right?"*, and the honest answer is
mostly not. Lead with the half that re-runs to the same answer on the same commit; reach for
routing at question four, where it is the supporting claim rather than the promise.

**A buyer shopping for an AI code reviewer will not recognise that sentence as one, and that is
the intended trade.** It puts us nearer Semgrep and SonarQube than CodeRabbit. Being mistaken for
a reviewer is how we get judged on findings we do not sell — but the cost is real, so the second
sentence has to bridge back to the category they were searching in.

**Do not say "autonomous senior engineer."** Nine designs and four blind rater pools put the best
configuration at roughly one useful comment per forty pull requests. It is the one claim in this
category the evidence here directly contradicts, and it is the claim a sceptical engineer will test
first.

## Read this before the first meeting

**Most of it is built, and the tense rule now cuts a different way.** Thirty of fifty build rows
are done. The standards engine, the ranker, a commit status that blocks a merge, the append-only
audit trail, the dashboard, accounts and entitlement, and cost per review all run; the webhook
reviews real pull requests; `quantamind retrospective` replays a prospect's own history from a
clone. Present tense is correct for those.

**Four things are not built, and the present tense about any of them is the misrepresentation
this section exists to prevent:**

| not built | what that means in the room |
|---|---|
| **Billing** | Nobody can pay. There is a price list, not a checkout |
| **Customers** | There are none. Nobody has run the retrospective against a prospect |
| **A posted check run** | Rehearsed and asserted; never written to a real pull request |
| **Air-gapped in a real network** | The refusals are tested; the environment has never been entered |

**And two things are built but must not be sold**: the reviewer's findings are **25.0% correct**,
and the enforceable surface is narrower than "your standards" sounds — three rule kinds
(`forbid_call`, `forbid_import`, `naming_pattern`) declared in `.quantamind/rules.toml`, **on
Python files only**. Everything else is recorded `UNCHECKABLE`, which is honest and is not coverage.

**So the rule is no longer "say it in future tense."** It is: *present tense for what a parser
does, future tense for anything that needs a customer, a payment or a model to be right.* The old
blanket rule was safe when nothing existed. Applied now it understates a working product to a
customer and describes a materially different company to an investor — which is the same failure
as overclaiming, pointing the other way, and it is the one this file actually committed.

**Do not explain how it works.** `publishing-rules.md` lists what must never leave the room.

---

## 1. "What is QuantaMind?"

> **Every team has already written down how it works — a CONTRIBUTING file, a style guide, a wiki
> page. None of it is enforced. We enforce it on every pull request, identically, and work that
> breaks it does not merge.**

If they want a second sentence:

> And when someone asks you to prove it, you can: every rule, against every file, on the record —
> including the files nothing could decide about, named rather than quietly counted as passing.

If they ask about the reviewing:

> We also do not read every file at the same depth. We work out which part of the change is
> riskiest and spend the effort there, and we tell you which parts we did not look at.

**Then stop.** Every extra sentence here explains the mechanism.

**Do not lead with the coverage line or the routing here.** Both are true and both are at question
four. Leading with them makes this a reviewer pitch, and a reviewer pitch is judged on findings —
which are 25.0% correct and are not what the price is for.

---

## 2. "How are you different from CodeRabbit or Greptile?"

**Do not say we see more files than they do.** It is false against Greptile — they index the
entire codebase — and claiming it loses the comparison in one sentence.

> **They see more than us. That is not the difference.**
>
> Greptile reads your whole codebase. CodeRabbit reads your whole diff. We are not trying to beat
> them on how much we look at. **None of them enforces anything** — every one of them produces a
> comment, and a comment is advisory by construction. We hold the merge on the standards your team
> already wrote, and we tell you what was looked at.
>
> **Silence from a reviewer has two meanings and no tool separates them.** *Examined, nothing
> wrong* and *never really read* arrive as the same blank space. You cannot act on that, so you
> open the file and read it yourself — which is the work the tool was supposed to remove.

### Do not say "at 50% recall, silence is wrong as often as it is right"

**It is false, and a technical buyer can disprove it on a napkin.** Recall is the share of *real
issues* found. It says nothing about how often silence is wrong, because most files contain no
issue at all.

With `d` the share of files carrying a real defect and `r` recall, the chance that silence hides
one is `d(1−r) / (1 − dr)`:

| Defect base rate | Chance silence is wrong, at 50% recall |
|---|---|
| 5% | 2.6% |
| 10% | 5.3% |
| 20% | 11.1% |
| 50% | 33.3% |

**Reaching a coin flip needs roughly two thirds of every file in every pull request to carry a
real defect.** The claim overstates by five to ten times at any plausible rate, and it breaks
our own rule — *say two and be right*.

**And we do not need it.** The argument is about **type, not rate**: you cannot distinguish
*checked and clear* from *never read* at **any** recall. That holds at 90% as it does at 50%.
Anchoring it to today's numbers makes a permanent argument look temporary — if someone reaches
80% next year, the line reads as retired.

### If they ask about the benchmarks

Get the framing right, because it changed and the obvious version is now stale:

> Martian runs the only genuinely independent benchmark in this market — real pull requests,
> open-sourced pipeline. **Greptile currently leads it**: 60.8% F1 and 76.2% precision as of
> 30 July 2026, with **recall of 50.6%**. CodeRabbit led earlier on January–February data with
> 51.2% F1, 49.2% precision and **53.5% recall**.

**Do not say "they both came first, both are true."** It is one leaderboard and two dates.
CodeRabbit's claim is months stale, and Greptile now leads on F1 *and* precision.

**Do not say "the best tools catch about half."** Recall sits near half for both leaders;
precision does not — it runs from 49.2% to 76.2%. The field is not uniformly at half.

**Say "recall on the Martian benchmark", never "catches half the bugs."** Recall against a
curated set of verified issues is not the share of all defects in a diff, and we do not know
which denominator produced those figures.

---

## 3. "Anyone could add that. Why can't they just build it?"

**This is the investor question**, and it has to be answered with the architecture, not with
marketing.

**Do not say "it is a hard thing to want" or "they will not do it because it hurts their
numbers."** Our own master document throws that out: *marketing positions reverse in a quarter.*
An unfalsifiable claim about a competitor's willpower is the weakest answer available.

**And do not defend the coverage line as the moat.** Our own competitor timeline rates it at
**two to three months** for a funded competitor. Defending the deal-deciding objection with the
shortest-lived item on the board is a mistake.

> **You are right that a coverage line is not hard. It is also not the moat, and I would not
> pitch it as one.**
>
> To emit *"41 of 43 call sites resolved, 2 unresolved — dynamic dispatch in registry.py"* you
> need three things: a parser that enumerates call sites, a resolver that attempts each one, and
> a typed record of every failure. **A retrieval-plus-prompt pipeline has no component that
> produces that number.** It is a different layer of software, and reading the diff more deeply
> does not produce it — dynamic dispatch does not resolve at any depth.
>
> So they must build a layer they do not have. And the first thing it does when they turn it on
> is tell their customers how much of each diff their reviewer never understood.

**Then move to the two things that are actually permanent**, because that is what the question
deserves:

> **A reviewer cannot credibly publish its own miss rate.** Not because it would refuse — because
> no buyer would believe it, the way no company audits its own books. You have four vendors
> claiming first place on the same leaderboard; that is the market pricing this in already.
>
> **And the measurement underneath is broken.** The standard rule for attributing a fix back to
> the change that caused it is **wrong on 67.9% of its verdicts** — measured here, reproduced
> three times. Every dashboard telling you where rework comes from is built on it.
>
> That is the company: **the only trustworthy answer to "is this working", in a market where
> every existing answer is two thirds wrong.** The reviewer is how we earn the right to sell it.

---

## 4. "Why does the coverage line matter?"

**Two separate features, and conflating them is the easiest mistake to make in a room.**

| | What it does | Status |
|---|---|---|
| **Routing** | says which part of the change to read first | **Measured, and replicated on repositories it was never built against** — 1.21% miss against an alphabetical control's 3.12%, n = 2,400, p < 0.000001, 6 of 6 repositories. **Still unproven:** whether a *reviewer shown it* catches anything they otherwise would not. Those are different claims and only the first is measured |
| **Coverage line** | says which parts could not be analysed | A construction, not a measurement. It either works or it does not |
| ~~**Findings**~~ | ~~what the model reports~~ | **MEASURED AND STOPPED.** 66.7% and 74.2% wrong under two blind raters, 3 of 66 correct by consensus. Not shipped, and nothing may imply otherwise |

**Do not tell the "reviewer said nothing about the payment function" story as a coverage-line
story.** In our own worked example that function is rank 1 and gets the deep read — the coverage
line reports the *unresolved* region, not the analysed one. **That story sells routing, and routing
is now the half we can defend** — but tell it as routing, because told as coverage it is simply
false about our own architecture.

**And the sentence to say when routing comes up, because it is the only externally replicated
number in the company:** *"We ranked the changed files by how often each has needed a follow-up
fix, read the top three, and missed 1.21% of the changes a later fix came back to. Sorting the same
files alphabetically missed 3.12%. That is on six repositories we had never touched, and it lands
within a twentieth of a point of what we measured on the eight we developed it against."*

Tell it about the unresolved region instead:

> Your change touches a handler that is registered at runtime rather than called directly.
> Every reviewer on the market reads past it, silently, because a dynamic registration is not a
> call it can follow. Nobody tells you. **The review comes back clean and the gap is invisible.**
>
> We name it. Not a finding — an admission, in the place where you can still act on it.

**QUOTE THE LINE THE PRODUCT ACTUALLY PRINTS, NOT THE ONE THIS FILE USED TO PROMISE.** It said
*"four call sites unresolved, dynamic dispatch in registry.py"* and nothing emits that sentence.
`render/blocks/coverage_line.py` names **files** — read, and not read — and appends unresolved
constructs in its own words:

> Ranked 4 file(s) by prior-fix history and read the top 3: `src/pay/app.py`, `tests/test_pay.py`,
> `src/pay/ledger.py`. Not read: `src/pay/settle.py`.
>
> …2 construct(s) could not be parsed and are outside everything above: …

**The call-site form is the design target, not the output**, and promising it in a room is how a
demo contradicts a deck. The shipped line makes the same argument — *this is what we read, this is
what we did not* — and it has the advantage of being what appears on their pull request.

Then land it:

> Where it says *checked*, you stop re-reading. Where it says *not checked*, that part is yours,
> named, before you merge instead of after something breaks.

**If you get one line only:**

> *A reviewer that tells you which parts it could not analyse is one you can build a process
> around. One that stays quiet about them is a coin toss with a subscription.*

**And be ready for the honest follow-up.** The **model** speaks on roughly one pull request in ten
— measured at 8–15% on six of seven repositories, and computed from theirs before they install.
On the rest there is a standards verdict and a coverage line, and no model finding. **Do not let
that be heard as "the product is silent nine times in ten":** the standards engine runs on every
pull request, every rule, every governed file. Nine times in ten we answered deterministically and
had nothing further to add. If they ask whether we would have caught
their last incident, the answer is *"possibly not — but you would have known which parts we never
examined."* Say that before they work it out.

**In the room, that number is now measured and it is the strongest version of this argument.**
On the research corpus, the defect sits in a unit our budget never funded about **one change in
eleven**. Do not hide it — it is the whole case:

> Our allocation reads a few units and skips the rest. On roughly one change in eleven, the
> defect is in something we skipped. **Every reviewer has a number like that and none of them
> publishes it — and more to the point, none of them can tell you which units it was.** We name
> them. So the one-in-eleven stops being a coin toss and becomes a short list with your name
> against it, before you merge.

**That is why we did not simply buy the number down.** A wider budget would roughly halve it and
cost about 50% more inference. **The cost of a skipped unit is not the skip — it is that nobody
knew.** Naming them removes that for nothing.

---

## 5. "Your first product failed. Why should I believe this one?"

**Answer it as the credential it is.** Do not soften the null, and do not imply the same test was
re-run and passed — it was not.

> **The first bet was that the places static analysis cannot resolve are the places that break.
> That is false.**
>
> We preregistered a stop threshold of 1.5 relative risk. The measurement came back at **1.040**
> — dead centre on no effect, 310 pull requests. We then applied the correction that would have
> rescued it, and it moved to 1.251. **The null survived the fix that would have helped it.** So
> we killed that product. None of its architecture is in this one.

Then the part that matters, and be exact about it:

> **What we build now is not that test re-run. It is a different and deliberately weaker claim.**
>
> The old one tried to *predict* — will this change break? The new one only *allocates* — of the
> parts of this change, which should be read first. We stopped asking what the parser could not
> resolve and started asking what has needed fixing before. And we moved from files to symbols,
> because the standard rule for attributing a fix to its cause is wrong on 67.9% of verdicts.
>
> That claim holds: the ranked unit is the one a later fix returns to, **85.3% against a 72.0%
> non-informative ranker, positive in 17 of 17 repositories.**

If they push on whether it is measuring anything real:

> Fair question, and it is the one we spent the most on. A busy file gets touched for lots of
> reasons. So we had 300 change pairs labelled **blind** — our verdict withheld, order shuffled
> by content hash — by a model from a **different family** with no stake in the answer. The
> ranker named the symbol on **69% of genuine repairs against 47% of non-repairs. +22 points.**
> The author's own hand labels had said 70% and 48%, so the independent rater reproduced it to
> within a point, and the biased rater was the more generous one.

**Close on what is still open**, before they ask:

> Three things are unproven and I would rather say them than have you find them. Whether a
> reviewer shown the routing line before the defect exists catches anything they otherwise would
> not — every number above is retrospective. Whether the ranking survives moving from files to
> functions, which is a gate that can end this. And whether the token saving is real; it is
> arithmetic, not a measurement.

**Say "disagrees with", not "is wrong".** What was measured is that the two rules *disagree*
on 67.9% of verdicts, with symbol-level treated as ground truth. **That is an argument, not a
measurement**, and a VP's analyst will find the seam. Have the argument ready:

> The file rule implies base rates of 90%, 83%, 44% and 33% across those repositories — nine in
> ten changes causing a defect is not a rate any codebase runs at. The symbol rule gives 62%,
> 42%, 27% and 29%. **Neither is verified ground truth. The file rule's rates are impossible;
> the symbol rule's are merely high** — and for changed units that later needed a repair, high
> is what you would expect.

**And print the interval before someone else computes it.** 36 of 53 is a small base for a number
now doing most of the commercial work. 55%–79% is still decisively "most", which is all the
argument needs — quoting 67.9% bare invites the recomputation, and being seen to have avoided it
costs more than the width of the interval.

**The one-line version:**

> *The failure is the credential. We ran a preregistered test, hit a null, tried the correction
> that would have saved it, watched it fail anyway, and wrote it into the first paragraph of our
> own engineering rules. That is the same thing this product does for your code — and we did it
> to ourselves first.*

**Do not say "we pivoted."** It invites the read that a hypothesis was shopped around until one
worked. What happened is narrower and more defensible: a strong claim was refused, and a weaker
one the same data could carry was tested and held.

---

## 6. "Will this make our pull requests move faster?" — the VP question

**Do not say yes.** It is checkable within a month, we have no measurement, and the arithmetic
is against us.

> **Probably not much, and I would not sell it to you on speed.**
>
> Review cycle time is dominated by waiting, not reading. **The largest single component is the
> gap between a pull request opening and anyone starting on it** — and a coverage line does
> nothing about that. Nobody begins reviewing sooner because the tool is more honest.
>
> So the speed claim would be a fraction of a fraction: the share of cycle time that is actual
> reading, times the share of reading spent re-checking files a tool already cleared. **And we
> have not measured it.** Whether a reviewer shown our routing line acts differently is the
> largest unproven item in this project.

**Then say what it does change**, which is a different and defensible claim:

> It changes what a reviewer is allowed to skip. Today silence is unreadable, so a careful
> reviewer re-reads anyway — you are paying for a tool and doing the work. With coverage there
> is a rule: **high coverage and no findings, approve without a full re-read; low coverage, one
> person looks at the named part only.**
>
> That is not reviewing faster. It is **reviewing less**, and it is the claim we can keep.

**Then move to the ground that is actually yours**, because this is a VP and the reviewer is not
the strongest thing on offer:

> There is a second thing, and for your role it is the larger one. **You cannot answer "was that
> change actually reviewed" for any specific merge today** — not "did a tool comment on it", but
> did anything examine it. Coverage makes that a query rather than a shrug.
>
> And every dashboard telling you where rework comes from is built on an attribution rule that
> **disagrees with symbol-level attribution on 67.9% of its verdicts — 36 of 53, 95% interval
> 55% to 79%** — reproduced on two further corpora at 36.1% and 35.7% survival. We give you a
> quarterly report on where rework actually concentrates, computed the other way.

**Say "disagrees with", not "is wrong".** What was measured is that the two rules *disagree*
on 67.9% of verdicts, with symbol-level treated as ground truth. **That is an argument, not a
measurement**, and a VP's analyst will find the seam. Have the argument ready:

> The file rule implies base rates of 90%, 83%, 44% and 33% across those repositories — nine in
> ten changes causing a defect is not a rate any codebase runs at. The symbol rule gives 62%,
> 42%, 27% and 29%. **Neither is verified ground truth. The file rule's rates are impossible;
> the symbol rule's are merely high** — and for changed units that later needed a repair, high
> is what you would expect.

**And print the interval before someone else computes it.** 36 of 53 is a small base for a number
now doing most of the commercial work. 55%–79% is still decisively "most", which is all the
argument needs — quoting 67.9% bare invites the recomputation, and being seen to have avoided it
costs more than the width of the interval.

**The one-line version:**

> *We are not selling you a faster review. We are selling you the ability to say which parts of
> a change were examined — and, once a quarter, where your rework actually comes from, measured
> with a rule that does not disagree with symbol-level attribution two times in three.*

**Do not put a percentage on the waiting.** Three different LinearB datasets are in
circulation — a 2021 analysis of ~2,000 teams and 847,000 branches, the 2026 Engineering
Benchmarks across 8.1M pull requests and ~4,800 organisations, and a 6.1M-pull-request set — and
the widely repeated "pickup is 40–60% of cycle time" does not map cleanly onto any of them. The
2021 figure is *idle share of lifespan*, reported as a distribution across cohorts rather than a
mean, and idle time is not the pickup phase.

**The qualitative claim survives all of that and is the one that matters**: waiting dominates,
and we cannot move it. **If a number is needed, read the current report and cite it by name and
year** — this document's own appendix cites the 2026 benchmark, and quoting a 2021 study beside
it is the same drift that put a superseded cost figure in three files.

**If they press for a number**, give them the measurement instead of a guess:

> One month, three repositories, shadow mode: does a reviewer shown the routing line act
> differently? Nothing substitutes for that run, and if it shows a speed effect we will tell you
> the size of it. **Right now the honest answer is that we do not know.**

**Why this beats the confident version.** A VP who is told "30% faster reviews" tests it in one
sprint. A VP who is told "we do not know, here is the run that would settle it, and here is what
we can back today" has been given something no other vendor in this market will give them —
which is the product's whole argument, made in the room before the product is installed.

---

## Two things to have ready

**When they ask for our benchmark:**

> We do not publish one. Benchmarks are chosen by the vendor — four companies are currently
> claiming first place on the same leaderboard. Give us a repository and we will run it on your
> own history, and you can check the answer yourself.

**When they ask what we are worse at.** Answer fast; hesitating costs more than the admission:

> CodeRabbit writes your unit tests, answers questions in the pull request, scans for
> vulnerabilities, and has a free tier that posts findings. Greptile indexes your whole
> repository and answers questions about it. We build none of that, and we are not better at
> finding bugs than either of them.

---

## Numbers that must not be said

- **"They only check 61% of a change."** Invented. There is no measurement anywhere in our
  corpus of what a competitor's coverage would be. It will be heard as measured.
- **Our own reviewer catch-rate observation (10 of 65). WITHDRAWN — do not use it at all.**
  Its Wilson 95% interval is 8.6% to 26.1% and the 23.9% comparison figure sits inside it, so
  the measurement cannot separate that reviewer's rate on changes that broke from its rate on
  changes that did not. It demonstrates nothing in either direction, and it named a company.
  **What survives needs no measurement of ours: nobody in this market publishes their own miss
  rate**, which anyone can verify by looking.
- **Any accuracy figure of our own.** See `publishing-rules.md`.

**Re-check the two Martian figures before any meeting where you quote them.** The ranking has
already turned over once.
[CodeRabbit's post](https://www.coderabbit.ai/blog/coderabbit-tops-martian-code-review-benchmark) ·
[Greptile's post](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark)
