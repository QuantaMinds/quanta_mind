# Six blog posts, ready to publish

Written to be published in this order. Each names its target search, its claim, the data behind
it, and the citations — every one of which was checked against the source rather than recalled.

---

## The editorial line, which is the whole strategy

**We publish our negative results in full detail, and we decline to publish our positive one.**

That sounds backwards and it is deliberate:

- **A null costs nothing to give away.** It tells a competitor what does not work, which helps
  them, but it buys the only thing that is scarce in this market — a reason to believe anything
  else we say. Nobody else publishes a failed experiment.
- **A positive number invites a fight about method**, tells a competitor exactly what to
  optimise, and is one vendor's benchmark on one vendor's chosen corpus. It turns us into
  another row in a table of self-reported wins.
- **The reader gets their own number instead.** Every post ends by offering to run the same
  analysis on their repository. That is more persuasive than any figure we could print, and it
  gives away nothing.

**No post claims we find more bugs.** We do not, nobody has shown that anyone does, and the
first reader to test it would find out. Every post here is about *where attention goes* and
*what gets admitted*.

---

## Citation rules

This project has already had one fabricated statistic survive into a draft. So:

- **Link the primary source, never a summary of it.** No citing a blog that cites a paper.
- **Quote the number the paper actually reports**, with its sample size.
- **Vendor benchmarks are marketing and are cited as marketing**, including when they flatter
  us. Every "independent benchmark" in this market so far ranks its publisher first.
- **If a claim cannot be sourced, it is cut**, not softened.

---

# Post 1 — We tested five ways to predict which changes break. Four found nothing.

**Target search:** `predicting which pull requests cause bugs`, `code review risk signals`
**Length:** ~1,400 words · **Publish first.** This is the post that makes the other four
credible.

### The hook

Every code quality vendor publishes what worked. We are going to publish what did not — because
it is the more useful half, and because without it you have no way to calibrate the rest.

### The body

Each null as: what we expected, what we measured, what came back.

| Signal tested | Expectation | Result |
|---|---|---|
| **Gate merges on static-analysis coverage** | Poorly-covered changes break more | **Null.** Relative risk 0.916, 95% CI [0.557, 1.505], Fisher p = 0.746, n = 211. Held changes broke at 22.11%, passed ones at 24.14% — while the gate fired on **45% of pull requests** |
| **Exposure to unresolvable call sites** | Code the analyser cannot follow is riskier | **Null.** RR 1.040, cluster-robust CI [0.598, 1.890], 310 pull requests |
| **"You forgot to change file X"**, from co-change history | Missing companion edits cause breakage | **Dead.** Fired on 8 genuine breakages and named the right file **0 times** |
| **Test-coverage gap** | Untested changes break more | **Null, and reversed.** Changes touching no test broke *less* (RR 0.91 and 0.76) |
| **Ten pull-request metadata signals** | Some combination predicts risk | **Nothing survived Bonferroni correction.** Only diff size replicated, at RR ≈ 2.1 — and every competitor already gates on it |

### The part that makes it worth reading

**A gate that fires on 45% of pull requests and discriminates on none of them is worse than no
gate.** It costs every team the same friction and returns nothing — and because that is
uncomfortable to admit, it stays in the product.

Then the honest close: a fifth signal did work, and **we are not printing its number here.**
Say why plainly — it would be our benchmark on our corpus, which is worth close to nothing to a
sceptical reader. Offer the report instead.

### Carry the caveats the source carries

The coverage-gate interval is **naive Katz and Fisher exact, not cluster-robust**, across 211
pull requests. The exposure interval is cluster-robust across 310. **Say which is which in the
post.** A null published without its own limitations is the same overclaim as a positive result
published without them, and this post's entire value is that it does not do that.

### Citations

- All figures are our own measurements. **Link the raw artefacts**, not a summary — the
  repository holds the input records behind the coverage-gate null.
- Include the measurement defects we found and withdrew, and link them. **The withdrawals are
  the credibility**, not a footnote.

### Do not add

The signal that worked, what it is built from, the unit it operates on, or the threshold rule.

---

# Post 2 — Your AI reviewer cannot tell you what it did not read

**Target search:** `what does ai code review miss`, `ai code review coverage`
**Length:** ~1,100 words · **The product argument. Publish second.**

### The hook

The scene from the home page, told once and briefly: nine files, four comments, nothing about
the function that broke two weeks later. The review never said that function was fine. It did
not mention it.

