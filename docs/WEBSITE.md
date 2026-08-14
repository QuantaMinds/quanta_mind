# Website copy, SEO, and what stays off the site

Nine pages, written to be read by a busy engineer in under a minute each. Plain words. No
"seamless", no "revolutionise", no "empower", no "leverage". Short sentences. If a ten-year-old
could not follow a sentence, it gets rewritten.

**One rule runs through all of it: describe what the customer gets, never how it is computed.**
The list at the end says exactly what must never appear on the site, and why.

---

## The writing rules

- **Say the thing, then stop.** No sentence exists to sound impressive.
- **Numbers only where we would defend them under questioning.** If a number needs three
  sentences of caveat, it belongs in the report we hand the customer, not on a page.
- **Never claim to catch more bugs.** We do not, and the first customer to test it will find out.
- **Name the weakness before the reader does.** It is the only thing on the site a competitor
  cannot copy in a week, because copying it means admitting the same weakness.
- **Every page ends with one action.** Not three.

---

# Page 1 — Home `/`

**Read the copy straight through first.** It is written to be read aloud, top to bottom, as one
piece — each section hands off to the next. Layout notes are kept out of the way, at the end.

Nothing here says how the product works internally. That is deliberate and the reasons are in
*What never goes on the website*.

---

---

## THE PAGE

---

### *(hero)*

# The file nobody checked looks exactly like the file that was fine.

When a code reviewer says nothing about a file, you cannot tell which one it is.

**We tell you which one it is.**

**[ See it on your own code ]**   ·   How it works →

---

### *(section)*

## Two weeks later

Someone opened a pull request. Nine files. The AI reviewer left four comments — a naming
suggestion, a tidier loop, two things everybody already knew.

It said nothing about `process_refund`.

The change was approved. It shipped. Two weeks later, refunds were wrong, and somebody lost a
Thursday finding out why.

---

### *(section)*

## Now go back and read that review again

It never said `process_refund` was fine.

It just did not mention it.

**And there was no way to tell those two things apart.**

---

### *(section)*

## That is the thing we fixed. Not the refund — the silence.

Every AI reviewer reads your change and writes down what it noticed. Whatever it did not get
to, it simply does not mention.

So silence means two completely different things, and they arrive looking identical:

*This is fine.*

*I did not really look here.*

You cannot tell. So you half-trust the review, read the code yourself anyway, and pay for both.

---

### *(section)*

## We do two things

**We decide where to look before we look.**

Not every file in a change deserves the same attention. Pretending otherwise is where the noise
comes from, and where the bill comes from.

**We publish where we looked.**

Every review ends by saying what we checked and what we did not, and why.

That is the whole product. No test generation, no security scanner, no chat, no dashboard.
Other people build those, and build them well.

---

### *(section)*

## What you actually get

```
QuantaMind

Checked      2 files · 3 functions
Not checked  1 file — generated · 4 call sites — could not resolve

In process_refund, the partial-refund path returns before the ledger
entry is written. On a full refund the entry is written at line 88.
The new early return at line 71 skips it.
```

Two lines you have never had from a review tool, followed by the finding.

Most changes get no finding at all. They still get the two lines.

---

### *(section)*

## What changes on Monday

You open a pull request and read the comment, the way you always have.

Then you read one line telling you how much of that change it actually covers.

If it covers most of it, you approve.

If it covers half, **you now know which half still needs you** — and you have never known that
before, from any tool.

---

### *(section)*

## Do not believe any of this. Check it.

Give us read access to one repository.

We go back over your last six months of merged pull requests and show you, change by change,
where we would have pointed — and whether a later fix landed there.

**You will not be reading our claims. You will be reading your own history.**

**[ Get the report ]**

Free. Nothing installed. Nothing written to your repository. Most come back the same day.

---

### *(section)*

## What we are not

We are not better at finding bugs.

Nobody is much better than anyone else at that right now, and any vendor telling you otherwise
is selling. We will not build our pitch on it.

