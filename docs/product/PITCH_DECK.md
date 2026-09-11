# QuantaMind

### Your team already wrote the rules. We make sure nobody breaks them.

**Pre-seed · Raising $500K**

---

> ## The 15-second version
>
> **Robots now write a lot of the code. Humans still have to check all of it. They can't keep up.**
>
> Every team already wrote down how their code should be written. Nobody enforces it.
>
> **We check every change against your team's own rules. If a change breaks one, it can't go in.**
>
> And we tell you which parts we looked at — and which parts we did not.
> **No other tool will tell you that.**

---

## 1 · The Problem

**Checking code is like marking homework. The pile just got three times bigger. The teachers did not.**

| What is happening | The number |
|---|---|
| Code written by AI, today | **42%** — heading to **65%** next year |
| Developers who don't fully trust AI code | **96%** |
| AI-written changes that actually get accepted | **33%** — human-written ones: **84%** |
| Top reason they get thrown away | **Nobody got to them in time** |
| Senior engineer time spent checking code | **8–12 hours a week** |

**So teams bought robot helpers to check the robot code. It got worse.**

An independent audit of the biggest one found **36% of its comments were noise or nitpicking**.
The pile went from 20 changes to 60, and each one now arrives buried in bot comments.

> **The real problem is not finding bugs. It is attention.**
> Every tool answers a flood by making more text. You cannot fix a "too much to read" problem
> by writing more.

**And there is a second problem underneath it.** Every team has a written guide — *"this is how
we do things here."* It sits in a file nobody enforces. It is remembered by whoever happens to be
looking that day. **And the AI writing most of your code has never read it.**

---

## 2 · The Solution

**We do two things. Both are boring. That is why they work.**

### One — we enforce your rules

We read the guide your team already wrote. We check every single change against it.
**Break a rule, and the change cannot go in.** Not a comment. Not a suggestion. A locked door.

- You write nothing new. We read the files you already keep.
- Same answer every time. Run it again on the same code, get the same result.
- **Every check is written down** — including the ones we could not decide. Those are named, not
  quietly counted as "fine."

### Two — we say where to look, and where we did not look

We tell a human which part of the change deserves their eyes first. Then we print a plain line
saying **which files we read and which we did not.**

> **Why that line matters, in one sentence:**
> When a robot checker says nothing about a file, you cannot tell if it *looked and found nothing*
> or *never looked at all*. Those are completely different. They look identical. So a careful
> person re-reads it anyway — which is the work you paid the tool to remove.

**We are honest about the other half.** We do **not** claim to find more bugs than anyone else.
Nobody in this market has shown they do. We do not sell that, and nothing in our price depends on it.

---

## 3 · Why Now

**Four things became true at the same time. None of them were true three years ago.**

1. **Machines started writing the code.** 42% today, 65% next year. The thing writing your code
   has never read your team's guide.
2. **The pile tripled. The checkers didn't.** Work that was paid for now dies waiting — the single
   biggest reason AI changes get thrown away is that nobody got to them.
3. **The robot checkers made it noisier.** A third of what the market leader writes is not worth
   reading. Everyone now knows this.
4. **Somebody is about to be asked to prove it.** Auditors and customers are starting to ask
   *"show me this code was actually checked."* Today, nobody can answer. **The answer is a record,
   and a record only exists if you started keeping one.**

---

## 4 · How It Works

**Four steps. A developer sees only the last one.**

```
  Someone proposes a change
        │
   1 ▸  WE CHECK THE RULES          your team's own guide, every change, every time
        │                           → passed · broken · couldn't tell · not our job
        │                           → four answers, never two
        │
   2 ▸  WE PICK WHERE TO LOOK       using your repository's own history
        │
   3 ▸  WE READ, ONLY THERE         and a second, independent checker throws out
        │                           anything it cannot confirm
        │
   4 ▸  WE ANSWER                   ✗ a locked door if a rule is broken
                                    ▸ where a human should look first
                                    ▸ and what we did NOT look at
```

