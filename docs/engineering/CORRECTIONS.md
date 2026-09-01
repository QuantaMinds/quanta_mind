# Corrections — a claim that turned out to have nothing behind it

> **ADVISORY — no mechanism, and the reason is stated rather than the tag being a shrug.**
> This file records claims that turned out to have nothing behind them. No guard can check
> that an entry is honest or that the log is complete, and a guard that appeared to would
> be worse than none — the argument `AGENTS.md` already makes for its own advisory rules.
>
> Its job is not enforcement. It is to make one class **recognisable**, so a human catches
> the next instance: **stated authority with nothing behind it.**
>
> Every entry carries four things. The last column is the one that stops this becoming
> decorative — if most entries read "caught by reading", that is a finding about where
> coverage is thin, and the format is what makes it visible.

> **THIS LOG WAS ITSELF SPLIT IN TWO FOR EIGHTEEN DAYS, AND THE HALF LEFT BEHIND DECLARED
> THE OTHER HALF FABRICATED.** Entries 1–5 lived here; a second file at the pre-rename path
> held 6–11 and opened by stating that entries 1, 3 and 5 "did not exist" and "were
> referenced and never written down". They existed, four directories away, in the file
> `git mv` had moved. **Entry 12 is that defect, filed in the log it happened to.** There is
> one file now, entries run 1 through 12, and `guard:citations/identity` fails the build if a
> second document ever claims a basename this one already holds.

**Entries 1–4 are short enough for a table. From 5 on they are long enough to need sections,
which is a fact about the defects and not about the format.**

| # | The claim | What actually held | How it was caught | Mechanism now |
|---|---|---|---|---|
| 1 | A protocol file was cited by path **and section number** as established policy governing how the 20-PR gate must be run. | The file had never been committed. Neither had the section. The real instruction was one line in `PHASE0_RUNBOOK.md` — "Read them yourself" — which predated the citation and said something the fabricated section did not. | By reading. The cited path was checked against the tree, twice, and did not exist either time. | **YES** — `guard:citations/resolve`, sabotage-verified against this exact citation. |
| 2 | A31 recorded `--filter=blob:none` as ABANDONED. | The flag stayed in `pipeline/worktree.py` for a day, and **both arms were walked under the strategy the amendment said was abandoned.** | By reading the code after the walks had already run. | **YES** — `guard:runtime/check_no_partial_clone` rejects any `--filter`, and `guard:check_withdrawn_amendments` requires a withdrawal to name its enforcer. |
| 3 | The 20-PR gate validated the outcome classifier. | `draw._as_record` **rebuilt** the classifier's input instead of consuming the `PRRecord` the pipeline had written, and got `base_ref`, `arm` and `merged_sha` wrong. The gate certified a classifier the study does not run, on roughly one PR in six. | By reading, after it had already invalidated a gate — chased down from a single disagreement where machine and human gave three different answers for the same PR. | **NO.** No guard catches "this tool rebuilds its input instead of consuming it". `record_for` now returns the stored object and is asserted on **identity**, but that is a test of one call site, not of the class. |

| 4 | "All four base branches merged into main later than the PR merged into them, so walking default measures a different week." Stated as a measurement, and a taxonomy was designed on it — the fourth arm was said to be one that *will* fire. | **All four arrived inside the window.** Measured: 1 minute, 3 minutes, 10 minutes, and 3 days 12 hours, against a 7-day window. Walking default would have been valid for every one. | By finally running the query — `git rev-list --ancestry-path <merge_sha>..<default>`, last entry, its committer date. Minutes of work, never done until after the claim had been built on. | **NO.** Nothing catches an unmeasured claim in prose. See the mitigation below. |

---

## The mitigation for entry 4

No guard reads prose for whether a claim was measured. What would have worked here is a
habit, not a mechanism:

> **A claim about the data is either accompanied by the query that produced it, or marked
> as a hypothesis.**

Entry 4 also has a shape worth naming, because it is the reason it went unexamined by
either party. **The unverified claim was conservative** — it predicted more exclusions,
more caution, a wider limitation. That made it comfortable to accept and extend.

