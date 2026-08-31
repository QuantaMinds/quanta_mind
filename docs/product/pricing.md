# Pricing

**This page is written to be published.** It follows `publishing-rules.md`: say what the customer
gets, never how it is worked out. The build status of each line, the cost behind the margins and
the tier arithmetic are internal and live in `unit-economics.md` — do not merge the two files.

---

|  | **Free** | **Team** | **Enterprise** |
|---|---|---|---|
|  | **$0** | **$29** per developer / month | **from $60** per developer / month |
|  | up to 10 developers | unlimited | unlimited |
|  | Your standards, enforced on every pull request | Everything in Free, across your whole team | Everything in Team, plus the controls procurement asks for |

**Bring your own model key: $26** per developer / month on Team.

---

## What you get

| | Free | Team | Enterprise |
|---|:--:|:--:|:--:|
| **The standards your team already wrote are enforced** — not remembered, not applied differently by each reviewer | ✅ | ✅ | ✅ |
| **Work that breaks them does not merge** ¹ | ✅ | ✅ | ✅ |
| **Review attention goes to the riskiest changes first**, from your repository's own history | ✅ | ✅ | ✅ |
| **A reviewer sees the answer before they open the pull request** | ✅ | ✅ | ✅ |
| **Every check, on every file, on the record** — and what could not be checked, named | 30 days | full history | full history |
| **Evidence you can hand to an auditor** — every check recorded as it happens, never backfilled, never edited | — | ✅ | ✅ |
| **One dashboard for the whole estate** — what was reviewed, what it found, what it cost | ✅ | ✅ | ✅ |
| **Catch it before you open the PR** — locally, including uncommitted work | ✅ | ✅ | ✅ |
| **A machine-readable answer** your own tools and agents can act on | ✅ | ✅ | ✅ |
| **Your code is never used to train anything** | ✅ | ✅ | ✅ |
| **Define a standard once; every repository is held to it** | — | — | ✅ |
| **Runs where your policy requires** — your cloud, your region, or your own hardware | — | — | ✅ |
| **SSO, a signed DPA, and an SLA** | — | — | ✅ |

¹ Blocking a merge relies on your host's required-check setting. GitHub reserves that for paid
plans on private repositories; on a free private repository the result is posted and visible, but
your host will not enforce it.

---

## What it is for

**Free — your standards, enforced.** Everything a team needs to hold itself to what it has already
written down, at no cost, with no expiry. Up to ten developers.

**Team — $29 per developer, per month.** The same across an unlimited team, with the full
full recorded history and a dashboard over every repository. **That is less than twenty minutes of one
engineer's time a month.** It is a fair bar to hold us to, and it is the one we would use.

**Enterprise — from $60 per developer, per month.** For organisations where the question is not
whether the tool works but whether it is allowed: one standard across every repository, deployment
where your policy requires, SSO, a DPA, an SLA.

**Bring your own model key — $26.** Use your own provider account, your own rates and commitments,
your own data-retention terms. Available on Team and Enterprise.

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
No. It does not expire and it does not degrade.
