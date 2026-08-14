## What changed

One paragraph. Reference `file.py:42`, do not paste code.

## Why

Link the issue. If there is no issue, explain why this could not wait for one.

## How it was verified

- [ ] `just check` green — paste the summary line
- [ ] `just verify` green — paste the summary line *(the call-site census layer onward; not runnable yet)*
- [ ] Live test asserts on real output (not a mock), at `tests/live/...`
- [ ] Golden file changed? If yes, explain *why the output changed* and why the new
      output is more correct. "Regenerated" is not an explanation.
- [ ] Coverage of the changed module did not decrease

## What could still silently fail here

**Required.** Answering "nothing" gets the PR sent back — everything can silently fail;
the question is whether you looked. Name at least one plausible failure and say why you
believe the current tests would catch it.

## Docs

- [ ] `docs/engineering/CODEBASE.md` updated *(enforced by `check_docs_sync.py`)*
- [ ] Module docstrings updated where imports changed
- [ ] New rule added? It has an entry in `.claude/settings.json` `$enforcement_map`
      pointing at a real enforcer, or is tagged **ADVISORY** in `AGENTS.md`
      *(both directions enforced by `check_enforcement_map.py`)*
- [ ] New way to fail quietly? Added to the table in `docs/engineering/`VALIDATION.md` “The silent-failure suite”`

## Phase gate

- [ ] This change does not add product code under `src/quantamind/` beyond what the correlation test
      authorises. `docs/findings/PHASE0_PREREGISTRATION.md `PHASE0_PREREGISTRATION.md` “Results”` is still empty — if this
      PR implements a layer, say which filled Results section authorises it.