An unverified claim that argues for caution attracts less scrutiny than one that argues
for a result, and that asymmetry is how a study accumulates unearned conservatism. The
measured answer was the opposite of the comfortable one in every case.

---

## What the last column says

Two of three are now mechanised. The third is the one that matters, and it is the one no
guard reaches.

Entries 1 and 2 are **reference** failures: a citation that resolves to nothing, a
withdrawal that names no enforcer. Both are decidable by pattern, which is why both now
have guards.

Entry 3 is a **provenance** failure — two code paths that each look correct in isolation,
where one silently stands in for the other. Nothing distinguishes a legitimate constructor
from a drifting reconstruction without knowing which artefact is authoritative, and that is
a judgement about intent. It went three fields wrong in a path with **zero test coverage**,
inside the tool whose entire purpose was to validate something else.

The generalisable form, and the thing to watch for:

> **A validation tool must consume the artefact under test, never reconstruct it.**
> Reconstruction is where drift enters, and it enters silently because both paths look
> correct on their own.

---

## 5 · A pre-registered check with no possible input

**Claimed:** A56 registers, before the exposure pass, *"`TIMEOUT` rate for EXPOSED against
UNEXPOSED PRs"* as a test of whether graph attrition correlates with the treatment.

**What actually held:** the check cannot be computed and never could have been. A PR that
times out has **no exposure classification**, because timing out is what prevents one —
all 46 timeouts and both OOMs classify as `unanalyzed_resource`. The check compares
timeout rates between two groups that a timeout removes you from.

**How it was caught:** by running it. The join returned zero exposed and zero unexposed
timeouts, which is not a null result — it is the only result the check can produce.

**Mechanism now:** none, and that is the point of this entry. This is a NEW class, distinct
from the ones already logged. Rule 14 asks *what does this check output when the thing it
checks is broken?* — and answers "the same thing", which catches a check that cannot
discriminate. **This check cannot even be evaluated**: its input set is empty by
construction, so it has no output at all, working or broken. The question that would have
caught it is one step earlier: **can this check receive data?**

The second half of A56's timeout check — TIMEOUT rate by scope-file quartile — stands and
is computable. Size selectivity is measurable; correlation with exposure, through this
route, is not.

**ADVISORY.** No guard proposed. A mechanism that decided whether a pre-registered check
has a reachable input set would have to understand the check, and inventing one on a
single instance is how a guard ends up asserting more than it can test.

---

## 6 · The wrong answer was more publishable than the right one

**2026-08-21, measuring whether the firing rate drifts within a repository.**

The question was whether a repository's firing rate trends over its lifetime. It was measured three
times. The first two were wrong. **The second wrong version produced by far the most interesting
result.**

| version | what it did | what it produced |
|---|---|---|
| 1 | sliced the calibration set itself | in-sample; the newest slice shared a period with the bar |
| 2 | disjoint windows, scored against **today's** floor | **`trpc/trpc`: 70%, 68%, 62%, 54% against 12% now** |
| 3 | disjoint windows, each against **its own** floor | `angular`: 12, 11, 11, 10, now 11 |

**Version 2 reads as a finding. Version 3 reads as nothing happening.**

A rate collapsing from 70% to 12% is a story: the product is getting quieter, the customer should be
told a direction, the install output needs a trend line, the sign test needs checking. All of that
reasoning happened. **It was reasoning about an artefact** — version 2 compared a top counted in one
era against a bar derived from another, so it measured how busy the repository used to be, not how
selective the rule was.

**Version 3 is the true one and it says the rate is a steady per-repository constant.** Which is the
better product property, and the more useful thing to tell a customer, and completely unexciting.

### The pattern, which is not "check your statistics"

**The defect made the result more interesting, so nothing about the result invited suspicion.** A
null looks like a mistake and gets re-examined; a strong effect looks like a finding and gets
written up. **The check has to fire on the shape of the measurement, not on the shape of the
answer.**

This project has the same pattern on record already: **the score-gap policy had the best lift and
the worst miss rate of any arm measured.** Beating the control by +14.3 points was the publishable
half; missing 17.76% was the half that mattered. The number that flattered the design was the one
that got quoted.

