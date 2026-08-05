# `research/phase0/audit/` — one-off checks whose results are committed

Four scripts that produced numbers now recorded in
`docs/findings/PHASE0_PREREGISTRATION.md` "Detection stops reading the corpus, and the
exclusion stops evaporating" and in `results/`. They live here for one reason: the results
are committed, and a result whose method exists only in someone's shell history is not
reproducible. Same rule as `results/.gitkeep` — *if you are not willing to publish the
inputs, you do not believe the output.*

| Script | Writes | Answers |
|---|---|---|
| `verify_trunk_parent.py` | `trunk_parent_check.json` | is each resolved parent GitHub's `merge_commit_sha^1`? |
| `rebase_prevalence.py` | `rebase_prevalence.json` | how often would the resolver call a PR a rebase? |
| `rebase_structural.py` | `rebase_structural.json` | does a check that reads no message text agree? |
| `verify_rebase_parents.py` | `rebase_parent_check.json` | are the REBASE parents right — the only shape where that question has an answer? |

They are **not** part of the pipeline and nothing imports them. They are deliberately
outside `src/`, so they do not enter the package's import surface, the module-identity
check, or the per-directory caps that keep the measurement code small.

## Read them in that order, because each exists because the previous one was not enough

`verify_trunk_parent.py` compares the resolved parent against `merge_commit_sha`'s first
parent. Over a sample of 16 squashes and 3 merge commits that is **near-tautological** —
the resolver returns `merge^1` for both shapes by construction. Its real power is
narrower: it would catch a PR misrouted to REBASE, and none was.

`rebase_prevalence.py` then asks how often rebase occurs — but it applies the resolver's
own predicate to different data. Same predicate, so it measures how often the resolver
*would say* rebase, not how often one *happened*. It cannot see a real rebase whose
message was amended, which routes to squash and returns a wrong parent silently.

`rebase_structural.py` fixes that by reading no message text at all: GitHub's rebase-merge
rewrites committer information, so a rebase of N leaves N commits sharing one committer
timestamp and a squash leaves exactly one.

`verify_rebase_parents.py` finally verifies the parents themselves, against that
structural truth rather than against the rule being tested.

## Cost

API-only except the last, which clones three small repositories. No writes outside
`results/`. Re-running them costs a few hundred cached-or-cheap GitHub calls.
