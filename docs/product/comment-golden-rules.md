# The golden rules of the comment

**What a QuantaMind pull-request comment may contain, in what order, and what it may never say.**
Written 2026-08-31 after reading what Qodo and Greptile actually post, what developers say about
those comments, and our own measurements of ourselves. Every rule names its evidence. A rule
without evidence is a preference and does not belong here.

**The comment is the product.** Nine of ten layers exist to produce it, and a developer waiting to
merge sees nothing else. `docs/product/publishing-rules.md` governs what may be said in public;
this governs what is worth saying at all.

---

## What the competition posts

| | **Qodo** | **Greptile** | **us, before this** |
|---|---|---|---|
| Opening | model summary of intent, tags, review-time estimate | plain-language summary | verdict line |
| A score | severity per finding, category, quality-impact label | **confidence 0–5**, per finding too | none |
| Per file | file-level change overview | **files changed & issues, in the open** | a folded list of paths |
| Intent | model-written | model-written | the author's own words |
| Diagrams | architecture | sequence / ER / class / flow, by change type | none |
| Per finding | description, code ref, relevance ⭐⭐⭐, the rule involved, agent prompt, committable fix | P0/P1/P2, Logic/Syntax/Style, suggested diff | claim + line |
| Footer | — | review counter, commit link, re-run button | — |

