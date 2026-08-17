# Why Greptile beats us — the gap, measured

**The question:** Greptile leads us by 12.9 precision points on Martian's offline layer,
p = 0.0228. The hypothesis put to me was that they index the whole repository first and we read
one diff. **This is what the data says, and the hypothesis is not what it shows.**

Artefacts: `research/phase0/bench/gap_detail.json`, `analyze_gap.py`, `blind_score.py`.

---

## READ THIS FIRST — our arm is judged by its own model family, and the correction runs against us

**Our reviewer is Gemini. Our judge is Gemini. Greptile's and CodeRabbit's candidates were written
by other systems.** That is not a symmetric limitation. It pushes one way and it touches **every
table below**.

No non-Gemini model is reachable on this Vertex project — Anthropic, Meta and Mistral publishers
all return 404 — so the check is the pattern this project already uses in
`research/phase0/vertex/rater2`..`rater6`: blind markdown chunks rated outside the family, arm key
in a separate file. **40 of the 67 discordant issues, 20 per arm, seed fixed.** Every item was
scored MATCH by the Gemini judge, so a hand "no" is its false positive.

| arm | n | upheld | over-matched | rate |
|---|---|---|---|---|
| **OURS** | 20 | 17 | **3** | **15.0%** |
| THEIRS | 20 | 19 | 1 | 5.0% |

**+10.0 points, Fisher exact p = 0.605. Directionally self-preference; three events against one,
so far too underpowered to assert.**

**What it does to the headlines, at the point estimate:**

| | as measured | corrected |
|---|---|---|
| **High-severity net** | **0 — "dead even"** | **−1.0** |
| net gap | −9 | −11.5 |
| our precision | 43.6% | **37.1%** |
| CodeRabbit | 36.5% | 36.5% |

**The response is to downgrade the claims, not to publish corrected numbers.** "Even on High
severity" was never robust to a judge asymmetry of a size this run cannot exclude. **"At level with
CodeRabbit" survives. Everything stronger does not.**

**The one finding this does NOT touch is the prompt-ban result below**, because that compares our
arm against itself across a boundary we drew in our own prompt — self-preference applies equally on
both sides of it.

---

## The four cells

| | issues | share |
|---|---|---|
| caught by **both** | 52 | 30.1% |
| **only Greptile** | 38 | 22.0% |
| **only us** | 29 | 16.8% |
| **neither** | 54 | 31.2% |

**Net gap: 9 issues out of 173**, before the correction above; ~11.5 after it.

**The overlap is 43.7% (Jaccard).** We are not a worse version of Greptile; **we find substantially
different things.**

---

## The gap is at the BOTTOM of the severity scale

| severity | n | both | only THEM | only US | net | corrected net |
|---|---|---|---|---|---|---|
| Critical | 12 | 5 | 2 | 1 | −1 | −1.0 |
| **High** | **54** | 22 | 10 | 10 | **0** | **−1.0** |
| Medium | 61 | 19 | 14 | 12 | −2 | −3.1 |
| **Low** | **46** | 6 | **12** | 6 | **−6** | **−6.3** |

**Two-thirds of the gap is Low severity, and that holds under the correction.** The High-severity
row does not survive it — "ten each" becomes roughly −1, which is a downgrade from *even* to
*indistinguishable*.

---

## By category

| category | n | both | only THEM | only US | net |
|---|---|---|---|---|---|
| bug | 94 | 32 | 20 | 15 | −5 |
| **style** | **10** | 1 | **5** | **0** | **−5** |
| perf | 6 | 2 | 2 | 0 | −2 |
| data | 7 | 1 | 2 | 1 | −1 |
| doc_defect | 9 | 0 | 2 | 1 | −1 |
| speculative | 5 | 0 | 2 | 1 | −1 |
| api | 13 | 7 | 1 | 2 | +1 |
| concurrency | 14 | 8 | 2 | 3 | +1 |
| test_gap | 4 | 0 | 0 | 1 | +1 |
| security | 11 | 1 | 2 | 5 | +3 |

**Cells of 4–14 are directional only.** The security row (+3 on n = 11) is the kind of result this
project has learned not to lead with, and the self-preference correction eats most of it.

---

## The mechanism: we told our own reviewer not to look

`research/phase0/bench/reviewer.py` instructs the model:

> *"Do not report style, formatting, naming, test coverage or documentation unless the change is
> actually incorrect."*

| | golden comments | only THEM | only US | net | **deficit rate** |
|---|---|---|---|---|---|
| **banned by our prompt** (style, doc_defect, test_gap, speculative) | 28 | 9 | 3 | −6 | **−21%** |
| allowed by our prompt | 145 | 29 | 26 | −3 | **−2%** |

**Our deficit rate is ten times higher in the categories we instructed the model to skip.
Two-thirds of the total gap comes from 16% of the golden comments** — the ones we opted out of.

**This is the load-bearing finding, and it is the one least dependent on the judge.** Both sides of
the ban line are our own arm, scored by the same judge, so self-preference cancels.

**It is a configuration difference, not a capability gap.**

### The rule that follows

**Greptile spent an engineering programme learning to suppress exactly the comments this benchmark
rewards.** Their published quality result is a vector filter that blocks a comment when it
resembles ≥3 downvoted ones — address rate **19% → 55%** in two weeks. That filter exists to delete
nits.

> **This benchmark's gold set and the product goal are anti-correlated on nits. Benchmark position
> is therefore not a product target, and closing this gap by turning nits on would walk us into the
> problem Greptile already solved.**

---

