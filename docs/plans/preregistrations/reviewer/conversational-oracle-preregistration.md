# The conversational architecture — the model asks, the oracle answers, and what would end it

**Written before the run. Bars fixed here. A near-miss is a fail.**

## The change being tested

Today the reviewer **asserts** external facts it has no way to check: that a SHA does not exist,
that a release is not on PyPI, that a date is in the future. Measured live, its discrimination on
the SHA class is **−8.3%** — a coin flip — and in 7 of 24 trials it declared a SHA absent that had
been fetched from GitHub minutes earlier.

The architecture under test makes it **ask** instead. The model emits a question; a deterministic
oracle answers from GitHub or PyPI; the model reasons from the answer. Two rules, both already
enforced in `verify/`:

1. **The model may not answer its own question.** `UNRESOLVABLE` drops the finding.
2. **The oracle never judges.** It returns facts. A tool that returns "this looks wrong" is a second
   model wearing a parser's clothes, and five of those have been measured failing.

## Step 0 — the oracle's own accuracy, measured before it is wired into anything

**Four instrument bugs across three fixes say this is not optional.** `tags_at` scanned a
one-line JSON document line by line; exact-tag matching called the universal `# v6`-on-`v6.4.0`
convention a defect and ran at a **77% false positive rate**; a `\b`-terminated regex silently
discarded two thirds of a sample; and `adjudicate_release` **confirmed every false claim it was
built to refute**.

A model reasoning from a bad fact produces a **well-grounded false finding**, and that is harder to
catch than confabulation, not easier — nothing supports a confabulation, and that absence is the
signal a reader uses. A wrong confirmation removes it.

**So before the arm runs, each oracle is measured on live data in both directions**, and the result
is published whatever it is:

| oracle | must refute a false claim | must NOT refute a true one |
|---|---|---|
| `pin_mismatch.detect` | 12/12 wrong pairings | 12/12 correct pairings silent |
| `releases.adjudicate_release` | awscli 1.45.34, isort 9.0.0b2 | flask 99.99.99 stays unrefuted |

Both currently pass. **A regression in either ends the experiment before it starts**, because the
arm would then be measuring the oracle's errors.

## Step 1 — the arm

The design-13 pool, read from its blind key rather than from memory: **86 real items — 45 WRONG,
7 CORRECT, 18 TRIVIAL, 16 UNFALSIFIABLE** — plus 10 planted sabotage items, every one of which the
raters caught as WRONG.

**The correct-finding denominator is 7, not 12.** This document first said 12, which is the count
across all 207 adjudicated findings and not the count in the pool this arm runs on. Corrected
before the run. Each is run through
the conversational architecture. Three counts:

- **ASKED** — the model emitted a question instead of an assertion
- **SETTLED** — the oracle returned `REFUTED` or `CONFIRMED` rather than `UNRESOLVABLE`
- **LOST** — a finding that was CORRECT and no longer publishes

## Bars

**HARD STOP, and it is not traded against anything.**

> **Losing 2 or more of the 7 correct findings ends the experiment as a FAIL, whatever happens to
> the wrong-rate. Losing 1 is reported as a cost against any gain, never netted out of it.**

Seven correct findings is the entire correct yield of this pool of 86. **Losing two is 29% of
everything the reviewer got right here** — a larger share than the 17% the original (wrong)
denominator implied, so the bar is stricter than first written, not looser. **The correct-rate is
what closed Half B**; a mechanism that improves the wrong-rate by damaging it has made the product
worse on the axis that decided the question.

This is design 8 arriving again by a new road. **That design's quote requirement was satisfied by
abstaining rather than by better anchoring** — the model complied by saying less. A model asked to
ask permission has exactly the same escape available.

**PASS** requires all three:
- ≥ 60% of the 45 wrong findings ASKED rather than asserted
- ≥ 50% of those asked are SETTLED by the oracle
- ≤ 1 of the 7 correct findings LOST

**INCONCLUSIVE** — the drop in wrong findings does not exceed the chance value below.

**FAIL** — the hard stop, or fewer than 60% asked.

## The chance value, stated before the run

**An arm that drops findings at random loses the same proportion of correct ones as wrong ones.**
So if the architecture suppresses D% of the 45 and loses L% of the 7, random suppression predicts
**D = L**. The arm has demonstrated something only if **L is far below D**.

Reporting a drop in the wrong-rate without L is the "precision rises whatever you delete" error,
which this project has made before and has a name for.