We are better at telling you where we looked. That is a smaller claim, and it is one we can
keep.

So, honestly:

If you want the most features today, use **CodeRabbit**.

If reading your whole codebase for context matters more to you than knowing what got skipped,
use **Greptile**.

If your team has quietly stopped reading the comments, talk to us.

---

### *(section)*

## Questions people actually ask

**Do you find more bugs than the others?**
No. See above. We are selling the coverage line, not a longer list.

**Will it comment on everything?**
No. Most pull requests get the two lines and nothing else. A reviewer that comments on
everything is not reviewing, it is decorating.

**Where does my code go?**
Only the specific parts being reviewed leave your repository, and on our larger plans they go to
your own account instead of ours. The details are on the security page, in full.

**Do you train on my code?**
No. Not us, and not the model provider — that is off by contract.

**What if I do not trust any of this?**
Start with the report. It costs you read access to one repository and ten minutes, and you can
check every line of it against what you remember happening.

---


### *(section)*

## One last thing

If the report is not useful, you have lost ten minutes and given nobody your code.

**[ Get the report ]**

---

### *(footer)*

```
QuantaMind
The code reviewer that tells you what it did not check.

PRODUCT           COMPARE            COMPANY          LEGAL
How it works      vs CodeRabbit      Contact          Privacy
Pricing           vs Greptile        Changelog        Terms
Docs                                                  DPA
Security                                              Sub-processors

GitHub · LinkedIn · hello@quantamind.co

© 2026 QuantaMind
```

---

---

## THE DESIGN

Notes by section, kept out of the copy so the copy can be read as a page.

### Overall

- **One column, centred, roughly 640px of text.** This page is an argument, and an argument
  reads down, not across. Multi-column marketing grids exist to fill space we do not need.
- **Two typefaces at most.** Code in monospace, everything else in one sans.
- **One accent colour, used only on buttons and the coverage line.** If the accent appears in
  five places it stops meaning "act here".
- **Plenty of vertical space between sections.** The page's rhythm is the story's pacing; a
  cramped page reads as a pitch, a spaced one reads as an explanation.
- **No illustrations, no stock photography, no abstract 3D shapes.** The only picture on the
  page is the review comment, because that is the actual product.

### Hero

Text left-aligned, not centred — centred headlines read as slogans, left-aligned reads as
someone talking to you. The review comment sits to the right on desktop and directly beneath on
mobile. **Show the artefact above the fold.** No animation.

### "Two weeks later"

Set slightly larger than body text and given the most space on the page. This is the only
section carrying a scene, so let it breathe. `process_refund` in monospace both times it
appears, so the eye connects them.

### "Now go back and read that review again"

Short lines, large spacing, each on its own line. **This is the turn of the argument** and it
should take four seconds to read, not one.

### "That is the thing we fixed"

The two italic lines — *This is fine* and *I did not really look here* — sit side by side on
desktop, identical in every respect. **The design makes the point: they look the same.** Stacked
on mobile, still identical.

### "We do two things"

Two blocks, stacked, not a three-column feature grid. The closing paragraph naming what we do
not build is set in muted text — an aside, not a boast.

### "What you actually get"

A real terminal block with the site's code styling. `Checked` and `Not checked` in the accent
colour. **Do not screenshot this** — real text so it can be copied, read by a screen reader, and
indexed.

### "What changes on Monday"

Three short paragraphs with real space between them. The if/then pair reads as a decision, so
give the two branches their own lines.

### "Do not believe any of this"

**Full-bleed band, background colour change, the only one on the page.** This is the centre of
gravity and it sits two-thirds down, not at the end. Button large. The "Free. Nothing
installed." line small and grey underneath.

### "What we are not"

Plain body text, no box, no card. **A design that decorates this section undoes it.** The three
competitor lines are ordinary paragraphs — no logos, no comparison table on the home page.

### Questions

Plain question-and-answer, all open. **No accordions.** A collapsed FAQ says "we would rather
you did not read this", and every answer here is one we want read.

### Price