## The indexing hypothesis does not survive — but the disproof is weaker than the finding

**Test one — does the golden comment name a symbol absent from the diff we supplied?**
Only 18 of 173 golden comments quote any identifier, so the marker barely applied.
**Reported as inconclusive, not as support.**

**Test two — lexical markers for cross-file reasoning** (*caller, elsewhere, imported, usage, call
site, convention, codebase, defined in*):

| | n | only THEM | only US | net |
|---|---|---|---|---|
| cross-file wording | 18 | 4 | 1 | −3 |
| local-only wording (typo, naming, colour) | 10 | 5 | 1 | −4 |
| neither marker | 145 | 29 | 27 | −2 |

**The gap is not concentrated in cross-file issues; it is marginally worse in purely local ones.**

**The strongest evidence is reading the missed issues.** The twelve Greptile caught and we did not
include a misspelled `stopNotificiationsText`, an `end if` that is invalid ERB, a theme colour
changed from 30% to 70% lightness, and a case-sensitive `indexOf`. **Every one is decidable from
the diff alone.** That is better evidence than either lexical test.

### What the CodeRabbit comparison does and does not prove

**CodeRabbit also builds a full code graph** — plus 40+ linters and SAST tools, a per-review
microVM with the repository cloned, agentic exploration, and a multi-LLM ensemble. It scores
**36.5%** on the offline layer; we score **43.6%** (37.1% corrected) with no repository access.

**This establishes that indexing is not SUFFICIENT for precision. It does not establish that
indexing is unnecessary** — two systems differing in everything is a single comparison, and our
number carries the self-preference inflation while theirs does not.

### Which benchmark layer each number comes from

**These are two different measurements and must never be quoted side by side:**

| layer | question asked | CodeRabbit | Greptile |
|---|---|---|---|
| **offline** (used throughout this document) | does the comment match a human-verified issue in a fixed 50-PR gold set? | **36.5%** | 41.5–56.5% by version |
| **online** (the public leaderboard) | did a developer change the code after the comment, on live PRs? | 49.2% *(Jan–Feb 2026)* | 76.2% *(30 Jul 2026)* |

**Every figure in this document is offline.** The apparent contradiction between 36.5% and 49.2% is
two layers and two dates, not a discrepancy.

---

## What Greptile actually built

**Indexing** — tree-sitter AST parse, then recursively generated natural-language docstrings per
node, then embeddings of the docstrings rather than of the code. Their measurement: query-to-code
cosine similarity 0.7280 against query-to-natural-language 0.8152, and function-level chunks beat
file-level (0.768 against 0.718) because "adding noise dramatically reduces semantic similarity".

**Review (v3)** — an agentic loop rather than a pipeline. Tools: codebase search, learned rules,
**git history**, file reading. Multi-hop: function → nested call → related implementation →
historical context. Reported +256% upvote/downvote ratio and +70.5% action rate.

**Precision** — prompt engineering failed; LLM-as-judge severity rating was "nearly random". The
vector filter described above is what worked. **It needs team feedback history and the benchmark
runs on fresh forks, so it cannot be helping them here** — their offline number is graph and agent.

**They reached two of our conclusions independently:** prompt engineering could not separate
findings from nits, and an LLM rating its own severity was near random. We measured the same two
nulls — a rejection filter that moved nothing and a length gate at p = 0.281.

---

## The 43.6% here against 5.80% under our own adjudication

**A reader will notice the order of magnitude and ask which one describes our reviewer. Both do,
and they answer different questions.**

- **Martian's judge asks:** does this comment match an issue on a curated human list?
- **Our adjudication asked:** is this claim **true of the code AND anchored to the line it cites**?

**87.3% of our claims fail the second condition, and this benchmark never tests it.** Different
corpus too — Python functions against Java/Go/TypeScript/Ruby diffs — and a different task.

**Neither number corrects the other. What follows is narrower: 5.80% should never have been placed
beside the industry's published figures**, because those are measured the lenient way and ours was
measured the strict way. That comparison ran through this project's reasoning for months.

---

## The union result — parked, not claimed

**68.8% of the golden set is found by at least one of us, against 52.0% for Greptile alone, at
43.7% overlap** — above the ~63% ceiling no single tool of 48 has passed.

**That is an argument for complementarity, and this company does not ship findings.** The review
half stopped at 5.80% correct under our own adjudication. So the union result describes a product
we decided not to build, and it cannot sit here as an uncommitted claim.

**It goes to the parked-hypotheses list with a pre-registration**, alongside model-confusion-as-
defect-locator and the cold-start hypothesis. **The bar it must clear is not a benchmark score.**
A complementarity product publishes findings, so it must first clear the bar the review half
failed seven times: **under 50% of published findings wrong under adjudication that checks anchors.**

**And it may simply be an artefact.** The self-preference correction removes roughly 4 of our 29
unique catches; a second judge outside the Gemini family could remove more.

---

## What this analysis cannot say

**The cross-file test was inconclusive, not negative.** 155 of 173 golden comments quote no
identifier, so the mechanical marker never ran on them. A real test needs golden comments labelled
for cross-file dependence, which this dataset does not carry.

**Several cells are small** — style n = 10, security n = 11, perf n = 6. The severity table is the
robust one; single-category claims are directional.

**Martian's gold set is incomplete by their own account** — real issues scored as false positives —
so every arm's precision is understated and every arm's recall overstated.

**The self-preference measurement is itself underpowered** at three events against one, p = 0.605.
It is enough to downgrade a claim and not enough to quantify a correction.
