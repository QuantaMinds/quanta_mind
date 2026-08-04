# Contributing

> This project is a correctness product. A subtle bug here does not produce a crash — it
> produces a confident wrong answer that an AI agent then acts on. The process below is
> stricter than most repositories deserve. This one does.

---

## First hour

```bash
git clone <repo> && cd qmctx
just install          # uv sync, pre-commit, symlink CLAUDE.md -> AGENTS.md
just fixtures         # pinned real repos for live tests (large, one time)
just check            # must be green before you change anything
```

Then read, in this order: `ARCHITECTURE.md` → `docs/PROJECT_CONTEXT.md` →
`docs/VALIDATION.md`. Skip `docs/BUILD_PLAN.md` unless you are picking up a phase.

If `just check` is red on a fresh clone, that is a bug and it is the highest-priority
issue in the repository. Report it before doing anything else.

---

## One change, one branch, one PR

Every bug, feature or issue gets its own branch. No exceptions, no batching.

```
feat/<area>-<short-description>      new capability
fix/<issue-number>-<short>           bug fix, must reference an issue
chore/<short>                        deps, tooling, CI
docs/<short>                         documentation only
spike/<short>                        throwaway exploration, never merged
```

Examples: `feat/resolve-celery-registry`, `fix/412-super-chain-dropped`,
`docs/validation-silent-failures`.

Enforced by `scripts/guard/check_branch_name.py` and by branch protection on `main`.
`main` is protected: no direct pushes, no force pushes, no merge without a green
`just verify` and one approving review.

### The flow

```bash
git switch -c fix/412-super-chain-dropped

# 1. Reproduce first. A fix without a failing test is a guess.
#    Write the test. Watch it fail. Only then write the fix.

# 2. Work in small commits.
just check                     # after every meaningful step

# 3. Before you push:
just verify                    # live data verification
just verify-determinism        # if you touched store/ or label/
just docs-sync                 # regenerate docs/CODEBASE.md, review the diff

git push -u origin fix/412-super-chain-dropped
gh pr create --fill
```

### Merge

Squash merge only. The PR title becomes the commit message and must read as a changelog
entry. Delete the branch on merge. Never merge your own PR.

---

## The PR description template

```markdown
## What changed
One paragraph. Reference file:line, do not paste code.

## Why
Link the issue. If there is no issue, explain why this could not wait for one.

## How it was verified
- [ ] `just verify` green — paste the summary line
- [ ] Live test asserts on real output (not a mock), at tests/live/...
- [ ] Golden file changed? If yes, explain *why the output changed* and why the new
      output is more correct. "Regenerated" is not an explanation.
- [ ] Coverage of the changed module did not decrease

## What could still silently fail here
Required. Answering "nothing" gets the PR sent back — everything can silently fail;
the question is whether you looked. Name at least one plausible failure and say why
you believe the current tests would catch it.

## Docs
- [ ] docs/CODEBASE.md regenerated
- [ ] Module docstrings updated where imports changed
- [ ] New rule added? It has an entry in .claude/settings.json $enforcement_map,
      or is tagged ADVISORY in AGENTS.md
- [ ] New way to fail quietly? Added to the table in docs/VALIDATION.md
```

---

## Review standard

A reviewer is accountable for the change, not just for reading it.

**You must run `just verify` locally before approving.** Reading a diff is not review on a
correctness product. If you approve without running it, and it breaks, that is on you.

**Reject on sight:**

- a test whose only assertion is `assert result` or `assert x is not None`
- a `try/except` that swallows and continues
- a fallback that fabricates data when a resolver fails — the correct behaviour is
  `Unresolved`, always
- a widened type or an `Any` added to satisfy mypy
- a golden file regenerated without an explanation of the delta
- a new module without a WHAT / WHY / IMPORTS docstring
- a change that raises a guard threshold instead of splitting the file

**Ask about, do not reject:** design disagreements. Write them down; if a rule in
`AGENTS.md` is wrong, argue it in the PR and change the rule. Silently working around a
rule is the only unacceptable response.

---

## Working with AI agents on this codebase

Agents are welcome. The rules are the same, plus:

1. **Plan mode first** for anything in `resolve/` or `label/`. Those layers decide what we
   claim to know. Write the plan to `docs/plans/<branch>.md`, have a human read it, then
   implement.
2. **The agent does not merge.** A human runs `just verify` and approves.
3. **Hooks are the contract, not the prompt.** `.claude/settings.json` runs the structural
   and convention guards after every write, so violations surface on the turn that created
   them. Do not disable them to move faster.
4. **Scope investigations.** "Read `resolve/frameworks/`" beats "understand the codebase" —
   the second floods context and produces confident nonsense.
5. **Attribution stays on.** Commits made with an agent keep their trailer. We are building
   a provenance product; we do not obscure our own provenance.

---

## Adding a rule

Rules live in three places and each has a cost:

| Place | Cost | Use when |
|---|---|---|
| `.claude/settings.json` hook | zero instruction budget, 100% enforcement | mechanical and checkable |
| CI guard (`scripts/guard/`) | CI minutes | checkable but slow, or repo-wide |
| `AGENTS.md` | **instruction budget — every line reduces adherence to every other line** | genuinely requires judgement |

Default to a hook. `AGENTS.md` is capped at 200 lines and the cap is enforced. If you want
to add a line there, you must either delete a line or justify the trade in the PR.
