# What to say when someone asks

Four questions, in the order they get asked. Say the bold line, then stop — the paragraphs under
it are what to reach for **if** they push, not a script to recite.

---

## Read this before the first meeting

**Nothing is built yet.** `src/quantamind/` holds a package root and nothing else. The coverage
line, the routing and the verifier are stages two, three and four of
`docs/plans/implementation.md`, each behind a gate.

So **every answer below is in future or design tense, deliberately.** *"That is the line we are
building"*, never *"that is what we print."* To a customer the present tense is a product claim
about software that does not exist; to an investor it describes a materially different company
from the one the evidence documents. This is not pedantry — it is the line between a pitch and a
misrepresentation, and it has to be held in the room where nobody is checking.

**Do not explain how it works.** `publishing-rules.md` lists what must never leave the room.

---

## 1. "What is QuantaMind?"

> **We are building a code reviewer that tells you which parts of your change it actually looked
> at.**
>
> Every AI reviewer leaves comments. None of them says what it skipped. So when one is silent
> about a file, you cannot tell whether it examined the file and found nothing, or never really
> read it. Those are different facts and they arrive looking identical.

If they want a second sentence:

> We also will not read every file at the same depth. We work out which part of the change is
> riskiest and spend the effort there.

**Then stop.** Every extra sentence here explains the mechanism.

---

## 2. "How are you different from CodeRabbit or Greptile?"

**Do not say we see more files than they do.** It is false against Greptile — they index the
entire codebase — and claiming it loses the comparison in one sentence.

> **They see more than us. That is not the difference.**
>
> Greptile reads your whole codebase. CodeRabbit reads your whole diff. We are not trying to beat
> them on how much we look at. We are building the thing that tells you what was looked at.
>
> **Silence from a reviewer has two meanings and no tool separates them.** *Examined, nothing
> wrong* and *never really read* arrive as the same blank space. You cannot act on that, so you
> open the file and read it yourself — which is the work the tool was supposed to remove.

### Do not say "at 50% recall, silence is wrong as often as it is right"

**It is false, and a technical buyer can disprove it on a napkin.** Recall is the share of *real
issues* found. It says nothing about how often silence is wrong, because most files contain no
issue at all.

With `d` the share of files carrying a real defect and `r` recall, the chance that silence hides
one is `d(1−r) / (1 − dr)`:

| Defect base rate | Chance silence is wrong, at 50% recall |
|---|---|
| 5% | 2.6% |
| 10% | 5.3% |
| 20% | 11.1% |
| 50% | 33.3% |

**Reaching a coin flip needs roughly two thirds of every file in every pull request to carry a
real defect.** The claim overstates by five to ten times at any plausible rate, and it breaks
our own rule — *say two and be right*.

**And we do not need it.** The argument is about **type, not rate**: you cannot distinguish
*checked and clear* from *never read* at **any** recall. That holds at 90% as it does at 50%.
Anchoring it to today's numbers makes a permanent argument look temporary — if someone reaches
80% next year, the line reads as retired.

### If they ask about the benchmarks

Get the framing right, because it changed and the obvious version is now stale:

> Martian runs the only genuinely independent benchmark in this market — real pull requests,
> open-sourced pipeline. **Greptile currently leads it**: 60.8% F1 and 76.2% precision as of
> 30 July 2026, with **recall of 50.6%**. CodeRabbit led earlier on January–February data with
> 51.2% F1, 49.2% precision and **53.5% recall**.

**Do not say "they both came first, both are true."** It is one leaderboard and two dates.
CodeRabbit's claim is months stale, and Greptile now leads on F1 *and* precision.

**Do not say "the best tools catch about half."** Recall sits near half for both leaders;
precision does not — it runs from 49.2% to 76.2%. The field is not uniformly at half.

**Say "recall on the Martian benchmark", never "catches half the bugs."** Recall against a
curated set of verified issues is not the share of all defects in a diff, and we do not know
which denominator produced those figures.

---

## 3. "Anyone could add that. Why can't they just build it?"

**This is the investor question**, and it has to be answered with the architecture, not with
marketing.

**Do not say "it is a hard thing to want" or "they will not do it because it hurts their
numbers."** Our own master document throws that out: *marketing positions reverse in a quarter.*
An unfalsifiable claim about a competitor's willpower is the weakest answer available.

**And do not defend the coverage line as the moat.** Our own competitor timeline rates it at
**two to three months** for a funded competitor. Defending the deal-deciding objection with the
shortest-lived item on the board is a mistake.