Four lines of text, not four pricing cards. The full table lives on `/pricing`, and putting
cards here makes the home page end in a shop.

### Footer

Four columns on desktop, stacked on mobile. Muted, small, no newsletter box, no trust badges
until SOC 2 is real and dated. **`Changelog` ships as a real page or comes out of the footer** —
a dead footer link is the cheapest possible way to look abandoned.

### Performance

Server-rendered HTML. No framework needed for a page with one interaction. Under 100KB, loads
in under a second on a phone. **A code-quality product with a slow website is arguing against
itself.**

---

## What never goes on this page

Trimmed from the previous draft, because a site is read by competitors before it is read by
customers, and the free report proves every claim without explaining any of it.

| Cut | Why |
|---|---|
| **What the ranking is built from** | The earlier draft named the source in the second section. That is the product |
| **That part of the pipeline runs without a model** | It explains the cost structure, which explains why the free report is possible, which is the strategy. The offer stands alone without the reason |
| **The share of pull requests we comment on** | A tuned number. "Most get no finding" says enough |
| **How many repositories and changes we tested on** | Invites method questions and points at the source data |
| **The list of supported languages** | Belongs in the docs where it can be kept current. On a home page it becomes a promise the parser has to catch up to |
| **Any accuracy percentage** | Two reasons. It tells a competitor what to optimise, and one number invites a fight about method. **The report gives each customer their own number** — more convincing, and it gives away nothing |
| **Why competitors cannot match the free report** | Correct, and it is strategy written down for them. Make the offer; skip the reasoning |

**The line: say what the customer gets. Never say how it is worked out.**

When someone asks for the benchmark:

> *We do not publish one. Benchmarks are chosen by the vendor. Give us a repository and we will
> run it on your own history, and you can check the answer yourself.*

# Page 2 — Free report `/report`

# See where we would have pointed, on your own code.

Pick one repository. We read its history and replay the last six months of merged pull
requests. For each one we show the part of the change we would have flagged, and whether a
later fix went to that same place.

### What you get back

- Every merged pull request from the last six months, listed
- The function we would have pointed at, for each
- Whether a later fix actually landed there
- How much of the repository we can read, and what we cannot
- The parts of your codebase that have cost you the most repeat work

### What we need

- Read access to one repository. Nothing else.
- Ten minutes of your time when the report comes back.

### What we do not do

- We do not write anything to your repository.
- We do not post comments.
- We do not need an API key from you.
- We do not keep your code after the report is made.

**[ Send a repository ]**

### Why this is free

The part of our tool that decides where to look runs on ordinary computing, not an AI model.
Running it across your whole history is cheap for us. It is the most honest sales pitch we
have: you check our claim on your code before you give us anything.

---

# Page 3 — How it works `/how-it-works`

# How it works

Four steps. No magic in any of them.

### 1. We read your repository's history

Before any review, we build a picture of your codebase from its own past. This step uses no AI
model and no key. It is fast and it is the same every time you run it.

### 2. We rank the parts of your change

When a pull request opens, we split the change into the actual functions it touched. Then we
rank them, using what step one learned. The ranking decides where the effort goes.

### 3. We read the top of that list properly

The highest-ranked part gets a careful read. The next ones get a shorter look. Parts far down
the list get none — and **that is written into the review, not hidden.**

### 4. We check the answer before you see it

An AI model will sometimes describe code that is not there. So before anything is published, we
check the checkable parts of what it said against the real code. A claim that does not hold up
is dropped before you ever see it.

**We are clear about the limit of that check.** It can confirm that a function exists, that a
return really does come before a write, that a caller really is reachable. It cannot judge
whether logic is *wrong*. Nothing can do that reliably yet, including us. So the review is
checked where checking is possible, and the rest is labelled as a suggestion.

### What we do not claim

- We are not better at finding bugs than the other tools. Nobody is much better than anyone
  else at that yet.
- We do not find every bug. Neither does anything else you can buy.
- We do not read languages we cannot parse. We name them instead of skipping quietly.