### What actually caught it

Not a test. **An outside reader asking what the windows were measuring before reasoning about their
shape.** The three internal checks that fired during this work — the arithmetic not closing at
38+12 from 24 candidates, the checksum on vendored data, the module-identity collision — all caught
mechanical faults. **None of them could have caught this, because version 2 was mechanically
correct and semantically wrong.**

### The rule this leaves

**Before reasoning about what a number means, state what it is a count of, and check that both sides
of any comparison are counts of the same thing.** `assert_spans()` now enforces the narrow version
of that for the firing gate — the bar and the score must be drawn from the same span — after the
same defect produced three different plausible answers, twice as a clean zero and once as a trend.

---

## 7 · Four analyses read a field for something it does not hold — what is void, and what is not

`gap_detail.json` carries a key called `ours_caught`. It holds **golden comments our arm covered**.
During a forensic pass on 2026-08-22 I read it as **our candidates that were correct**, and asked
`candidate in ours_caught`. That test is false for every candidate by construction — the two sets
are drawn from different populations and never intersect. **All 194 of our candidates classified as
false positives**, and everything computed from that split was arithmetic on a constant.

### Void — do not cite these

1. **"68% of our false positives are in the wrong place, 32% are in the right place with the wrong
   claim."** The population it split was every candidate, not the false ones.
2. **"Our false positives concentrate in async and error-handling code."** Same population, so this
   describes our output in general and says nothing about our errors.
3. **"Our duplicate rate is 0.0%."** Nothing could match, so the measurement could only return
   zero. **The true figure is 17.3%** — the highest of the three arms it was compared against.
4. **"Four `forEach`-with-`async` candidates are in the wrong place."** A symbol-overlap marker,
   run over the same mis-typed split. A matching golden exists.

A fifth error in the same pass had a different cause and is void for that reason: **the keycloak
PR 36880 "near-verbatim golden recorded as a miss"** compared the *nits* arm's candidate text
against the *strict* arm's scoreboard. Two arms, one scoreboard.

### NOT void — checked, re-derived, and reproducing today

The concern that prompted this entry was broader than the defect. Every committed consumer of the
field iterates `for g in d["golden"]` and asks `g in ours_caught`, which is the field used for
exactly what it holds. Re-running `analyze_gap.py` on 2026-08-23 reproduces the published tables:

- **the severity table** — Low n = 46, both 6 / only THEM 12 / only US 6, net −6, and **"two-thirds
  of the gap is Low severity" stands**
- **the category table** — bug n = 94, security n = 11 at 45% only-US, style n = 10 at 50% only-THEM
- **the prompt-ban deficit rates** in `docs/product/reviewer/greptile-gap-analysis.md`
- the both / onlyTHEM / onlyUS / neither split: 52 / 38 / 29 / 54 of 173

**These are golden-level and were never candidate-level.** The withdrawal is narrower than it first
appeared, and saying so precisely is part of the correction — an over-broad retraction discards
sound work and is its own kind of inaccuracy.

### The pattern

**A field name described the container, not the contents.** `ours_caught` is true of goldens we
caught and reads equally well as candidates that caught something. Nothing failed: no exception, no
empty result, no implausible number. A 68/32 split is exactly what a real finding looks like.

Two sibling defects in the same session, same root:

- an apparent **+32 swing** in CodeRabbit's true positives on a re-judge, attributed to judge
  non-determinism and reported to the user as an unreliable instrument. Three replicates over
  identical candidates spread **2.1 points**. The +32 was `run.py:judge_arm()` counting *goldens
  matched* against a newer path counting *candidates matching* — and **that difference is the
  redundancy rate**, so the artefact was the measurement.
- **our judge's count placed beside Martian's published count for Qodo** in one table. Two
  instruments, one column — the same defect as quoting Macroscope's 55% comment-volume figure as a
  false-positive rate.

### The rule this leaves

