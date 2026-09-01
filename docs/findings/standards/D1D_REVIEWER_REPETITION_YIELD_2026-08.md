# D1d's premise, measured before building: reviewers repeat, but thinly

**Date:** 2026-08-31. **Corpus:** `research/phase0/results/oss_review_comments.json` — 1,213 real
inline review comments from 8 public repositories, fetched for
`research/phase0/corpus/checkability.py`. **Model-free throughout.**

---

## The claim being tested

> **D1d Mine rules from past review comments.** Senior engineers repeat themselves, and the
> repetition IS the standard.

That is an empirical claim about real review comments, and it was measurable before writing any
D1d code. **It holds, weakly.**

---

## What was measured

Comments were grouped by repository, stripped of code spans, reduced to a content-word bag
(stopwords and words of ≤3 characters removed), and clustered within each repository at Jaccard
≥ 0.5 by union-find. No model was involved at any step.

**First pass, everything included:** 152 of 1,213 comments (12.5%) sat in a repeated cluster, 54
clusters total. **That number is not quotable and the inspection is why.** The largest clusters
were `nit: ```suggestion``` ` ×11, `done` ×6, `fixed` ×6, `Done` ×4, `ditto` ×4, `docstring` ×5,
`Nice` ×5, `Same as above` ×3. Repetition, and not one of them a standard.

**Second pass, acknowledgements and thin comments dropped** (a regex for `done|fixed|lgtm|nit|
ditto|thanks|…`, plus a floor of 6 content words): 1,213 → 746 substantive comments, and

| | |
|---|---|
| candidate rules (a substantive point repeated ≥2× in one repository) | **13** |
| repositories | 8 |
| **per repository** | **1.62** |

---

## Reading the 13, which is the part that matters

A cluster count is not a rule count. Of the 13:

- **~5 are genuine, generalizable standards.** The best is `huggingface/transformers`: *"we won't
  add X to the required dependencies, so there should be a test and a detailed error message"* —
  said three times about three different libraries (KyTea, NLTK, pythainlp). That is exactly what
  D1d describes. Also real: `cartography`'s *"has a paginator — use it"*, *"log an INFO-level
  message that this project is being synced"*, and *"move to ON CREATE SET as it will never
  change"*.
- **~4 are one reviewer restating themselves inside a single thread**, not a standard recurring
  across changes. `This PR has been added <link>` ×2 is character-identical.
- **~4 are change-specific**, generalizing to nothing: *"these can be moved to
  examples/custom-functions/group_ungroup.py"*, *"see <pull request> #866"*.

**So the honest yield is under one real standard per repository per ~150 comments.**

---

## A contamination this corpus carries

`research/phase0/corpus/human_attention.py` records that in this corpus **about a third of inline
comments are written by other AI reviewers**, which is why that experiment restricted itself to
pre-2022 pull requests. The comment records here carry `body`, `path` and `repo` and **no author**,
so that filter cannot be applied. Two of the 13 candidates read like machine output — *"Ensure that
`input_token_count` and `output_token_count` are initialized to 0 if they are None before
attempting to increment them"* — and mining a rule from another AI reviewer's comment would make
D1d a mirror rather than a miner.

**This is a limit of the measurement, not a result.** Re-fetching with authors, and excluding bot
accounts, would tighten it.

---

## What this changes about D1d

It resizes the row; it does not kill it.

1. **The output must be a proposal a human approves**, which the row already says. At ~1 rule per
   repository the cost of a wrong proposal is a human saying no, and that is affordable.
2. **The acknowledgement filter is not optional.** Without it the miner's headline number is
   `done` ×6 and the feature ships as noise. It belongs in the code, not in the analysis.
3. **≥2 occurrences is the floor, and it is not sufficient** — 8 of 13 clusters at that threshold
   were restatements or change-specific. Occurrences must be **in different pull requests** to
   count, which this corpus cannot verify because it carries no PR number.
4. **Nothing may claim a yield this measurement does not support.** "Learns your team's standards"
   is a fair description of ~1 rule per repository only if the number is said out loud.

---

## What would refute the design built on this

- A miner that proposes more than ~2 rules per repository on this corpus is finding noise, and its
  proposals should be read before its count is believed.
- A miner that proposes zero on `huggingface/transformers` is missing the clearest true positive
  in the corpus, and that repository is therefore the known-answer case.