> **You are right that a coverage line is not hard. It is also not the moat, and I would not
> pitch it as one.**
>
> To emit *"41 of 43 call sites resolved, 2 unresolved — dynamic dispatch in registry.py"* you
> need three things: a parser that enumerates call sites, a resolver that attempts each one, and
> a typed record of every failure. **A retrieval-plus-prompt pipeline has no component that
> produces that number.** It is a different layer of software, and reading the diff more deeply
> does not produce it — dynamic dispatch does not resolve at any depth.
>
> So they must build a layer they do not have. And the first thing it does when they turn it on
> is tell their customers how much of each diff their reviewer never understood.

**Then move to the two things that are actually permanent**, because that is what the question
deserves:

> **A reviewer cannot credibly publish its own miss rate.** Not because it would refuse — because
> no buyer would believe it, the way no company audits its own books. You have four vendors
> claiming first place on the same leaderboard; that is the market pricing this in already.
>
> **And the measurement underneath is broken.** The standard rule for attributing a fix back to
> the change that caused it is **wrong on 67.9% of its verdicts** — measured here, reproduced
> three times. Every dashboard telling you where rework comes from is built on it.
>
> That is the company: **the only trustworthy answer to "is this working", in a market where
> every existing answer is two thirds wrong.** The reviewer is how we earn the right to sell it.

---

## 4. "Why does the coverage line matter?"

**Two separate features, and conflating them is the easiest mistake to make in a room.**

| | What it does | Status |
|---|---|---|
| **Routing** | says which part of the change to read first | **Unproven.** Whether a reviewer shown it before the defect exists catches anything they otherwise would not is our largest open question |
| **Coverage line** | says which parts could not be analysed | The thing we can stand behind |

**Do not tell the "reviewer said nothing about the payment function" story as a coverage-line
story.** In our own worked example that function is rank 1 and gets the deep read — the coverage
line reports the *unresolved* region, not the analysed one. That story sells routing, and routing
is the untested half.

Tell it about the unresolved region instead:

> Your change touches a handler that is registered at runtime rather than called directly.
> Every reviewer on the market reads past it, silently, because a dynamic registration is not a
> call it can follow. Nobody tells you. **The review comes back clean and the gap is invisible.**
>
> We will name it: *four call sites unresolved, dynamic dispatch in registry.py.* Not a finding —
> an admission, in the place where you can still act on it.

Then land it:

> Where it says *checked*, you stop re-reading. Where it says *not checked*, that part is yours,
> named, before you merge instead of after something breaks.

**If you get one line only:**

> *A reviewer that tells you which parts it could not analyse is one you can build a process
> around. One that stays quiet about them is a coin toss with a subscription.*

**And be ready for the honest follow-up.** We intend to speak on roughly one pull request in ten.
On the rest there is a coverage line and no finding. If they ask whether we would have caught
their last incident, the answer is *"possibly not — but you would have known which parts we never
examined."* Say that before they work it out.

---

## Two things to have ready

**When they ask for our benchmark:**

> We do not publish one. Benchmarks are chosen by the vendor — four companies are currently
> claiming first place on the same leaderboard. Give us a repository and we will run it on your
> own history, and you can check the answer yourself.

**When they ask what we are worse at.** Answer fast; hesitating costs more than the admission:

> CodeRabbit writes your unit tests, answers questions in the pull request, scans for
> vulnerabilities, and has a free tier that posts findings. Greptile indexes your whole
> repository and answers questions about it. We build none of that, and we are not better at
> finding bugs than either of them.

---

## Numbers that must not be said

- **"They only check 61% of a change."** Invented. There is no measurement anywhere in our
  corpus of what a competitor's coverage would be. It will be heard as measured.
- **Our own reviewer catch-rate observation (10 of 65).** It exists, and the master document
  says of it: *treat this as an observation, not a finding, and do not put it in front of that
  vendor.* No control, and 65 observations cannot separate 15.4% from 23.9%. It supports
  *"nobody has published a catch rate and the one we measured was not high"* — nothing narrower,
  and never with the vendor named.
- **Any accuracy figure of our own.** See `publishing-rules.md`.

**Re-check the two Martian figures before any meeting where you quote them.** The ranking has
already turned over once.
[CodeRabbit's post](https://www.coderabbit.ai/blog/coderabbit-tops-martian-code-review-benchmark) ·
[Greptile's post](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark)
