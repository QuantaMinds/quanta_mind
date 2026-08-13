# Four negative results on AI-authored pull requests

**Draft for external publication. Written 2026-08-12.**
Every number here is produced by code in this repository against a real corpus. Nothing is
cited from memory, and the claims that did not survive checking are listed rather than
deleted. The evidence files are named at the end.

---

## Summary

We spent six weeks building an instrument to test a claim the AI-code-review market treats as
obvious: **that code an analyser cannot resolve is code more likely to break.**

It is not true in our corpus. It stayed untrue after we corrected the one measurement error
that would have helped it. A second, independent framing of the same claim — as a merge gate
rather than a risk score — returned the same null, from a condition that fires on **45% of
pull requests**.

Along the way we found two defects that matter more than our own result, because they are in
instruments other people are using right now:

- The file-level outcome rule used to attribute breakage to a pull request is wrong on
  **65–71%** of the verdicts it produces.
- **No shipping AI reviewer can report that it failed to analyse something.** We checked
  seven. The one tool that could is dead.

We are publishing because the failure mode is attractive, the intermediate signals look like
validation, and the error is only visible if you check discrimination instead of frequency.

---

## What we set out to test

Preregistered before the data was collected, in `docs/findings/PHASE0_PREREGISTRATION.md`,
with a stop rule written in advance: relative risk below 1.5 means stop.

> **Exposure.** A changed symbol is *exposed* when a static call-graph analyser cannot name
> its callers or callees — dynamic dispatch, reflection, a handler table, `getattr`.
>
> **Outcome.** The pull request *broke* when a later commit fixed something it introduced.
>
> **Claim under test.** Exposed pull requests break more often than unexposed ones.

Corpus: **310 pull requests**, 200 repositories walked, 107 in the analysed set, **1,517
changed symbols classified**. Python, agent-authored, run under a pinned Linux image.

---

## Result one — exposure does not predict breakage

```
                broke     did not break     rate
EXPOSED           32            75          29.91%
UNEXPOSED         21            52          28.77%

Relative risk                1.040
  naive Katz 95% CI          [0.654, 1.652]
  cluster-robust 95% CI      [0.598, 1.890]
  Fisher exact p             1.0000
```

The interval spans 1 in both directions. Power was met — the preregistered target was at
least 20 breakages in the exposed arm and we observed 32. **This is a null, not an
underpowered miss.**

No dose-response either. Stratified by changed-lines quartile the relative risks run 0.684,
1.020, 1.283, 0.700. **No monotone trend.** A real effect would have shown a gradient.

### The correction that should have rescued it

Our breakage labels came from a file-level rule, and that rule is noisy (see result four).
Noise attenuates a relative risk toward 1.0, so a corrected measure could in principle move.
We ran the correction — restricting breakage to evidence that shares a changed symbol with
the pull request — and it gave **RR 1.251, p = 0.797**.

Higher, and still nowhere near the preregistered threshold. **The null survives the
correction that would have helped it.**

---

## Result two — the one direction that moved, stated with its own weakness

The instrument failed on a third arm: 47 pull requests it could not analyse at all, 46
timeouts and 2 out-of-memory.

```
UNANALYZED        20 broke / 27 did not      42.55%
  vs UNEXPOSED    RR 1.479   naive Katz 95% CI [0.906, 2.416]   Fisher p = 0.1672
```

The pull requests our tooling **choked on** break at the highest rate of the three arms. It
is the only result pointing anywhere, and we are reporting it because suppressing it would be
dishonest — but the interval crosses 1, the p-value is 0.17, and the plausible confound is
obvious: timeouts and out-of-memory track repository size and complexity, which plausibly
track breakage on their own. It was not preregistered as a hypothesis.

**We do not claim it. We are flagging it as the thing worth testing next, by someone with a
corpus large enough to separate it from size.**

---

## Result three — a merge gate that fires constantly and decides nothing

The natural product form of the claim is not a warning, it is a precondition: *auto-merge
only what we could fully resolve; anything else goes to a human.* That reframing survives the
first result, because it makes no claim about risk — it is a machine refusing to automate
what it did not understand.

We tested it as its own contingency table.

```
                  gate HOLDS     gate PASSES
broke                 21              28
did not break         74              88
breakage rate      22.11%          24.14%

Relative risk (held vs passed)   0.916    naive Katz 95% CI [0.557, 1.505]
Fisher exact two-sided p         0.7462
n = 211 pull requests across 96 repositories
```

**The gate holds pull requests at a marginally lower breakage rate than the ones it lets
through.** It does not discriminate.

The firing rate is the part worth dwelling on:

| Measure | Value |
|---|---|
| Pull requests where at least one call site has no static callee name | **95 of 211 — 45.0%** |
| Individual call sites with no static callee name | **884 of 367,874 — 0.24%** |
| Hold rate, pull requests touching 3 files or fewer | **45.3%** |
| Hold rate, pull requests touching more than 3 files | **44.3%** |

**A 45% firing rate reads as a working product.** Our own build plan set a floor of 5% for
the condition to be worth shipping — we cleared it nine times over. The gate is not
decoration. It is active, load-bearing, and uninformative, which is the worse outcome:
enabling it holds nearly half of a team's otherwise-mergeable pull requests and prevents
nothing measurable.

