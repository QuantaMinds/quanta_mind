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

The 45 real wrong findings and the 12 correct findings from the design-13 pool. Each is run through
the conversational architecture. Three counts:

- **ASKED** — the model emitted a question instead of an assertion
- **SETTLED** — the oracle returned `REFUTED` or `CONFIRMED` rather than `UNRESOLVABLE`
- **LOST** — a finding that was CORRECT and no longer publishes

## Bars

**HARD STOP, and it is not traded against anything.**

> **Losing 2 or more of the 12 correct findings ends the experiment as a FAIL, whatever happens to
> the wrong-rate.**

Twelve correct findings is the entire yield of 207 adjudicated. Losing two is 17% of everything the
reviewer has ever got right, and it would take the correct-rate from 5.8% to 4.8%. **The
correct-rate is what closed Half B**; a mechanism that improves the wrong-rate by damaging it has
made the product worse on the axis that decided the question.

This is design 8 arriving again by a new road. **That design's quote requirement was satisfied by
abstaining rather than by better anchoring** — the model complied by saying less. A model asked to
ask permission has exactly the same escape available.

**PASS** requires all three:
- ≥ 60% of the 45 wrong findings ASKED rather than asserted
- ≥ 50% of those asked are SETTLED by the oracle
- ≤ 1 of the 12 correct findings LOST

**INCONCLUSIVE** — the drop in wrong findings does not exceed the chance value below.

**FAIL** — the hard stop, or fewer than 60% asked.

## The chance value, stated before the run

**An arm that drops findings at random loses the same proportion of correct ones as wrong ones.**
So if the architecture suppresses D% of the 45 and loses L% of the 12, random suppression predicts
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
