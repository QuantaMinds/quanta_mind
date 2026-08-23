# What we may and may not say in public

Kept when the site and blog drafts were deleted, because these are not drafts. Each rule below
exists because a specific sentence was written, reviewed and found to be wrong — the example is
part of the rule.

---

## Never publish these

A site is read by competitors before it is read by customers. Everything here took real work to
find, and none of it is needed to sell — **the free retrospective proves every claim without
explaining any of it.**

| Never publish | Why |
|---|---|
| **What the ranking is built from** | This is the product. "Your repository's own history" is all a customer needs |
| **The unit we rank at, and why** | Choosing it correctly took the longest and is invisible from outside |
| **How we decide whether to speak at all** | The rule that keeps us quiet on most pull requests. Trivial to copy once described |
| **That a stage of the pipeline runs without a model** | It explains the cost structure, which explains why the free retrospective is possible, which is the strategy. **Make the offer; skip the reasoning** |
| **How we link a later fix back to the change that caused it** | Standard practice here is wrong most of the time. That we know this is worth more than saying it |
| **How the budget is split across a change** | Reveals cost structure and lets a competitor price against us |
| **What a review costs us** | Invites a price war we would rather have on value |
| **The share of pull requests we comment on** | A tuned number. "Most get no finding" says enough |
| **How many repositories and changes we tested on** | Invites method questions and points at the source data |
| **Our accuracy, precision, recall or F1** | Two reasons. It tells a competitor what to optimise, and one number invites a fight about method. **Hand the customer their own number instead** — more convincing, and it gives away nothing |
| **Our own miss rate, on a public page** | Different from the rest of this list, and the line is subtle. **Say it in a room, never in print.** In conversation "the defect is in a unit we skipped about one change in eleven" is the strongest thing we can say, because no competitor will say theirs. Printed, it becomes a soundbite detached from the coverage line that makes it survivable — and it discloses the budget, which is mechanism |
| **Which model, at what setting** | Free tuning advice for anyone reading |
| **Customer names without written permission** | Obvious, and people still get it wrong |

**The line: say what the customer gets. Never say how it is worked out.**

When someone asks for our benchmark:

> *We do not publish one. Benchmarks are chosen by the vendor. Give us a repository and we will
> run it on your own history, and you can check the answer yourself.*

---

## How to write it

- **Say the thing, then stop.** No sentence exists to sound impressive. No "seamless",
  "revolutionise", "empower", "leverage".
- **Never claim to catch more bugs.** We do not, and the first customer to test it will find out.
- **The routing number is sayable, out loud, with the control attached — and it is the only one
  that has ever replicated.** *"Ranking the changed files by prior fix history and reading the top
  three missed 1.21% of the changes a later fix returned to; alphabetical ordering missed 3.12%.
  Six repositories we had never touched. n = 2,400, p < 0.000001."* **Say the control every time.**
  A miss rate without the thing it beats is the number a competitor quotes back at you, and this
  project has already withdrawn one figure for exactly that.
  **Quote the POOLED figure across all twenty repositories, never one repository's lift** — the
  alphabetical control's strength swings 3.4 points on directory layout alone, so a single repo's
  number is mostly a fact about folder naming. The defensible pooled statement: **history misses
  1.53%, alphabetical 2.97%, exact chance 3.37%, n = 7,989, McNemar p = 1.3e-14, 17 of 20
  repositories positive.** Against chance the ranker is **+1.84 points**, so the
  history-versus-alphabetical figure quoted in the pitch is the conservative one.
  **Quote the conservative effect size when a single number is needed: excluding the strongest
  repository the lift is +0.90 points rather than +1.92.** Both are true; the smaller one is the
  one that cannot be attacked.
  **And two caveats travel with the number or it is being misquoted.** *"Changes a later fix
  returns to"* is an **outcome-rule proxy, not a defect oracle** — a fix-word commit within 90 days
  touching the same file — and **only 14% of the pairs it admits are genuine repairs**. The
  measurement also takes the **earliest 400 events per repository**, so it describes early
  repository history and says nothing about a mature codebase. **Neither caveat may be dropped
  because a sentence reads better without it.** This is the drift class that produced the $15
  figure and the granularity row: a number survives, its conditions do not, and nobody notices
  because the sentence still parses.
- **Never imply our findings are correct — that has now been measured, and they are not.** Two
  blind raters put **66.7% and 74.2% of published findings wrong** (κ = 0.82 on the binary), with
  **3 of 66 correct by consensus**. Nothing may be said or implied about the quality of what this
  reviewer finds, and the review half is not shipped. **The dangerous sentence is not a boast, it
  is the true one that gets completed for us:** a reader who hears *"we tell you what we could not
  read"* finishes it as *"…so what they did read, they got right."* **Whenever the coverage line
  is stated externally, that inference has to be closed off in the same breath**, because it is
  the one a customer will make unprompted and it is the one the evidence contradicts.
