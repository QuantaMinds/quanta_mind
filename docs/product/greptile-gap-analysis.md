# Why Greptile beats us — the gap, measured

**The question:** Greptile leads us by 12.9 precision points on Martian's offline layer,
p = 0.0228. The hypothesis put to me was that they index the whole repository first and we read
one diff. **This is what the data says, and the hypothesis is not what it shows.**

Artefacts: `research/phase0/bench/gap_detail.json`, `analyze_gap.py`. Both arms re-judged
per-issue against the same 173 golden comments on the same 50 pull requests, one judge.

---

## The four cells

| | issues | share |
|---|---|---|
| caught by **both** | 52 | 30.1% |
| **only Greptile** | 38 | 22.0% |
| **only us** | 29 | 16.8% |
| **neither** | 54 | 31.2% |

**Net gap: 9 issues out of 173.** Not a class difference — a 5-point difference in coverage of one
curated list.

**The overlap is 43.7% (Jaccard).** We are not a worse version of Greptile; **we are finding
substantially different things.** Together we cover **68.8%** of the golden set against Greptile's
**52.0%** alone — above the ~63% ceiling no single tool on this benchmark has passed.

---

## The gap is at the BOTTOM of the severity scale, not the top

| severity | n | both | only THEM | only US | **net** |
|---|---|---|---|---|---|
| Critical | 12 | 5 | 2 | 1 | −1 |
| **High** | **54** | **22** | **10** | **10** | **0** |
| Medium | 61 | 19 | 14 | 12 | −2 |
| **Low** | **46** | **6** | **12** | **6** | **−6** |

**On High-severity issues we are exactly even — ten each.** Two-thirds of the entire gap is
**Low** severity.

**This is the single most important row in the analysis.** Whatever Greptile's index buys them, it
is not buying serious defects we are missing.

---

## By category — and we win on security

| category | n | both | only THEM | only US | **net** |
|---|---|---|---|---|---|
| bug | 94 | 32 | 20 | 15 | −5 |
| **style** | **10** | **1** | **5** | **0** | **−5** |
| perf | 6 | 2 | 2 | 0 | −2 |
| data | 7 | 1 | 2 | 1 | −1 |
| doc_defect | 9 | 0 | 2 | 1 | −1 |
| speculative | 5 | 0 | 2 | 1 | −1 |
| api | 13 | 7 | 1 | 2 | +1 |
| concurrency | 14 | 8 | 2 | 3 | +1 |
| test_gap | 4 | 0 | 0 | 1 | +1 |
| **security** | **11** | **1** | **2** | **5** | **+3** |

**We find more than twice as many security issues as Greptile does on this corpus** — 5 to 2
uniquely, and security is the category where cross-file reasoning is supposedly most needed.

**We find zero of ten style issues. They find five.**

---

## The mechanism: we told our own reviewer not to look

`research/phase0/bench/reviewer.py` instructs the model:

> *"Do not report style, formatting, naming, test coverage or documentation unless the change is
> actually incorrect."*

Splitting the golden set by whether our own prompt bans the category:

| | golden comments | only THEM | only US | **net** | **deficit rate** |
|---|---|---|---|---|---|
| **banned by our prompt** (style, doc_defect, test_gap, speculative) | 28 | 9 | 3 | **−6** | **−21%** |
| allowed by our prompt | 145 | 29 | 26 | **−3** | **−2%** |

**Our deficit rate is ten times higher in the categories we instructed the model to skip.**
**Two-thirds of the total gap comes from 16% of the golden comments** — the ones we opted out of.

This is a **configuration choice, not a capability gap.** It is also a choice made for a reason:
Martian's golden set counts a CSS lightness value and a misspelled property name as issues a
reviewer should catch, and this project's position has been that a nit is not a finding.

---

## The indexing hypothesis does not survive

Two tests, both weak, both pointing the same way.

**Test one — does the golden comment name a symbol absent from the diff we supplied?**
Only 18 of 173 golden comments quote any identifier at all, so the marker barely applied.
**Reported as inconclusive rather than as support.**

**Test two — lexical markers for cross-file reasoning** (*caller, elsewhere, imported, usage, call
site, convention, codebase, defined in*):