**[ Get your free report ]**

---

# Page 4 — Pricing `/pricing`

# Pricing

Unlimited reviews on every paid plan. We are not going to bill you per review.

| | **Free** | **Team** | **Business** | **Enterprise** |
|---|---|---|---|---|
| | $0 | **$19** per developer / month | **$39** per developer / month | **$55** per developer / month |
| | forever | billed yearly | billed yearly | plus a yearly minimum |
| Ranking and coverage line | ✓ | ✓ | ✓ | ✓ |
| Free history report | ✓ | ✓ | ✓ | ✓ |
| Findings on pull requests | — | ✓ unlimited | ✓ unlimited | ✓ unlimited |
| All your repositories in one view | — | — | ✓ | ✓ |
| Quarterly written report | — | — | ✓ | ✓ |
| Single sign-on | — | — | ✓ | ✓ |
| Use your own AI key | — | — | ✓ | ✓ |
| Use your own AI model | — | — | — | ✓ |
| Run it on your own servers | — | — | — | ✓ |
| Audit logs, data location, support agreement | — | — | — | ✓ |

**[ Start free ]**  ·  **[ Talk to us ]**

### Which one am I?

- **Free** — you want to see whether this is real before you spend anything.
- **Team** — one team, one or two repositories, you want the reviews.
- **Business** — you run several teams and you want the report that tells you where the repeat
  work is happening.
- **Enterprise** — your security team needs to approve it first.

### Questions

**Do you charge for people who only read pull requests?**
No. Only people who open them.

**What counts as a review?**
Nothing. Reviews are unlimited on every paid plan. We do not count them.

**Why is your free plan smaller than CodeRabbit's?**
Because theirs runs an AI model and ours does not. Our free plan gives you the ranking, the
coverage line, and the full history report — it will not post AI findings on your pull
requests. We would rather be straight about that than pretend.

**Can I bring my own AI key?**
Yes, from Business up, for the models we have tested. For a model we have not tested, that is
Enterprise — because the coverage number has our name on it, and we will not publish a number
for a setup we have never measured.

**Does bringing my own key make it cheaper?**
No. You are paying for the ranking and the checking, not for tokens.

**Is there a discount for open source?**
Yes. Free, for public repositories.

**Can I cancel?**
Any time. Monthly plans stop at the end of the month.

---

# Page 5 — Docs `/docs`

Structure only — written by whoever builds each part.

- **Start here** — install, first review, reading the comment
- **The comment explained** — what "checked" and "not checked" mean, line by line
- **Settings** — which repositories, which branches, how noisy
- **Languages** — what we parse fully, partly, and not at all. **Kept honest and current.**
- **The weekly Slack message** — what it contains and how to turn it off
- **Your own AI key** — supported models, how to connect one
- **Running it yourself** — self-hosted setup
- **Limits** — what this tool does not do. A real page, not a hidden one.

---

# Page 6 — Security `/security`

# Security

Short, because the answers are short.

### Where does my code go?

The ranking step runs against a copy of your repository and sends nothing anywhere.

The reading step sends only the specific functions being reviewed to the AI provider — not your
whole repository, not your whole diff. On Business and above you can use your own key, so it
goes to your account instead of ours.

### What do you store?

The ranking data built from your history, and the reviews we posted. Not your source code.

### Do you train on my code?

No. Not us, and not the model provider — that is off by contract.

### Can I run it on my own servers?

Yes, on Enterprise.

### What access do you need?

Read on code. Write on pull request comments. Nothing else. We will not ask for more.

### Who do I tell about a vulnerability?

security@quantamind.co. We reply within one working day.

*Then: sub-processor list, data location options, retention periods, and a link to the DPA.*

---

# Page 7 — `/vs/coderabbit`

# QuantaMind vs CodeRabbit

CodeRabbit is the biggest AI reviewer, with about 17,000 customers. It is a real product and
this page is not going to pretend otherwise.

### Where CodeRabbit is stronger

