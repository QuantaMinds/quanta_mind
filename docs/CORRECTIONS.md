# Corrections — defects in how something was measured, not in what it measured

**This file is cited from `docs/findings/HAND_LABELLING_PROTOCOL.md` as entries 1, 3 and 5 and did
not exist.** Those entries were referenced and never written down; the citations are left in place
rather than deleted, because removing a reference on a failed lookup is the same defect as inventing
one — this project has done that once already with the 4.61% figure. **Whoever holds that context
should write them.** Numbering starts at 6 so the gap stays visible.

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