- **Never quote a competitor's ONLINE precision beside one of our own numbers.** Martian's
  leaderboard precision is *behavioural* — did the developer make the change — and our adjudication
  measured whether a claim is *true and anchored*. They are different quantities, and the
  comparison was made internally before it was caught. That band is quotable **about them**, never
  as a backdrop for us.

  **AMENDED — the offline layer is comparable and we have entered it.** Martian's offline layer
  scores every tool against the same 50 pull requests and the same human-verified issue lists. We
  ran our reviewer through it, calibrated our judge against theirs first, and may quote those
  figures side by side: **Greptile 56.5%, ours 43.6%, CodeRabbit 36.5%.** Three conditions attach
  and all three must travel with the numbers. **One:** offline and online figures must never appear
  in the same table — 36.5% and 49.2% are the same tool on different layers and different dates.
  **Two:** our arm was judged by its own model family and a blind out-of-family check put our
  over-match rate at 15.0% against 5.0%, so the honest reading is *at level with CodeRabbit, behind
  Greptile* and never *better than CodeRabbit*. **Three:** none of it says our findings are correct
  — this benchmark never checks whether a claim is anchored to the line it cites, which is where
  87.3% of ours fail. → `docs/product/reviewer/greptile-gap-analysis.md`

- **When two measurements of the reviewer disagree, the stricter one governs shipping.** Martian's
  offline layer asks whether a comment matches a known issue; our adjudication asked whether the
  claim is true of the code AND anchored to the line it cites. **43.6% there, 5.80% here. Both are
  real and they answer different questions.** A comment naming a real defect while pointing at the
  wrong line is worth nothing to the developer who opens the file and finds nothing — and the judge
  that scored 43.6% never had to open the file. **The review half stays stopped on the 5.80%, and
  no benchmark that does not check anchors can reopen it.**

- **Never present benchmark position as a product goal.** Removing our nit suppression closed and
  reversed the Greptile gap while adding 238 false positives for 21 true ones — **a marginal
  precision of 8.1%**. This gold set and the product are opposed on nits, and Greptile's own
  quality filter exists to delete what it rewards. A better rank bought this way is a worse
  product, and the exchange rate is measured.
- **Concede only what is true, and detection is not one of the true things.** Honesty is not
  agreeing with whatever the market assumes. A page saying *"use them if you want the most bugs
  found"* hands over the one contest nobody has won, on no evidence, and turns us into the lite
  option. Competitors verifiably have features, maturity, integrations, bigger free tiers —
  concede those without flinching. On detection the honest line is that **nobody has shown it,
  them or us.**
- **Never write our value as a niche remedy.** *"If your team has stopped reading the comments"*
  tells everyone who has not yet hit that pain that this is not for them. Knowing what was
  examined is what any team signing off on a merge needs.
- **Never offer a trade the product does not make.** *"You care more about coverage than finding
  one more bug"* implies choosing us costs bugs. It does not.
- **No performance claim without a measurement.** *"Reviews finish in under two minutes"* is the
  easiest sentence on any site to write and we have never timed a review. A speed claim is
  checkable on day one, which makes it the fastest way to lose the trust everything else is
  built on.
- **Lead with the problem the reader's current tool leaves them holding.** Every visitor already
  has a reviewer. Opening by ranking vendors asks them to re-run a decision they have made.
  **Concede the competitor's strengths after that, never before** — conceding first reads as
  apologising for existing.
- **Every button names its destination and what happens.** *"See both on your own history"* told
  a reader nothing: whose history, found where, costing what. A button is a promise about the
  next screen.
- **Name the weakness before the reader does.** It is the only thing on the site a competitor
  cannot copy in a week, because copying it means admitting the same weakness.
- **Numbers only where we would defend them under questioning.** If a number needs three
  sentences of caveat, it belongs in the report we hand the customer, not on a page.

---

## Citation rules

This project has already had one fabricated statistic survive into a draft.

- **Link the primary source, never a summary of it.** No citing a blog that cites a paper.
- **Read the live page while writing.** Not from memory, and not from a search summary — both
  have been wrong here.
- **Quote the number the source actually reports**, with its sample size.
- **Vendor benchmarks are marketing and are cited as marketing**, including when they flatter us.
- **Carry the caveats the source carries.** A null published without its own limitations is the
  same overclaim as a positive one published without them.
- **Re-verify competitor pricing and benchmark figures on the day of publishing.** They move,
  and a stale number in a post about someone else's numbers is the worst error available.
- **If a claim cannot be sourced, it is cut**, not softened.
- **Carry the citation inline, at the moment the number lands.** Source name, report year, the
  exact metric, and the date checked — in the sentence, not in a footnote and not in a
  reconciliation pass run later. **A reconciliation pass catches drift that already exists; it
  does nothing about drift introduced afterwards**, which is how a 2021 figure came to sit beside
  a 2026 one in this repository *one commit after* the pass built to catch that was written. It
  is the same argument as the drop-rate counter and the shadow ranker: a check that runs once is
  not a check. This one has to run where the number enters.
- **A load-bearing figure carries a re-check date, not only a checked date.** The next drift is
  not a wrong citation — it is a **correct one that goes stale**. CodeRabbit's leaderboard claim
  was accurate the day it was written and superseded five months later. *Date checked* records
  when someone looked; it says nothing about when the fact expired. Anything the argument rests
  on gets a cadence attached, or the same failure recurs with a clean audit trail behind it.
- **Name the metric, not just the source.** "LinearB says pickup is 40–60% of cycle time" failed
  here because three LinearB datasets are in circulation and the figure traced to *idle share of
  lifespan*, reported as a distribution across cohorts rather than a mean. The source was real,
  the year was wrong, and the metric was a different quantity.
