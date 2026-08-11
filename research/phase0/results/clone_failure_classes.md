# Clone failures, separated by class — and one class is not attrition at all

**Snapshot taken mid-walk at 52 of 200 repositories. 8 clone failures.**

Written from the run log rather than the journal, because the journal *cannot* record
the distinction: it stores one `stage` cell per row, and
`research/phase0/src/phase0/pilot/covariates.py` `clone_failure_stage` produces the
WRONG value for one class. The journal schema is frozen while the walk runs
(`research/phase0/src/phase0/pipeline/resume.py` parses by column index), so this file
is the record until the walk lands.

## The defect: a missing binary on this machine is recorded as a missing repository

`clone_failure_stage` decides with one substring test:

    return "repo_gone" if "not found" in str(exc).lower() else "clone_timeout"

The string `git-lfs: command not found` contains `not found`. **git-lfs is not
installed on this machine**, so two repositories were recorded as *the repository no
longer exists* — a fact about the world — when the fact is about us. This is the
harness-failure-wearing-a-corpus-label class, found for the fourth time.

Its own docstring states why the two must never be pooled: *"A repository that no
longer exists selects on nothing and has no size to measure."* **That is now false for
two of the three rows in that bucket.** git-lfs use correlates with large binary
assets, so a size-selective failure lands in the bucket DEFINED as size-free — and
biases the size-bias bound in the direction that hides it.

**WITHDRAWN: "probably fully analysable" was an assumption, not a finding.**
`fatal: <path>: smudge filter lfs failed` terminates the checkout at the FIRST LFS
object; every file ordered after it is absent from the tree whether LFS-tracked or not.
Reported failures show `Checking out files: 1% (60/5925)` — a percentage, not a file
list. Survival of a repository's `.py` files depends on their path order relative to the
first LFS asset. The tree is partial by an unknown amount and recoverability is
**untested**; `worktree.cloned` deletes the tree in `finally`, so `git status` on these
two needs a re-clone.

**Established from the code, not inferred:** a partial tree cannot understate an
ADMITTED record in this walk. Every pilot derivation reads the object database —
`changed_python_files` is `git diff --name-only`, `touched_line_ranges` is
`git diff -U0`, `source_at` is `git show <sha>:<path>`. And `git clone` runs under
`check=True`, so the non-zero exit raises `CloneFailed` and the tree is removed: the
repository is excluded whole, never admitted partially.

**The EXPOSURE pass has neither protection.** `run_pipeline.one_pr` uses
`worktree.at_commit`, which materialises a working tree, and `measure` reads it via
`scope.resolve` off the filesystem. A partial checkout there understates the exposure
denominator silently, in the arm that has not run.

`ENVIRONMENT.lock` does not mention git-lfs, so nothing declared it a dependency and
nothing checks for it.

## The four classes

| class | the truth is about | recoverable | count |
|---|---|---|---|
| `clone_timeout` | OURS — our bound, their size | maybe — a longer bound, or a shallower clone | 3 |
| `transport_failure` | OURS+WORLD — network | **YES** — retry; nothing about the repo failed | 3 |
| `git_lfs_absent` | HARNESS — this machine | **YES** — install git-lfs, re-walk these repos | 2 |

## Every failure, and what the pipeline called it

| repository | true class | recorded as | git said |
|---|---|---|---|
| `AMICI-dev/AMICI` | `git_lfs_absent` | `repo_gone` **WRONG** | clone failed: AMICI-dev/AMICI: git-lfs filter-process: git-lfs: command not |
| `Azure/azure-sdk-for-java` | `clone_timeout` | `clone_timeout` | clone failed: Azure/azure-sdk-for-java: clone exceeded 900s [16/200] Azure/ |
| `Azure/azure-sdk-for-net` | `clone_timeout` | `clone_timeout` | clone failed: Azure/azure-sdk-for-net: clone exceeded 900s [17/200] Azure/a |
| `BerriAI/litellm` | `clone_timeout` | `clone_timeout` | clone failed: BerriAI/litellm: clone exceeded 900s [24/200] Blaizzy/mlx-aud |
| `BoundaryML/baml` | `git_lfs_absent` | `repo_gone` **WRONG** | clone failed: BoundaryML/baml: git-lfs filter-process: git-lfs: command not |
| `FrameOS/frameos` | `transport_failure` | `clone_timeout` | clone failed: FrameOS/frameos: error: RPC failed; curl 56 Recv failure: Ope |
| `Hi-Dolphin/datamax` | `transport_failure` | `repo_gone` | clone failed: Hi-Dolphin/datamax: remote: Repository not found. fatal: repo |
| `HumanSignal/label-studio-ml-backend` | `transport_failure` | `clone_timeout` | clone failed: HumanSignal/label-studio-ml-backend: error: RPC failed; curl |

## What is still NOT separated: renamed versus deleted

A 404 from `git clone` cannot tell a renamed repository from a deleted one. The GitHub
API can — a rename redirects, a deletion does not. **A rename is recoverable and a
deletion is not**, so pooling them overstates permanent corpus loss. Not queried here:
it costs quota the walk is using, and throttling the walk would manufacture exactly the
size-selective `clone_timeout` attrition this file is trying to measure.

## Rate

8 failures across 52 repositories = **15.4%**. Held to 200 that is
roughly **31 repositories**. The split decides whether that is one
bound or three — and one of the three is not a bound at all, it is a machine to fix.

**Nothing here is corrected in the data yet.** The walk continues under the defect, and
these rows are reclassified from this file once it lands.
