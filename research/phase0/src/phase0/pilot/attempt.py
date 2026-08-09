"""One PR the pilot tried to admit, and the covariates attrition may track.

WHAT: The `Attempt` record -- what was tried, whether it was admitted, why not, and the
      covariates every later cross-tabulation reads.
WHY:  Split from `report.py`, which reduces attempts to metrics, because `journal.py`
      also writes and reads this type. A record shared by a writer and a reducer belongs
      to neither of them; leaving it inside the reducer meant the persistence layer
      imported the analysis layer to learn its own row format.

      Three of its fields are deliberately three-valued rather than boolean. `outcome`
      separates "clean" from "not scanned"; `merge_on_base` separates "not on the branch"
      from "could not check". Collapsing either to a bool forces the unknown case to
      impersonate one of the known ones, which is the failure this whole instrument keeps
      re-learning.
IMPORTS: nothing.
CONSUMED BY: pilot/report.py, pilot/run.py, pipeline/journal.py; tests/pipeline/.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Attempt:
    """One PR the pilot tried to admit, with the covariates attrition may track."""

    pr_id: str
    repo: str
    admitted: bool
    stage: str  # "" when admitted
    category: str  # "" when admitted
    commit_count: int
    # The CORPUS's claim about how many `.py` files this PR touched, never a measurement.
    # Verified against GitHub on seven rejections: the corpus said 104, 65, 40, 23, 17, 15
    # and 1; GitHub's own `changed_files` for the same PRs was 2, 9, 2, 9, ?, 5 and 1, with
    # ZERO `.py` among them. `mlflow#14364` is "Fix API reference link in preview" and
    # touches a CI config and a docs sidebar. Read it as the corpus's assertion and nothing
    # more -- `github_py_files` below is the measurement.
    corpus_py_files: int
    # None when derivation did not run or its result was never read. It was `0` for every
    # rejected row, which made "we never measured" indistinguishable from "we measured
    # zero" -- and the count of rows reading 0 was arithmetically identical to the count of
    # rejected rows, the same objects rather than merely the same total. Only a `no_python`
    # rejection genuinely derived zero, because `assemble.py`'s `if not derived` IS that
    # rejection; a `no_symbols` row cannot have, since that path runs only when `derived`
    # is non-empty, yet it recorded 0 all the same.
    derived_files: int | None
    changed_symbols: int | None
    # GitHub's own file list for this PR, recorded rather than discarded after use. With it
    # on the row, "did derivation find what GitHub says changed" is answerable from the run
    # instead of costing ~200 API calls per arm afterwards. None when the API did not
    # supply a list; `github_files_truncated` says whether the one it did supply was whole.
    github_changed_files: int | None = None
    github_py_files: int | None = None
    github_files_truncated: bool = False
    stars: int = -1
    # "broke" | "clean" | "" when the outcome was not scanned. Three states, not two:
    # an unscanned PR and a clean one must not be the same value, or the breakage rate
    # silently divides by the wrong denominator.
    outcome: str = ""
    # Whether the PR merged into the repository's default branch. 15.5% do not, and
    # those repositories have release processes -- so the split is a population
    # question, not just a bug's footprint.
    # "yes" | "no" | "unknown". Three states, like `merge_on_base` and for the same
    # reason: `default_branch` returns "" when a repository's `gh` lookup times out, and
    # as a bool that read `False` -- a MEASUREMENT of "merged into a non-default branch".
    # The off-default share is a population finding the analysis stratifies on, so a
    # failed lookup silently manufacturing off-default rows is the same shape as the
    # missing-`gh` crash, at one-repo granularity instead of all-repos. Fixed BEFORE it
    # produced a wrong number, which is the first time that has happened here.
    base_on_default: str = "unknown"
    # "yes" | "no" | "unknown": is the merge commit an ancestor of its own base branch?
    # Recorded at ADMISSION, on every attempt, because the outcome scan only sees PRs that
    # survived the gate -- agentops #811/#817/#818/#819 are all unreachable-merge cases
    # and all four were rejected at `no_python` first. Counting only at scan time would
    # report the post-filter residue and call it prevalence.
    merge_on_base: str = "unknown"
    # additions + deletions from the GitHub API. A20 pre-registers the file-set
    # disagreement rate by changed-lines QUARTILE; commit count and corpus file count are
    # correlates of size, not the variable named. -1 when the API did not supply it, so
    # "not measured" cannot masquerade as "a very small PR".
    changed_lines: int = -1
    # Which arm this PR is from, carried on EVERY row rather than assumed by the reader.
    # "" means a journal written before this column existed -- NOT MEASURED, never
    # "human". The 90-repo pilot was entirely human-arm and no artefact it produced said
    # so, which is why its breakage rate was compared against the agent reference for
    # weeks. `phase0.arm.verify` checks the claim against AIDev before the run starts.
    arm: str = ""
