# Execution grounding — the runtime as the oracle for claims no lookup can settle

**Written before the run. Bars fixed here. A near-miss is a fail.**

## What is left, and why it needs a different mechanism

The conversational arm passed: 64% of wrong findings asked an external question, 72% of those were
settled, 40% stopped publishing, and 1 of 7 correct findings was lost against a chance null of 2.8.

**16 of the 45 wrong findings asked nothing at all.** Their claims are:

> "The logic in this block causes an infinite loop when `unquote_plus` is false…"
> "This condition is too broad because it incorrectly matches any URL where a path segment ends
> with `/simple`…"
> "The function does not ensure that a base URL with a path component ends with a trailing slash…"

**There is no authority to ask.** Whether a loop terminates is not a fact GitHub holds; it is a
conclusion, and the model derived it wrongly. A lookup cannot reach this class and neither can a
better prompt — five have moved nothing.

**The runtime can.** That is the whole hypothesis.

## THE PROBLEM THIS DESIGN MUST CONFRONT: our own execution arm INVERTED

Design 13 measured an execution gate and got the opposite of the expected result:

> **Where the model *proves* its claim, the code is LESS likely to be fixed: 36.5% against 50.5%,
> p = 0.003, and p = 0.001 controlling for length.**

**That is not a null. It is significant and it points the wrong way**, and any proposal to run code
has to explain it or expect to reproduce it.

### The proposed explanation, and the part of it that is already refuted

The argument is that design 13 **asked the model to author a demonstration**, so what got measured
was the model's ability to write one — and it can only write demonstrations of code simple enough
to reason about in isolation, which is code that does not break.

**The "simple code" half of that is already tested and does not survive.** The inversion held at
p = 0.001 *controlling for length*, and length is the obvious proxy for simplicity-by-size.

**What survives is narrower and it is the actual hypothesis**: the selection was on *the model's
capacity to construct a proof*, which is not the same as the code being short. This experiment
removes that selection entirely — **nothing is authored by the model.** The repository's own test
suite runs, and the runtime decides.

**If the inversion reproduces here, the explanation is wrong and execution does not transfer to
pull-request review.** That is the outcome this arm is built to be able to report.

## The mechanism

For each finding, on the pull request's own base commit:

1. Check out the base, install, and run the repository's existing test suite. **Record the result
   before the change.**
2. Check out the head and run it again.
3. **The runtime is the oracle.** A finding claiming behaviour X is broken is checked against
   whether any test exercising that path changed state between base and head.

**The model authors nothing.** It is shown the outcome — "these 3 tests fail at head and passed at
base" or "the suite is unchanged" — and asked only whether its finding still stands, exactly as in
the conversational arm.

**A finding about code no test touches is `UNCOVERED`, and that is a third value.** It is not
evidence the finding is wrong. Collapsing "no test covers this" into "the tests say it is fine" is
the same defect as collapsing UNRESOLVABLE into CONFIRMED, and that one shipped a verifier that
confirmed every false claim it was built to refute. → `docs/CORRECTIONS.md` entry 8

## Step 0, before the arm — three checks, each of which can end it

**Four instrument bugs across three fixes, and two of three runs of the conversational arm measured
the harness rather than the architecture.** Step 0 is not optional.

1. **The suites must actually run.** Report how many of the pull requests reach a green base. A
   corpus where most do not is a corpus this arm cannot use, and that is a finding to publish, not
   a reason to sample differently.
2. **Coverage must be measured, not assumed.** For each finding, does ANY existing test execute the
   lines it names? **If the covered share is small, the arm's ceiling is that share** and the bars
   below are unreachable by construction. Report it before running the arm.
3. **A known-answer test.** Introduce a defect the suite provably catches, and require the harness
   to report it. A harness that finds nothing looks identical to a clean run.

## Bars

**HARD STOP, unchanged in kind from the conversational arm and not traded against anything:**

> **Losing 2 or more of the 7 correct findings ends the experiment as a FAIL, whatever happens to
> the wrong-rate.**

**PASS** requires all three:
- ≥ 50% of the 16 unasked wrong findings are `COVERED` — the runtime can speak to them at all
- ≥ 60% of covered wrong findings stop publishing
- ≤ 1 of the 7 correct findings lost

**FAIL** — the hard stop, or the design-13 inversion reproduces: correct findings dropping at a
higher rate than wrong ones.

**INCONCLUSIVE** — coverage is too small for the arm to have been tested, which step 0 should catch
first.

## The chance null, stated before the run

Random suppression loses the same share of correct findings as wrong ones. **If D% of wrong
findings drop and L% of correct ones do, the null is D = L.** The arm has shown something only if
L is far below D — the conversational arm cleared this at 40% against an observed 1 of 7 where 2.8
was predicted.

**And the inversion has its own null**: design 13 found L > D. Reporting D alone would hide exactly
the result that already happened once.

## What this cannot show

**The same historical pool.** 45 wrong and 7 correct from design 13, and this arm runs on the
16-finding residue of it. **Sixteen is a small denominator and the bars are stated as shares of it
for that reason** — a two-finding swing moves the headline by 12 points. A PASS here is a signal
that the mechanism is worth measuring properly, not a result about live rates.

**And it cannot make the yield argument go away.** The ceiling arithmetic is unchanged: 207
adjudicated findings, 12 correct, and a perfect verifier for every failure class reaches
**C/n = 16.7%** against a field floor of 49%. **A verifier deletes; it cannot create.** Execution
grounding deletes more accurately than a prompt does. It does not produce a correct finding that
was not already there.

## What could still silently fail

**A suite that fails to run returns no evidence for every finding, every finding drops, and the
wrong-rate improves.** That is the arm looking like a success while measuring nothing — the same
shape as an unreachable oracle. The count of pull requests whose base suite did not go green is
reported per run, and a run where it is large is void rather than clean.

**And a flaky test is an answer that is adjacent to the question.** The conversational arm lost its
one correct finding to exactly that: an oracle answered what tag a SHA carries when the question
was about a rename, and the model withdrew anyway. A test that fails at head for an unrelated
reason will read as confirmation. **Each base/head pair is run twice and a test that disagrees with
itself is excluded**, reported as a count.