- More features. Test generation, security scanning, IDE and CLI reviews, chat.
- A bigger free plan — it posts AI findings on your pull requests for nothing.
- More integrations, and more people have already used it.

### Where we are different

**It reads your whole change at one depth. We do not.** Reading everything at the same depth is
where the token bill comes from, and it is also where the noise comes from.

**It does not tell you what it missed.** No AI reviewer does. Every one of our reviews ends
with what we could not check.

**We will run on your history for free before you install anything.** They cannot — replaying
six months of your pull requests would cost them six months of AI bills.

### Price

CodeRabbit is $24 per developer per month, or $48 for the higher plan. We are $19.

### Who should pick which

**Pick CodeRabbit** if you want the most features today, or you want free AI comments and are
happy to filter them yourself.

**Pick us** if the noise has already made your team stop reading the comments, or if you need
to be able to say which parts of your code were actually checked.

**[ Get your free report and compare them yourself ]**

---

# Page 8 — `/vs/greptile`

# QuantaMind vs Greptile

Greptile reads your whole codebase for context and reviews pull requests against it. Over
22,000 teams use it.

### Where Greptile is stronger

- Whole-codebase context is genuinely useful on large repositories.
- It has been in the market longer and has more customers.

### Where we are different

**They now charge per review. We do not.** Greptile is $30 a seat with 50 reviews included and
$1 for each one after that. Ours are unlimited, and we are not planning to change that.

That difference is not a promotion. Their cost goes up with every review because every review
reads a lot. Ours does not, because most of our work does not use an AI model at all.

**They do not publish what they missed.** We do, on every review.

**We will run on your history before you sign anything.** They cannot do that at their cost.

### Price

Greptile is $30 per seat per month plus $1 per extra review. We are $19 per developer, with no
per-review charge.

**[ Get your free report ]**

---

# Page 9 — Contact `/contact`

# Talk to us

**Sales and demos** — sales@quantamind.co, or book 20 minutes: [link]

**Support** — support@quantamind.co. One working day.

**Security** — security@quantamind.co.

**Anything else** — hello@quantamind.co.

*One form: name, work email, company, repository host, message.*

---

# SEO

## The honest position first

"ai code review" is dominated by companies with years of content and links. **You will not win
it this year, and chasing it wastes the only time you have.** Everything below targets searches
where a small site can rank because the big sites have not written the page.

## Money pages, in priority order

| Target search | Page | Why we can win it |
|---|---|---|
| `coderabbit alternative` | `/vs/coderabbit` | High intent. Currently owned by review-farm sites with no product |
| `greptile pricing` / `greptile alternative` | `/vs/greptile` | Their per-review change made people search this |
| `ai code review too many comments` | blog post | Real complaint, almost nothing written for it |
| `what does ai code review miss` | `/how-it-works` | Nobody wants to answer this. We do |
| `ai code review coverage` | `/how-it-works` | Close to no competition. It is our own idea |
| `cursor bugbot alternative` | later page | Their move to per-run pricing pushes people to search |
| `ai code review false positives` | blog post | Big search volume, poor existing answers |

**If a competitor will not write the page because the honest answer embarrasses them, that is
the page to write.**

## Titles and descriptions

Under 60 characters for titles, under 155 for descriptions.

| Page | Title | Description |
|---|---|---|
| `/` | QuantaMind — the code reviewer that says what it missed | We check the riskiest part of your pull request first, then list what we could not check. Free report on your own history. |
| `/report` | Free code review report on your own repository | We replay your last six months of pull requests and show where we would have pointed. No install, no credit card. |
| `/how-it-works` | How QuantaMind reviews a pull request | Four steps: read the history, rank the change, read the top properly, check the answer before you see it. |
| `/pricing` | Pricing — unlimited reviews from $19 per developer | Four plans. Unlimited reviews on all paid plans. No per-review charges. |
| `/security` | Security — where your code goes and what we store | Read on code, write on comments, nothing else. Bring your own key or run it yourself. |
| `/vs/coderabbit` | QuantaMind vs CodeRabbit — an honest comparison | Where CodeRabbit is stronger, where we differ, and who should pick which. |
| `/vs/greptile` | QuantaMind vs Greptile — per-review pricing compared | Greptile charges per review after 50. We do not. What else is different. |