**Step 1 never guesses.** A machine decides it, and you can run it again tomorrow and get the same
answer. That is the part we sell.

**"Couldn't tell" is a real answer.** If a file cannot be checked, we say so. We never count it as
passing. Everyone else has two answers — pass or fail — so an unreadable file quietly becomes a
tick. **An auditor who learns that once stops believing the whole report.**

### The part that makes people say yes

**We can show you your own answer before you install anything.**

Give us a copy of your repository. We replay your last six months and show you what we would have
said — on your code, your history, your team. No sign-up, no access, nothing leaves your machine.

> *We do not publish a benchmark. Benchmarks are chosen by the vendor.
> Give us a repository and we will run it on your own history, and you can check the answer yourself.*

---

## 5 · Market Size — built from the bottom up

**No "1% of a big number." We counted customers and multiplied by the price.**

| | Who | Count | × price/year | Size |
|---|---|---|---|---|
| **TAM** | Every professional developer in the world | 28.7M | $348 | **$10.0B** |
| **SAM** | US professional developers — our first market | 4.4M | $348 | **$1.5B** |
| **SOM** | 1,500 companies, ~40 developers each, in 3 years | 60,000 | $348 | **$21M ARR** |

*$348 = $29 per developer per month, our middle tier.*

**Why we think 1,500 companies is real, not a wish:** every one of them can be shown their own
answer before they pay anything. Our first market is teams already on GitHub with enough history
to replay — which is most teams that have existed for two years.

---

## 6 · Competition — how we are different

| | CodeRabbit | Greptile | Qodo | **QuantaMind** |
|---|---|---|---|---|
| What it tells you | *this line is wrong* | *this is wrong architecturally* | *this is wrong, here's a test* | **this broke a rule you wrote** |
| Enforces YOUR written rules | ✗ | ✗ | ✗ | **✓** |
| Can it stop a bad change | it comments | it comments | it comments | **✓ a locked door** |
| Same answer if you run it again | ✗ | ✗ | ✗ | **✓** |
| Can you prove what was checked | ✗ | ✗ | ✗ | **✓ every rule, every file** |
| Says what it could NOT check | ✗ | ✗ | ✗ | **✓** |
| Free forever | trial | trial | credits | **✓ never expires** |

**The one-line difference:**

> **They all answer "is this code wrong?" — which is an opinion.
> We answer "does this break a rule you already agreed to?" — which is a fact.**

### Why a big company cannot just copy this in a month

- **The scorer cannot be the player.** A tool that reviews your code cannot credibly tell you how
  much it missed — the same reason no company audits its own books. Four vendors currently claim
  to be #1 on the same scoreboard. Nobody publishes what they got wrong.
- **You cannot add "what I missed" later.** Saying *what you could not check* means knowing it,
  every step, from the first line of output. A tool not built that way from day one does not have
  the information to start. And the first thing it would say, if it could, is how much of your code
  its own reviewer never understood.
- **They cannot give away what we give away.** Every review they run costs them money, so their
  free tier is a trial with an end date and their demo is a toy project. **Ours doesn't expire,
  and our demo is your actual code.**

### What we are NOT better at — said before you ask

CodeRabbit writes your tests, answers questions, scans for security holes, and has a bigger free
tier. Greptile reads your whole codebase and answers questions about it. **We build none of that,
and we are not better than either of them at finding bugs.** Nobody has shown they are better at
that — them or us. **We sell the part that does not depend on a guess being right.**

---

## 7 · Pricing

**One number a buyer can compare: per developer, per month.**

| | **Free** | **Team** | **Enterprise** |
|---|---|---|---|
| | **$0** | **$29** /dev/month | **from $60** /dev/month |
| | up to 10 developers | unlimited | unlimited |
| | Your rules, enforced | Everything, whole team, full history | Plus what procurement asks for |

