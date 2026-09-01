# Telling the model what the change looks like — NULL. The effect is smaller than the noise.

> **DECIDED 2026-08-30: THE CONTEXT STAYS IN THE PROMPT, AND THIS NULL DOES NOT ARGUE OTHERWISE.**
> What was measured is one thing — whether shape context lifts DEFECT DETECTION against a golden
> set — and it does not, by less than the instrument's own wobble. What the context is FOR is
> another: the prompt is structured as facts about the change, in the conversational form the
> product uses on every pull request, and the shape line is one of those facts. A null on
> detection lift is not a licence to stop telling the model what the change looks like.
>
> Recorded because this file was read twice as "remove it" — once from a stale memory that had it
> as a PASS, once from the null. Neither reading was the decision, and now there is one.

> **NULL. Do not cite the +5.2 headline; it was noise clearing a bar set below the noise.**
> A same-arm replicate — two runs with no context on either side — landed **7 defects apart**. The
> shape effect was 9 defects, then 6 on re-judging. **One of the no-context runs scored 91, beating
> the 90 that the treated arm scored.** The pre-registered bar was +2.1 points; the floor is at
> least 4.0.

Pre-registered in `research/phase0/bench/forensic/shape_context.py` before any model call. Fifty
golden changes across five repositories, two arms, the same judge and the same 173 human-verified
defects on both.

## The three measurements, in the order they arrived

| | PLAIN | WITH_SHAPE | difference |
|---|---|---|---|
| first judging | 81 | **90** | +9 (**+5.2 points**) — cleared both bars |
| re-judge, same comments | 81 | **87** | +6 (**+3.5 points**) |
| **same-arm replicate** | **91 / 84** | — | **±7 (±4.0 points) from nothing at all** |

**The effect is smaller than the instrument's own wobble.** And `PLAIN_A` scored **91** — higher
than WITH_SHAPE's 90 in the run that produced the headline. A no-context arm beat the treated arm
inside the same experiment.

### The paired statistic said so first

```
both arms found      72        McNemar b:c = 9:15
PLAIN only    (b)     9        exact two-sided p = 0.31
WITH_SHAPE only (c)  15
neither              77
```

### And the effect was one repository

| repository | plain → shape | of | discordant b:c |
|---|---|---|---|
| cal.com | 22 → **28** | 41 | 2:8 |
| discourse | 22 → **24** | 41 | 1:3 |
| grafana | 14 → **12** | 25 | 2:0 |
| keycloak | 12 → 12 | 30 | 2:2 |
| sentry | 11 → 11 | 36 | 2:2 |

Two of five improve, one worsens, two are flat at the defect level. Remove cal.com and nothing
remains. The ranker claim this company rests on is 6 of 6 positive.

## Where the noise comes from, per change

Two identical runs, no context either side, 46 changes reviewed twice:

- mean disagreement **0.76 comments** per change, maximum **4**
- run A higher on 10, run B higher on 11, equal on 25
- one sentry change drew **2 comments in one run and 6 in the other**

Total volume barely moved — 221 against 224 — but **which** comments appear moves a great deal, and
defects found is computed from exactly those comments. That is the mechanism.

## Why the bar did not catch it

**The 2.1-point bar was the JUDGE's replicate spread: re-scoring the same outputs.** It never
included generation variance, which this measures at roughly double. So the bar sat below the noise
it existed to exclude, and a run in which nothing happened could clear it. One did.

**This is a corpus finding, not a shape finding, and it travels.** Any arm scored on this 50-change
corpus against a bar under about 4 points has the same problem — including results recorded as
SOUND. → `docs/findings/reviewer/corpus-noise-floor.md`.

## What survives

**The volume result.** 210 → 206 comments while the arms stayed matched change by change: shape
emitted more on 19, fewer on 20, level on 11, median delta zero. Nothing here was bought by talking
more — unlike the nits-on arm in `greptile-gap-analysis.md`, which bought +14 F1 with 270 extra
comments at 8.1% marginal precision. **That is a fact about how the arm behaved, not evidence that
it worked.**

**The instrument is sound now**, and its seven defects were all attenuating. Both true, and neither
rescues the result: a fixed instrument pointed at 173 defects with ±4 points of noise still cannot
resolve an effect of six.

## What would be needed to ask this question properly

- **A corpus large enough to resolve it.** At ±4 points of noise, detecting a 3-point effect needs
  several times this many defects. That is a sample-size problem, not a prompt problem.
- **Repeated arms, not single runs.** Every future arm on this corpus should run its control twice
  and publish the gap alongside the result.
- **A different-family judge**, which also addresses the phrasing channel below.

## What the model is given

Facts a diff cannot supply, counted from the repository's own history and rendered by
`render/shape_line.py`:

```
- Touches 11 file(s) and 142 line(s). This repository's median change is 3 file(s) and 73 line(s).
- In the 30 days before it, these files changed 16 time(s), and 9 other person/people touched them.
- It landed on a Tuesday 11:45.
- Outside this repository's normal range: 11 files against a median of 3.
```