| | n | only THEM | only US | **net** |
|---|---|---|---|---|
| cross-file wording | 18 | 4 | 1 | −3 |
| local-only wording (typo, naming, colour, comment) | 10 | 5 | 1 | −4 |
| neither marker | 145 | 29 | 27 | −2 |

**The gap is not concentrated in cross-file issues. It is marginally worse in issues that are
purely local** — typos and colour values, where a repository index is irrelevant.

**And the twelve issues Greptile caught that we missed, read verbatim, contain no cross-file
reasoning at all:** a misspelled `stopNotificiationsText`, an `end if` that is invalid ERB, a
theme colour changed from 30% to 70% lightness, a case-sensitive `indexOf`. Every one is decidable
from the diff alone.

### The strongest counter-evidence is CodeRabbit

**CodeRabbit also builds a full code graph** — plus 40+ linters and SAST tools, a per-review
microVM with the repository cloned, agentic codebase exploration, and a multi-LLM ensemble.

**It scores 36.5% precision. Our single prompt over a raw diff, with no repository access at all,
scores 43.6%.**

**Indexing the codebase is neither necessary nor sufficient for precision on this benchmark.**

---

## What Greptile actually built

From their own engineering writing:

**Indexing** — tree-sitter AST parse, then *recursively generated natural-language docstrings per
node*, then embeddings of the docstrings rather than of the code. Their measurement: query-to-code
cosine similarity 0.7280, query-to-natural-language 0.8152, and function-level chunks beat
file-level (0.768 against 0.718) because "adding noise dramatically reduces semantic similarity".

**Review (v3)** — an agentic loop, not a pipeline. Tools: codebase search, learned rules, **git
history**, file reading. Multi-hop: function → nested call → related implementation → historical
context. Reported +256% upvote/downvote ratio, +70.5% action rate, 75% lower inference cost on 3×
the context tokens through cache efficiency.

**Precision (the part that matters, and the part that cannot help them here)** — prompt
engineering failed; LLM-as-judge severity rating was "nearly random". What worked was a vector
filter: block a comment when cosine similarity exceeds a threshold against **≥3 unique downvoted
comments**, pass when similar to ≥3 upvoted, trained on upvotes, downvotes and *whether developers
addressed the comment in later commits*. Address rate **19% → 55%** in two weeks, partitioned per
team.

**That filter needs team feedback history, and the benchmark runs on fresh forks.** So Greptile's
56.5% offline precision is their graph and their agent — **not the mechanism they credit for their
real-world quality.**

**Note what they concluded independently of us:** prompt engineering could not separate good
comments from nits, and an LLM rating its own severity was near random. We measured the same two
failures — a rejection filter that moved nothing and a length gate at p = 0.281.

---

## What this means

**Closing the measured gap does not require an index.** It requires deciding whether to report
nits. Six of the nine issues are categories we suppressed on purpose, and turning them on is a
prompt change, not an architecture.

**But turning them on is exactly what Greptile spent an engineering programme learning to turn
off.** Their 19%→55% result is a filter that *removes* the comments this benchmark rewards. The
benchmark and the product pull in opposite directions, and optimising for the benchmark would walk
us into the problem they solved.

**Where we are already equal or ahead is where it counts** — even on High severity, ahead on
security, api, concurrency.

**And the union number is the commercially interesting one.** 68.8% together against 52.0% for
Greptile alone, at 43.7% overlap. **The tools are complementary, which is not what a 12.9-point
deficit sounds like.**

---

## What this analysis cannot say

**The cross-file test was inconclusive, not negative.** 155 of 173 golden comments quote no
identifier, so the mechanical marker never ran on them. A real test needs golden comments labelled
for cross-file dependence, which this dataset does not carry.

**Several cells are small.** style n = 10, security n = 11, perf n = 6. The severity table is the
robust one; single-category claims are directional.

**The gold set is Martian's own admission of incompleteness** — real issues scored as false
positives, so every arm's precision is understated.

**Our arm is the only one judged by its own model family** (Gemini reviewing, Gemini judging).
Self-preference would inflate our side of every table here.