Entry 6 left "state what a number is a count of before reasoning about it". This is that rule
failing at the level below: **the two sides were both counts of comments, and were counts of
comments from different populations.** So the narrower rule is —

**When testing membership, name the population on both sides of the `in`.** `candidate in
ours_caught` is a type error the language cannot see, because both sides are `str`. Where a
container holds one population and its consumers use another, an empty intersection is the
signature — and **an intersection that is empty for every element is not a finding, it is a
mismatch.** `label_candidates.py` now stores the per-candidate verdict as an artefact so the
question never has to be re-derived from a field that does not answer it.

---

## 8 · A verifier that fails toward CONFIRMING is worse than no verifier

**This is the most dangerous defect in this log, and it shipped as a fix for a different one.**

`adjudicate_release()` was built to refute the reviewer's false claims that a package release does
not exist. It took the first name-shaped token before the version number. In

> "The version 1.45.34 of awscli does not exist on PyPI"

that token is **`The`**. It asked PyPI for `The/1.45.34`, received a 404, and read the 404 as
evidence that the claim was true. **It returned `CONFIRMED` for every false claim it existed to
refute** — and `CONFIRMED` is the verdict that publishes.

### Why this is worse than the 77% run, and worse than confabulation

Three defects in this sequence produced wrong numbers. This one produces a wrong number **with a
fact attached to it**, and the two are not the same kind of error:

- **A verifier that wrongly REFUTES costs a true finding.** Bad, bounded, and visible: something
  that should have published did not.
- **A verifier that wrongly CONFIRMS takes a confabulation and grounds it.** The reviewer's
  invented claim now has an authority behind it.

**Nothing supports a confabulation, and that absence is itself the signal a reader uses.** A wrong
confirmation removes the signal. A well-grounded false finding is harder to catch than an
unsupported one, not easier — which inverts the entire reason for building the oracle.

### The rule, and it is about the direction of a default

**Fail toward dropping, never toward confirming.** `UNRESOLVABLE` is the default; every candidate
subject is tried; a claim whose subject cannot be identified drops the finding rather than
publishing it. The asymmetry is deliberate and it is not a tuning parameter.

### The screening rule this sequence also produced

Three base rates were measured before building on them: SHA→tag **0.24%**, registry existence
**0.00%**, dates did not reproduce. Two of three detectors were closed before they were built.

The registry zero came with a mechanism, and the mechanism generalises:

> **A pinned version that does not exist fails CI on the first install, so almost none survive on a
> main branch.**

**So: before measuring a base rate, ask whether CI would already have caught the defect. If it
would, expect zero.** That would have predicted the registry result without the run, and it is
cheaper than measuring. It does NOT replace the measurement where the answer is not obvious — the
SHA class is invisible to CI, which is exactly why its rate was non-zero.

### And a zero means nothing without a control

The registry scan reported 0 of 176. It is believable only because `flask==99.99.99` was asked in
the same run and came back absent. **Without that, a zero is indistinguishable from a broken
scan** — which is precisely what the other three defects in this sequence turned out to be.

---

## 9 · The rule was written down, and I broke it anyway, all week

`docs/product/publishing-rules.md` says:

> **Never quote a competitor's ONLINE precision beside one of our own numbers.** Martian's
> leaderboard precision is *behavioural* — did the developer make the change — and our adjudication
> measured whether a claim is *true and anchored*. **That band is quotable about them, never as a
> backdrop for us.**

And, as an explicit condition: **"offline and online figures must never appear in the same table."**

**Across this week I compared our 5.8% strict-adjudication correct-rate against "a 49% field floor"
repeatedly** — in conversation, in the execution pre-registration's bars, and in
`why-the-correct-rate-is-low.md`, which was committed with the sentence *"The field floor is 49%.
The best slice of anything is 13.0%."*

### The two quantities

- **49–76%** is Martian's ONLINE layer: **did a developer change the code.** Behavioural.
- **5.8%** is a blind hand-adjudication of **whether the claim is true.**

They are not the same question about the same population, and the gap between them is not a gap in
performance.

### What the comparable numbers actually are