### The argument

**Silence carries two meanings and no reviewer separates them.**

*This is fine.* · *I did not really look here.*

Every tool in the category — CodeRabbit, Greptile, Bugbot, Copilot's reviewer — writes down what
it noticed and stays quiet about the rest. Not one publishes what it skipped.

**That is not laziness. It is uncomfortable.** A coverage line is a number that can only look
worse the more honestly you compute it, and no vendor wants the first line of their comment to
be an admission.

### The turn, which makes it a post rather than an advert

The problem is not that reviewers miss things. Everything misses things. It is that **an
unreadable silence forces the human to redo the work anyway.** You cannot act on "no comment",
so you open the file. You are paying for a reviewer and performing the review.

A coverage line is worth less than a finding on any single pull request, and worth more across a
hundred — because it is the only thing that tells you where your own attention should go.

### Citations

- **[GitHub Copilot code review documentation](https://docs.github.com/en/copilot/using-github-copilot/code-review/using-copilot-code-review)** — check the live page and quote its own stated limitations verbatim. A vendor documenting its own limits is the strongest support available for this argument.
- **[Bugs in Large Language Models Generated Code: An Empirical Study](https://arxiv.org/abs/2403.08937)** — 333 bugs across three LLMs, ten distinct bug patterns including *Missing Corner Case* and *Incomplete Generation*. Use for: the defects arriving now are not the ones a linter was built to catch.

### Do not add

Any figure for our own coverage percentage. It varies per repository, and quoting one invites an
argument about a number that was never meant as a benchmark.

---

# Post 3 — More comments is not more bugs

**Target search:** `ai code review too many comments`, `ai code review false positives`
**Length:** ~1,200 words

### The hook

Macroscope tested 118 real bugs across 45 repositories and published the table. It scored 48%
and placed itself first. Tenki ran 122 bugs and produced a completely different ranking —
CodeRabbit at 29% where Macroscope had it at 46%, Greptile at 36% where Macroscope had it at
24%. Greptile's own benchmark reports 82%.

**Every benchmark in this market is published by a company in it, and no two agree.** That is
not a scandal — it is a structural fact about who pays for benchmarks. But it means the numbers
being compared were chosen by the people being compared.

**And the bottom line nobody quotes: the best score any vendor claims for itself is 48%.**

### The argument

**Comment count is an input being reported as a result.**

A tool writing forty notes on a change has not found forty problems. It has written forty notes.
The industry reports what it can count instead of what matters, because counting defects
requires knowing which were real, and that requires waiting.

Then the part that makes the post honest rather than an attack: **we do not know that we find
more bugs than anyone else, and neither do they.** Published false-positive rates in this market
range from single to double digits depending entirely on who ran the test. No head-to-head study
exists that every vendor submitted to.

### The constructive half

If comment count is the wrong measure, propose better ones — and every one of these is a measure
the customer can take themselves:

1. **What share of comments did anyone act on?** Resolved and dismissed are both signals.
2. **What share of the change did the tool actually examine?** Nobody but us reports it.
3. **When something broke, had the reviewer commented where it broke?** Retrospective,
   checkable, and the only one that is about defects rather than about output volume.

### Citations

- **[Macroscope's benchmark](https://macroscope.com/content/best-ai-code-review-tools-github-2026)** — 118 self-contained runtime bugs, 45 repositories, 8 languages. Macroscope 48%, CodeRabbit 46%, Cursor Bugbot 42%, Greptile 24% (on 72 of 118; access revoked mid-run), Graphite Diamond 18%. Also records CodeRabbit at 10.84 comments per pull request, 4.69 runtime-relevant. **Published by a competing tool that ranked itself first — say so every time it is cited.**
- **[Tenki's benchmark](https://tenki.cloud/benchmarks/code-reviewer)** — 122 bugs, a different ranking: Greptile 36%, Cursor 32%, CodeRabbit 29%. Also a competing tool.
- **[Greptile's own benchmarks](https://www.greptile.com/benchmarks)** — 82% recall, two to three times every outside measurement of the same product.
- Also vendor-published and self-favouring: [DeepSource](https://deepsource.com/resources/ai-code-review-tools), [CodeAnt](https://www.codeant.ai/blogs/ai-code-review-benchmark-results-from-200-000-real-pull-requests), [Augment Code](https://www.augmentcode.com/guides/deep-code-review-recall-vs-precision). **Do not use any of these as evidence for a claim of ours** — the post's point is that none can carry that weight, including the ones that flatter us.
- **[Towards Understanding the Characteristics of Code Generation Errors Made by Large Language Models](https://arxiv.org/abs/2406.08731)** — 557 labelled errors across six LLMs on HumanEval. Finds a large share exhibit **complex semantic characteristics** rather than the subtle slips human programmers make. Use for: the errors arriving now are not the ones a rule-based checker was designed for.

### Do not add

Our own precision or recall figure. Publishing one puts us in the exact table this post exists
to criticise.

---

# Post 4 — The research on where bugs cluster is twenty years old. No reviewer uses it.

**Target search:** `defect prediction code review`, `which files are most likely to have bugs`
**Length:** ~1,300 words · **The most linkable post. Expect academic sharing.**

### The hook

In 2007, four researchers showed that faults do not arrive uniformly — they cluster, and a
project's own history predicts where. The work has been cited for nearly two decades.

**Not one AI code reviewer on the market reads a repository's history before deciding how hard
to read the diff.** They all read the whole change at one depth.

### The argument

Walk the literature honestly and give it full credit:

- **[Predicting Faults from Cached History](https://dl.acm.org/doi/10.1145/1342211.1342216)** — Kim, Zimmermann, Whitehead & Zeller, ICSE 2007. Analysed version history across **seven software systems**. The premise: *faults do not occur in isolation, but in bursts of related faults*. Caching the location of a fixed fault, locations changed alongside it, and recently changed locations lets a developer prioritise verification effort. [Full text](https://www.cs.ucdavis.edu/~devanbu/teaching/289/Schedule_files/Kim-Predicting.pdf).

Then the gap. This line of work aimed at **prioritising human and testing effort**. Nobody
retargeted it at the thing that now has a real marginal cost per unit of attention — a large
model reading a diff. When reading was free, reading everything was correct. Reading stopped
being free and the industry has not noticed.

### The turn

**Uniform depth is a choice, and it is wrong twice over.** It is where the bill comes from and
it is where the noise comes from, and both fall out of the same decision.

So the first question a reviewer should answer is not *"what is wrong with this code"* but
*"which part of this change deserves the expensive read"* — and there is twenty years of
evidence that the second question is answerable.

Close honestly: we built on this idea, it beats a non-informative baseline, **and the margin is
not printed here.** Run it on your own repository.

### Citations

- Kim et al., ICSE 2007, as above — **the anchor of the post**, quoted accurately with its
  seven-system sample.
- Optional second source: a well-cited follow-up on change-history defect prediction, **read in
  full before citing.** Do not cite a paper from its abstract.

### Do not add

Which signal we compute, over what window, at what granularity, or how the threshold is set.
The literature is public; our instantiation is not, and the post works without it.

---

# Post 5 — Everyone moved to per-review pricing in 2026. We are not going to.

**Target search:** `greptile pricing`, `ai code review pricing`, `cursor bugbot pricing`
**Length:** ~900 words · **Shortest and most shared. Publish last, once the others give it
standing.**

### The hook

In March 2026 Greptile began charging **$1 per review beyond 50 per seat**. In May, Cursor's
Bugbot moved to usage-based billing at roughly **$1–1.50 per run**. Two of the best-funded
reviewers in the market abandoned flat pricing within two months of each other.

That is not a coincidence and it is not greed.

### The argument

**A vendor whose cost rises with every review will eventually charge for every review.** If
reading a change costs real money each time, flat pricing is a bet against your own customers
using the product — and that is an unpleasant bet to hold.

Then the consequence, which is the reader's problem rather than the vendor's: **per-review
pricing prices the thing you want people to do.** A team that thinks twice before asking for a
review is a team getting less review. The billing model quietly argues against the product.

### Our position

Unlimited reviews on every paid plan at a flat seat price, **because our cost does not scale the
way theirs does.** We are not going to detail our cost structure on a public page — but we will
commit to the consequence, which is the only part that affects the reader.

And state the limit honestly: at extreme volume we ask you to bring your own model key. **That
is an upgrade, not a cap**, and it is better written down now than discovered at renewal.

### Citations

- **[Greptile's per-review pricing change](https://www.agent-wars.com/news/2026-05-01-greptile-per-review-pricing)** and [current plans](https://costbench.com/software/ai-code-review/greptile/) — $30/seat, 50 reviews included, $1 each after.
- **[Cursor Bugbot pricing](https://getoptimal.ai/blog/cursor-bugbot-pricing)** — usage-based from mid-2026, roughly $1–1.50 per run.
- **[CodeRabbit pricing](https://aicodereview.cc/blog/coderabbit-pricing/)** — $24 and $48 per developer per month, still per seat.
- **Re-check every one of these on the day of publishing.** Pricing pages change, and a stale
  figure in a post about someone else's pricing is the most embarrassing error available.

### Do not add

Our cost per review, how many model calls we make, or how the budget is split. The post works on
the consequence alone, and the mechanism is the part worth keeping.

---

# Post 6 — Four companies say they are number one on the same independent benchmark

**Target search:** `ai code review benchmark`, `coderabbit vs greptile vs qodo`, `best ai code
reviewer 2026`
**Length:** ~1,600 words · **This is the strongest post in the set. Publish it second, after
the nulls post has established that we publish inconvenient things.**

**Every figure below was read off the vendor's own live page. Re-read them before publishing —
these numbers move, and that is the point of the post.**

### The hook

Martian, a research lab, built the first genuinely independent benchmark for AI code review:
roughly **300,000 real pull requests**, scored on which comments developers actually acted on,
with the dataset, judge prompts and evaluation pipeline **open-sourced**.

It is the best thing that has happened to this market. And right now, four different companies
are each telling you they came first on it.

| Vendor | Their headline | Leaderboard date | Their F1 |
|---|---|---|---|
| [CodeRabbit](https://www.coderabbit.ai/blog/coderabbit-tops-martian-code-review-benchmark) | *"CodeRabbit tops the first independent AI code review benchmark"* | March 2026 | 51.2% |
| [Qodo](https://www.qodo.ai/blog/qodo-ranked-1-ai-code-review-tool-in-martians-code-review-benchmark/) | *"Qodo Ranked #1 AI Code Review Tool"* | — | 64.3% |
| [Greptile](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark) | *"Greptile Ranks #1 on Martian's AI Code Review Benchmark"* | 30 July 2026 | 60.8% |
| [cubic](https://www.cubic.dev/blog/cubic-is-the-best-ai-code-reviewer-on-martian-s-benchmark) | *"cubic is the #1 AI code reviewer on Code Review Bench"* | — | — |

**None of them is lying.** It is a rolling leaderboard. Each announced the week it led, and left
the announcement up.

That is worth sitting with. **Even with a genuinely independent, open-source, 300,000-pull-request
benchmark, a buyer comparing four vendors finds four number ones and no way to resolve them.**

### The number that appears in every one of those announcements and never in the headline

Read the second line of each.

**CodeRabbit's number-one announcement reports recall of 53.5% and precision of 49.2%.**

**Greptile's number-one announcement reports recall of 50.6%.**

So the tool at the top of the most credible benchmark in this market — in its own celebratory
blog post — **catches about half of what developers cared about.** And in CodeRabbit's case
roughly half the comments it wrote were not ones developers acted on.

Nobody is hiding this. It is in the announcements. It is simply never the sentence in bold.

### Before Martian, everyone marked their own paper

Worth showing, because it explains why Martian mattered and why it did not fix the problem:

| Benchmark | Published by | Sample | Who won |
|---|---|---|---|
| [Greptile's](https://www.greptile.com/benchmarks) (July 2025) | Greptile | **50 bugs, 5 repos** | Greptile 82%, Bugbot 58%, Copilot 54%, CodeRabbit 44%, Graphite 6% |
| [Macroscope's](https://macroscope.com/content/best-ai-code-review-tools-github-2026) | Macroscope | 118 bugs, 45 repos | Macroscope 48%, CodeRabbit 46%, Bugbot 42%, Greptile 24%, Graphite 18% |
| [Tenki's](https://tenki.cloud/benchmarks/code-reviewer) (May 2026) | Tenki | 122 bugs, 5 repos | Tenki 68.9%, Devin 36.1%, Greptile 36.1%, Cursor 32%, CodeRabbit 28.7%, Graphite 3.3% |

**Every one is published by a tool in the ranking, and every one puts its publisher first.**

Follow a single product across the three. **Greptile scores 82% on its own benchmark, 36.1% on
Tenki's, and 24% on Macroscope's.** CodeRabbit scores 46%, 44% and 28.7% depending on whose test
it is sitting. Graphite scores 18%, 6% and 3.3%.

And note Greptile's headline rests on **50 bugs across 5 repositories** — a sample small enough
that a handful of cases moves it several points.

### What the research says about why this is the wrong race

Two things, both older than any of these products.

**Noise is what kills analysis tools, not weak detection.** Bessey and colleagues at Coverity
wrote up a decade of selling static analysis to roughly 700 customers in
[*A Few Billion Lines of Code Later*](https://cacm.acm.org/research/a-few-billion-lines-of-code-later/)
(CACM, 2010). The commercial lesson was not that the tool needed to find more. It was what false
positives did to adoption. **A precision figure near 50% is the exact condition that paper warns
about**, arriving twenty-six years later with a different label on the box.

**The defects arriving now are not the kind more rules will catch.** Two empirical studies:
[557 labelled errors across six LLMs](https://arxiv.org/abs/2406.08731) finds a large share
exhibit *complex semantic characteristics* rather than the subtle slips human programmers make;
[333 bugs across three LLMs](https://arxiv.org/abs/2403.08937) gives ten patterns including
*Missing Corner Case* and *Incomplete Generation*. These are judgement calls, and judgement is
where a reviewer is least reliable and most confident.

### The pain point they are all selling against is not the one you have

**Every product in that table is marketed on detection** — catch more, catch it earlier, catch
what humans miss. That is the race, and by the leaders' own published figures it is being run at
around 50% recall by everybody.

**The pain you actually have is different.** When a reviewer with 50% recall says nothing about
a file, you cannot tell whether it checked and cleared it or never really looked. At that hit
rate, silence is wrong about as often as it is right.

**So you open the file and read it yourself.** The tool has not removed the work on the part that
mattered. You are paying for a reviewer and performing the review — and adding a sixth tool at
55% recall does not change that arithmetic at all.

### What we found, and what we do about it

We are not entering the detection race. We have no evidence we would win it, nobody has shown
anyone wins it, and the table above is what winning looks like.

**We tested five ways to predict which changes break, and four returned nothing** — a
static-analysis coverage gate at relative risk 0.916 while firing on 45% of pull requests, an
exposure signal at 1.040, a co-change localiser that fired on eight real breakages and named the
right file zero times, and a test-coverage gap that pointed the wrong way. Those are in
[the nulls post](#), with intervals and sample sizes.

The one thing we do that nobody in that table does: **we publish what we did not examine.**

```
Checked      2 files · 3 functions
Not checked  1 file — generated · 4 call sites — could not resolve
```

**That does not fix the 50%. It makes it addressable.** Where we say *checked*, you stop
re-reading. Where we say *not checked*, that is yours, named, before you merge rather than after
something breaks.

A reviewer that misses half and tells you which half it looked at is a tool. One that misses half
and stays quiet about where is a coin toss with a subscription.

### The close

We are not going to publish our own benchmark. On the evidence above, one more vendor-run
number would be worth nothing — and the honest version of this post cannot end by doing the
thing it spent 1,500 words criticising.

Run it on your own repository instead. We replay your last six months and show you where we
would have pointed.

### Citations, all verified live

Every link above was read from the live page while writing. **Re-verify on the day of
publishing**: the Martian leaderboard moves, and a post about other people's moving numbers is
the worst possible place to carry a stale one.

### Do not add

Our own recall, precision or F1. The entire argument is that another self-reported number is
worthless — printing one would be the post refuting itself.


---

# Publishing notes

**One post a month, in this order.** Six honest posts build more than twenty filler pieces, and
this order earns credibility before it makes an argument. **Post 6 is the strongest and goes
second**, once Post 1 has established that we publish inconvenient things about ourselves.

**Every post ends with the same offer, in the same words:** *we do not publish a benchmark. Give
us a repository and we will run it on your own history.*

**Post 1 goes to Hacker News. Nothing else does.** A null-results post from a vendor is the only
item here with a real chance on that audience, and submitting the others burns the goodwill it
earns.

**Before any post ships, re-read the withheld list at the end of `WEBSITE.md`.** Four of these
five sit close to it. Post 4 sits closest — it describes the research the approach is built on,
which is public, while the instantiation is not.

**Nothing here claims we find more bugs.** An edit that introduces that claim is a wrong edit.
