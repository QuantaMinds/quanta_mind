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