Martian's OFFLINE layer scores every tool against the same 50 pull requests and the same
human-verified issues: **Greptile 56.5%, ours 43.6%, CodeRabbit 36.5%** — ours corrected to ~37.1%
for out-of-family judging. **At level with CodeRabbit, behind Greptile.**

**And the 5.8% has no comparator at all.** A search of the August 2026 literature found no
published strict-adjudication rate for any tool: the field reports behavioural exact-match (best
published research result **28.0%**) or benchmark matching against planted defects (best tool
**F1 47%** over 8 tools and 67 real bugs). **Nobody publishes the number we hold ourselves to.**

### Why it survived so long

**Because it made the case stronger.** "43 points below the worst tool in the field" is a more
decisive sentence than "our strictest instrument has no comparator", and the decision it supported
— closing Half B — was correct on other grounds. **A wrong argument for a right conclusion is the
hardest kind to notice**, and this project has entry 6 on record for the same shape: the defect
that made the result more publishable was the one nobody re-examined.

### What does NOT change

The closure. **The stricter measurement governs shipping** — that rule is also written down — and
12 correct of 207 is the stricter measurement. The yield argument, one useful comment per 27 to 77
pull requests, is instrument-independent. **What changes is one sentence that was never
supportable**, not the decision it was used to support.

### The rule this leaves

**A rule already written is not a rule already followed.** `check_decided_vocabulary.py` exists
because decisions drift in the sentence people quote; this one drifted the same way, and the guard
does not cover `publishing-rules.md`'s bans. **When a comparison makes the argument notably
stronger, that is the moment to check both sides are the same instrument** — not after it has been
committed.

---

## 10 · The first defect in a PLAN rather than a measurement

`feat-execution-corpus.md` specified **≥ 30 correct findings** and costed the round at **"~200
findings by one independent rater. Days, not hours."**

At the pool's 5.8% correct-rate, 200 findings yields **11.6 correct**. **The spec asked for 30 and
the cost stated would have bought 12** — which is the pool we already have, and the size that
collapsed to 2 coverable at step 0.

The two numbers describe the same quantity, sat in the same document, and never met. Done properly:
30 correct is **518 findings across 407 pull requests, about 52 hours** — a fortnight of one
person, roughly an order of magnitude from "days, not hours".

### Why this one is different from the nine above it

**Every earlier entry is a defect in a measurement.** A wrong regex, a mis-read field, a verifier
that confirmed by default — things that produced a number, where the number was wrong.

**This one produced no number at all.** It was a plan whose two halves contradicted each other, and
nothing would have caught it until someone had spent a fortnight discovering that a fortnight was
the price. **A measurement gets checked because it is a claim. A cost estimate reads as an aside.**

The same shape is on record once already: four fixes were recorded in a register that pointed at a
branch, so the register and the thing it described disagreed and neither was wrong on its own.

### The rule this leaves

**Where a plan states a requirement and a cost, they are two views of one quantity and must be
computed from each other, not written down separately.** The cost table in that document is now
derived from the correct-count requirement rather than asserted beside it, so moving the
requirement moves the cost.

---

## 11 · A success figure reported as a failure figure, three times, in one week

I wrote — in conversation, and into three committed documents — that

> **85.3% of admitted events are not genuine repairs.**

**85.3% is the ranker's top-1 attention hit rate**: 85.3% against a 72.0% null, 17 of 17
repositories, n = 4,293, recorded as SOUND in `gravity-reviewer-build-plan.md`. **It is the
headline success number of the half of this product that works, and I reported it as the
contamination rate of that half's label.**

The real contamination figure is nearby and different: **roughly 86% of symbol-overlap pairs are
not genuine repairs**, from blind labelling, in `QUANTAMIND.md` — a different population
(symbol-overlap pairs, not admitted file-level events) reached by a different method.

**Two numbers a point apart, meaning opposite things about the same system.**

### And its complement was inverted too, in the document I inherited it from

`jira-datadog.md`, written 2026-08-20 and not by this week's work, read: *"the firing precision
caps at roughly one in seven — 85.3% of admitted events are not genuine repairs."*

