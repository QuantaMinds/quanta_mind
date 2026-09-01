# Pre-registration — collapsing findings that say the same thing twice

**Registered 2026-08-30, before any dedup code was written and before any outcome was read.**

## The claim

We emit **194 comments covering 81 of 173 golden defects (0.42 per comment)**. Qodo-extended-v2
emits **152 covering 98 (0.64)**. The gap is not that we find less — it is that we say the same
defect repeatedly: **17.3% redundancy against Qodo's 1.0%**, measured in
`docs/findings/reviewer/why-the-correct-rate-is-low.md`.

**The claim under test: a mechanical dedup removes repeats without removing coverage.**

This is worth registering because it is the one lever here that is model-free. Every mechanism
tried against the correctness rate has been a filter on generation and five moved nothing;
redundancy is an emission property and does not need the model to improve.

## What is NOT available, stated before it becomes an excuse

**Our own per-comment output for those 50 pull requests is not on disk.** `arm_OURS.json` holds
`tp/fp/fn/errors/prs_with_output` and nothing else, and no harness in the tree reproduces it.
So the 194/81/0.42 row **cannot currently be recomputed**, and dedup cannot be scored against it
without re-running our arm — 50 model calls at roughly 6,321 output tokens each.

That is a real limit on this work and it is why the bars below are split into what can be paid
for now and what cannot.

## The corpus, fixed now

`research/phase0/bench/martian/data/results/anthropic_claude-opus-4-5-20251101/candidates.json`
— **50 pull requests × 48 rival arms**, each comment carrying `path`, `line`, `source`, `text`.
Goldens in `research/phase0/bench/martian/data/golden_comments/`, 50 entries.

**The rule is developed against the RIVAL arms, never against ours.** Ours is unavailable anyway,
but the point stands independently: a rule tuned on the arm it must later judge is tuned on its
own test set.

## Bar 1 — the rule must reproduce a redundancy ordering already measured (free)

Qodo-extended-v2 was independently measured at **1.0% redundancy** and our arm at **17.3%**. A
dedup rule that fires on 15% of Qodo's comments is not detecting redundancy, it is detecting
something else and would delete real findings.

**PASS:** the rule removes **≤ 3.0%** of `qodo-extended-v2`'s comments.
**FAIL:** anything above that, and the rule is rejected rather than retuned on this arm.

This is a known-answer test: the answer is on record from a different method, so the rule can be
wrong in a way that shows.

## Bar 2 — coverage must not fall (requires model calls, NOT yet authorised)

Removing comments trivially reduces comment count. The claim is that it does not reduce **goldens
covered**, and only a judge can say which golden a comment covers.

**PASS:** on the arms tested, goldens covered after dedup equals goldens covered before, and
comments emitted falls.
**FAIL:** any drop in goldens covered. A rule that trades a covered defect for a shorter comment
list has made the product worse and is rejected outright — not tuned until it passes.

**Cost: one judge call per collapsed pair.** Until that is spent, **nothing ships to `render/`.**
A dedup merged on Bar 1 alone would be exactly the "we removed output and hope we lost nothing"
this project keeps finding in other people's evidence.

## What would make me drop this

- Bar 1 fails and the rule cannot be made conservative without removing nothing at all.
- Bar 2 fails on any arm.
- The rule removes fewer than **5%** of comments on any arm, which would make it not worth the
  code regardless of safety — the measured gap it is meant to close is 17.3%.

## What could still silently fail

Two comments about genuinely different defects on the same line would read as duplicates to any
text-similarity rule. Bar 2 is the only thing that would catch it, which is why Bar 1 alone is
not a licence to ship.

---

# Result — Bar 1 only, 2026-08-30

**BAR 1: PASS.** The rule removes **0.0%** of `qodo-extended-v2`'s 152 comments against a
registered ceiling of 3.0%. The ordering across arms is the one the independent measurement
implies:

| arm | removed | comments |
|---|---|---|
| graphite | 12.5% | 16 |
| greptile | 9.3% | 140 |
| copilot | 3.6% | 280 |
| coderabbit | 1.3% | 318 |
| greptile-v4-1 | 0.6% | 168 |
| qodo | 0.0% | 196 |
| **qodo-extended-v2** | **0.0%** | **152** |