Sources: [Qodo, anatomy of a finding](https://docs.qodo.ai/code-review/comment-anatomy),
[Greptile, anatomy of a review](https://www.greptile.com/docs/code-review/first-pr-review).

**They are ahead of us on structure and we should say so.** The file-by-file breakdown, the
per-finding category, the committable fix and the re-run affordance are all good, and none of them
costs honesty. Taking them is not imitation; refusing them because a competitor got there first
would be.

---

## The rules

### 1. Every line must be actionable, or it goes

The most-cited complaint about human and machine review alike is **"47 comments about variable
naming while missing actual logic bugs"**
([DEV](https://dev.to/itsiqbal/stop-nitpicking-simplifying-code-reviews-for-greater-impact-2jbk)).
Greptile's published quality is largely **a suppression filter** — we removed the sentence banning
style, formatting, naming, test coverage and documentation from their prompt and re-ran the
benchmark: **270 extra comments, 21 real, 238 noise**
(`docs/product/reviewer/greptile-gap-analysis.md`).

**A comment nobody acts on is worse than no comment**, because it teaches the reader to skip the
next one.

### 2. Publish a selection, never everything generated

Qodo generates up to nine suggestions, **scores every one, and publishes about three**. We generate
up to twelve and publish twelve — **we have no scoring stage at all**, which
`docs/product/reviewer/qodo-mechanism.md` names as the single largest structural difference between
the pipelines. They emit **152 comments across 50 pull requests to our 194, and find 106 real
issues to our 79.**

**Volume is not coverage.** It is the thing that makes coverage unreadable.

### 3. Nothing carries a number we have not measured

Greptile ships a 0–5 confidence per review and per comment. **We measured ours: findings are 25.0%
correct**, and `docs/plans/preregistrations/reviewer/design14-model-lever-preregistration.md` shows
the generator cannot rank its own output — a same-family judge agreed with a careful rater on
**34.9%**. A confidence score from us would be a number we have specifically disproven our ability
to produce.

`render/comment.py` already states it: *no severity we cannot calibrate, no confidence we have not
measured.* **The honest substitute is a record of what ran**: a count of the customer's own declared
rules, checked and passed, which they can re-run on the same commit themselves.

### 4. What was not checked is stated — and outside evidence says this makes reviewers better

This is the rule most likely to be argued away, so it carries the most evidence.

**Automation complacency:** operators detect only **~30% of a system's errors when it appears
consistently reliable, against ~75% when its failures are visible**
([Atomic Robot, review fatigue](https://atomicrobot.com/blog/ai-review-fatigue/)). A tool that
hides its edges does not reassure a reviewer — **it degrades them**, and the degradation is
invisible from inside.

Teams on large repositories report **30–50% of Greptile's findings need manual triage**
([daily.dev](https://daily.dev/posts/coderabbit-vs-greptile-vs-vercel-agent-2026-review--pn3zvabm2))
— a reader who cannot see the tool's limits has no way to calibrate that.

And it is what this product is: `serve/cli.py` describes it as *"a code reviewer that reports what
it did not check."*

**But the WORDS are not the number.** "53 not reviewed" says *untouched* when every one of those
files was ranked and checked against the customer's rules. Stating scope is mandatory; frightening
people with it is a defect. **Lead with what every file got.**

### 5. The comment is about their code, never about our method

`publishing-rules.md` never-publishes what the ranking is built from and how the budget is split.
This rule goes further: **the words "ranked", "history", "budget", "decile" and "percentile" appear
nowhere a customer can see them**, because a developer opening a pull request wants to know what
happened to their change, not how we decide.

Enforced by `tests/unit/layers/render/test_never_our_method.py`, which renders through `comment()`
so a leak in any block fails — three leaked at once and each was individually defensible.

### 6. Four things, not forty

Working memory holds **about four items**, and review performance decays after roughly 30 minutes
and past ~400 lines ([Atomic Robot](https://atomicrobot.com/blog/ai-review-fatigue/)).

**A section a reader must hold in their head is a cost.** Caps are stated in the modules that own
them, and every cap prints its remainder rather than truncating in silence.

### 7. A parser's claim outranks a model's, and ordering says so without a heading

A rule the customer declared, checked deterministically, can be **asserted**: they can re-run it on
the same commit and get the same answer. A model finding at 25.0% correct is **a claim to check**.
`types/rule.py` derives `Provenance` from the check so a model-judged rule cannot claim a parser
verified it, and that distinction is carried in the audit trail a compliance reader queries.

**IN THE COMMENT IT IS CARRIED BY ORDER, NOT BY A HEADING, AND THAT IS A DECIDED POSITION.**
`render/blocks/found_block.py` used to print two headed sections — "found by a parser, these are
facts" and "found by the model, a reading" — and dropped them: *a developer deciding whether to
look at line 84 does not act on which of our components produced the line, and a heading explaining
our internals is the thing they scroll past.* That is rule 5 applied to rule 7. Violations come
first, they name the customer's own rule by id, and the reader can tell.

**This is still the only thing we sell that the competition does not have.** Greptile and Qodo both
score every finding on one scale; we have two kinds of claim and only one of them is assertable.

### 8. A claim carries the quote it is about, not a line number

**Qodo does not ask the model for a line number. It asks for a quote**
(`docs/product/reviewer/qodo-mechanism.md`). Ours asked for a line, and **87.3% of claims that quote
code quote code absent from the line they cite.**

### 9. The comment does not demand a reply

*"AI comments should be suggestions; if a developer dismisses one with a reason, that's fine — don't
create a process where every AI comment needs a response"*
([NexaSphere](https://nexasphere.io/blog/ai-code-review-tools-guide-2026)). Nothing we post asks a
question the author must answer, and nothing blocks on a model's opinion —
`verify/blocking.py` gates the status check on `Provenance.PARSER` only.

---

## The order, and why

1. **Verdict** — one line, the only line some readers act on.
2. **What this change is for** — the goal and the tickets behind it.
3. **Worth checking** — model findings, each anchored to a quote, worded as claims.
4. **Against the rules you declared** — deterministic verdicts, asserted, rendered unlike 3.
5. **This code already exists somewhere else** — D2c, a parser's claim.
6. **The file table** — every changed file, what changed in it, and what was found there.
7. **Scope** — what every file got, and how many were read line by line.

**3 before 4 is deliberate and uncomfortable.** The findings are the least reliable thing here and
they sit above the most reliable thing. They are there because a bug is what the reader came for,
and they are worded so that being wrong costs the reader a glance rather than their trust.

## What we are not taking, and why

- **A confidence score.** Rule 3.
- **A source/test split in the file table.** Tried, then subsumed: the reason to group tests was
  that developers skip them, and the signal they were actually skipping on is *nothing was found
  here* — which is what the fold means now. A test file with a real finding stays in the open,
  where a source/test split would have buried it.
- **Diagrams.** Greptile picks a diagram by change type; we have no measurement that a diagram
  changes what a reviewer finds, and it is a large surface to maintain on a guess.
- **A model-written summary of intent as the opening.** The author already wrote what the change is
  for, and their sentence is the one the review is measured against. A paraphrase moves the target.
- **Agent prompts and committable fixes.** Both are good and both assume the finding is right.
  At 25.0% correct, a one-click apply is a one-click defect. **Revisit when the correct-rate does.**