**One in seven is 14.7%, which is the ranker's top-1 ERROR rate** — halved from the null's 28.0%,
recorded two documents away as *"85.3% is +13.3 points — error roughly halved, 28.0% to 14.7%."*
So the ranker's hit rate AND its error rate were both reported as evidence the ranker's label is
worthless.

**I did not originate it and I did not check it either**, which is the part that matters: it was
load-bearing in an argument I made all week and one `grep` would have found the run.

### What it was used to argue

That the ranker's label is too contaminated to trust, so Jira and Datadog are needed as independent
labels. **The conclusion may still be right** — the label does carry known contamination — but the
number offered for it was the ranker's accuracy, and an argument that a measurement is worthless
supported by that measurement's success rate is not an argument.

### The shape, which is entry 9's shape

**The wrong number made the case stronger.** "85.3% of admitted events are not genuine repairs" is
a devastating sentence about a proxy label; "the label carries known contamination" is a careful
one. The devastating version went unchecked for a week because it was pushing toward a conclusion
already believed.

**Entry 9 was the same:** a barred behavioural figure quoted as our backdrop, surviving because it
made the closure look more decisive than the evidence needed.

### The rule this leaves

**A number that damages your own work is not thereby verified.** Scepticism is applied to numbers
that flatter and relaxed on numbers that indict, and the second half of that habit is the one this
log keeps catching. `check_decided_vocabulary.py` guards decided values; nothing guards a figure
carried from one measurement to another because it fit the sentence being written.

**Before quoting a number against your own product, find the run that produced it** — the standing
rule, applied in the direction it is never applied.

---

## 12 · The corrections log had two copies, and the copy declared its own entries fabricated

**2026-08-13 moved eight loose documents into folders, every one by `git mv`, and git recorded all
eight as renames. `docs/CORRECTIONS.md` became `docs/engineering/CORRECTIONS.md`.** That commit's  <!-- citation:allow — the vacated path is the SUBJECT here; it must not resolve. -->
own "could still silently fail" section reads:

> the citation guard's basename fallback is what let eight files move without touching a single
> citation, and the same fallback means **two documents with one basename in different folders
> would resolve to whichever the index happened to keep**. Nothing in the tree collides today.
> `check_module_identity.py` enforces this for `src/` and **nothing enforces it for `docs/`**.

**A file was then created at the vacated path, and the predicted collision was live for eighteen
days.** It opened:

> This file is cited from `HAND_LABELLING_PROTOCOL.md` as entries 1, 3 and 5 and **did not exist**.
> Those entries were referenced and never written down. **Whoever holds that context should write
> them.** Numbering starts at 6 so the gap stays visible.

**Entries 1, 3 and 5 were written down.** They are the first three rows and the closing section of
the file the rename produced. The citations in `HAND_LABELLING_PROTOCOL.md` were correct when made
and correct still; what had moved was the file, not the entry.

### What was actually wrong, in three separate places

1. **The claim.** A corrections log — whose whole subject is stated authority with nothing behind
   it — asserted that three of its own entries had never been written, on the evidence of a failed
   lookup at one path. It is the only entry here that is an instance of its own file's class.
2. **Twenty-five citations resolved to the wrong file.** Every consumer in the repository cited
   `docs/CORRECTIONS.md`, and roughly half named an entry living in the other copy.  <!-- citation:allow -->
   `guard:citations/resolve` passed all twenty-five, because the path existed. **A citation that
   resolves is not a citation that resolves to the right thing**, and the guard could not see the
   difference.
3. **`docs/` had a stated invariant and nothing held it.** The rename commit made "docs/ has zero
   loose files and five folders" a property of the tree and wrote it into `README.md`. The
   recreated file was the only loose file in `docs/` from the day it landed. Nothing failed.

### Why no mechanism caught it

**Because each half was individually well-formed.** Both files parsed, both were cited, both were
edited by people who had read them. The resolver's basename fallback — the thing that let eight
documents move without a single citation edit, and a genuinely good property — is the same thing
that made two documents with one name indistinguishable to every automated reader.

