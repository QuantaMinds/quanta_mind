# Telling the model what the change looks like — measured, and it passed

Pre-registered in `research/phase0/bench/forensic/shape_context.py` before any model call, with the
bars written into the file's own docstring. Fifty golden changes across six repositories, two arms,
the same judge and the same 173 human-verified defects on both.

**This is the first context lever in this project that moved anything.**

## The headline: nine more defects, four fewer comments

| pre-registered bar | | result | |
|---|---|---|---|
| **defects found** | rise > 2.1 points (the judge's replicate spread) | 81 → **90**, **+5.2 points** | **PASS** |
| **comments emitted** | rise ≤ 15% | 210 → **206**, **−2%** | **PASS** |
| **verdict** | both, or it does not count | | **PASS** |

```
PLAIN        81 of 173 defects, 210 comments
WITH_SHAPE   90 of 173 defects, 206 comments
```

**+5.2 points is two and a half times the noise floor the bar was set against.** And it was not
bought by talking more: volume fell.

**That last column is what separates this from every benchmark arm in `greptile-gap-analysis.md`.**
The nits-on arm there bought +14 F1 by emitting 270 extra comments at **8.1% marginal precision** —
finding more by saying more, which this project measured five times and does not count. This arm
said *less*.

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
run it was wrong in seven distinct ways. Every one of them destroys signal:

| defect | what it would have produced |
|---|---|
| read the clone's HEAD, not the change | shape of an unrelated commit |
| measured the head commit, not the range | "26 lines" for a 694-line pull request |
| rebuilt its own prose | a string the product does not send |
| empty context left the arms identical | silent dilution toward null |
| commit URLs crashed the run | no result at all |
| `pr/` branch refspec collision | discourse unclonable |
| 83,202 refs fetched to resolve ten | grafana unclonable, three times |

**A broken instrument makes a real effect disappear. It does not manufacture +5.2 points across 49
changes and five repositories.** Had any of these survived, the run would have reported a null and
this project would have recorded a sixth dead lever. → `docs/engineering/CODEBASE.md`, the section
on `ingest/review_window.py`.

## What this does NOT say

**It is recall against a gold set, not precision in front of a customer.** The judge counts how many
of 173 known defects each arm's comments cover. It says nothing about the other ~120 comments per
arm, and raw findings remain **66.7–82.1% wrong** across four blind rater pools. Shape context does
not change that and was not measured against it.

**The judge is same-family.** `generator-cannot-judge-itself` in the project record puts same-family
agreement with a careful rater at **34.9%**. Both arms were judged identically so the comparison is
sound, but the absolute 81 and 90 carry that judge's error.

**The mechanism is not localised.** Only aggregate defect counts were recorded, so no individual
finding can be pointed at and shown to have arrived because of the context — the way
`expansion-conventions-result.md` could point at falcon's URI decoder. Per-finding attribution needs
the judge to emit per-change verdicts, which this run did not ask for.

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
| getsentry/sentry | 8 | 8 |
| ai-code-review-evaluation/sentry-greptile | 2 | 1 |
| **total** | **50** | **49** |

Shape emitted more comments on 19 changes, fewer on 20, the same on 11 — median delta zero, range
−6 to +4. **The volume result is not one outlier**; the arms are matched change by change.

## What it costs

One `git log`, one `git diff --numstat` and two short `git log` reads per change, all local. No
model call, no network. The block is about 700 characters of prompt.

→ `research/phase0/bench/results/shape_context.json` holds both arms' comments, every context block,
and the scores.
