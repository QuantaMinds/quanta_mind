# Four companies say they are number one on the same benchmark

*Published [DATE]. Every figure below was read from the vendor's own live page. Links go to the
source, not to a summary of it.*

---

Martian, a research lab, built the first genuinely independent benchmark for AI code review.
Roughly 300,000 real pull requests. Scored not on whether a comment sounded clever, but on
whether developers actually acted on it. The dataset, the judge prompts and the evaluation
pipeline are open source.

It is the best thing that has happened to this market.

Right now, four different companies are each telling you they came first on it.

| Vendor | Their headline | Leaderboard date | F1 |
|---|---|---|---|
| [CodeRabbit](https://www.coderabbit.ai/blog/coderabbit-tops-martian-code-review-benchmark) | *"CodeRabbit tops the first independent AI code review benchmark"* | March 2026 | 51.2% |
| [Qodo](https://www.qodo.ai/blog/qodo-ranked-1-ai-code-review-tool-in-martians-code-review-benchmark/) | *"Qodo Ranked #1 AI Code Review Tool"* | — | 64.3% |
| [Greptile](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark) | *"Greptile Ranks #1 on Martian's AI Code Review Benchmark"* | 30 July 2026 | 60.8% |
| [cubic](https://www.cubic.dev/blog/cubic-is-the-best-ai-code-reviewer-on-martian-s-benchmark) | *"cubic is the #1 AI code reviewer on Code Review Bench"* | — | — |

None of them is lying.

It is a rolling leaderboard. Each company announced during the week it led, and left the
announcement up. Every one of those posts was true on the day it was written.

Sit with that for a second. We finally have an independent, open-source, 300,000-pull-request
benchmark — the thing this market genuinely needed — and a buyer comparing four vendors still
finds four number ones and no way to tell which is current.

## The number that is in every one of those posts and never in the headline

Read the second line of each announcement.

**CodeRabbit's number-one post reports recall of 53.5% and precision of 49.2%.**

**Greptile's number-one post reports recall of 50.6%.**

So the tool sitting at the top of the most credible benchmark in this market — in its own
celebratory blog post — catches about half of what developers cared about. In CodeRabbit's case,
about half the comments it wrote were not ones developers acted on.

Nobody is hiding this. It is right there in the announcements, in the tables, under the
headline. It is simply never the sentence anybody bolds.

## Before Martian, everyone marked their own paper

This is worth showing, because it explains why Martian mattered — and why it did not fix the
problem.

| Benchmark | Published by | Sample | Result |
|---|---|---|---|
| [Greptile's](https://www.greptile.com/benchmarks) (July 2025) | Greptile | 50 bugs, 5 repos | Greptile 82%, Bugbot 58%, Copilot 54%, CodeRabbit 44%, Graphite 6% |
| [Macroscope's](https://macroscope.com/content/best-ai-code-review-tools-github-2026) | Macroscope | 118 bugs, 45 repos | Macroscope 48%, CodeRabbit 46%, Bugbot 42%, Greptile 24%, Graphite 18% |
| [Tenki's](https://tenki.cloud/benchmarks/code-reviewer) (May 2026) | Tenki | 122 bugs, 5 repos | Tenki 68.9%, Devin 36.1%, Greptile 36.1%, Cursor 32%, CodeRabbit 28.7%, Graphite 3.3% |

Every one of these is published by a tool that appears in its own ranking. Every one puts its
publisher first.

Follow a single product across all four measurements. Greptile scores **82%** on its own
benchmark, **50.6%** on Martian's, **36.1%** on Tenki's, and **24%** on Macroscope's. CodeRabbit
scores 46%, 44%, 28.7% and 53.5% depending on whose test it is sitting.

And notice the sample behind that 82%: fifty bugs across five repositories. A handful of cases
moves a number like that several points in either direction. That is not dishonesty — it is
what a small sample does, and it is why in-house benchmarks should be read as a starting point
rather than a finding.

## Why "catch more bugs" is the wrong race

Two pieces of research, both older than any product in that table.

**Noise is what kills analysis tools. Not weak detection.**

In 2010, Al Bessey and colleagues at Coverity published
[*A Few Billion Lines of Code Later*](https://cacm.acm.org/research/a-few-billion-lines-of-code-later/)
in *Communications of the ACM* — a write-up of a decade spent selling static analysis to around
700 customers and analysing billions of lines of code. The lesson they came away with was not
that the tool needed to find more. It was what false positives did to whether anyone kept using
it at all.

A precision figure near 50% is precisely the condition that paper warns about. It has arrived
sixteen years later wearing a different label.

**And the defects showing up now are not the kind more rules will catch.**

Two empirical studies of LLM-generated code:
[557 labelled errors across six models](https://arxiv.org/abs/2406.08731) finds a large share
exhibit *complex semantic characteristics* rather than the subtle slips human programmers make.
[333 bugs across three models](https://arxiv.org/abs/2403.08937) sorts them into ten patterns,
including *Missing Corner Case* and *Incomplete Generation*.

Those are judgement calls. Judgement is where a reviewer is least reliable and most confident.

## The pain point they are all selling against is not the one you have

Every product in that table is marketed on detection. Catch more. Catch it earlier. Catch what
humans miss. That is the race, and by the leaders' own published figures, everybody is running
it at around 50% recall.

Your actual problem is different, and you have probably never seen it written down.

When a reviewer with 50% recall says nothing about a file, you cannot tell which of two things
happened. It read the file and found nothing wrong. Or it never really looked there.

At that hit rate, silence is wrong about as often as it is right.

So you open the file and read it yourself. Which means the tool has not removed the work on the
part that actually mattered — you are paying for a reviewer and performing the review.

Adding a sixth tool at 55% recall does not change that arithmetic at all.

## What we did about it, and what we found on the way

We are not entering the detection race. We have no evidence we would win it, nobody has shown
that anyone wins it, and the table above is what winning currently looks like.

What we did instead was test whether the risk in a change is predictable before anyone reads it.
Mostly, it is not. Five signals, four of them dead:

- **Gating merges on static-analysis coverage.** Relative risk 0.916, 95% CI [0.557, 1.505],
  Fisher p = 0.746, n = 211. Held changes broke at 22.11%, passed ones at 24.14% — while the gate
  fired on 45% of pull requests. A gate that stops nearly half your merges and discriminates on
  none of them is worse than no gate.
- **Exposure to call sites the analyser cannot resolve.** RR 1.040, cluster-robust CI
  [0.598, 1.890], 310 pull requests.
- **"You forgot to change file X", from co-change history.** Fired on 8 genuine breakages. Named
  the right file 0 times.
- **Test-coverage gap.** Null, and reversed — changes touching no test broke *less*.

The fifth signal worked. We are not going to print its number here, and the reason is the whole
point of this post: it would be our benchmark, on our corpus, marked by us. You have four of
those in the table above already.

What we ship instead is the thing nobody in that table ships. Every review ends with what we did
**not** examine:

```
Checked      2 files · 3 functions
Not checked  1 file — generated · 4 call sites — could not resolve
```

That does not fix the 50%. Nothing on the market fixes the 50%. It makes it *addressable*.
Where the review says *checked*, you stop re-reading. Where it says *not checked*, that part is
yours — named, specifically, before you merge rather than after something breaks.

A reviewer that misses half the bugs and tells you which half it looked at is a tool you can
build a process around. One that misses half and stays quiet about where is a coin toss with a
subscription.

## One last thing

We are not going to publish our own benchmark.

On the evidence above, one more vendor-run number would be worth approximately nothing — and
this post cannot honestly end by doing the thing it just spent fifteen hundred words describing.

So: give us one repository, read access only. We will replay your last six months of merged
pull requests and show you, change by change, where we would have pointed and whether a later
fix landed there.

You will not be reading our benchmark. You will be reading your own history.

**[ Run it on your last six months ]**

---

*Corrections and disagreements: info@quantamind.co. If any figure here is out of date we would
rather hear it from you than leave it up — the leaderboard moves, which is rather the point.*