**Our gate criterion was the wrong criterion.** It asked whether coverage is the *deciding*
condition often enough to matter. It should have asked whether coverage is the *correct*
condition. Frequency measures use. Only discrimination measures value.

One genuinely interesting property, which does not save it: the hold rate is **flat across
pull-request size**. Coverage is orthogonal to every attribute an existing merge-queue
product can gate on, so none of them can approximate it by proxy. It is orthogonal *and*
uninformative — an independent measurement of nothing that predicts defects.

---

## Result four — the outcome rule the field uses is wrong most of the time

To ask "did this pull request break something", you need a rule that attributes a later fix
back to an earlier change. The standard rule is file-level: a fix commit touching a file the
pull request touched counts as evidence against it.

Measured against symbol-level ground truth on our corpus, **65–71% of breakage verdicts share
no changed symbol with the pull request they are attributed to.**

That is not a criticism of one tool. It is the default attribution rule in defect-prediction
work, and it means a majority of the labels are pointing at the wrong change. Any result
built on it — ours included, before we corrected it — inherits that noise, and noise pushes
every relative risk toward "no effect."

**If you are measuring whether AI-written code is more defective, this is the first thing to
check in your own pipeline.**

---

## Result five — no shipping reviewer can say "I could not analyse this"

Verified against vendor documentation and the GitHub API, not from memory:

| Tool | What it emits | Can it report an analytical failure? |
|---|---|---|
| Cursor Bugbot | `success`, `neutral`, `failure` | **No** |
| Qodo | severity-ranked findings | **No** |
| Greptile | confidence 0–5, P0/P1/P2 | **No** — `Failed` means the run itself broke |
| CodeRabbit | 5 severities, 6 categories | **Administrative only** — draft, paused, ignored title |
| GitHub Copilot | always a "Comment" review | **No** |
| Graphite | a negative-comment-rate figure | **No** — no blind spots documented |
| BreakBot | Success / Neutral / **Skipped** | **Yes** |

Cursor documents the collapse in its own words:

> `neutral`: "Bugbot found issues, the run was cancelled by a newer commit, **or Bugbot hit an
> internal error**."

Three unrelated situations, one signal, and Cursor states plainly that Bugbot does not emit a
`skipped` conclusion. Qodo's judge agent filters "anything low-confidence before it reaches
the pull request" — uncertainty is deleted rather than reported. GitHub's own community
thread documents Copilot reporting files as reviewed that it demonstrably did not open, and
labelling capacity failures as the risk judgement "Evaluated as low risk."

**The one tool that typed absence correctly is dead**: BreakBot, 8 stars, last code push
2023-12-16, and its client list is configured by hand rather than discovered — so its own
coverage denominator is declared, not computed.

This is the finding with the longest shelf life. A reviewer that cannot report its blind
spots produces silence that is indistinguishable from safety, and every buyer in this market
is currently reading one as the other.

---

## What we are not claiming

- Not that AI-written code is safe. We measured one exposure definition against one outcome
  definition on one language.
- Not that static-analysis coverage is worthless. We measured that **a missing static callee
  name** does not predict breakage. A call site whose name resolves to the *wrong* target is
  a different failure and we did not test it.
- Not that the third-arm signal is real. It is underpowered and confounded by size.
- Not that these reviewers are bad at reviewing. We measured what they can *say*, not what
  they can find.

---

## Limits, stated rather than implied

- **Python only, agent-authored, one corpus.** No claim generalises past that.
- The merge-gate table is **not cluster-robust** — 211 pull requests across 96 repositories.
  A clustered interval would be wider, not narrower, so it cannot rescue the result.
- Both tables are wide. The corrected correlation runs on 53 re-derived verdicts.
- The gate was evaluated marginally, not jointly with ticket type, CI status, or test
  coverage, none of which our corpus carries.
- Breakage labels outside the corrected analysis still come from the file-level rule that
  result four shows is 65–71% wrong.

---

## Method and data

Preregistration, including the stop rule and every amendment, is in
`docs/findings/PHASE0_PREREGISTRATION.md`. The merge-gate analysis is in
`docs/findings/COVERAGE_GATE_NULL_2026-08.md`. Vendor claims and their verification status
are in `docs/findings/MARKET_POSITION_2026-08.md` and
`docs/findings/COMPETITIVE_LANDSCAPE_2026-08.md`, where each row carries VERIFIED, QUOTED,
MEASURED, UNVERIFIED, or REJECTED.

Records the instrument could not analyse are **excluded and counted**, never coded as
passing. A timeout is not a clean bill of health, and the third arm exists so that failure is
visible in the table rather than absorbed into it.

---

## Why publish a null

Someone else will build the thing we just falsified. The reasoning is attractive, the firing
rate is high enough to look like validation, and the failure is invisible unless you build
the contingency table.

Elapsed time from proposing the merge-gate measurement to the result that killed it: **about
twenty minutes**, against a product build measured in months. That ratio is the argument for
the method, and it is the only thing here we would ask anyone to adopt.
