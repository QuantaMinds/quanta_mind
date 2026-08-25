# Corrections — defects in how something was measured, not in what it measured

**This file is cited from `docs/findings/HAND_LABELLING_PROTOCOL.md` as entries 1, 3 and 5 and did
not exist.** Those entries were referenced and never written down; the citations are left in place
rather than deleted, because removing a reference on a failed lookup is the same defect as inventing
one — this project has done that once already with the 4.61% figure. **Whoever holds that context
should write them.** Numbering starts at 6 so the gap stays visible.

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