**And the numbering hid it from human readers too.** A log running 6, 7, 8, 9, 10, 11 with a
written explanation of the gap looks deliberate. The explanation is what made it look deliberate,
which is the uncomfortable part: **a well-written account of an absence is harder to doubt than a
bare absence.**

### The rule this leaves

**A failed lookup is a question, not a finding.** The other copy was one `find . -name` away, and
"whoever holds that context should write them" was written instead of running it. Entry 8 says fail
toward dropping rather than confirming; this is the same asymmetry one level up — **when a lookup
fails, the cheap hypothesis is that you are looking in the wrong place, not that the thing was
never written.**

**Mechanism now: YES**, and it is the one the rename commit said was missing. `guard:citations/
identity` fails when two documents under `docs/` share a basename, and `guard:citations/resolve`
now fails a bare-basename citation that matches more than one file instead of silently taking the
first. The first check would have fired on the day the duplicate was created; the second closes the
fallback that hid it afterwards. Both were sabotage-verified against this exact collision.

---

## 13 · I asserted the direction of an artefact I could have measured in one line

**2026-08-31, closing D2e on a pre-registered null.**

I found a defect in my own instrument — `drift = shifts/churn` and `fix_rate = fixes/churn` share a
denominator, so part of any association between them is arithmetic — reported it prominently, and
then wrote:

> A shared `1/churn` induces a POSITIVE association between drift and fix rate. B2 asked for a
> positive one and observed a **negative** one — so the artefact could only have flattered the
> hypothesis, and it still failed. The bar is if anything more securely unmet than the headline
> number suggests.

**That is false.** A shared denominator induces a positive association **only when the denominator
is independent of the numerators**. Measured on the same 305 rows, in one line:
`corr(shifts, churn) = +0.696`, `corr(fixes, churn) = +0.841`. Both track it hard, so the induced
sign is not reliably positive and the negative result I read as evidence may be the artefact itself.

**On raw counts with no ratio anywhere, two of three churn bands run the OTHER way.**

### What makes this the worst kind of entry in this log

**It came immediately after catching the defect, in the sentence that disposed of it.** Finding the
shared denominator was the good half; the bad half was reaching for a reason it did not matter
rather than spending one line finding out. **A caveat that is raised and then dismissed is more
dangerous than one that is never raised**, because the raising is what buys the reader's trust and
the dismissal is what spends it.

The shape is entry 6's and entry 11's, one level up: **the convenient answer went unchecked because
it was convenient.** There I quoted a number that damaged our own work without finding the run; here
I argued away a defect in our own work without doing the arithmetic.

### How it was caught

**By an isolated model of a different family, asked to attack the document.** It got the statistics
right immediately and named the assumption I had not noticed making. That is the product's own
thesis — *we do not build a better bug-finder, we build the judge* — turned on our own research, and
it earned its keep on the first try.

**It also found a second bias I had not considered**: `fix_rate` counts commits whose SUBJECT
matches fix-words, and fixes in high-churn refactored files are more likely to be folded into
"Refactor to use new API" than labelled "Fix X". That undercounts fixes in exactly the high-drift
group, and could produce the observed direction on its own. Unverified, and recorded as a claim to
check rather than a finding.

### The rule this leaves

**Before arguing that a defect does not change your conclusion, measure the thing your argument
assumes.** Mine assumed independence between a denominator and its numerators — one correlation
each, thirty seconds, and I wrote a paragraph instead.

**Mechanism now: NO**, and the honest reason is that no guard can read an argument for an unstated
assumption. What is available is cheaper and was not used: **put the finished document to a judge of
a different family and tell it to attack.** `docs/product/QUANTAMIND.md` already requires that of
every published model finding. It was not being required of our own research.

---

## Adding an entry

Add one when a claim in this repository — a comment, an amendment, a docstring, a
citation, a test name — turns out not to have been backed by what it asserted. Not for
ordinary bugs. The distinguishing mark is that **something stated a property and nothing
held it**, so the reader had no way to tell from the artefact alone.

Fill the mechanism column honestly, including "NO". An entry claiming coverage it does not
have would be an instance of the class it is filed under.
