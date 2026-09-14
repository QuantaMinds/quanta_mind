# Pricing

**This page is written to be published.** It follows `publishing-rules.md`: say what the customer
gets, never how it is worked out. The build status of each line, the cost behind the margins and
the tier arithmetic are internal and live in `unit-economics.md` — do not merge the two files.

> **THREE THINGS MUST NEVER BE ADDED TO THIS PAGE, AND ALL THREE WERE ON THE LIVE SITE ON
> 2026-09-11 WHILE THIS FILE SAID OTHERWISE.**
>
> 1. **"We hold no copy of your code."** We do. `serve/working_clone.py` keeps a full clone and
>    fetches it on every use; `sweep()` deletes the least recently used ones. The honest version is
>    in "What happens to our code?" below and it is a better answer — **a retention claim that is
>    false is the one mistake on this page that becomes a contract problem rather than a
>    credibility problem.**
> 2. **A scheduled or automatic export.** The compliance artefact is produced by a command somebody
>    runs. Nothing produces one periodically, and nothing in the build plan does.
> 3. **A price for bring-your-own-model-key.** That row is parked (decision 2026-08-27). A price
>    published for something nobody can buy is the same error as a feature published for something
>    nobody built.

---

|  | **Free** | **Team** | **Enterprise** |
|---|---|---|---|
|  | **$0** | **$29** per developer / month | **from $60** per developer / month |
|  | up to 10 developers | unlimited | unlimited |
|  | Your rules, enforced on every pull request | Everything in Free, across your whole team | Everything in Team, plus the controls procurement asks for |

---

## What you get

| | Free | Team | Enterprise |
|---|:--:|:--:|:--:|
| **The rules you write down are enforced on every change** — not remembered, not applied differently by each reviewer | ✅ | ✅ | ✅ |
| **Work that breaks them does not merge** ¹ | ✅ | ✅ | ✅ |
| **Review attention goes to the riskiest changes first**, from your repository's own history | ✅ | ✅ | ✅ |
| **A reviewer sees the answer before they open the pull request** | ✅ | ✅ | ✅ |
| **Every check, on every file, on the record** — and what could not be checked, named | 30 days | full history | full history |
| **Evidence you can hand to an auditor** — exportable on demand, recorded as it happens, never backfilled, never edited ² | — | ✅ | ✅ |
| **One signed-in dashboard covering every repository you install** — what was reviewed, what it found, what it cost | ✅ | ✅ | ✅ |
| **Catch it before you open the PR** — from your editor's agent or the command line, on uncommitted work and untracked files. Nothing leaves your machine | ✅ | ✅ | ✅ |
| **A machine-readable answer** your own tools and agents can act on | ✅ | ✅ | ✅ |
| **Your code is never used to train anything** — and we say plainly what we do keep ³ | ✅ | ✅ | ✅ |
| **Define a standard once; every repository is held to it** | — | — | ✅ |
| **Runs where your policy requires** — your cloud, your region, or your own hardware | — | — | ✅ |
| **SSO, a signed DPA, and an SLA** | — | — | ✅ |

¹ Blocking a merge relies on your host's required-check setting. GitHub reserves that for paid
plans on private repositories; on a free private repository the result is posted and visible, but
your host will not enforce it.

² You run the export when you need it. We do not mail you one on a schedule.

³ One working copy of your repository, on our servers, used for reviewing and nothing else. See
"What happens to our code?" below.

---

## What it is for

**Free — your rules, enforced.** Everything a team needs to hold itself to the rules it has
written down, at no cost, with no expiry. Up to ten developers.

**Team — $29 per developer, per month.** The same across an unlimited team, with the full
recorded history and a report on every repository. **That is less than twenty minutes of one
engineer's time a month.** It is a fair bar to hold us to, and it is the one we would use.

**Enterprise — from $60 per developer, per month.** For organisations where the question is not
whether the tool works but whether it is allowed: one standard across every repository, deployment
where your policy requires, SSO, a DPA, an SLA.

---

## Questions we get

**Do you have a benchmark?**
We do not publish one. Benchmarks are chosen by the vendor. Give us a repository and we will run it
against your own history, and you can check the answer yourself.

**You name what you could not check. Does that mean the rest is verified?**
No. Naming what we did not check is not a claim about what we did. It is there so you can see the
edge of the answer instead of assuming there isn't one.

**Will this find more bugs than what we use now?**
We do not claim that, and we would rather you test it than take our word. What we will claim is
that your standards get applied the same way every time, and that you can prove it afterwards.

**What happens to our code?**
It is never used to train any model. To review a change we keep a working copy of your repository
on our servers, because a review reads its history — that copy is what the reviewing happens
against, and it is used for nothing else.

**Is the free tier a trial?**
No. It does not expire and it does not degrade. **We would not claim that as a differentiator** —
CodeRabbit and Greptile both run permanent free tiers too, and theirs carry no seat limit where
ours stops at ten developers. Ours is here so a team can start keeping a record today, not because
it is more generous than everyone else's.
