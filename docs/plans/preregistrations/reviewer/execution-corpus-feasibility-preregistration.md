# Pre-registration — can ANY corpus support the execution-grounding arm?

**Registered 2026-08-30, before the instrument was written and before any repository was read.**

## Why this exists

`docs/product/reviewer/why-the-correct-rate-is-low.md` establishes four things, and the fourth is
the reason for this document:

1. The correct-rate is **5.8%** under strict adjudication, and **no slice of any factor beats
   13.0%** at n ≥ 15.
2. **Every mechanism tried has been a filter** — anchor repair, structured context, a rejection
   filter, hunk expansion, three prompt-direction arms, three oracles, the isolated judge, the
   conversational architecture. They make it less wrong; none makes it more right.
3. **The perfect-filter ceiling is 16.7%.** Delete all 135 wrong findings and 72 remain, 12 of
   them correct. Nothing anyone deletes gets past that.
4. **The one mechanism that could raise the numerator is execution grounding**, aimed at the
   `TRACE` class — 17 of 45 wrong findings where the code was fully present and traced
   incorrectly. It is **UNTESTED, not refuted**.

`execution-grounding-preregistration.md` Step 0 ended that arm on this pool: **31% of findings
were about source a suite even names, against a 50% bar.** Seven of sixteen were about test files
themselves, where the suite that would adjudicate is the subject of the claim. It records what
would make it runnable — *"a corpus of semantic findings about source code covered by an existing
suite"* — and stops.

**This measures whether such a corpus exists before anybody builds one.** Step 0's lesson was that
a ceiling below a bar is worth knowing before the spend, not after.

## The question, stated so it can come back NO

> Over changes in repositories this project has never measured, what share of changed **source**
> files are named by an existing test file?

If no candidate repository clears 50%, execution grounding is not testable by this route at all,
and that closes the road with evidence instead of leaving it open with a hope.

## Corpus, fixed now

**Ten repositories, none of them among the 36 already burned** — the list is
`research/phase0/quote/corpus.py` and `scripts/guard/records/check_burned_corpora.py` enforces it.
A repository measured twice is a design tuned on its own test set.

Selection is by name before any measurement, on two stated properties: written in Python, and
carrying a test directory. Both are visible without cloning and neither is the outcome.

**As-of is fixed at the run and recorded.** A corpus drawn from the present cannot answer a
question about the future — `research/phase0/corpus_age.py` exists because that mistake was made
twice — so the window is stated in the result rather than left as "recent".

## The measurement

For each repository, over the last 200 non-merge commits:

- **changed files**, split into `source`, `test`, `config`, `other` by path, using the same
  reasoning Step 0 used: a claim about a test file cannot be adjudicated by that test.
- for each changed **source** file, whether **any** test file in the tree mentions its module
  name — the same proxy Step 0 used, so the two numbers are comparable.

**This is a proxy, and Step 0 called it one.** "A test names the module" is weaker than "a test
executes the line". It over-counts, which means a repository failing this bar cannot pass the
stronger one, and that is the direction that makes a NO trustworthy.

## Bars, fixed before the run

- **PASS** — at least three repositories reach **≥ 50%** covered source, the bar Step 0 used.
- **INCONCLUSIVE** — one or two reach it: enough to suspect, not enough to build a corpus on.
- **FAIL** — none do. Execution grounding is not testable by this route, and that is published.

## What would make me drop it regardless of the number

- The instrument cannot tell a test file from a source file on real trees. A known-answer check
  runs first: a repository whose layout is known must classify as expected, or the run is void.
- Fewer than 50 changed source files in a repository — the share would be noise.

## What this cannot show

**It cannot show the arm would work.** It measures whether the arm could be *tested*. A corpus
clearing 50% still has to be labelled, and the labelling is the expensive half — the protocol
forbids an agent doing it, which is why `research/phase0/src/phase0/findings/` exists.

**And it selects on adjudicability, not on truth.** Choosing changes a suite can speak to is a
legitimate corpus decision, declared here in advance; it does narrow what any later result would
mean, to covered source rather than to code in general. That limit travels with any number this
produces.

---

# RESULT — 2026-08-30. PASS: the corpus that Step 0 lacked does exist.

Ten repositories, none among the 36 burned, shallow-cloned at 200 commits. Nine measured; one
refused by the instrument, for a reason worth more than its number.

| repository | changed source | covered | share |
|---|---|---|---|
| typer | 329 | 321 | **98%** |
| scrapy | 190 | 178 | **94%** |
| celery | 256 | 233 | **91%** |
| pytest | 255 | 220 | **86%** |
| sphinx | 260 | 209 | **80%** |
| black | 61 | 35 | **57%** |
| python-telegram-bot | 268 | 91 | 34% |
| loguru | 21 | 12 | too few source files to read |
| tornado | 41 | 35 | too few source files to read |

**Six of nine clear the 50% bar. The registered bar was three, so this is a PASS**, and the
finding is specific: **the 31% that ended the execution arm was a property of that pool, not of
open-source Python.** A corpus of findings about source a suite can speak to is buildable.

## The instrument refused a tenth repository, and that is the useful part

`django-rest-framework` came back **0.0% of 76 changed source files** on the first run. It has one
of the most thorough suites in the ecosystem, so a clean zero was a broken comparison rather than
a result — `AGENTS.md` rule 14, and the fifth instance of this class in the project.

**The cause was `git-lfs` not being installed.** DRF's `.gitattributes` routes files through an
LFS filter; the checkout fails, `git clone` exits 0, and the working tree is left empty while
`git ls-tree HEAD` still lists 585 files including 154 Python ones. The instrument read an empty
tree as a repository whose tests name nothing.

`NoSuite` now refuses a clone with no test file at all, because **a share of zero over a real
suite is a finding about that repository and a share of zero over no suite is a finding about the
instrument.** The re-run refuses DRF by name instead of reporting it as 0%.

## What this does and does not license

**It licenses building the corpus.** It does not license the arm: this is the same PROXY Step 0
used — "a test names the module", not "a test executes the line" — and it over-counts. That
direction is deliberate, because it makes a FAIL trustworthy; it makes a PASS an upper bound.
A corpus built from these repositories still has to clear the stronger check per finding.

**And the expensive half is untouched.** These repositories can support the arm; the findings
still have to be generated and hand-adjudicated, and the protocol forbids an agent doing the
labelling. That is the cost this result puts a floor under, not one it removes.