**The free tier never expires and never gets worse.** It is not a trial.

**Why $29 is easy to say yes to:** one senior engineer spends **8–12 hours a week** checking code
— roughly **$28,000–$42,000 a year**. At $348 a year, we pay for ourselves if we give back
**twenty minutes per developer per month.** That is the bar. We would hold us to it too.

---

## 8 · Team

**Four people. Three of us have known each other seven years, since engineering school, and
built systems projects together before this.**

| | | |
|---|---|---|
| **Dhanush G** | **CEO** | 2+ years in Systems Engineering — test engines, agent pipelines |
| **Chirag V K** | **CTO** | 5+ years in backend, infrastructure and hardware testing |
| **KN Gowri** | **CDO** | 3+ years as a Data Scientist — data pipelines, test sets, validation |
| **Aanya Sampath** | **COO** | Operations and go-to-market |

**Why this team for this problem:** this is a testing and measurement company wearing a code-review
coat. Between us we have spent years building **test engines, data pipelines and validation sets**
— deciding whether a result is real. That is the entire job here. The hard part of this product was
never writing the checker; it was proving the checker was right, and then proving it again on
repositories we had never seen.

---

## 9 · The Ask

# $500,000

**18 months of runway for four people, to turn a working product into a paying one.**

| Where it goes | Why |
|---|---|
| **Let people pay us** | The product runs. There is no checkout. This is the shortest gap between us and revenue |
| **First 25 design partners** | We can show each of them their own answer for free. Nobody has run that play yet |
| **Widen what we can enforce** | More languages, more rule types — each one widens who can buy |
| **The evidence product** | Turn the record we already keep into the report an auditor asks for |

### What you get

- **A category nobody occupies.** Every competitor sells opinions about code. We sell proof about
  process. That is closer to Semgrep and SonarQube than to a chatbot — and it carries their price,
  not a chatbot's.
- **A sales motion no competitor can run.** We hand a prospect their own six months of history
  before they sign anything. For a tool that pays a model on every change, that demo costs them
  real money per prospect. For us it is cheap.
- **A team that kills its own ideas.** Our first product idea was tested, came back empty, and we
  killed it rather than defend it. The thing we build now is the one claim that survived — and then
  **reproduced on repositories it had never seen.** That is unusual, it is checkable, and it is why
  the claims on this page are ones we will still stand behind in a year.

### Where we are honest

**No customers yet. No revenue yet.** The product runs end to end and is tested against real
repositories, not mock-ups. What we have not yet proven is that a buyer will pay for it — and the
$500K is to find that out quickly, with the cheapest demo in the category.

---

## Where these numbers come from

**Every figure on this page is somebody else's published number or our own measured one. None is
an estimate dressed as a fact.**

| Claim | Source |
|---|---|
| 42% of code is AI-written, 65% by 2027; 96% don't fully trust it | Sonar, *State of Code*, 8 January 2026, 1,100+ developers |
| AI changes accepted 33% vs 84%; top rejection reason is inactivity | LinearB *Engineering Benchmarks 2026*, 8.1M pull requests, ~4,800 teams |
| 36% of the market leader's comments are noise or nitpicking | Independent audit of 28 pull requests, 32,784 lines, 693 files — reported, not confirmed by us |
| 8–12 hours a week reviewing; $28,000–$42,000 a year | Industry figures at a $150K salary |
| 28.7M professional developers worldwide; 4.4M in the US | Developer-population surveys, 2026 |
| Our own routing result | Measured here, replicated on repositories the method had never seen. Numbers and full method on request |

**What we deliberately do not put on a page:** our own accuracy, precision or recall. Two reasons —
it tells a competitor what to optimise, and one number invites an argument about method.
**We would rather hand you your own number, computed on your own repository.**

---

*Company detail and every measurement behind these claims: `docs/product/QUANTAMIND.md`.
What may and may not be said in public: `docs/product/publishing-rules.md`.*
