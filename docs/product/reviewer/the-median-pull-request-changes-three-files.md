# The top-3 hit-rate study is not affordable — and finding that out said something about the product

**The pre-registration's own floor check fired before any hit rate was computed, which is what it
was for.** Second time a gate has closed a road before the experiment ran.

## What was checked, in the order the pre-registration demanded

### 1. The control: is GitHub's file order alphabetical?

**29 of 29 pull requests with ≥3 changed files: the files API returns them in alphabetical order.**

**That is the API's order and not the rendered page's**, which cannot be verified from here — GitHub
ships file-tree navigation and sort controls, and the default may vary or be user-set. So the
control is *alphabetical*, with the caveat stated rather than hidden: **if the rendered default is
not alphabetical, the control measures the wrong thing.**

### 2. The floor: how many pull requests survive a top-3 study?

**The median pull request in the corpus changes three files.**

| floor | survive of 173 | share |
|---|---|---|
| ≥ 3 files | 111 | 64% |
| ≥ 5 | 49 | 28% |
| **≥ 8** | **22** | **13%** |
| ≥ 10 | 11 | 6% |

**At the ≥8 floor, 22 pull requests remain and 10 of them come from two repositories.** That is not
a study — it is a study of `tornado` and `starlette`.

### 3. Feasibility on a different corpus

The coverage filter was built for execution grounding, so a hit-rate study should not inherit it.
Scanning the largest, most active Python repositories instead — django, home-assistant, airflow,
pandas, numpy, scikit-learn, ansible, matplotlib:

| | of 148 merged pull requests |
|---|---|
| ≥ 8 changed files | 9 = **6%** |
| ≥ 8 files **and** carrying inline review comments | 3 = **2%** |

**A 170-pull-request study needs roughly 8,400 merged pull requests scanned.** That is a scraping
project against rate limits, not a three-day data pull.

## The finding that is about the product, not the experiment

**The median pull request changes three files.** On public Python repositories, "forty files land in
your queue and you don't know where to start" is **the tail, not the median** — pull requests with
eight or more changed files are about 6% of merged work.

That does not kill the ranker. It narrows one framing of it:

- **On a three-file pull request a top-3 ranking is degenerate** — the reviewer reads everything,
  and the ranking's only content is "skip the lockfile".
- **The ordering value concentrates in large pull requests**, which are roughly 6% of merged work —
  close to the firing gate's own 8–15%, which may not be a coincidence.
- **It still costs nothing on the other 94%**, and a fact about history cannot be false the way a
  claim about code can. The reframing survives; *"every PR, every day"* survives; *"you don't know
  which of forty files to read"* does not describe the median day.

**This is measured on public Python repositories and a customer's pull requests may be shaped
differently** — a monorepo with generated files would look nothing like this. It is a reason to
measure their distribution on day one, and a reason not to build the pitch on a file count nobody
has checked.

## What the study could still be

**Not top-3, which is degenerate at a median of three files.** A rank correlation over all changed
files has no floor problem and uses the 111 pull requests with ≥3 files — and it must still carry
**diff-line count as a covariate**, because reviewers comment more where there is more to comment
on and hot files are often large ones.

**And it would still not settle the orientation thesis.** Concordance with where attention already
went means the ranking is redundant; discordance means it is either wrong or pointing where humans
systematically fail. **Both directions are ambiguous for the product**, which is why this is a
redundancy-and-convergence check and why a null — indistinguishable from alphabetical — is the only
outcome that decides anything on its own.
