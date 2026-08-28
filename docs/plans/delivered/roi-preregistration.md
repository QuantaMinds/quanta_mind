# The buyer's test — pre-registered before the run

**Every measurement so far scores the method. This one scores the purchase.** A business does not
buy a miss rate; it buys reviewer hours back, or fewer defects reaching production, or both. The
chain from our number to their money has never been measured and is written out here so the weak
links are visible before the result is.

**Written before the run. If the result misses these bars, the answer is no.** This project has
adjusted a threshold after seeing a number exactly zero times and that is the only reason any of
its figures are worth quoting.

---

## The chain, and which links are evidence

| link | status |
|---|---|
| 1. the ranking puts the file a later fix returns to in the top three | **measured** — 1.53% miss, 20 repos, 7,989 events, p = 1.3 × 10⁻¹⁴ |
| 2. reading three files instead of all of them saves real effort | **this run** |
| 3. the reviewer actually reads what we rank first | unmeasured — needs humans |
| 4. reading it, they find the defect | unmeasured — needs humans |
| 5. the defect does not reach production | unmeasured — needs a live deployment |

**This run tests link 2 only, and link 2 is the one that converts to an invoice without a human
study.** Links 3–5 need the thirty-day pilot. **No ROI claim built on this run may assert links
3–5**, and any deck that does is overstating what we know.

---

## What is measured

On the **twelve out-of-sample repositories** — the six of `defect_return_external.json` and the six
of `defect_return_third.json`, none used to develop the method — for every admissible change:

- **effort asked**: `min(3, n_files)` files read against `n_files` changed
- **catch rate**: share of changes where the top three include a file a later fix returns to
- the same two for the **alphabetical control** and for **reading everything**

Admissibility is copied from `research/phase0/external/defect_return.py`, unchanged: 2–12 `.py`
files, a fix-word commit within 90 days touching one of them. **Non-discriminating changes are
included**, unlike the headline run, because a buyer's pull requests include them.

**The size confound is checked, not assumed.** Effort is counted in files, and files are not equal.
If the top-ranked files are systematically the *largest*, reading three of nine saves less than the
file count suggests. A sample of events is re-read with `git show --numstat` and the ranked files'
line counts are compared against the unranked ones. **`--numstat` reads patch content, and a
blob-filtered clone is where this project lost four measurements, so the exit code is asserted and
a commit whose numstat file set disagrees with its `--name-only` file set is dropped and counted.**

---

## The bars

| # | bar | rationale |
|---|---|---|
| **B1** | effort reduction ≥ **50%** pooled | below half, "read these three" is not a workflow change and there is nothing to sell |
| **B2** | catch rate ≥ **95%** | the miss is what the buyer is exposed to; 1 in 20 is the most I would defend in a room |
| **B3** | catch rate beats alphabetical by ≥ **1.0 point**, McNemar p < 0.05 | without this we are selling `sort(filenames)` |
| **B4** | positive in ≥ **8 of 12** repositories | a pooled win carried by two repositories is a pooled win we cannot promise a new customer |
| **B5** | ranked files are **not** more than **25% larger** in changed lines than unranked | if they are, the file-count saving overstates the effort saving and B1 must be restated in lines |

**All five must pass.** Four of five is a fail, reported as a fail.

---

## What the result may and may not be used to claim

**May:** "A reviewer reading our top three files instead of the whole change reads X% less and
still lands on the file a later fix returns to Y% of the time, on twelve repositories the method
has never seen."

**May not:** any sentence containing "prevents", "reduces incidents", or "catches bugs". **Links
3–5 are unmeasured.** A file being read is not a defect being found.

**May not:** an absolute defect count. The outcome rule is a fix-word commit within 90 days and
**only 14% of those are genuine repairs**. The rule scores both arms identically so the
*comparison* holds; the *absolute* number does not.

---

## What could still make this wrong

**Effort is not linear in files.** Reading three files a reviewer already understands may cost more
than nine trivial ones. B5 checks size and nothing checks familiarity.

**The 90-day outcome window bounds the catch rate from below.** A defect fixed on day 91 counts as
no defect. This makes both arms look better and is not corrected.

**Nothing here says a reviewer would otherwise have read everything.** The honest comparison for a
buyer is against what they do today, which is unknown and probably already partial. Reading-all is
a *ceiling*, not the status quo, and must be labelled as one.