**It is not passing by refusing to fire.** Loosening the threshold from 0.90 to 0.50 takes
greptile from 8.6% to 15.7% and copilot from 2.9% to 9.6% while `qodo-extended-v2` stays at or
below 1.3%. The rule discriminates between arms rather than tracking comment volume.

## What this result does NOT establish

**Whether it detects the phenomenon the 17.3% figure counted.** That number came from a different
method on our own arm; this rule matches near-verbatim prose about one file. "The same defect said
again in different words" is a semantic claim and a `SequenceMatcher` ratio is not. The two may
measure different things, and **our per-comment output is not on disk, so the two cannot be
compared.**

That is the honest state: the rule is safe on the arm whose low redundancy is independently known,
and its usefulness on ours is unmeasured.

## Bar 2 is unmet and nothing is wired

`verify/repeats.py` exists, is tested, and **is called by nothing.** Wiring it into `render/`
requires the coverage bar, which requires a judge — one call per collapsed pair — and the arm
regeneration that would produce pairs to judge: 50 model calls at roughly 6,321 output tokens.

**Not authorised, not spent, not merged into the review path.**


---

# Result — Bar 2 NOT RUN, and the rule is DROPPED by this document's own criterion, 2026-08-31

**No model calls were spent, and none should be.** The drop criterion registered above — *"the rule
removes fewer than 5% of comments on any arm"* — is met on every arm, measured on the judged
benchmark comments rather than estimated. → `scripts/measure/dedup_reach.py`

| arm | comments | repeats WITHIN a file (what the rule collapses) | same claim ACROSS files (kept) | semantic redundancy |
|---|---|---|---|---|
| OURS | 194 | **0** | 3 | 17 (17.3%) |
| qodo-extended-v2 | 152 | **0** | 0 | 1 (1.0%) |
| greptile-v4-1 | 168 | **0** | 1 | 7 (7.5%) |
| coderabbit | 318 | **0** | 5 | 34 (24.3%) |

The instrument reproduces the published 17.3% and 1.0% from `redundancy.json`, so it is reading the
same corpus those figures came from.

## The two measurements are different things, and that is now VERIFIED rather than open

This document recorded it as unknown: *"Whether it detects the phenomenon the 17.3% figure counted
... The two may measure different things."* They do.

**17.3% is `redundant / candidates_matching` — 17 comments matching a golden a SIBLING had already
covered.** That is semantic duplication: one defect described twice in different words, usually on
different files. **`repeats()` collapses near-verbatim prose about the SAME file**, and there are
**zero** such pairs in the corpus. The rule cannot reach the redundancy that justified building it.

Bar 2 asks whether coverage falls when comments are removed. **The rule removes no comments here,**
so coverage trivially cannot fall — and the judge calls would have bought a PASS that means nothing.
Spending them would have produced a green bar for a rule with no effect.

## What this does NOT say

**It does not say redundancy is not worth attacking.** 17 of our 98 matching comments restate a
golden a sibling already covered, against qodo's 1 of 99. That gap is real and remains the one
model-free lever with positive evidence. What is dead is *this* rule as the way to close it: any
mechanism that works has to compare claims across files and by meaning, not by shared prose within
one file.

## A defect found while measuring, fixed separately

`alike()` called `SequenceMatcher(None, a, b)`, whose `autojunk` default ignores any element
appearing in more than 1% of a sequence longer than 200 characters. Compared character by
character, that is ordinary letters and spaces. **Two real findings measured 97.3% alike scored
0.100.** Most review comments exceed 200 characters, so the rule was close to inert on real input
while all thirteen unit tests passed — every one compared strings short enough that the heuristic
never engaged.

**This also undermines the Bar 1 evidence.** Bar 1 passed on the reading that the rule fires
sensibly and discriminates between arms, and the check offered against "passing by refusing to
fire" was loosening the threshold. That check could not detect this: the threshold does not affect
whether long strings are compared at all. Bar 1's own table cannot be re-examined either — it names
arms (`graphite`, `copilot`) that appear in no results file here, and **the commit recording it
added no instrument**, which is why `scripts/measure/dedup_reach.py` now exists.


## What the 17 comments actually ARE — read, not inferred, 2026-08-31