## The basics, done once

- One `<h1>` per page, containing the words people search for.
- Real URLs, no `#` routing. Server-rendered HTML, not an empty page filled in by JavaScript.
- `sitemap.xml` and `robots.txt`. Submit to Google Search Console on day one.
- `Organization` and `FAQPage` structured data on home and pricing.
- Page loads in under two seconds on a phone.
- Every page links to `/report`.

## What to publish, and how often

**One post a month, and only when there is something real.** A blog nobody reads costs
credibility; a blog with four honest posts builds it.

Write these four first:

1. **What we could not measure** — the things that came back null. Nobody publishes this, and
   it is the most linkable thing you will ever write.
2. **Why your AI reviewer will not tell you what it skipped** — the argument, in plain words.
3. **What we learned reading 25 repositories' history** — findings only, no method.
4. **Why we charge per seat when everyone else moved to per review** — this one gets shared.

## Where to be, besides Google

- **Hacker News** — the honest-numbers post, not the launch post.
- **`r/ExperiencedDevs`, `r/programming`** — answer the noise complaints. Do not advertise.
- **Dev.to and Lobsters** — repost the findings.
- **GitHub Marketplace** — a real listing. People search inside it.
- **G2 and Capterra** — only once you have five customers who like you.

---

# LinkedIn

## One-liner for the company page

> **We build the code reviewer that tells you what it did not check.**

Three others, if that one does not fit:

- *We read the risky part of your pull request properly, and say what we skipped.*
- *Every AI reviewer reads your whole change at one depth. We decide where to look first.*
- *Code review that shows its coverage, not just its comments.*

**Use the first.** It is one idea, eleven words, no jargon, and it is the thing competitors
cannot say back.

## Company page "About"

> Teams now write more code than they can read, and AI reviewers answer that by commenting on
> everything at the same depth. The result is noise, and worse, silence you cannot read — when
> the tool says nothing about a file, you cannot tell if the file is fine or if it was never
> really checked.
>
> QuantaMind picks the riskiest part of each change and reads that part properly. Then it
> prints what it could not check.
>
> We do not claim to find more bugs than anyone else. We claim to tell you where we looked.

## Founder headline

> Building QuantaMind — the code reviewer that tells you what it did not check.

---

# What never goes on the website

These are the things that took real work to find. On the site they become a competitor's
weekend project. **None of them are needed to sell — the free report proves the claim without
explaining it.**

| Never publish | Why |
|---|---|
| **What the ranking is actually built from** | This is the product. "Your repository's history" is all a customer needs. The specific signal is the thing to protect |
| **The unit we rank at, and why** | Choosing this correctly took the longest and it is invisible from outside |
| **How we decide whether to speak at all** | The rule that keeps us quiet on most pull requests. Easy to copy once described |
| **How we link a later fix back to the change that caused it** | Standard practice here is wrong most of the time. That we know this is worth more than saying it |
| **How the budget is split across a change** | Directly reveals cost structure and lets a competitor price against us |
| **What a review costs us** | Invites a price war we would rather have on value |
| **Our accuracy numbers** | Two reasons. They tell a competitor what to optimise, and a single number invites a fight over method. **Hand the customer their own number instead** — that is more convincing and gives nothing away |
| **Which model, at what setting** | Free tuning advice for anyone reading |
| **Customer names, without written permission** | Obvious, and people still get it wrong |

**The line to hold:** describe **what the customer gets**. Never **how it is worked out**.

And when someone asks for the benchmark, the answer is a better one than a number:

> *We do not publish a benchmark. Benchmarks are chosen by the vendor. Give us a repository and
> we will run it on your history, and you can check the answer yourself.*

That sentence sells better than any figure, and it gives away nothing.
