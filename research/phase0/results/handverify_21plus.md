# Hand-verification: the three human-arm `parent_commit` failures at 21+ commits

The gradient check reported `still_rises_with_size: false` while the human arm's 21-plus
band failed at **25.0% (3 of 12)** against **1.96%** in the band below — a 12.8x jump,
`P(>=3 of 12 | pooled 3.23%) = 0.0060`. This verifies whether the resolver was RIGHT to
give up on those three.

**Verdict: all three failures were correct. A28 has no residual on large PRs.**

## The three

| pr_id | repo | commits | resolver said | shape (mine) | true parent | file sets match | verdict |
|---|---|---|---|---|---|---|---|
| 2462185471 | featureform/enrichmcp#16 | 27 | `parent_commit` | **undeterminable** | none — merge commit absent from the repository | n/a | **failure correct** |
| 2476323666 | featureform/enrichmcp#24 | 43 | `parent_commit` | **undeterminable** | none — merge commit absent from the repository | n/a | **failure correct** |
| 2476534203 | featureform/enrichmcp#26 | 45 | `parent_commit` | **undeterminable** | none — merge commit absent from the repository | n/a | **failure correct** |

## Why they are undeterminable

**All three are one repository.** The band-level rate is one project's history, not a
size effect across the corpus.

Measured live against GitHub, not from `data/gh_cache` — the cached merge SHAs were then
checked against the API and matched exactly, so staleness was not the issue, but that is
only known because it was checked:

- GitHub **resolves** all three merge commits by SHA and reports one parent each.
- A fresh `git clone` contains **no such object** — `cat-file -t` fails for all three.
- `compare/main...{sha}` **fails** for all three: they are not in `main`'s history.
- `main` carries **83 commits**, against PRs claiming 27, 43 and 45 commits each.

**The history was rewritten after these merged** — force-push, branch recreation, or a
squash-and-reset. The merge commits survive on GitHub as unreachable objects and exist in
no clone, so no parent can be resolved from them by any method. The resolver reached the
same conclusion for the same reason.

This is Bird et al.'s Peril 4, *"git history is revisionist"*, arriving in this corpus. It
is the one peril from the canonical list that applies here, and it has a distinctive
signature: **GitHub's API returns metadata for a merge commit that no clone contains.**

## How this verification nearly produced the opposite answer

The first structural check printed `SHAPE=squash` for all three, with `ts_run=1`.

It was fabricated. The git helper returned `None` on failure, the caller wrote `or ""`,
and an empty result computed a committer-timestamp run of `1` — which reads as "squash" by
the rule. **Three failed lookups became three confident shape verdicts.**

It surfaced only because `parents=None` was printed beside it and was visibly wrong. Had
the check printed only its verdict, the record would say "all three squash-merged, parent
is `^1`, resolver has a residual" — the opposite conclusion, from no data at all.

The generalisable form, and the reason this section exists rather than a clean table:

> **Print the intermediate values, not only the verdict. A verdict is one field; the
> inputs that produced it are the check on the check.**

It is the same class the pipeline has now removed from five layers, reproduced inside the
verification written to test for it. `docs/CORRECTIONS.md` records the class.

## What this does not settle

- **`HISTORY_REWRITTEN` is not yet its own exclusion.** These three are counted at
  `parent_commit`, which is ambiguous between "the repository rewrote its history" and "our
  resolver has a bug" — the distinction this project has drawn five times elsewhere.
- **Incidence is unmeasured.** Three PRs in one repository is a curiosity. If the signature
  is spread across repositories it is a scope limit and belongs beside A40.
- The gradient check still reports `flattened` on this data, and would report `elevated`
  under a naive top-band fix. Neither is right: the band is single-repo.