---

# The result — **FAILED**, four bars of five

Run: `research/phase0/external/reviewer_effort.py`. 9,600 admissible changes, 12 out-of-sample
repositories. Artefact: `research/phase0/external/reviewer_effort.json`.

| bar | result | |
|---|---|---|
| B1 effort reduction ≥ 50% | **28.9%** | **FAIL** |
| B2 catch rate ≥ 95% | 98.60% | PASS |
| B3 beats alphabetical ≥ 1.0pt, p < 0.05 | +1.73pt, McNemar p = 3.89 × 10⁻²³ | PASS |
| B4 positive in ≥ 8 of 12 repositories | **12 of 12** | PASS |
| B5 ranked files ≤ 1.25× the size of skipped | **0.93×** on 260 sampled changes | PASS |

**Four of five is a fail and is reported as a fail.** The bar was not adjusted after seeing the
number and must not be.

## Why B1 failed — the mechanism, not the excuse

**Two thirds of changes touch three files or fewer.**

| files touched | share | cumulative |
|---|---|---|
| 2 | 45.66% | 45.66% |
| 3 | 20.39% | **66.04%** |
| 4–12 | 33.96% | 100% |

Mean 3.57 files. **On 66.0% of changes a three-file budget asks the reader for everything** —
effort reduction is zero there by construction, and catch is 100% for the same reason.

**The bar was badly set, and that is an error in this document rather than in the result.** 50%
was written without first looking at the file-count distribution of the population it judged.
A bar chosen against an unexamined population is a guess wearing a threshold.

## What this does to the headline number

**The published 1.53% miss rate is arithmetically dominated by changes where missing is
impossible.** Pooled = (66% × 0%) + (34% × ~4.5%).

Restated on the changes where a three-file budget actually binds:

| policy | miss | effort saved |
|---|---|---|
| read everything | 0% | 0% |
| **top 3 by fix history** | **4.11%** | **50.3%** |
| top 3 alphabetically | 9.20% | 50.3% |

**The lift is three times larger there (+5.09 points, against +1.73 pooled) and so is the
absolute miss.** Both halves of that sentence must travel together.

**This is a caveat on how the number is quoted, not a retraction.** Both arms are scored on the
identical population, so the comparison holds and `QUANTAMIND.md` already names the pooled row as
the operational one. But **"we miss 1.53%" without "because two thirds of the time we ask you to
read everything" is a sentence that misleads a buyer**, and it is not to be used.

## What passed that is worth keeping

**B4 at 12 of 12** is the strongest consistency result the project has produced. **B5 came back
favourable and mildly surprising: the files we rank are 0.93× the size of the ones we skip**, so
a line-based effort saving is *larger* than the file-based one — measured only on binding changes,
since the sample requires a skipped file to exist.

**40 of 300 sampled commits were dropped because `--numstat` disagreed with `--name-only`.** That
is the blob-filtered-clone defect being caught by `patch_size.numstat` rather than absorbed. A
13% silent-truncation rate is exactly what voided four earlier measurements.

## The ROI arithmetic, with its assumptions exposed

200 pull requests per month. 34.0% bind → **68 affected**, 3.04 files skipped each.

| minutes per file reviewed *(assumed, not measured)* | hours saved / month | at $100/hr |
|---|---|---|
| 3 | 10.3 | $12,376 / yr |
| 5 | 17.2 | $20,627 / yr |
| 10 | 34.4 | $41,254 / yr |

**The cost of those hours: 2.8 changes per month where the returning file goes unread.**

**Minutes-per-file is an assumption and the range spans 3.3×.** Nothing here measures it, and the
whole dollar figure is linear in it. The first thing a pilot should instrument is review time per
file, not satisfaction.

## The re-run this earns, pre-registered now

**Population:** changes touching **four or more files** — the only ones where the policy does
anything. **Corpus:** repositories not among the 20 already used. **Bars:** B1 ≥ 50%, B2 ≥ 95%,
B3 ≥ 1.0pt with p < 0.05, B4 ≥ two thirds of repositories, B5 ≤ 1.25×.

**The subgroup figures above are POST-HOC and are a hypothesis, not a result.** They were computed
after seeing B1 fail, on the same data, and this project has recorded what happens when a subgroup
found that way is quoted as a finding.
