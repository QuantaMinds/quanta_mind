# What to say when someone asks

Four questions, in the order they actually get asked. Say the bold line, then stop — the
paragraphs under it are what to reach for **if** they push, not a script to recite.

**Do not explain how any of it works.** `publishing-rules.md` lists what must never leave the
room, and the reason to hold that line in conversation is the same as on the website: the
retrospective proves every claim without explaining any of it.

---

## 1. "What is QuantaMind?"

> **We are a code reviewer that tells you which parts of your change it actually looked at.**
>
> Every AI reviewer leaves comments. None of them tells you what it skipped. So when it says
> nothing about a file, you cannot tell whether it checked and cleared it, or never really read
> it. We print that line.

If they want a second sentence:

> We also do not read every file at the same depth. We work out which part of the change is
> riskiest and spend the effort there.

**Then stop.** The next question is theirs to ask, and every extra sentence here is one that
explains the mechanism.

---

## 2. "How are you different from CodeRabbit or Greptile?"

**Do not say we see more files than they do.** It is the weakest ground available and it is not
true against Greptile — they index the entire codebase. Claim to see more and they win the
comparison in one sentence, and the meeting with it.

> **They see more than us. That is not the difference.**
>
> Greptile reads your whole codebase. CodeRabbit reads your whole diff. We are not trying to
> beat them on how much we look at. We tell you what we looked at.
>
> **Their own numbers make the point better than ours would.** CodeRabbit's post announcing they
> came first on Martian's independent benchmark reports **53.5% recall**. Greptile's post
> announcing *they* came first reports **50.6%**. Both are true — it is a rolling leaderboard and
> each announced the week it led.
>
> So the best tools catch about half. Fine — nobody is better. **But at 50%, when the tool goes
> quiet on a file, that silence is wrong about as often as it is right, and you have no way to
> tell which.** So you open the file and read it yourself. You are paying for a reviewer and
> doing the review.
>
> We give you the line that makes the silence readable.

---

## 3. "Anyone could add that. Why can't they just build it?"

**This is the objection that decides the deal.** Concede the engineering immediately — arguing
it is hard makes you sound like you have not thought about it — then explain why it will not
happen anyway.

> **You are right. It is not hard to build. That is not what stops them.**
>
> Think about what that line would say on their product. A tool marketed as *catches what humans
> miss* would have to print **"checked 61% of this change."** Every review becomes an admission
> against their own marketing.
>
> **We can print it because we never claimed to read everything. They cannot, because they did.**
>
> And it is worse than embarrassing — it is architectural. They read the whole diff at one
> depth, so their honest coverage line is either always 100%, which tells you nothing, or it
> reveals that reading everything is not the same as examining everything. Neither is a good day
> for them.

Close it:

> **It is not a hard feature. It is a hard thing to want.** A company adds this the year after it
> stops competing on catching the most bugs — and not one of them has stopped.

---

## 4. "Why does 'tells you what it did not check' matter?"

**Do not argue it. Make them picture it.**

> A pull request comes in. Nine files. The reviewer leaves four comments — a naming suggestion,
> a tidier loop, two things you already knew.
>
> It says nothing about the payment function.
>
> You ship it. Two weeks later refunds are wrong and somebody loses a Thursday.
>
> Now go back and read that review again. **It never said that function was fine. It just did
> not mention it.** And there was no way to tell those two things apart.

Then land it:

> That is what the line fixes. Where it says *checked*, you stop re-reading — that is your time
> back. Where it says *not checked*, that part is yours, named, **before you merge instead of
> after something breaks.**
>
> It does not fix the 50%. Nothing on the market fixes the 50%. It makes it something you can
> act on.

**If you get one line only:**

> *A reviewer that misses half the bugs and tells you which half it looked at is a tool you can
> build a process around. One that misses half and stays quiet about where is a coin toss with a
> subscription.*

---

## Two things to have ready

**When they ask for our benchmark:**

> We do not publish one. Benchmarks are chosen by the vendor — there are four companies right
> now each claiming first place on the same leaderboard. Give us a repository and we will run it
> on your own history, and you can check the answer yourself.

**When they ask what we are worse at.** Answer fast and specifically; hesitating here costs more
than the admission does:

> CodeRabbit writes your unit tests, answers questions in the pull request, scans for
> vulnerabilities and has a free tier that posts findings. Greptile indexes your whole
> repository and will answer questions about it. We build none of that. If you need it, buy
> theirs — and we are not better at finding bugs than either of them.

---

## Before any meeting where you quote a number

**Re-check the two recall figures.** They come from a leaderboard that moves — Greptile's July
position already replaced CodeRabbit's March one. Being corrected on a competitor's number in
the room costs far more than the number was worth.

Sources: [CodeRabbit's announcement](https://www.coderabbit.ai/blog/coderabbit-tops-martian-code-review-benchmark) ·
[Greptile's announcement](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark)