## What this cannot show, named now rather than discovered afterwards

**The 45 and the 12 are one pool.** Two of three base-rate runs came back smaller than the
taxonomy predicted from that same pool — SHA→tag at **0.24%** in the wild, registry existence at
**0.00%** — and the date class **did not reproduce at all** on three unrelated live diffs.

So "22 of 45 handled" describes **coverage of a historical pool, not a rate anyone would see
live**, and this experiment inherits that pool exactly. A PASS means the architecture works on the
findings we have, not that those findings occur at that rate in a customer's repository. **Any
claim about live rates needs a live corpus and this is not one.**

## What it cannot reach at all

**The 17 `TRACE` findings have no oracle**, because the answer is not a fact to look up — it is a
conclusion to derive. *"This loop spins forever"* has nobody to ask. Asking does not help where
there is no authority, and this arm is not expected to move that class. **If it appears to, that is
a defect in the measurement**, not a result.

That class is where execution grounding would go, and it is a separate preregistration.

## What could still silently fail

An oracle that cannot reach its authority returns `UNRESOLVABLE` for everything. Every finding in
the class then drops, the wrong-rate improves, and **the arm looks like a success**. The
unreachable count is therefore reported per run, and a run where it is non-trivial is a void run
rather than a clean one — the same defect as a filter that admits nothing across a whole pass.
→ `docs/CORRECTIONS.md` entry 7

---

# RESULT — PASS on all three bars. Recorded after the run; nothing above was edited.

Run on 2026-08-25 over the 86 real design-13 items. Step 0 passed as a gate first.

| bar | required | observed | |
|---|---|---|---|
| asked rather than asserted | ≥ 60% of 45 | **29/45 = 64%** | met |
| settled by an oracle | ≥ 50% of those asked | **21/29 = 72%** | met |
| correct findings LOST | ≤ 1 of 7 | **1 of 7** | met, at the limit |

**Wrong findings that would no longer publish: 18 of 45 = 40%.**

## The chance null is cleared, and that is the result

Random suppression at a 40% drop rate predicts losing **2.8 of the 7** correct findings. **Observed:
1.** The architecture is not deleting blindly — it removes wrong findings roughly three times more
often than correct ones.

Of the 21 wrong findings the oracle answered, **the model withdrew 16** once given the fact. It was
told what GitHub holds, never whether it was right, and it changed its own mind.

## The one lost correct finding, and it is at the bar not under it

> "The action `hynek/build-and-inspect-python-package` was renamed to `hynek/build-and-inspect` in
> v3, but the workflow uses the old name…"

The model asked whether that rename happened. The oracle answered that the SHA carries `v3.0.1`
under the **old** name — which does not settle a rename question, and the model withdrew anyway.

Checked by hand afterwards: `hynek/build-and-inspect` returns **404**, so the rename claim appears
false while a blind rater marked the finding CORRECT — most likely for a different clause in the
same sentence. **This is the failure mode to watch: an answer that is adjacent to the question
rather than responsive to it, taken as dispositive.** One instance, at the bar.

## Three runs, and the first two measured the harness

- **Run 1** reported a 2% settle rate. `settle()` passed the repository the FINDING was about, so
  "in `actions/setup-python`, what tag corresponds to 5fda3b95?" was looked up as
  `aws/aws-cli@5fda3b95`. Underneath it, a design error: **`adjudicate()` is a verifier and a
  question asserts nothing**, so it returned UNRESOLVABLE for every question. Two stages of a
  three-stage loop, called the loop.
- **Run 2** was correct and incomplete: 3 of 45 answered. `"What is today's date?"` was asked five
  times and never answered — no date oracle was wired — and eight questions said **"the given commit
  hash"** without naming it, which the answerer required.
- **Run 3**, above, with both closed.

**A near-miss is a fail and 56% was reported as one in run 2.** The 64% here is a real pass, and it
is four points over the bar rather than comfortable.

## What this does NOT show

**The 45 and the 7 are one historical pool**, exactly as this document said before the run. Two of
three base rates came back smaller than that pool predicted and the date class did not reproduce
live at all. **A PASS means the architecture works on the findings we have.**

**And it does not touch the semantic class.** Of the 16 wrong findings that never asked anything,
the questions in the unanswered set are things like *"Can multiple processes execute this code
concurrently?"* — there is no authority to ask. That is the boundary, and it is where execution
grounding would go.