**Every line is settled by two git commands.** "Nine other people touched these files in the thirty
days before this landed" cannot be false the way "this is a null dereference" can, and the model
cannot compute any of it from the text it reads. That is the argument for why shape might be
different in kind from the five prompt levers that moved nothing — and the reason it was measured
rather than assumed.

The block also states that an unusual shape is **not** a defect and must not be reported as one.
Without that instruction a model shown "23 files against a median of 2" reports the size as the
finding, which the prompt already forbids.

## Why the instrument is the story, and why it does not threaten the result

`shape_context.py` was written months ago, pre-registered, and **never run**. When it was finally
run it was wrong in seven distinct ways:

| defect | what it would have produced |
|---|---|
| read the clone's HEAD, not the change | shape of an unrelated commit |
| measured the head commit, not the range | "26 lines" for a 694-line pull request |
| rebuilt its own prose | a string the product does not send |
| empty context left the arms identical | silent dilution toward null |
| commit URLs crashed the run | no result at all |
| `pr/` branch refspec collision | discourse unclonable |
| 83,202 refs fetched to resolve ten | grafana unclonable, three times |

**All seven are attenuating, so the measured effect is a floor.** Each lives in shape generation,
each touches only the WITH_SHAPE arm, and each substitutes a wrong or absent shape for a true one —
which can only move the arms closer together. Had any survived, the run would have reported a
smaller effect or a null, and this project would have recorded a sixth dead lever.

**That argument is specific to these seven and is not a general law.** An asymmetric defect — one
flattering the treated arm rather than starving it — manufactures effects rather than hiding them.
An earlier draft stated the general version; it should not have.

→ `docs/engineering/CODEBASE.md`, the section on `ingest/review_window.py`.

## What this does NOT say

**It is recall against a gold set, not precision in front of a customer.** The judge counts how many
of 173 known defects each arm's comments cover. It says nothing about the other ~120 comments per
arm, and raw findings remain **66.7–82.1% wrong** across four blind rater pools. Shape context does
not change that and was not measured against it.

**The judge is blind to arm, and that is not enough.** `judge.JUDGE_PROMPT` receives one golden
comment and one candidate and nothing else — no arm name, no ordering, no shape block — and every
pair is judged independently, so label leakage is impossible by construction.

**But blinding does not close the phrasing channel.** Shape context plausibly changes how a finding
is *worded*: a comment referencing file counts and recent churn reads as better-grounded. A
same-family judge agreeing with a careful rater **34.9%** of the time has ample room to reward that
without the finding being more correct — which would raise the score without raising recall.
Nothing here rules that out, and blinding is the wrong instrument for it. What would: a
different-family judge, which this project has argued for and never run.

**The mechanism is not localised yet.** The first run stored only aggregate counts, so no
individual finding could be pointed at and shown to have arrived because of the context — the way
`expansion-conventions-result.md` points at falcon's URI decoder.
`research/phase0/bench/forensic/shape/rejudge.py` recovers it by re-judging the stored comments,
which generates no new model output and so compares the same texts that produced the headline.

**And 81 against 90 are margins, which do not settle a paired comparison.** 9:0 and 25:16 give the
same +9 and opposite conclusions. Every comparable result in this project reports the discordant
pairs — 62:16, 17:5, 26:6 — and the one favourable result reporting differently is exactly what a
reader should be suspicious of. McNemar is outstanding, not omitted.

**"Unusual" fires on 43 of 49 changes here, and that is a corpus artefact.** The threshold is three
times the repository's median; a curated benchmark of interesting pull requests is far larger than
typical traffic. On real traffic the ranker's own firing rate is **8–15%**. So the discriminating
content in the block is probably the raw counts, not the unusual flags — untested either way.

**One change of fifty carried no context** (`ai-code-review-evaluation/sentry-greptile` pull 5, whose
base is a non-default branch). Its two arms were byte-identical, so the measured effect is very
slightly **understated**. It refused rather than fabricating a shape from the wrong base, which
would have handed the model false file and line counts.

## Coverage

| repository | changes | context resolved |
|---|---|---|
| calcom/cal.com | 10 | 10 |
| discourse/discourse | 10 | 10 |
| grafana/grafana | 10 | 10 |
| keycloak/keycloak | 10 | 10 |
| sentry | 10 | 9 |
| **total** | **50** | **49** |

**It is five repositories, not six, and the URLs do not say so.** Two of sentry's ten point at
`ai-code-review-evaluation/sentry-greptile`, an evaluation mirror; the corpus labels both with
`repo_file: sentry`, and 8 + 2 restores the ten-per-repository pattern the other four follow. An
earlier draft of this table grouped by URL host and reported six. Grouping that way would also
split sentry's defects across two clusters in any per-repository analysis.

Shape emitted more comments on 19 changes, fewer on 20, the same on 11 — median delta zero, range
−6 to +4. **The volume result is not one outlier**; the arms are matched change by change.

## What it costs

One `git log`, one `git diff --numstat` and two short `git log` reads per change, all local. No
model call, no network. The block is about 700 characters of prompt.

→ `research/phase0/bench/results/shape_context.json` holds both arms' comments, every context block,
and the scores.