`redundant` is a subtraction and names nobody, so the comments were recovered per pull request:
TP comments minus goldens covered. The positive excesses sum to **17 across 10 pull requests**, the
same figure the aggregate reports. → `scripts/measure/dedup_reach.py`

**They are not repetition. They are one defect class reported at each site where it occurs.**
`calcom/cal.com#8087` is the clearest: **one** golden — *"the code uses `forEach` with async
callbacks"* — and **four** of our comments, each naming a different file that does it:
`app-store/vital/lib/reschedule.ts`, `app-store/wipemycalother/lib/reschedule.ts`,
`features/bookings/lib/handleCancelBooking.ts`, `trpc/server/routers/viewer/bookings.tsx`.
`cal.com#10967` is the same shape: three comments about `createEvent` in three CalendarService
files. `grafana#90045` reports the same metrics defect in `Create`, `Update`, `Delete` and
`DeleteCollection`.

**Every one of those comments is CORRECT and names a real site.** The benchmark's golden is per
defect CLASS; we emit per SITE. So a share of the 17.3% is a granularity mismatch between us and
the scoring, not waste — and **deleting three of those four comments would delete three real
locations a developer has to fix.** Any dedup that simply drops them makes the product worse while
improving the score, which is the shape this project exists to refuse.

## What this means for the mechanism

Across the 10 pull requests holding all 17: **13 of the comments name no file at all** — they key
on a function (`Create`, `deleteScheduledEmailReminder`) — and only **3 share a file with a
sibling**. Three is therefore the ceiling on what any within-file rule could ever reach, and
`repeats()` reaches none of them, because the prose genuinely differs: different file, different
function, different specifics.

**The right mechanism is grouping, not deletion.** One finding that names the defect once and lists
its sites keeps every location while spending one comment instead of four. ~~It needs no judge~~ —
**that was wrong, and the section below measures why.** Grouping needs a judge exactly as much as
dedup did, because deciding that two comments describe one defect is the same semantic judgement as
deciding that one is redundant. What grouping fixes is the CONSEQUENCE, not the cost. A pre-registration for it must set its bar on **sites retained**, not on
comments removed, because comments-removed is trivially satisfiable by making the product worse.


# Result — grouping cannot be done model-free either, 2026-08-31

**NEGATIVE. A text rule reaches at most a quarter of the redundancy, and buying more means fusing
defects it cannot tell apart.** → `scripts/measure/dedup_reach.py`

The mechanism tested is the most favourable one available without a model: strip the backticked
spans — paths, functions, symbols — which are exactly the part that differs between two reports of
one defect at different sites, then compare what is left.

| threshold | grouped, of the 17 |
|---|---|
| 0.86 (the shipped threshold) | **4 (24%)** |
| 0.70 | 5 (29%) |
| 0.60 | 6 (35%) |
| 0.50 | 7 (41%) |

`calcom/cal.com#8087` shows why, on four comments about one `forEach`-async defect. Comments 1 and
2 are 0.973 alike raw and 1.000 with identifiers stripped — they group. Comments 3 and 4 describe
the SAME defect and score **0.440**. Stripping identifiers makes that pair WORSE, 0.449 → 0.377,
because part of what they shared was the identifiers.

**Two comments about one defect share MEANING, not WORDING** — different file, different function,
different surrounding explanation. No text metric reaches that, and the thresholds that would are
the thresholds that start merging genuinely different defects, which nothing model-free can detect.

`types/finding.Finding` carries `path`, `quote`, `claim`, `fix`, `provenance`, `line` — **no defect
kind**, so there is no free categorical label to group on either.

## What this costs the standing story

**Redundancy is no longer "the model-free lever".** The gap is real — 17 of our 98 matching
comments against qodo's 1 of 99 — but every mechanism that could close it needs a judge to decide
defect identity. That puts it in the same category as the five prompt levers that moved nothing,
rather than in a category of its own. `docs/product/QUANTAMIND.md` and `product-build.md` both
describe redundancy as the model-free half; that framing does not survive this measurement.

## The integrity caveat, which counts AGAINST the mechanism

The normalisation was designed after reading five pull requests OF THIS CORPUS, so the numbers
above are a fit rather than a test. **That makes the negative stronger, not weaker: the rule fails
on the very data it was shaped to fit.** A confirmatory measurement would need a corpus nobody has
read, and is not worth drawing for a mechanism that already fails here.
